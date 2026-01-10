"""
ElevenLabs TTS Provider - SINGLE_STREAM Mode
Handles HTTP streaming response for traditional streaming TTS
"""
import os
import queue
import asyncio
import traceback
import aiohttp
from typing import Optional

from core.utils.tts import MarkdownCleaner
from config.logger import setup_logging
from core.utils import opus_encoder_utils, textUtils
from core.utils.util import check_model_key
from core.providers.tts.base import TTSProviderBase
from core.providers.tts.dto.dto import SentenceType, ContentType

TAG = __name__
logger = setup_logging()


class TTSProvider(TTSProviderBase):
    """ElevenLabs TTS Provider - SINGLE_STREAM Mode (HTTP Streaming)"""

    def __init__(self, config, delete_audio_file):
        super().__init__(config, delete_audio_file)

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

        # Opus encoder for PCM to Opus conversion
        self.opus_encoder = opus_encoder_utils.OpusEncoderUtils(
            sample_rate=16000, channels=1, frame_size_ms=60
        )

        # Build API URLs
        self.stream_url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}/stream"

        # PCM buffer for streaming mode
        self.pcm_buffer = bytearray()

        # Text buffering for SINGLE_STREAM
        self.tts_text_buff = []
        self.processed_chars = 0
        self.tts_stop_request = False

        # Validate API key
        model_key_msg = check_model_key("TTS", self.api_key)
        if model_key_msg:
            logger.bind(tag=TAG).error(model_key_msg)

        logger.bind(tag=TAG).info(
            f"[SINGLE_STREAM] ElevenLabs TTS initialized | "
            f"voice_id={self.voice_id} | "
            f"model={self.model_id} | "
            f"output_format={self.output_format}"
        )

    def tts_text_priority_thread(self):
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
                    logger.bind(tag=TAG).info(
                        f"[SINGLE_STREAM] Adding audio file to play queue: {message.content_file}"
                    )
                    if message.content_file and os.path.exists(message.content_file):
                        self._process_audio_file_stream(
                            message.content_file,
                            callback=lambda audio_data: self.handle_audio_file(
                                audio_data, message.content_detail
                            ),
                        )
                if message.sentence_type == SentenceType.LAST:
                    self._process_remaining_text_stream(True)
            except queue.Empty:
                continue
            except Exception as e:
                logger.bind(tag=TAG).error(
                    f"[SINGLE_STREAM] TTS text processing error: {str(e)}, "
                    f"type: {type(e).__name__}, stack: {traceback.format_exc()}"
                )
                continue

    def _get_segment_text(self):
        """Get text segment for processing"""
        full_text = "".join(self.tts_text_buff)
        remaining_text = full_text[self.processed_chars :]

        if remaining_text:
            segment_text = textUtils.get_string_no_punctuation_or_emoji(remaining_text)
            if segment_text:
                self.processed_chars += len(remaining_text)
                return segment_text
        return None

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
        """Convert text to speech using HTTP streaming"""
        await self._text_to_speak_single_stream(text)

    async def _text_to_speak_single_stream(self, text: str):
        """SINGLE_STREAM mode: HTTP streaming response"""
        try:
            filtered_text = MarkdownCleaner.clean_markdown(text)

            payload = {
                "text": filtered_text,
                "model_id": self.model_id,
                "voice_settings": {
                    "stability": self.stability,
                    "similarity_boost": self.similarity_boost,
                    "style": self.style,
                    "use_speaker_boost": self.use_speaker_boost,
                },
            }

            headers = {
                "xi-api-key": self.api_key,
                "Content-Type": "application/json",
            }

            # Calculate frame size in bytes
            frame_bytes = int(
                self.opus_encoder.sample_rate
                * self.opus_encoder.channels
                * self.opus_encoder.frame_size_ms
                / 1000
                * 2
            )

            self.tts_audio_queue.put((SentenceType.FIRST, [], text))
            self.pcm_buffer.clear()

            logger.bind(tag=TAG).debug(f"[SINGLE_STREAM] Sending HTTP POST to {self.stream_url}")
            logger.bind(tag=TAG).debug(f"[SINGLE_STREAM] Text: {filtered_text}")

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.stream_url, json=payload, headers=headers, timeout=30
                ) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        logger.bind(tag=TAG).error(
                            f"[SINGLE_STREAM] TTS request failed: {resp.status}, {error_text}"
                        )
                        self.tts_audio_queue.put((SentenceType.LAST, [], None))
                        return

                    logger.bind(tag=TAG).debug(f"[SINGLE_STREAM] Response status: {resp.status}")
                    logger.bind(tag=TAG).debug(f"[SINGLE_STREAM] Response headers: {dict(resp.headers)}")

                    chunk_count = 0
                    async for chunk in resp.content.iter_any():
                        if not chunk:
                            continue

                        data = chunk[0] if isinstance(chunk, (list, tuple)) else chunk
                        self.pcm_buffer.extend(data)

                        logger.bind(tag=TAG).debug(
                            f"[SINGLE_STREAM] Received chunk: {len(data)} bytes, "
                            f"buffer size: {len(self.pcm_buffer)} bytes"
                        )

                        # Process complete frames
                        while len(self.pcm_buffer) >= frame_bytes:
                            frame = bytes(self.pcm_buffer[:frame_bytes])
                            del self.pcm_buffer[:frame_bytes]
                            self.opus_encoder.encode_pcm_to_opus_stream(
                                frame,
                                end_of_stream=False,
                                callback=self.handle_opus,
                            )

                        chunk_count += 1

                    logger.bind(tag=TAG).debug(
                        f"[SINGLE_STREAM] Stream complete, received {chunk_count} chunks"
                    )

                    # Flush remaining PCM data
                    if self.pcm_buffer:
                        logger.bind(tag=TAG).debug(
                            f"[SINGLE_STREAM] Flushing {len(self.pcm_buffer)} remaining bytes"
                        )
                        self.opus_encoder.encode_pcm_to_opus_stream(
                            bytes(self.pcm_buffer),
                            end_of_stream=True,
                            callback=self.handle_opus,
                        )
                        self.pcm_buffer.clear()

        except Exception as e:
            logger.bind(tag=TAG).error(f"[SINGLE_STREAM] TTS request exception: {e}")
            logger.bind(tag=TAG).error(f"[SINGLE_STREAM] Traceback: {traceback.format_exc()}")
            self.tts_audio_queue.put((SentenceType.LAST, [], None))

    async def close(self):
        """Resource cleanup"""
        pass
