"""
ElevenLabs Streaming TTS Provider
Dual-stream WebSocket implementation for real-time text-to-speech synthesis.
Supports voice cloning (IVC) and multiple models.
"""
import os
import uuid
import json
import queue
import base64
import asyncio
import traceback
from typing import Callable, Any
import websockets
from core.utils.tts import MarkdownCleaner
from config.logger import setup_logging
from core.utils import opus_encoder_utils
from core.utils.util import check_model_key
from core.providers.tts.base import TTSProviderBase
from core.providers.tts.dto.dto import SentenceType, ContentType, InterfaceType

TAG = __name__
logger = setup_logging()


class TTSProvider(TTSProviderBase):
    def __init__(self, config, delete_audio_file):
        super().__init__(config, delete_audio_file)
        self.ws = None
        self.interface_type = InterfaceType.DUAL_STREAM
        self._monitor_task = None
        self.activate_session = False

        # Core configuration
        self.api_key = config.get("api_key")
        self.voice_id = config.get("voice_id")
        self.model_id = config.get("model_id", "eleven_multilingual_v2")

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

        # WebSocket connection management
        enable_ws_reuse_value = config.get("enable_ws_reuse", True)
        self.enable_ws_reuse = False if str(enable_ws_reuse_value).lower() == 'false' else True

        # Opus encoder for 16kHz PCM to Opus conversion
        self.opus_encoder = opus_encoder_utils.OpusEncoderUtils(
            sample_rate=16000, channels=1, frame_size_ms=60
        )

        # Build WebSocket URL
        self._build_ws_url()

        # Validate API key
        model_key_msg = check_model_key("TTS", self.api_key)
        if model_key_msg:
            logger.bind(tag=TAG).error(model_key_msg)

    def _build_ws_url(self):
        """Build ElevenLabs WebSocket URL with parameters"""
        base_url = f"wss://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}/stream-input"
        params = [
            f"model_id={self.model_id}",
            f"output_format={self.output_format}",
        ]
        if self.language_code:
            params.append(f"language_code={self.language_code}")
        self.ws_url = f"{base_url}?{'&'.join(params)}"

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
                max_size=10000000
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
                "generation_config": {
                    "chunk_length_schedule": [120, 160, 250, 290]
                },
                "xi_api_key": self.api_key
            }
            await self.ws.send(json.dumps(bos_message))
            logger.bind(tag=TAG).debug("BOS message sent with voice settings")

            # Start monitor task
            if self._monitor_task is None or self._monitor_task.done():
                logger.bind(tag=TAG).debug("Starting response monitor task...")
                self._monitor_task = asyncio.create_task(self._start_monitor_tts_response())

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
        except:
            pass

    def tts_text_priority_thread(self):
        """ElevenLabs dual-stream TTS text processing thread"""
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
                            # Send EOS to gracefully end current stream
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
                    # Initialize new session
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

    async def text_to_speak(self, text, _):
        """Send text to ElevenLabs TTS stream"""
        try:
            if self.ws is None:
                logger.bind(tag=TAG).warning("WebSocket connection does not exist, aborting text send")
                return

            # Clean markdown from text
            filtered_text = MarkdownCleaner.clean_markdown(text)

            # Send text chunk
            text_message = {
                "text": filtered_text,
                "try_trigger_generation": True
            }
            await self.ws.send(json.dumps(text_message))
            return
        except Exception as e:
            logger.bind(tag=TAG).error(f"Failed to send TTS text: {str(e)}")
            if self.ws:
                try:
                    await self.ws.close()
                except:
                    pass
                self.ws = None
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
        try:
            while not self.conn.stop_event.is_set():
                try:
                    msg = await self.ws.recv()
                    data = json.loads(msg)

                    if self.conn.client_abort:
                        logger.bind(tag=TAG).debug("Client abort detected, stopping monitor")
                        break

                    # Handle audio response
                    if "audio" in data and data["audio"]:
                        audio_bytes = base64.b64decode(data["audio"])
                        # Convert PCM to Opus and push to queue
                        self.opus_encoder.encode_pcm_to_opus_stream(
                            audio_bytes, False, callback=self.handle_opus
                        )

                    # Handle alignment info (for sentence tracking)
                    if "alignment" in data:
                        alignment = data["alignment"]
                        if "chars" in alignment:
                            chars = alignment["chars"]
                            if chars:
                                text = "".join([c.get("char", "") for c in chars])
                                if text.strip():
                                    logger.bind(tag=TAG).debug(f"Alignment received: {text}")

                    # Handle normalizedAlignment for word-level tracking
                    if "normalizedAlignment" in data:
                        normalized = data["normalizedAlignment"]
                        if "chars" in normalized:
                            chars = normalized["chars"]
                            if chars:
                                text = "".join([c.get("char", "") for c in chars])
                                if text.strip():
                                    self.tts_audio_queue.put(
                                        (SentenceType.FIRST, [], text)
                                    )

                    # Check if final chunk
                    if data.get("isFinal", False):
                        logger.bind(tag=TAG).debug("Received final audio chunk")
                        self.activate_session = False
                        self._process_before_stop_play_files()
                        if not self.enable_ws_reuse:
                            break

                except websockets.ConnectionClosed:
                    logger.bind(tag=TAG).warning("WebSocket connection closed")
                    break
                except Exception as e:
                    logger.bind(tag=TAG).error(f"Monitor error: {e}")
                    traceback.print_exc()
                    break

            # Close WebSocket on exit
            if self.ws:
                try:
                    await self.ws.close()
                except:
                    pass
                self.ws = None
        finally:
            self.activate_session = False
            self._monitor_task = None

    def wav_to_opus_data_audio_raw_stream(self, raw_data_var, is_end=False, callback: Callable[[Any], Any] = None):
        """Convert raw PCM data to Opus stream"""
        return self.opus_encoder.encode_pcm_to_opus_stream(raw_data_var, is_end, callback=callback)
