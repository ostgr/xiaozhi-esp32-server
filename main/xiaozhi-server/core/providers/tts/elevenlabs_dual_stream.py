"""
ElevenLabs TTS Provider - DUAL_STREAM Mode
Handles WebSocket bidirectional streaming for real-time low-latency TTS
"""
import os
import uuid
import json
import queue
import base64
import asyncio
import traceback
import websockets
from typing import Optional

from core.utils.tts import MarkdownCleaner
from config.logger import setup_logging
from core.utils import opus_encoder_utils
from core.utils.util import check_model_key
from core.providers.tts.base import TTSProviderBase
from core.providers.tts.dto.dto import SentenceType, ContentType

TAG = __name__
logger = setup_logging()


class TTSProvider(TTSProviderBase):
    """ElevenLabs TTS Provider - DUAL_STREAM Mode (WebSocket)"""

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
            self.use_speaker_boost = self.use_speaker_boost.lower() == "true"

        # Output format
        self.output_format = config.get("output_format", "pcm_16000")
        self.language_code = config.get("language_code", "")

        # WebSocket connection management
        enable_ws_reuse_value = config.get("enable_ws_reuse", True)
        self.enable_ws_reuse = False if str(enable_ws_reuse_value).lower() == "false" else True

        # Opus encoder for PCM to Opus conversion
        self.opus_encoder = opus_encoder_utils.OpusEncoderUtils(
            sample_rate=16000, channels=1, frame_size_ms=60
        )

        # Build API URLs
        self._build_api_urls()

        # Validate API key
        model_key_msg = check_model_key("TTS", self.api_key)
        if model_key_msg:
            logger.bind(tag=TAG).error(model_key_msg)

        logger.bind(tag=TAG).info(
            f"[DUAL_STREAM] ElevenLabs TTS initialized | "
            f"voice_id={self.voice_id} | "
            f"model={self.model_id} | "
            f"output_format={self.output_format} | "
            f"ws_reuse={self.enable_ws_reuse}"
        )

    def _build_api_urls(self):
        """Build ElevenLabs API URLs"""
        ws_base_url = f"wss://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}/stream-input"
        ws_params = [
            f"model_id={self.model_id}",
            f"output_format={self.output_format}",
        ]
        if self.language_code:
            ws_params.append(f"language_code={self.language_code}")
        self.ws_url = f"{ws_base_url}?{'&'.join(ws_params)}"

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
            logger.bind(tag=TAG).error(f"Failed to open audio channels: {str(e)}")
            self.ws = None
            raise

    async def _ensure_connection(self):
        """Establish WebSocket connection with ElevenLabs"""
        try:
            if self.ws:
                if self.enable_ws_reuse:
                    logger.bind(tag=TAG).info("[DUAL_STREAM] Reusing existing WebSocket connection...")
                    return self.ws
                else:
                    try:
                        await self._close_connection()
                    except:
                        pass

            logger.bind(tag=TAG).debug("[DUAL_STREAM] Establishing new WebSocket connection...")

            headers = {"xi-api-key": self.api_key}
            self.ws = await websockets.connect(
                self.ws_url,
                additional_headers=headers,
                max_size=10000000,
                ping_interval=30,
                ping_timeout=10,
                close_timeout=10,
            )
            logger.bind(tag=TAG).debug("[DUAL_STREAM] WebSocket connection established")

            # Send BOS (Beginning of Stream) message with voice settings
            bos_message = {
                "text": " ",
                "voice_settings": {
                    "stability": self.stability,
                    "similarity_boost": self.similarity_boost,
                    "style": self.style,
                    "use_speaker_boost": self.use_speaker_boost,
                },
                "xi_api_key": self.api_key,
            }
            await self.ws.send(json.dumps(bos_message))
            logger.bind(tag=TAG).debug("[DUAL_STREAM] BOS message sent with voice settings")

            # Start monitor task
            if self._monitor_task is None or self._monitor_task.done():
                if self._monitor_task and self._monitor_task.done():
                    # Check if previous task crashed
                    try:
                        exc = self._monitor_task.exception()
                        if exc:
                            logger.bind(tag=TAG).error(f"[DUAL_STREAM] Previous monitor task failed: {exc}")
                    except Exception:
                        pass

                logger.bind(tag=TAG).debug("[DUAL_STREAM] Starting response monitor task...")
                self._monitor_task = asyncio.create_task(
                    self._start_monitor_tts_response()
                )

            return self.ws
        except Exception as e:
            logger.bind(tag=TAG).error(f"[DUAL_STREAM] Failed to establish connection: {str(e)}")
            self.ws = None
            raise

    async def _close_connection(self):
        """Close WebSocket connection"""
        try:
            if self.ws:
                logger.bind(tag=TAG).debug("[DUAL_STREAM] Closing WebSocket connection...")
                await self.ws.close()
                self.ws = None
        except Exception as e:
            logger.bind(tag=TAG).error(f"[DUAL_STREAM] Failed to close connection: {str(e)}")
            pass

    def tts_text_priority_thread(self):
        """DUAL_STREAM mode: WebSocket bidirectional streaming"""
        while not self.conn.stop_event.is_set():
            try:
                message = self.tts_text_queue.get(timeout=1)
                logger.bind(tag=TAG).debug(
                    f"[DUAL_STREAM] Received TTS task | {message.sentence_type.name} | "
                    f"{message.content_type.name} | Session: {self.conn.sentence_id}"
                )

                if message.sentence_type == SentenceType.FIRST:
                    self.conn.client_abort = False

                if self.conn.client_abort:
                    try:
                        logger.bind(tag=TAG).info(
                            "[DUAL_STREAM] Received abort signal, terminating TTS text processing"
                        )
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
                        logger.bind(tag=TAG).error(f"[DUAL_STREAM] Failed to handle abort: {str(e)}")
                        continue

                if message.sentence_type == SentenceType.FIRST:
                    try:
                        if not getattr(self.conn, "sentence_id", None):
                            self.conn.sentence_id = uuid.uuid4().hex
                            logger.bind(tag=TAG).debug(
                                f"[DUAL_STREAM] Generated new session ID: {self.conn.sentence_id}"
                            )

                        logger.bind(tag=TAG).debug("[DUAL_STREAM] Starting TTS session...")
                        future = asyncio.run_coroutine_threadsafe(
                            self.start_session(self.conn.sentence_id),
                            loop=self.conn.loop,
                        )
                        future.result()
                        self.before_stop_play_files.clear()
                        logger.bind(tag=TAG).debug("[DUAL_STREAM] TTS session started successfully")
                    except Exception as e:
                        logger.bind(tag=TAG).error(f"[DUAL_STREAM] Failed to start TTS session: {str(e)}")
                        continue

                elif ContentType.TEXT == message.content_type:
                    if message.content_detail:
                        try:
                            logger.bind(tag=TAG).debug(
                                f"[DUAL_STREAM] Sending TTS text: {message.content_detail}"
                            )
                            future = asyncio.run_coroutine_threadsafe(
                                self.text_to_speak(message.content_detail, None),
                                loop=self.conn.loop,
                            )
                            future.result()
                            logger.bind(tag=TAG).debug("[DUAL_STREAM] TTS text sent successfully")
                        except Exception as e:
                            logger.bind(tag=TAG).error(
                                f"[DUAL_STREAM] Failed to send TTS text: {str(e)}"
                            )
                            continue

                elif ContentType.FILE == message.content_type:
                    logger.bind(tag=TAG).info(
                        f"[DUAL_STREAM] Adding audio file to play queue: {message.content_file}"
                    )
                    if message.content_file and os.path.exists(message.content_file):
                        self._process_audio_file_stream(
                            message.content_file,
                            callback=lambda audio_data: self.handle_audio_file(
                                audio_data, message.content_detail
                            ),
                        )

                if message.sentence_type == SentenceType.LAST:
                    try:
                        logger.bind(tag=TAG).debug("[DUAL_STREAM] Finishing TTS session...")
                        future = asyncio.run_coroutine_threadsafe(
                            self.finish_session(self.conn.sentence_id),
                            loop=self.conn.loop,
                        )
                        future.result()
                    except Exception as e:
                        logger.bind(tag=TAG).error(
                            f"[DUAL_STREAM] Failed to finish TTS session: {str(e)}"
                        )
                        continue

            except queue.Empty:
                continue
            except Exception as e:
                logger.bind(tag=TAG).error(
                    f"[DUAL_STREAM] TTS text processing error: {str(e)}, "
                    f"type: {type(e).__name__}, stack: {traceback.format_exc()}"
                )
                continue

    async def text_to_speak(self, text, output_file: Optional[str]):
        """Send text via WebSocket"""
        filtered_text = MarkdownCleaner.clean_markdown(text)
        await self._text_to_speak_dual_stream(filtered_text)

    async def _text_to_speak_dual_stream(self, text: str):
        """DUAL_STREAM mode: Send text via WebSocket"""
        try:
            if not await self._is_connection_healthy():
                logger.bind(tag=TAG).warning(
                    "[DUAL_STREAM] Connection unhealthy, attempting reconnection..."
                )
                await self._ensure_connection()

            text_message = {"text": text, "try_trigger_generation": True}
            await self.ws.send(json.dumps(text_message))
            logger.bind(tag=TAG).debug(f"[DUAL_STREAM] Sent text to WebSocket: {text}")
        except Exception as e:
            logger.bind(tag=TAG).error(f"[DUAL_STREAM] Failed to send TTS text via WebSocket: {str(e)}")
            if self.ws:
                try:
                    await self.ws.close()
                except Exception:
                    pass
                self.ws = None
            raise

    async def start_session(self, session_id):
        """Start TTS session"""
        logger.bind(tag=TAG).debug(f"[DUAL_STREAM] Starting session: {session_id}")
        try:
            # Wait for previous session to end
            for _ in range(3):
                if not self.activate_session:
                    break
                logger.bind(tag=TAG).debug("[DUAL_STREAM] Waiting for previous session to end...")
                await asyncio.sleep(0.1)
            else:
                logger.bind(tag=TAG).debug(
                    "[DUAL_STREAM] Previous session timeout, clearing connection state..."
                )
                await self.close()

            # Set session active flag
            self.activate_session = True

            # Ensure connection is established
            await self._ensure_connection()
            logger.bind(tag=TAG).debug("[DUAL_STREAM] Session start request sent")
        except Exception as e:
            logger.bind(tag=TAG).error(f"[DUAL_STREAM] Failed to start session: {str(e)}")
            await self.close()
            raise

    async def finish_session(self, session_id):
        """Finish TTS session by sending EOS"""
        logger.bind(tag=TAG).debug(f"[DUAL_STREAM] Finishing session: {session_id}")
        try:
            if self.ws:
                await self._send_eos()
                logger.bind(tag=TAG).debug("[DUAL_STREAM] Session finish request sent")
        except Exception as e:
            logger.bind(tag=TAG).error(f"[DUAL_STREAM] Failed to finish session: {str(e)}")
            await self.close()
            raise

    async def _send_eos(self):
        """Send End of Stream message"""
        if self.ws:
            eos_message = {"text": ""}
            await self.ws.send(json.dumps(eos_message))
            logger.bind(tag=TAG).debug("[DUAL_STREAM] EOS message sent")

    async def _start_monitor_tts_response(self):
        """Monitor ElevenLabs WebSocket responses"""
        logger.bind(tag=TAG).debug("[DUAL_STREAM] Monitor task started")
        try:
            while not self.conn.stop_event.is_set():
                try:
                    log_msg = "[DUAL_STREAM] Waiting for WebSocket message (timeout: 60s)"
                    logger.bind(tag=TAG).debug(log_msg)
                    try:
                        msg = await asyncio.wait_for(self.ws.recv(), timeout=60)
                    except asyncio.TimeoutError:
                        msg_text = (
                            "[DUAL_STREAM] WebSocket recv timeout - "
                            "no audio from ElevenLabs in 60s"
                        )
                        logger.bind(tag=TAG).warning(msg_text)
                        raise

                    msg_len = len(msg)
                    msg_preview = msg[:200]
                    log_msg = (
                        f"[DUAL_STREAM] Received: {msg_len} bytes, "
                        f"preview: {msg_preview}"
                    )
                    logger.bind(tag=TAG).debug(log_msg)
                    data = json.loads(msg)
                    keys = list(data.keys())
                    logger.bind(tag=TAG).debug(f"[DUAL_STREAM] Parsed keys: {keys}")

                    if self.conn.client_abort:
                        logger.bind(tag=TAG).debug(
                            "[DUAL_STREAM] Client abort detected, stopping monitor"
                        )
                        break

                    # Handle audio response
                    if "audio" in data and data["audio"]:
                        audio_len = len(data["audio"])
                        logger.bind(tag=TAG).debug(
                            f"[DUAL_STREAM] Found {audio_len} base64 chars"
                        )
                        try:
                            audio_bytes = base64.b64decode(data["audio"])
                            pcm_len = len(audio_bytes)
                            logger.bind(tag=TAG).debug(
                                f"[DUAL_STREAM] Decoded {pcm_len} PCM bytes"
                            )
                            # Convert PCM to Opus and push to queue
                            self.opus_encoder.encode_pcm_to_opus_stream(
                                audio_bytes, False, callback=self.handle_opus
                            )
                            logger.bind(tag=TAG).debug("[DUAL_STREAM] Sent to Opus encoder")
                        except Exception as e:
                            logger.bind(tag=TAG).error(f"[DUAL_STREAM] Failed: {e}")
                            raise
                    elif "audio" in data:
                        logger.bind(tag=TAG).warning("[DUAL_STREAM] Audio field empty")
                    else:
                        logger.bind(tag=TAG).debug("[DUAL_STREAM] No audio field in message")

                    # Handle alignment info (for sentence tracking)
                    if "alignment" in data:
                        alignment = data["alignment"]
                        if alignment and "chars" in alignment:
                            chars = alignment["chars"]
                            if chars:
                                if isinstance(chars, str):
                                    text = chars
                                else:
                                    text = "".join(
                                        [
                                            c.get("char", "") if isinstance(c, dict) else str(c)
                                            for c in chars
                                        ]
                                    )
                                if text.strip():
                                    logger.bind(tag=TAG).debug(
                                        f"[DUAL_STREAM] Alignment received: {text}"
                                    )

                    # Handle normalizedAlignment for word-level tracking
                    if "normalizedAlignment" in data:
                        normalized = data["normalizedAlignment"]
                        if normalized and "chars" in normalized:
                            chars = normalized["chars"]
                            if chars:
                                if isinstance(chars, str):
                                    text = chars
                                else:
                                    text = "".join(
                                        [
                                            c.get("char", "") if isinstance(c, dict) else str(c)
                                            for c in chars
                                        ]
                                    )
                                if text.strip():
                                    logger.bind(tag=TAG).debug(
                                        f"[DUAL_STREAM] Normalized alignment: {text}"
                                    )

                                    # Use original text from LLM to preserve Vietnamese diacritics
                                    if self.conn.tts_MessageText:
                                        self.tts_audio_queue.put(
                                            (SentenceType.FIRST, [], self.conn.tts_MessageText)
                                        )
                                        self.conn.tts_MessageText = None

                    # Check if final chunk
                    if data.get("isFinal", False):
                        logger.bind(tag=TAG).debug("[DUAL_STREAM] Received final audio chunk")
                        self.activate_session = False
                        self._process_before_stop_play_files()
                        if not self.enable_ws_reuse:
                            break

                except websockets.ConnectionClosed:
                    logger.bind(tag=TAG).warning("[DUAL_STREAM] WebSocket connection closed")
                    self.ws = None
                    if self.enable_ws_reuse:
                        # Try to reconnect in reuse mode
                        try:
                            logger.bind(tag=TAG).info(
                                "[DUAL_STREAM] Attempting reconnection..."
                            )
                            await self._ensure_connection()
                            logger.bind(tag=TAG).info("[DUAL_STREAM] Reconnection successful")
                            continue
                        except Exception as e:
                            logger.bind(tag=TAG).error(f"[DUAL_STREAM] Reconnection failed: {e}")
                    break
                except Exception as e:
                    logger.bind(tag=TAG).error(f"[DUAL_STREAM] Monitor error: {e}")
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
                logger.bind(tag=TAG).warning(f"[DUAL_STREAM] Error cancelling monitor task: {e}")
            self._monitor_task = None

        if self.ws:
            try:
                await self.ws.close()
            except:
                pass
            self.ws = None

    def wav_to_opus_data_audio_raw_stream(
        self, raw_data_var, is_end=False, callback=None
    ):
        """Convert raw PCM data to Opus stream"""
        return self.opus_encoder.encode_pcm_to_opus_stream(raw_data_var, is_end, callback=callback)
