from core.providers.tts.base import TTSProviderBase

class DefaultTTS(TTSProviderBase):
    """Fallback TTS that does nothing - used when no TTS is configured"""
    
    async def text_to_speak(self, text, output_file):
        return None
