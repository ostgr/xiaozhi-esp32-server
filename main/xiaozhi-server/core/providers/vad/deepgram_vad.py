from config.logger import setup_logging
from core.providers.vad.base import VADProviderBase

TAG = __name__
logger = setup_logging()


class VADProvider(VADProviderBase):
    """
    Deepgram VAD provider - lightweight wrapper that delegates to Deepgram ASR's built-in VAD

    This provider acts as a bridge between xiaozhi's VAD interface and Deepgram's
    SpeechStarted events. The actual VAD logic is handled by the Deepgram ASR provider
    via WebSocket events.
    """

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.asr_provider = None
        logger.bind(tag=TAG).info("Initialized Deepgram VAD wrapper")

    def is_vad(self, conn, data: bytes) -> bool:
        """
        Check if speech is active based on Deepgram's VAD events

        Args:
            conn: Connection handler object
            data: Audio data packet (not used, VAD state comes from ASR provider)

        Returns:
            True if speech is active, False otherwise
        """
        # Get reference to ASR provider on first call
        if not self.asr_provider and hasattr(conn, "asr"):
            self.asr_provider = conn.asr
            logger.bind(tag=TAG).debug("Linked Deepgram VAD to ASR provider")

        # Delegate to ASR provider's VAD state
        if self.asr_provider and hasattr(self.asr_provider, "get_vad_events"):
            vad_events = self.asr_provider.get_vad_events()
            speech_active = vad_events.get("speech_active", False)

            # Log state changes for debugging
            if hasattr(self, "_last_state") and self._last_state != speech_active:
                logger.bind(tag=TAG).debug(
                    f"VAD state changed: {self._last_state} -> {speech_active}"
                )
            self._last_state = speech_active

            return speech_active

        # Fallback: if ASR provider not available yet, return False
        return False
