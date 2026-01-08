import time
import asyncio
from typing import Optional, Callable
from config.logger import setup_logging
from deepgram import (
    DeepgramClient,
    DeepgramClientOptions,
    LiveTranscriptionEvents,
    LiveOptions,
)

TAG = __name__
logger = setup_logging()


class DeepgramConnectionManager:
    """Manages Deepgram WebSocket connection for streaming ASR with built-in VAD"""

    def __init__(self, conn_obj, config: dict, asr_provider):
        """
        Initialize Deepgram connection manager

        Args:
            conn_obj: Connection handler object from xiaozhi
            config: Deepgram configuration dict
            asr_provider: Reference to parent ASR provider for callbacks
        """
        self.conn = conn_obj
        self.asr_provider = asr_provider

        # Configuration
        self.api_key = config.get("api_key", "")
        self.model = config.get("model", "nova-2")
        self.language = config.get("language", "multi")
        self.endpointing_ms = config.get("endpointing", 300)
        self.encoding = config.get("encoding", "opus")
        self.sample_rate = config.get("sample_rate", 16000)
        self.channels = config.get("channels", 1)
        self.smart_format = config.get("smart_format", True)

        # Connection state
        self.dg_connection = None
        self.is_connected = False
        self.is_processing = False
        self.connection_opened = False

        # Audio buffering
        self.audio_buffer = []

        # Timing
        self.last_audio_time = time.time()
        self.connection_start_time = None

        # Error tracking
        self.retry_count = 0
        self.max_retries = 3
        self.consecutive_errors = 0

    async def connect(self):
        """Establish WebSocket connection to Deepgram"""
        if self.is_connected:
            logger.bind(tag=TAG).debug("Already connected to Deepgram")
            return

        if not self.api_key or self.api_key == "YOUR_DEEPGRAM_API_KEY":
            error_msg = "Invalid Deepgram API key in config.yaml. Please configure a valid API key."
            logger.bind(tag=TAG).error(error_msg)
            raise ValueError(error_msg)

        try:
            self.connection_start_time = time.time()
            logger.bind(tag=TAG).info(f"Establishing Deepgram connection (attempt {self.retry_count + 1}/{self.max_retries})")

            # Create Deepgram client
            config = DeepgramClientOptions(
                api_key=self.api_key,
                options={"keepalive": "true"}
            )
            deepgram = DeepgramClient(api_key=self.api_key, config=config)

            # Configure live transcription options
            options = LiveOptions(
                model=self.model,
                language=self.language,
                encoding=self.encoding,
                sample_rate=self.sample_rate,
                channels=self.channels,
                smart_format=self.smart_format,

                # VAD and endpointing
                vad_events=True,  # Enable SpeechStarted events
                endpointing=self.endpointing_ms,  # Silence threshold

                # Only final results (no interim)
                interim_results=False,
            )

            # Create connection
            self.dg_connection = deepgram.listen.asynclive.v("1")

            # Register event handlers
            self.dg_connection.on(LiveTranscriptionEvents.Open, self._on_open)
            self.dg_connection.on(LiveTranscriptionEvents.Transcript, self._on_message)
            self.dg_connection.on(LiveTranscriptionEvents.SpeechStarted, self._on_speech_started)
            self.dg_connection.on(LiveTranscriptionEvents.UtteranceEnd, self._on_utterance_end)
            self.dg_connection.on(LiveTranscriptionEvents.Close, self._on_close)
            self.dg_connection.on(LiveTranscriptionEvents.Error, self._on_error)

            # Start connection
            if await self.dg_connection.start(options):
                self.is_connected = True
                self.is_processing = True
                connection_time = (time.time() - self.connection_start_time) * 1000
                logger.bind(tag=TAG).info(f"Deepgram connection established in {connection_time:.0f}ms")

                # Reset error counters on successful connection
                self.retry_count = 0
                self.consecutive_errors = 0
            else:
                raise Exception("Failed to start Deepgram connection")

        except Exception as e:
            self.is_connected = False
            self.is_processing = False
            logger.bind(tag=TAG).error(f"Failed to connect to Deepgram: {e}")

            # Retry logic
            if self.retry_count < self.max_retries:
                self.retry_count += 1
                await asyncio.sleep(1.0)
                await self.connect()
            else:
                raise

    async def send_audio(self, audio_data: bytes):
        """
        Stream audio packet to Deepgram

        Args:
            audio_data: Audio packet in Opus or PCM format
        """
        if not self.is_connected or not self.dg_connection:
            logger.bind(tag=TAG).warning("Cannot send audio: not connected")
            return

        try:
            self.last_audio_time = time.time()
            await self.dg_connection.send(audio_data)

        except Exception as e:
            logger.bind(tag=TAG).error(f"Error sending audio to Deepgram: {e}")
            self.consecutive_errors += 1

            if self.consecutive_errors >= 3:
                logger.bind(tag=TAG).error("Too many consecutive errors, closing connection")
                await self.close()

    async def finish(self):
        """Signal end of audio stream"""
        if self.dg_connection and self.is_connected:
            try:
                await self.dg_connection.finish()
                logger.bind(tag=TAG).debug("Sent finish signal to Deepgram")
            except Exception as e:
                logger.bind(tag=TAG).debug(f"Error sending finish signal: {e}")

    async def close(self):
        """Close connection and cleanup resources"""
        if self.dg_connection:
            try:
                await self.dg_connection.finish()
                self.is_connected = False
                self.is_processing = False
                self.connection_opened = False
                self.audio_buffer.clear()
                logger.bind(tag=TAG).debug("Deepgram connection closed")
            except Exception as e:
                logger.bind(tag=TAG).debug(f"Error closing Deepgram connection: {e}")
            finally:
                self.dg_connection = None

    def _on_open(self, *args, **kwargs):
        """Handle connection open event"""
        self.connection_opened = True
        connection_time = (time.time() - self.connection_start_time) * 1000 if self.connection_start_time else 0
        logger.bind(tag=TAG).info(f"Deepgram WebSocket opened ({connection_time:.0f}ms)")

    def _on_speech_started(self, *args, **kwargs):
        """Handle SpeechStarted event from Deepgram VAD"""
        logger.bind(tag=TAG).debug("Deepgram detected speech start")

        # Update xiaozhi state machine
        if self.conn:
            self.conn.client_have_voice = True

        # Update ASR provider state
        if self.asr_provider:
            self.asr_provider.is_speech_active = True

    def _on_message(self, *args, **kwargs):
        """Handle transcript results from Deepgram"""
        try:
            # Extract result from args (Deepgram SDK passes result as first arg)
            if not args:
                return

            result = args[0]

            # Log raw result for debugging
            logger.bind(tag=TAG).debug(f"Deepgram result type: {type(result)}")

            # Check if this is a final result
            if hasattr(result, 'is_final') and result.is_final:
                # Extract transcript
                if hasattr(result, 'channel') and result.channel:
                    alternatives = getattr(result.channel, 'alternatives', [])
                    if alternatives and len(alternatives) > 0:
                        transcript = alternatives[0].transcript

                        if transcript and transcript.strip():
                            logger.bind(tag=TAG).info(f"Deepgram transcript: {transcript}")

                            # Store in ASR provider's buffer
                            if self.asr_provider:
                                self.asr_provider.transcription_buffer.append(transcript)

                            # Check if this is end of utterance (speech_final)
                            if hasattr(result, 'speech_final') and result.speech_final:
                                logger.bind(tag=TAG).debug("Deepgram detected utterance end")
                                self._trigger_voice_stop()

        except Exception as e:
            logger.bind(tag=TAG).error(f"Error processing Deepgram message: {e}")
            import traceback
            logger.bind(tag=TAG).debug(f"Traceback: {traceback.format_exc()}")

    def _on_utterance_end(self, *args, **kwargs):
        """Handle UtteranceEnd event (alternative endpointing signal)"""
        logger.bind(tag=TAG).debug("Deepgram UtteranceEnd event received")
        self._trigger_voice_stop()

    def _trigger_voice_stop(self):
        """Trigger voice stop in xiaozhi state machine"""
        if self.conn:
            self.conn.client_voice_stop = True

        if self.asr_provider:
            self.asr_provider.is_speech_active = False
            self.asr_provider.last_speech_end_time = time.time()

    def _on_close(self, *args, **kwargs):
        """Handle connection close event"""
        logger.bind(tag=TAG).info("Deepgram WebSocket closed")
        self.is_connected = False
        self.is_processing = False
        self.connection_opened = False

    def _on_error(self, *args, **kwargs):
        """Handle connection error event"""
        error = args[0] if args else "Unknown error"
        logger.bind(tag=TAG).error(f"Deepgram error: {error}")

        self.consecutive_errors += 1

        # Don't automatically retry here - let the receive_audio logic handle it
        self.is_connected = False
        self.is_processing = False
