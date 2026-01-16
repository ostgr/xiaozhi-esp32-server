"""UTF-8 Safe Stream Buffer for LLM Streaming

Ensures multi-byte UTF-8 characters are preserved during streaming.
"""

from loguru import logger


class UTF8StreamBuffer:
    """Buffer for UTF-8 safe text streaming.

    Handles incomplete multi-byte UTF-8 sequences (Vietnamese diacritics, emoji)
    to prevent character corruption during streaming.
    """

    def __init__(self):
        """Initialize the stream buffer."""
        self._text_buffer = ""

    def add_chunk(self, chunk: str) -> str:
        """Add chunk and return safe-to-yield text.

        If incomplete UTF-8 sequence detected, buffers and returns empty string.
        Otherwise returns accumulated text.

        Args:
            chunk: Text chunk from LLM streaming

        Returns:
            Complete text safe to yield, or empty string if buffering
        """
        if not chunk:
            return ""

        # Fast path: pure ASCII (0-127)
        if all(ord(c) < 128 for c in chunk):
            logger.trace(
                f"[UTF8_BUFFER] ASCII chunk (fast path): {repr(chunk[:50])}"
            )
            return chunk

        # Add to buffer
        self._text_buffer += chunk
        logger.trace(
            f"[UTF8_BUFFER] Added to buffer: {repr(chunk[:50])} "
            f"(total: {len(self._text_buffer)} chars)"
        )

        # Check for incomplete UTF-8 at end
        if self._has_incomplete_utf8_at_end(self._text_buffer):
            logger.trace(
                f"[UTF8_BUFFER] Incomplete UTF-8, buffering "
                f"(total: {len(self._text_buffer)} chars)"
            )
            return ""

        # Safe to yield
        result = self._text_buffer
        self._text_buffer = ""
        logger.trace(f"[UTF8_BUFFER] Yielding: {repr(result[:50])}")
        return result

    def flush(self) -> str:
        """Force flush remaining buffer content at stream end.

        Returns:
            Any remaining buffered text
        """
        result = self._text_buffer
        if result:
            logger.trace(f"[UTF8_BUFFER] Flushing: {repr(result[:50])}")
        self._text_buffer = ""
        return result

    def _has_incomplete_utf8_at_end(self, text: str) -> bool:
        """Check if text ends with incomplete UTF-8 sequence.

        UTF-8 Encoding:
        - 0xxxxxxx = 1-byte (ASCII)
        - 110xxxxx 10xxxxxx = 2-byte
        - 1110xxxx 10xxxxxx 10xxxxxx = 3-byte
        - 11110xxx 10xxxxxx 10xxxxxx 10xxxxxx = 4-byte

        Args:
            text: Text to check

        Returns:
            True if incomplete UTF-8, False if complete
        """
        if not text:
            return False

        try:
            text_bytes = text.encode("utf-8")
        except UnicodeEncodeError:
            logger.warning(
                "[UTF8_BUFFER] UnicodeEncodeError in validation"
            )
            return True

        if not text_bytes:
            return False

        # Check last 1-4 bytes for incomplete sequence
        for i in range(1, min(5, len(text_bytes) + 1)):
            offset = -i
            byte = text_bytes[offset]

            # Single-byte char: 0xxxxxxx
            if (byte & 0b10000000) == 0:
                return False

            # 2-byte start: 110xxxxx
            if (byte & 0b11100000) == 0b11000000:
                return i < 2

            # 3-byte start: 1110xxxx
            if (byte & 0b11110000) == 0b11100000:
                return i < 3

            # 4-byte start: 11110xxx
            if (byte & 0b11111000) == 0b11110000:
                return i < 4

            # Continuation byte: 10xxxxxx (keep looking)
            if (byte & 0b11000000) == 0b10000000:
                continue

            # Invalid UTF-8
            logger.warning(f"[UTF8_BUFFER] Invalid UTF-8 byte: {byte:08b}")
            return True

        return False
