"""UTF-8 Safe Stream Buffer for LLM Streaming

Ensures multi-byte UTF-8 characters and Vietnamese word boundaries
are preserved during streaming from LLM to TTS.
"""

from loguru import logger


class UTF8StreamBuffer:
    """Buffer for UTF-8 safe text streaming with word boundary detection.

    Handles:
    - Incomplete multi-byte UTF-8 sequences (Vietnamese diacritics, emoji)
    - Word boundary buffering for better Vietnamese word coherence
    - Optional timeout to prevent stalling on long words
    """

    def __init__(self, wait_for_word_boundary=True):
        """Initialize the stream buffer.

        Args:
            wait_for_word_boundary: If True, waits for space/punctuation
                                   before yielding. This prevents words
                                   like "Mình" from being split. If False,
                                   only ensures UTF-8 boundaries.
        """
        self._text_buffer = ""
        self.wait_for_word_boundary = wait_for_word_boundary

    def add_chunk(self, chunk: str) -> str:
        """Add chunk and return safe-to-yield text.

        If incomplete UTF-8 or word boundary not reached, buffers and
        returns empty string. Otherwise returns accumulated text.

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
            # For word boundary mode, check if this chunk ends with boundary
            if self.wait_for_word_boundary:
                return self._handle_word_boundary(chunk)
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

        # UTF-8 is complete, check word boundary
        if self.wait_for_word_boundary:
            return self._handle_word_boundary(self._text_buffer)

        # Safe to yield without word boundary check
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

    def _handle_word_boundary(self, text: str) -> str:
        """Handle word boundary buffering.

        Yields text up to last word boundary. If no boundary found,
        buffers text and returns empty string.

        Args:
            text: Text to check for word boundaries

        Returns:
            Text up to last boundary, or empty if buffering
        """
        if not text:
            return ""

        # Word boundaries: space, punctuation, newline
        boundaries = {
            ' ', '\t', '\n', '\r',
            '.', ',', '!', '?', ';', ':',
            '。', '，', '！', '？', '；', '：',
            '-', '—', '~'
        }

        # Find last word boundary
        last_boundary_pos = -1
        for i in range(len(text) - 1, -1, -1):
            if text[i] in boundaries:
                last_boundary_pos = i
                break

        if last_boundary_pos == -1:
            # No boundary found, buffer everything
            # But only if not already in buffer (for ASCII fast path)
            if text != self._text_buffer:
                self._text_buffer += text
            logger.trace(
                f"[UTF8_BUFFER] No word boundary, buffering "
                f"{len(self._text_buffer)} chars"
            )
            return ""

        # Found boundary, yield up to and including it
        result = text[:last_boundary_pos + 1]
        remaining = text[last_boundary_pos + 1:]

        self._text_buffer = remaining
        logger.trace(
            f"[UTF8_BUFFER] Word boundary found, yielding "
            f"{repr(result[:50])}"
        )
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
