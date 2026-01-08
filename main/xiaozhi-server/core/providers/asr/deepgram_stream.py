import time
import asyncio
from typing import Optional, Tuple, List
from config.logger import setup_logging
from core.providers.asr.base import ASRProviderBase
from core.providers.asr.dto.dto import InterfaceType
from core.providers.shared.deepgram_client import DeepgramConnectionManager

TAG = __name__
logger = setup_logging()


class ASRProvider(ASRProviderBase):
    """Deepgram streaming ASR provider with built-in VAD"""

    def __init__(self, config: dict, delete_audio_file: bool):
        super().__init__()
        self.interface_type = InterfaceType.STREAM
        self.config = config
        self.output_dir = config.get("output_dir", "tmp/")
        self.delete_audio_file = delete_audio_file

        # Connection manager
        self.connection_manager = None

        # Transcription state
        self.transcription_buffer = []
        self.is_speech_active = False
        self.last_speech_end_time = None

        # Connection state
        self.is_processing = False

        logger.bind(tag=TAG).info(
            f"Initialized Deepgram ASR: model={config.get('model', 'nova-2')}, "
            f"language={config.get('language', 'multi')}, "
            f"endpointing={config.get('endpointing', 300)}ms"
        )

    async def receive_audio(self, conn, audio: bytes, audio_have_voice: bool):
        """
        Receive and process audio packets

        Args:
            conn: Connection handler object
            audio: Audio packet (Opus or PCM format)
            audio_have_voice: Whether voice was detected by VAD
        """
        # Always buffer audio for potential replay
        conn.asr_audio.append(audio)
        conn.asr_audio = conn.asr_audio[-10:]  # Keep last 10 packets

        # If voice detected and not yet connected, establish connection
        if audio_have_voice and not self.is_processing:
            try:
                self.is_processing = True

                # Create connection manager if not exists
                if not self.connection_manager:
                    self.connection_manager = DeepgramConnectionManager(
                        conn, self.config, self
                    )

                # Establish WebSocket connection
                await self.connection_manager.connect()

                # Send buffered audio packets
                logger.bind(tag=TAG).debug(
                    f"Sending {len(conn.asr_audio)} buffered audio packets"
                )
                for buffered_audio in conn.asr_audio:
                    if buffered_audio:
                        await self.connection_manager.send_audio(buffered_audio)

            except Exception as e:
                logger.bind(tag=TAG).error(f"Failed to establish Deepgram connection: {e}")
                self.is_processing = False
                return

        # Stream current audio packet if connected
        if self.connection_manager and self.connection_manager.is_connected:
            if audio:
                await self.connection_manager.send_audio(audio)

    async def speech_to_text(
        self, opus_data: List[bytes], session_id: str, audio_format="opus"
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Convert speech to text (called when voice stops)

        Args:
            opus_data: Audio data (not used in streaming mode)
            session_id: Session identifier
            audio_format: Audio format

        Returns:
            Tuple of (transcript, language) or (transcript, None)
        """
        try:
            # Signal end of audio stream
            if self.connection_manager and self.connection_manager.is_connected:
                await self.connection_manager.finish()

            # Wait for final results (with timeout)
            final_transcript = await self._wait_for_final_results(timeout=3.0)

            # Close connection to free resources
            if self.connection_manager:
                await self.connection_manager.close()
                self.connection_manager = None

            # Reset state for next utterance
            self.transcription_buffer.clear()
            self.is_speech_active = False
            self.is_processing = False

            logger.bind(tag=TAG).info(f"Final transcript: {final_transcript}")

            return (final_transcript, None)

        except Exception as e:
            logger.bind(tag=TAG).error(f"Error in speech_to_text: {e}")
            import traceback
            logger.bind(tag=TAG).debug(f"Traceback: {traceback.format_exc()}")
            return ("", None)

    async def _wait_for_final_results(self, timeout: float) -> str:
        """
        Wait for final transcription results

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            Final transcript or empty string if timeout
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            if self.transcription_buffer:
                # Join all transcripts with space
                final_text = " ".join(self.transcription_buffer)
                return final_text

            await asyncio.sleep(0.1)

        # Timeout - return partial results if any
        if self.transcription_buffer:
            logger.bind(tag=TAG).warning(
                "Transcription timeout - returning partial results"
            )
            return " ".join(self.transcription_buffer)

        logger.bind(tag=TAG).warning("Transcription timeout - no results")
        return ""

    def get_vad_events(self) -> dict:
        """
        Get current VAD state for VAD provider wrapper

        Returns:
            Dictionary with speech_active and last_speech_end
        """
        return {
            "speech_active": self.is_speech_active,
            "last_speech_end": self.last_speech_end_time,
        }

    def stop_ws_connection(self):
        """Stop WebSocket connection (called by base class)"""
        if self.connection_manager:
            asyncio.create_task(self.connection_manager.close())
            self.connection_manager = None
        self.is_processing = False

    async def close(self):
        """Cleanup resources"""
        try:
            if self.connection_manager:
                await self.connection_manager.close()
                self.connection_manager = None

            self.transcription_buffer.clear()
            self.is_speech_active = False
            self.is_processing = False

            logger.bind(tag=TAG).debug("Deepgram ASR resources released")

        except Exception as e:
            logger.bind(tag=TAG).debug(f"Error releasing Deepgram ASR resources: {e}")
