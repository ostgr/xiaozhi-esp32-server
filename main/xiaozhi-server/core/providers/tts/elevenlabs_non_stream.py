"""
ElevenLabs TTS Provider - NON_STREAM Mode
Handles HTTP complete response mode with proper API usage and padding fixes
"""
import os
import re
import uuid
import json
import queue
import asyncio
import traceback
import requests
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
    """ElevenLabs TTS Provider - NON_STREAM Mode"""

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

        # Output format - always PCM 16kHz for consistency
        self.output_format = config.get("output_format", "pcm_16000")
        self.language_code = config.get("language_code", "")

        # Opus encoder for PCM to Opus conversion
        self.opus_encoder = opus_encoder_utils.OpusEncoderUtils(
            sample_rate=16000, channels=1, frame_size_ms=60
        )

        # Build API URL
        self.tts_url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}"

        # Validate API key
        model_key_msg = check_model_key("TTS", self.api_key)
        if model_key_msg:
            logger.bind(tag=TAG).error(model_key_msg)

        logger.bind(tag=TAG).info(
            f"[NON_STREAM] ElevenLabs TTS initialized | "
            f"voice_id={self.voice_id} | "
            f"model={self.model_id} | "
            f"output_format={self.output_format}"
        )

    def tts_text_priority_thread(self):
        """NON_STREAM mode: Accumulate text and send complete HTTP request"""
        accumulated_text = []

        while not self.conn.stop_event.is_set():
            try:
                message = self.tts_text_queue.get(timeout=1)
                logger.bind(tag=TAG).trace(
                    f"[NON_STREAM] Received TTS task | {message.sentence_type.name} | {message.content_type.name}"
                )

                # Reset on FIRST message
                if message.sentence_type == SentenceType.FIRST:
                    self.conn.client_abort = False
                    accumulated_text.clear()
                    self.before_stop_play_files.clear()

                # Check for abort
                if self.conn.client_abort:
                    logger.bind(tag=TAG).info("[NON_STREAM] Received abort signal, clearing buffer")
                    accumulated_text.clear()
                    continue

                # Accumulate text content
                if ContentType.TEXT == message.content_type:
                    if message.content_detail:
                        accumulated_text.append(message.content_detail)
                        logger.bind(tag=TAG).trace(
                            f"[NON_STREAM] Accumulated text: {message.content_detail}"
                        )

                # Handle audio files
                elif ContentType.FILE == message.content_type:
                    logger.bind(tag=TAG).info(
                        f"[NON_STREAM] Processing audio file: {message.content_file}"
                    )
                    if message.content_file and os.path.exists(message.content_file):
                        self._process_audio_file_stream(
                            message.content_file,
                            callback=lambda audio_data: self.handle_audio_file(
                                audio_data, message.content_detail
                            ),
                        )

                # On LAST message, send complete text to ElevenLabs
                if message.sentence_type == SentenceType.LAST:
                    full_text = "".join(accumulated_text)
                    if full_text.strip():
                        try:
                            logger.bind(tag=TAG).info(
                                f"[NON_STREAM] Sending complete text ({len(full_text)} chars) to ElevenLabs"
                            )
                            asyncio.run(self._text_to_speak_non_stream(full_text, None))
                            logger.bind(tag=TAG).info("[NON_STREAM] Audio generation complete")
                        except Exception as e:
                            logger.bind(tag=TAG).error(
                                f"[NON_STREAM] Failed to generate audio: {str(e)}"
                            )
                    else:
                        logger.bind(tag=TAG).debug("[NON_STREAM] No text to synthesize")

                    accumulated_text.clear()

            except queue.Empty:
                continue
            except Exception as e:
                logger.bind(tag=TAG).error(
                    f"[NON_STREAM] Processing error: {str(e)}, type: {type(e).__name__}, stack: {traceback.format_exc()}"
                )
                continue

    async def _text_to_speak_non_stream(self, text: str, output_file: Optional[str]):
        """NON_STREAM mode: Complete HTTP response"""
        try:
            # Clean markdown
            filtered_text = MarkdownCleaner.clean_markdown(text)

            # Fix spacing around punctuation that may have been introduced by streaming
            # Remove space before punctuation (e.g., " ," -> ",")
            filtered_text = re.sub(r'\s+([,!?;：。！？；、])', r'\1', filtered_text)

            # Build request payload - NO output_format here!
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

            # Build URL with output_format as query parameter (CORRECT WAY)
            url = f"{self.tts_url}?output_format={self.output_format}"

            logger.bind(tag=TAG).debug(f"[NON_STREAM] POST request to {url}")
            logger.bind(tag=TAG).debug(f"[NON_STREAM] Request headers: xi-api-key=***")
            logger.bind(tag=TAG).debug(
                f"[NON_STREAM] Request payload: {json.dumps(payload, indent=2, ensure_ascii=False)}"
            )

            # Send HTTP POST request
            response = requests.post(url, json=payload, headers=headers, timeout=30)

            logger.bind(tag=TAG).debug(f"[NON_STREAM] Response status: {response.status_code}")
            logger.bind(tag=TAG).debug(
                f"[NON_STREAM] Response headers: {dict(response.headers)}"
            )

            if response.status_code == 200:
                audio_data = response.content
                logger.bind(tag=TAG).info(
                    f"[NON_STREAM] Received {len(audio_data)} bytes of audio PCM data"
                )

                # Log first 100 bytes for debugging
                logger.bind(tag=TAG).debug(
                    f"[NON_STREAM] First 32 PCM bytes (hex): {audio_data[:32].hex()}"
                )

                if output_file:
                    # Save to file if requested
                    with open(output_file, "wb") as audio_file:
                        audio_file.write(audio_data)
                    logger.bind(tag=TAG).info(
                        f"[NON_STREAM] Audio saved to file: {output_file}"
                    )
                else:
                    # Process audio and send to queue
                    # Send FIRST marker
                    self.tts_audio_queue.put((SentenceType.FIRST, [], filtered_text))

                    # Convert PCM to Opus and send in chunks
                    await self._process_pcm_audio_non_stream(audio_data)

                    # Send LAST marker
                    self.tts_audio_queue.put((SentenceType.LAST, [], None))

                    return audio_data
            else:
                error_msg = f"[NON_STREAM] Request failed: {response.status_code}"
                logger.bind(tag=TAG).error(error_msg)
                logger.bind(tag=TAG).error(f"[NON_STREAM] Response body: {response.text}")

                # Send LAST marker on error to unblock downstream
                self.tts_audio_queue.put((SentenceType.LAST, [], None))
                raise Exception(
                    f"ElevenLabs TTS request failed: {response.status_code} - {response.text}"
                )

        except Exception as e:
            logger.bind(tag=TAG).error(f"[NON_STREAM] Failed to generate TTS: {e}")
            logger.bind(tag=TAG).error(f"[NON_STREAM] Traceback: {traceback.format_exc()}")
            # Send LAST marker on error to unblock downstream
            self.tts_audio_queue.put((SentenceType.LAST, [], None))
            raise

    async def _process_pcm_audio_non_stream(self, pcm_data: bytes):
        """
        Process complete PCM audio for NON_STREAM mode
        Converts PCM 16kHz mono to Opus frames

        Args:
            pcm_data: Complete PCM audio data from ElevenLabs
        """
        try:
            # Calculate frame size in bytes
            # frame_size_ms = 60ms, sample_rate = 16000Hz, channels = 1, bits = 16
            # frame_bytes = 16000 * 1 * 60 / 1000 * 2 = 1920 bytes
            frame_bytes = int(
                self.opus_encoder.sample_rate
                * self.opus_encoder.channels
                * self.opus_encoder.frame_size_ms
                / 1000
                * 2
            )

            total_bytes = len(pcm_data)
            logger.bind(tag=TAG).debug(
                f"[NON_STREAM] Processing {total_bytes} bytes PCM audio"
            )
            logger.bind(tag=TAG).debug(
                f"[NON_STREAM] Frame size: {frame_bytes} bytes ({self.opus_encoder.frame_size_ms}ms @ 16kHz)"
            )

            # Process complete frames
            offset = 0
            frame_count = 0

            while offset + frame_bytes <= total_bytes:
                frame = pcm_data[offset : offset + frame_bytes]
                self.opus_encoder.encode_pcm_to_opus_stream(
                    frame, end_of_stream=False, callback=self.handle_opus
                )
                offset += frame_bytes
                frame_count += 1

            # Handle remaining data (incomplete final frame)
            remaining_bytes = total_bytes - offset
            if remaining_bytes > 0:
                logger.bind(tag=TAG).debug(
                    f"[NON_STREAM] Remaining {remaining_bytes} bytes (incomplete frame, will be padded)"
                )

                # Pass incomplete frame to encoder with end_of_stream=True
                # The encoder will pad internally with zeros to complete the frame
                remaining_frame = pcm_data[offset:]
                self.opus_encoder.encode_pcm_to_opus_stream(
                    remaining_frame,
                    end_of_stream=True,  # Signal this is the final frame, encoder will pad
                    callback=self.handle_opus,
                )
                frame_count += 1
            else:
                # All data processed perfectly without remainder
                logger.bind(tag=TAG).debug(
                    f"[NON_STREAM] All frames complete, no padding needed"
                )

            logger.bind(tag=TAG).info(
                f"[NON_STREAM] Successfully encoded {frame_count} Opus frames from {total_bytes} bytes PCM"
            )

        except Exception as e:
            logger.bind(tag=TAG).error(f"[NON_STREAM] PCM processing error: {e}")
            logger.bind(tag=TAG).error(f"[NON_STREAM] Traceback: {traceback.format_exc()}")
            raise

    async def text_to_speak(self, text: str, output_file: Optional[str]):
        """
        Implementation of abstract method from TTSProviderBase
        Delegates to the NON_STREAM mode handler

        Args:
            text: Text to convert to speech
            output_file: Optional file path to save audio

        Returns:
            bytes: Audio data if output_file is None, otherwise None
        """
        return await self._text_to_speak_non_stream(text, output_file)

    async def close(self):
        """Resource cleanup"""
        pass
