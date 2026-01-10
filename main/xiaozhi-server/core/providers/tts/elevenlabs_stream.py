"""
ElevenLabs TTS Provider - Factory/Dispatcher

Routes requests to the appropriate streaming mode implementation:
- DUAL_STREAM (WebSocket): Real-time bidirectional streaming
- SINGLE_STREAM (HTTP): Traditional streaming response
- NON_STREAM (HTTP): Complete response with fixed API usage

This file maintains backward compatibility by acting as a factory.
New implementations are in separate files for cleaner code and easier debugging.
"""
from config.logger import setup_logging
from core.providers.tts.dto.dto import InterfaceType

TAG = __name__
logger = setup_logging()


def get_tts_provider(config, delete_audio_file):
    """
    Factory function to get the appropriate ElevenLabs TTS provider
    based on interface_mode configuration

    Args:
        config: TTS configuration dictionary
        delete_audio_file: Callback function to delete audio files

    Returns:
        TTSProvider instance for the specified mode
    """
    # Determine streaming mode
    interface_mode = str(config.get("interface_mode", "dual_stream")).lower()

    if interface_mode == "single_stream":
        from core.providers.tts.elevenlabs_single_stream import TTSProvider
        logger.bind(tag=TAG).info(
            "Loading ElevenLabs SINGLE_STREAM mode (HTTP streaming)"
        )
        return TTSProvider(config, delete_audio_file)

    elif interface_mode == "non_stream":
        from core.providers.tts.elevenlabs_non_stream import TTSProvider
        logger.bind(tag=TAG).info(
            "Loading ElevenLabs NON_STREAM mode (HTTP complete)"
        )
        return TTSProvider(config, delete_audio_file)

    else:  # Default to DUAL_STREAM
        from core.providers.tts.elevenlabs_dual_stream import TTSProvider
        logger.bind(tag=TAG).info(
            "Loading ElevenLabs DUAL_STREAM mode (WebSocket)"
        )
        return TTSProvider(config, delete_audio_file)


# For backward compatibility, also expose as TTSProvider class
class TTSProvider:
    """Backward compatibility wrapper - delegates to appropriate implementation"""

    def __new__(cls, config, delete_audio_file):
        """
        Create instance of appropriate TTS provider based on config
        This makes TTSProvider work transparently as a factory
        """
        return get_tts_provider(config, delete_audio_file)
