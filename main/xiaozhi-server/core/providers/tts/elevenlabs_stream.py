"""
ElevenLabs TTS Provider
Supports all three streaming modes: DUAL_STREAM (WebSocket), SINGLE_STREAM (HTTP streaming), NON_STREAM (HTTP complete).
Supports voice cloning (IVC) and multiple models.
"""
import os
import uuid
import json
import queue
import base64
import asyncio
import traceback
import aiohttp
import requests
from typing import Callable, Any, Optional
import websockets
from core.utils.tts import MarkdownCleaner
from config.logger import setup_logging
from core.utils import opus_encoder_utils, textUtils
from core.utils.util import check_model_key
from core.providers.tts.base import TTSProviderBase
from core.providers.tts.dto.dto import SentenceType, ContentType, InterfaceType

TAG = __name__
logger = setup_logging()


class TTSProvider(TTSProviderBase):
    def __init__(self, config, delete_audio_file):
        super().__init__(config, delete_audio_file)
        self.ws = None
        self._monitor_task = None
        self.activate_session = False

        # Core configuration
        self.api_key = config.get("api_key")
        self.voice_id = config.get("voice_id")
        self.model_id = config.get("model_id", "eleven_flash_v2_5")

        # Voice settings
        self.stability = float(config.get("stability", 0.5))
        self.similarity_boost = float(config.get("similarity_boost", 0.75))
        self.style = float(config.get("style", 0.0))
        self.use_speaker_boost = config.get("use_speaker_boost", True)
        if isinstance(self.use_speaker_boost, str):
            self.use_speaker_boost = self.use_speaker_boost.lower() == 'true'

        # Output format - pcm_16000 to match other providers
        self.output_format = config.get("output_format", "pcm_16000")
        self.language_code = config.get("language_code", "")

        # Interface mode - determines which streaming method to use
        interface_mode = str(config.get("interface_mode", "dual_stream")).lower()
        if interface_mode == "single_stream":
            self.interface_type = InterfaceType.SINGLE_STREAM
        elif interface_mode == "non_stream":
            self.interface_type = InterfaceType.NON_STREAM
        else:
            self.interface_type = InterfaceType.DUAL_STREAM

        # WebSocket connection management (only for DUAL_STREAM)
        enable_ws_reuse_value = config.get("enable_ws_reuse", True)
        self.enable_ws_reuse = False if str(enable_ws_reuse_value).lower() == 'false' else True

        # Opus encoder for 16kHz PCM to Opus conversion
        self.opus_encoder = opus_encoder_utils.OpusEncoderUtils(
            sample_rate=16000, channels=1, frame_size_ms=60
        )

        # Build API URLs
        self._build_api_urls()

        # PCM buffer for SINGLE_STREAM mode
        self.pcm_buffer = bytearray()

        # Validate API key
        model_key_msg = check_model_key("TTS", self.api_key)
        if model_key_msg:
            logger.bind(tag=TAG).error(model_key_msg)

        logger.bind(tag=TAG).info(
            f"ElevenLabs TTS initialized | "
            f"mode={self.interface_type.value} | "
            f"voice_id={self.voice_id} | "
            f"model={self.model_id} | "
            f"output_format={self.output_format} | "
            f"ws_reuse={self.enable_ws_reuse}"
        )

    def _build_api_urls(self):
        """Build ElevenLabs API URLs"""
        # WebSocket URL for DUAL_STREAM
        ws_base_url = f"wss://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}/stream-input"
        ws_params = [
            f"model_id={self.model_id}",
            f"output_format={self.output_format}",
        ]
        if self.language_code:
            ws_params.append(f"language_code={self.language_code}")
        self.ws_url = f"{ws_base_url}?{'&'.join(ws_params)}"

        # HTTP streaming URL for SINGLE_STREAM
        self.stream_url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}/stream"

        # HTTP complete URL for NON_STREAM
        self.tts_url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}"

    async def _is_connection_healthy(self) -> bool:
        """Check if WebSocket connection is alive and usable"""
        if self.ws is None:
            return False
        try:
            # Check connection state (state 1 = OPEN, state 3 = CLOSED)
            return self.ws.state.value == 1
        except Exception:
            return False

    async def open_audio_channels(self, conn):
        try:
            await super().open_audio_channels(conn)
        except Exception as e:
            logger.bind(tag=TAG).error(
                f"Failed to open audio channels: {str(e)}"
            )
            self.ws = None
            raise

    async def _ensure_connection(self):
        """Establish WebSocket connection with ElevenLabs"""
        try:
            if self.ws:
                if self.enable_ws_reuse:
                    logger.bind(tag=TAG).info("Reusing existing WebSocket connection...")
                    return self.ws
                else:
                    try:
                        await self._close_connection()
                    except:
                        pass

            logger.bind(tag=TAG).debug("Establishing new WebSocket connection to ElevenLabs...")

            headers = {"xi-api-key": self.api_key}
            self.ws = await websockets.connect(
                self.ws_url,
                additional_headers=headers,
                max_size=10000000,
                ping_interval=30,
                ping_timeout=10,
                close_timeout=10
            )
            logger.bind(tag=TAG).debug("WebSocket connection established")

            # Send BOS (Beginning of Stream) message with voice settings
            bos_message = {
                "text": " ",
                "voice_settings": {
                    "stability": self.stability,
                    "similarity_boost": self.similarity_boost,
                    "style": self.style,
                    "use_speaker_boost": self.use_speaker_boost
                },
                "xi_api_key": self.api_key
            }
            await self.ws.send(json.dumps(bos_message))
            logger.bind(tag=TAG).debug("BOS message sent with voice settings")

            # Start monitor task
            if self._monitor_task is None or self._monitor_task.done():
                if self._monitor_task and self._monitor_task.done():
                    # Check if previous task crashed
                    try:
                        exc = self._monitor_task.exception()
                        if exc:
                            logger.bind(tag=TAG).error(f"[MONITOR] Previous monitor task failed: {exc}")
                    except Exception:
                        pass

                logger.bind(tag=TAG).debug("Starting response monitor task...")
                self._monitor_task = asyncio.create_task(
                    self._start_monitor_tts_response()
                    )

            return self.ws
        except Exception as e:
            logger.bind(tag=TAG).error(f"Failed to establish connection: {str(e)}")
            self.ws = None
            raise

    async def _close_connection(self):
        """Close WebSocket connection"""
        try:
            if self.ws:
                logger.bind(tag=TAG).debug("Closing WebSocket connection...")
                await self.ws.close()
                self.ws = None
        except Exception as e:
            logger.bind(tag=TAG).error(f"Failed to close connection: {str(e)}")
            pass

    def tts_text_priority_thread(self):
        """ElevenLabs TTS text processing thread - supports all three modes"""
        if self.interface_type == InterfaceType.DUAL_STREAM:
            self._tts_text_priority_dual_stream()
        elif self.interface_type == InterfaceType.SINGLE_STREAM:
            self._tts_text_priority_single_stream()
        else:
            # NON_STREAM mode uses base class implementation
            super().tts_text_priority_thread()

    def _tts_text_priority_dual_stream(self):
        """DUAL_STREAM mode: WebSocket bidirectional streaming"""
        while not self.conn.stop_event.is_set():
            try:
                message = self.tts_text_queue.get(timeout=1)
                logger.bind(tag=TAG).debug(
                    f"Received TTS task | {message.sentence_type.name} | {message.content_type.name} | Session: {self.conn.sentence_id}"
                )

                if message.sentence_type == SentenceType.FIRST:
                    self.conn.client_abort = False

                if self.conn.client_abort:
                    try:
                        logger.bind(tag=TAG).info("Received abort signal, terminating TTS text processing")
                        if self.enable_ws_reuse:
                            asyncio.run_coroutine_threadsafe(
                                self._send_eos(),
                                loop=self.conn.loop,
                            )
                        else:
                            asyncio.run_coroutine_threadsafe(
                                self._close_connection(),
                                loop=self.conn.loop,
                            )
                        continue
                    except Exception as e:
                        logger.bind(tag=TAG).error(f"Failed to handle abort: {str(e)}")
                        continue

                if message.sentence_type == SentenceType.FIRST:
                    try:
                        if not getattr(self.conn, "sentence_id", None):
                            self.conn.sentence_id = uuid.uuid4().hex
                            logger.bind(tag=TAG).debug(f"Generated new session ID: {self.conn.sentence_id}")

                        logger.bind(tag=TAG).debug("Starting TTS session...")
                        future = asyncio.run_coroutine_threadsafe(
                            self.start_session(self.conn.sentence_id),
                            loop=self.conn.loop,
                        )
                        future.result()
                        self.before_stop_play_files.clear()
                        logger.bind(tag=TAG).debug("TTS session started successfully")
                    except Exception as e:
                        logger.bind(tag=TAG).error(f"Failed to start TTS session: {str(e)}")
                        continue

                elif ContentType.TEXT == message.content_type:
                    if message.content_detail:
                        try:
                            logger.bind(tag=TAG).debug(f"Sending TTS text: {message.content_detail}")
                            future = asyncio.run_coroutine_threadsafe(
                                self.text_to_speak(message.content_detail, None),
                                loop=self.conn.loop,
                            )
                            future.result()
                            logger.bind(tag=TAG).debug("TTS text sent successfully")
                        except Exception as e:
                            logger.bind(tag=TAG).error(f"Failed to send TTS text: {str(e)}")
                            continue

                elif ContentType.FILE == message.content_type:
                    logger.bind(tag=TAG).info(f"Adding audio file to play queue: {message.content_file}")
                    if message.content_file and os.path.exists(message.content_file):
                        self._process_audio_file_stream(
                            message.content_file,
                            callback=lambda audio_data: self.handle_audio_file(audio_data, message.content_detail)
                        )

                if message.sentence_type == SentenceType.LAST:
                    try:
                        logger.bind(tag=TAG).debug("Finishing TTS session...")
                        future = asyncio.run_coroutine_threadsafe(
                            self.finish_session(self.conn.sentence_id),
                            loop=self.conn.loop,
                        )
                        future.result()
                    except Exception as e:
                        logger.bind(tag=TAG).error(f"Failed to finish TTS session: {str(e)}")
                        continue

            except queue.Empty:
                continue
            except Exception as e:
                logger.bind(tag=TAG).error(
                    f"TTS text processing error: {str(e)}, type: {type(e).__name__}, stack: {traceback.format_exc()}"
                )
                continue

    def _tts_text_priority_single_stream(self):
        """SINGLE_STREAM mode: HTTP streaming response"""
        while not self.conn.stop_event.is_set():
            try:
                message = self.tts_text_queue.get(timeout=1)
                if message.sentence_type == SentenceType.FIRST:
                    self.tts_stop_request = False
                    self.processed_chars = 0
                    self.tts_text_buff = []
                    self.before_stop_play_files.clear()
                elif ContentType.TEXT == message.content_type:
                    self.tts_text_buff.append(message.content_detail)
                    segment_text = self._get_segment_text()
                    if segment_text:
                        asyncio.run(self.text_to_speak(segment_text, None))
                elif ContentType.FILE == message.content_type:
                    logger.bind(tag=TAG).info(f"Adding audio file to play queue: {message.content_file}")
                    if message.content_file and os.path.exists(message.content_file):
                        self._process_audio_file_stream(
                            message.content_file,
                            callback=lambda audio_data: self.handle_audio_file(audio_data, message.content_detail)
                        )
                if message.sentence_type == SentenceType.LAST:
                    self._process_remaining_text_stream(True)
            except queue.Empty:
                continue
            except Exception as e:
                logger.bind(tag=TAG).error(
                    f"TTS text processing error: {str(e)}, type: {type(e).__name__}, stack: {traceback.format_exc()}"
                )
                continue

    def _process_remaining_text_stream(self, is_last=False):
        """Process remaining text for SINGLE_STREAM mode"""
        full_text = "".join(self.tts_text_buff)
        remaining_text = full_text[self.processed_chars :]
        if remaining_text:
            segment_text = textUtils.get_string_no_punctuation_or_emoji(remaining_text)
            if segment_text:
                asyncio.run(self.text_to_speak(segment_text, None))
                self.processed_chars += len(full_text)
            else:
                self._process_before_stop_play_files()
        else:
            self._process_before_stop_play_files()

    async def text_to_speak(self, text, output_file: Optional[str]):
        """Convert text to speech - handles all three modes"""
        filtered_text = MarkdownCleaner.clean_markdown(text)

        if self.interface_type == InterfaceType.DUAL_STREAM:
            await self._text_to_speak_dual_stream(filtered_text)
        elif self.interface_type == InterfaceType.SINGLE_STREAM:
            await self._text_to_speak_single_stream(filtered_text)
        else:  # NON_STREAM
            return await self._text_to_speak_non_stream(filtered_text, output_file)

    async def _text_to_speak_dual_stream(self, text: str):
        """DUAL_STREAM mode: Send text via WebSocket"""
        try:
            if not await self._is_connection_healthy():
                logger.bind(tag=TAG).warning("Connection unhealthy, attempting reconnection...")
                await self._ensure_connection()

            text_message = {
                "text": text,
                "try_trigger_generation": True
            }
            await self.ws.send(json.dumps(text_message))
            logger.bind(tag=TAG).debug(f"Sent text to WebSocket: {text}")
        except Exception as e:
            logger.bind(tag=TAG).error(f"Failed to send TTS text via WebSocket: {str(e)}")
            if self.ws:
                try:
                    await self.ws.close()
                except Exception:
                    pass
                self.ws = None
            raise

    async def _text_to_speak_single_stream(self, text: str):
        """SINGLE_STREAM mode: HTTP streaming response"""
        try:
            payload = {
                "text": text,
                "model_id": self.model_id,
                "voice_settings": {
                    "stability": self.stability,
                    "similarity_boost": self.similarity_boost,
                    "style": self.style,
                    "use_speaker_boost": self.use_speaker_boost
                }
            }

            headers = {
                "xi-api-key": self.api_key,
                "Content-Type": "application/json"
            }

            frame_bytes = int(
                self.opus_encoder.sample_rate
                * self.opus_encoder.channels
                * self.opus_encoder.frame_size_ms
                / 1000
                * 2
            )

            self.tts_audio_queue.put((SentenceType.FIRST, [], text))
            self.pcm_buffer.clear()

            async with aiohttp.ClientSession() as session:
                async with session.post(self.stream_url, json=payload, headers=headers, timeout=30) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        logger.bind(tag=TAG).error(f"TTS request failed: {resp.status}, {error_text}")
                        self.tts_audio_queue.put((SentenceType.LAST, [], None))
                        return

                    async for chunk in resp.content.iter_any():
                        if not chunk:
                            continue

                        data = chunk[0] if isinstance(chunk, (list, tuple)) else chunk
                        self.pcm_buffer.extend(data)

                        while len(self.pcm_buffer) >= frame_bytes:
                            frame = bytes(self.pcm_buffer[:frame_bytes])
                            del self.pcm_buffer[:frame_bytes]
                            self.opus_encoder.encode_pcm_to_opus_stream(
                                frame,
                                end_of_stream=False,
                                callback=self.handle_opus
                            )

                    # Flush remaining PCM data
                    if self.pcm_buffer:
                        self.opus_encoder.encode_pcm_to_opus_stream(
                            bytes(self.pcm_buffer),
                            end_of_stream=True,
                            callback=self.handle_opus
                        )
                        self.pcm_buffer.clear()

        except Exception as e:
            logger.bind(tag=TAG).error(f"TTS request exception: {e}")
            self.tts_audio_queue.put((SentenceType.LAST, [], None))

    async def _text_to_speak_non_stream(self, text: str, output_file: Optional[str]):
        """NON_STREAM mode: Complete HTTP response"""
        try:
            payload = {
                "text": text,
                "model_id": self.model_id,
                "voice_settings": {
                    "stability": self.stability,
                    "similarity_boost": self.similarity_boost,
                    "style": self.style,
                    "use_speaker_boost": self.use_speaker_boost
                }
            }

            headers = {
                "xi-api-key": self.api_key,
                "Content-Type": "application/json"
            }

            response = requests.post(self.tts_url, json=payload, headers=headers, timeout=30)
            if response.status_code == 200:
                if output_file:
                    with open(output_file, "wb") as audio_file:
                        audio_file.write(response.content)
                    logger.bind(tag=TAG).info(f"TTS audio saved to file: {output_file}")
                else:
                    return response.content
            else:
                logger.bind(tag=TAG).error(f"TTS request failed: {response.status_code} - {response.text}")
                raise Exception(f"ElevenLabs TTS request failed: {response.status_code} - {response.text}")
        except Exception as e:
            logger.bind(tag=TAG).error(f"Failed to generate TTS: {e}")
            raise

    async def start_session(self, session_id):
        """Start TTS session"""
        logger.bind(tag=TAG).debug(f"Starting session: {session_id}")
        try:
            # Wait for previous session to end
            for _ in range(3):
                if not self.activate_session:
                    break
                logger.bind(tag=TAG).debug("Waiting for previous session to end...")
                await asyncio.sleep(0.1)
            else:
                logger.bind(tag=TAG).debug("Previous session timeout, clearing connection state...")
                await self.close()

            # Set session active flag
            self.activate_session = True

            # Ensure connection is established
            await self._ensure_connection()
            logger.bind(tag=TAG).debug("Session start request sent")
        except Exception as e:
            logger.bind(tag=TAG).error(f"Failed to start session: {str(e)}")
            await self.close()
            raise

    async def finish_session(self, session_id):
        """Finish TTS session by sending EOS"""
        logger.bind(tag=TAG).debug(f"Finishing session: {session_id}")
        try:
            if self.ws:
                await self._send_eos()
                logger.bind(tag=TAG).debug("Session finish request sent")
        except Exception as e:
            logger.bind(tag=TAG).error(f"Failed to finish session: {str(e)}")
            await self.close()
            raise

    async def _send_eos(self):
        """Send End of Stream message"""
        if self.ws:
            eos_message = {"text": ""}
            await self.ws.send(json.dumps(eos_message))
            logger.bind(tag=TAG).debug("EOS message sent")

    async def close(self):
        """Resource cleanup method"""
        self.activate_session = False
        # Cancel monitor task
        if self._monitor_task:
            try:
                self._monitor_task.cancel()
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            except Exception as e:
                logger.bind(tag=TAG).warning(f"Error cancelling monitor task: {e}")
            self._monitor_task = None

        if self.ws:
            try:
                await self.ws.close()
            except:
                pass
            self.ws = None

    async def _start_monitor_tts_response(self):
        """Monitor ElevenLabs WebSocket responses"""
        logger.bind(tag=TAG).debug("[MONITOR] Monitor task started")
        try:
            while not self.conn.stop_event.is_set():
                try:
                    log_msg = "[MONITOR] Waiting for WebSocket message (timeout: 60s)"
                    logger.bind(tag=TAG).debug(log_msg)
                    try:
                        msg = await asyncio.wait_for(self.ws.recv(), timeout=60)
                    except asyncio.TimeoutError:
                        msg_text = (
                            "[MONITOR] WebSocket recv timeout - "
                            "no audio from ElevenLabs in 60s"
                        )
                        logger.bind(tag=TAG).warning(msg_text)
                        raise
                    msg_len = len(msg)
                    msg_preview = msg[:200]
                    log_msg = (
                        f"[WS_RECV] Received: {msg_len} bytes, "
                        f"preview: {msg_preview}"
                    )
                    logger.bind(tag=TAG).debug(log_msg)
                    data = json.loads(msg)
                    keys = list(data.keys())
                    logger.bind(tag=TAG).debug(
                        f"[WS_RECV] Parsed keys: {keys}"
                    )

                    if self.conn.client_abort:
                        logger.bind(tag=TAG).debug("Client abort detected, stopping monitor")
                        break

                    # Handle audio response
                    if "audio" in data and data["audio"]:
                        audio_len = len(data['audio'])
                        logger.bind(tag=TAG).debug(
                            f"[AUDIO_RECV] Found {audio_len} base64 chars"
                        )
                        try:
                            audio_bytes = base64.b64decode(
                                data["audio"]
                            )
                            pcm_len = len(audio_bytes)
                            logger.bind(tag=TAG).debug(
                                f"[AUDIO_RECV] Decoded {pcm_len} PCM bytes"
                            )
                            # Convert PCM to Opus and push to queue
                            self.opus_encoder.encode_pcm_to_opus_stream(
                                audio_bytes, False,
                                callback=self.handle_opus
                            )
                            logger.bind(tag=TAG).debug(
                                "[AUDIO_RECV] Sent to Opus encoder"
                            )
                        except Exception as e:
                            logger.bind(tag=TAG).error(
                                f"[AUDIO_RECV] Failed: {e}"
                            )
                            raise
                    elif "audio" in data:
                        logger.bind(tag=TAG).warning(
                            "[AUDIO_RECV] Audio field empty"
                        )
                    else:
                        logger.bind(tag=TAG).debug(
                            "[AUDIO_RECV] No audio field in message"
                        )

                    # Handle alignment info (for sentence tracking)
                    if "alignment" in data:
                        alignment = data["alignment"]
                        if alignment and "chars" in alignment:
                            chars = alignment["chars"]
                            if chars:
                                # chars can be string or list of dicts
                                if isinstance(chars, str):
                                    text = chars
                                else:
                                    text = "".join([c.get("char", "") if isinstance(c, dict) else str(c) for c in chars])
                                if text.strip():
                                    logger.bind(tag=TAG).debug(f"Alignment received: {text}")

                    # Handle normalizedAlignment for word-level tracking (debugging only)
                    if "normalizedAlignment" in data:
                        normalized = data["normalizedAlignment"]
                        if normalized and "chars" in normalized:
                            chars = normalized["chars"]
                            if chars:
                                # chars can be string or list of dicts
                                if isinstance(chars, str):
                                    text = chars
                                else:
                                    text = "".join([c.get("char", "") if isinstance(c, dict) else str(c) for c in chars])
                                if text.strip():
                                    logger.bind(tag=TAG).debug(f"Normalized alignment: {text}")

                                    # Use original text from LLM instead of normalized alignment
                                    # This preserves Vietnamese diacritics and spaces that would be lost in ElevenLabs' normalization
                                    if self.conn.tts_MessageText:
                                        self.tts_audio_queue.put(
                                            (SentenceType.FIRST, [], self.conn.tts_MessageText)
                                        )
                                        self.conn.tts_MessageText = None

                    # Check if final chunk
                    if data.get("isFinal", False):
                        logger.bind(tag=TAG).debug("Received final audio chunk")
                        self.activate_session = False
                        self._process_before_stop_play_files()
                        if not self.enable_ws_reuse:
                            break

                except websockets.ConnectionClosed:
                    logger.bind(tag=TAG).warning(
                        "WebSocket connection closed"
                    )
                    self.ws = None
                    if self.enable_ws_reuse:
                        # Try to reconnect in reuse mode
                        try:
                            logger.bind(tag=TAG).info(
                                "Attempting reconnection..."
                            )
                            await self._ensure_connection()
                            logger.bind(tag=TAG).info(
                                "Reconnection successful"
                            )
                            continue  # Continue monitoring with new connection
                        except Exception as e:
                            logger.bind(tag=TAG).error(
                                f"Reconnection failed: {e}"
                            )
                    break
                except Exception as e:
                    logger.bind(tag=TAG).error(f"Monitor error: {e}")
                    traceback.print_exc()
                    break

            # Close WebSocket on exit only if not reusing
            if self.ws and not self.enable_ws_reuse:
                try:
                    await self.ws.close()
                except Exception:
                    pass
                self.ws = None
        finally:
            self.activate_session = False
            self._monitor_task = None

    def wav_to_opus_data_audio_raw_stream(self, raw_data_var, is_end=False, callback: Callable[[Any], Any] = None):
        """Convert raw PCM data to Opus stream"""
        return self.opus_encoder.encode_pcm_to_opus_stream(raw_data_var, is_end, callback=callback)
