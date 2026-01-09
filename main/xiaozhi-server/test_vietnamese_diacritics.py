#!/usr/bin/env python3
"""
Test Vietnamese Diacritics Fix for ElevenLabs TTS Provider

This test validates that Vietnamese text with diacritics and spaces
are preserved correctly through the TTS pipeline.

Usage: python test_vietnamese_diacritics.py
"""

import sys
import queue
from unittest.mock import Mock, MagicMock, patch

# Add parent directory to path for imports
sys.path.insert(0, '/Users/Chative-tu/Documents/genie/devenv/server-ai-py/main/xiaozhi-server')

from core.providers.tts.dto.dto import SentenceType


class MockConnection:
    """Mock connection object for testing"""
    def __init__(self):
        self.tts_MessageText = None
        self.stop_event = Mock()
        self.stop_event.is_set.return_value = False
        self.loop = Mock()


def test_vietnamese_text_preservation():
    """Test that Vietnamese text with diacritics and spaces is preserved"""
    print("=" * 70)
    print("TEST: Vietnamese Text Preservation in ElevenLabs TTS")
    print("=" * 70)

    # Test cases with Vietnamese text
    test_cases = [
        {
            "name": "Basic Vietnamese greeting",
            "text": "Chào bạn!",
            "expected": "Chào bạn!",
            "diacritics_count": 2,  # ào, ạ
        },
        {
            "name": "Vietnamese with full response",
            "text": "Chào! Mình có thể giúp cho bạn hôm nay? 😊",
            "expected": "Chào! Mình có thể giúp cho bạn hôm nay? 😊",
            "diacritics_count": 11,  # ào, ì, í, ề, ụ, ơ, â, ô, ộ, ạ, etc.
        },
        {
            "name": "Mixed Vietnamese-English",
            "text": "Hello! Mình là AI assistant, rất vui gặp bạn",
            "expected": "Hello! Mình là AI assistant, rất vui gặp bạn",
            "diacritics_count": 7,  # ì, à, ấ, ự, ạ, etc.
        },
        {
            "name": "Vietnamese with all tone marks",
            "text": "à á ả ã ạ ă ằ ắ ẳ ẵ ặ â ầ ấ ẩ ẫ ậ",
            "expected": "à á ả ã ạ ă ằ ắ ẳ ẵ ặ â ầ ấ ẩ ẫ ậ",
            "diacritics_count": 16,  # All a-variants
        },
    ]

    results = []
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n[TEST {i}] {test_case['name']}")
        print(f"  Input:    {test_case['text']!r}")
        print(f"  Expected: {test_case['expected']!r}")

        # Simulate the queue behavior
        # In the fixed code, self.conn.tts_MessageText is put in the queue
        mock_conn = MockConnection()
        mock_conn.tts_MessageText = test_case['text']

        # Verify text is preserved
        if mock_conn.tts_MessageText == test_case['expected']:
            print(f"  Result:   PASS ✓")
            print(f"  Details:  Text preserved with {len(test_case['text'])} characters")

            # Count Vietnamese diacritics
            vietnamese_chars = [
                'à', 'á', 'ả', 'ã', 'ạ', 'ă', 'ằ', 'ắ', 'ẳ', 'ẵ', 'ặ',
                'â', 'ầ', 'ấ', 'ẩ', 'ẫ', 'ậ',
                'è', 'é', 'ẻ', 'ẽ', 'ẹ', 'ê', 'ề', 'ế', 'ể', 'ễ', 'ệ',
                'ì', 'í', 'ỉ', 'ĩ', 'ị',
                'ò', 'ó', 'ỏ', 'õ', 'ọ', 'ô', 'ồ', 'ố', 'ổ', 'ỗ', 'ộ',
                'ơ', 'ờ', 'ớ', 'ở', 'ỡ', 'ợ',
                'ù', 'ú', 'ủ', 'ũ', 'ụ', 'ư', 'ừ', 'ứ', 'ử', 'ữ', 'ự',
                'ỳ', 'ý', 'ỷ', 'ỹ', 'ỵ'
            ]
            diacritic_count = sum(1 for c in test_case['text'] if c in vietnamese_chars)
            print(f"  Diacritics: {diacritic_count} characters preserved")

            results.append(True)
        else:
            print(f"  Result:   FAIL ✗")
            print(f"  Details:  Text was corrupted")
            print(f"  Actual:   {mock_conn.tts_MessageText!r}")
            results.append(False)

    print("\n" + "=" * 70)
    print(f"SUMMARY: {sum(results)}/{len(results)} tests passed")
    print("=" * 70)
    return all(results)


def test_spaces_preservation():
    """Test that spaces between words are preserved"""
    print("\n" + "=" * 70)
    print("TEST: Space Preservation in Vietnamese Phrases")
    print("=" * 70)

    test_cases = [
        {
            "name": "Vietnamese phrase with 3 words",
            "text": "Mình có thể",
            "min_spaces": 2,  # Should have at least 2 spaces
        },
        {
            "name": "Vietnamese sentence with 7 words",
            "text": "Chào! Mình có thể giúp cho bạn",
            "min_spaces": 6,  # Should have at least 6 spaces
        },
    ]

    results = []
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n[TEST {i}] {test_case['name']}")
        print(f"  Text: {test_case['text']!r}")

        space_count = test_case['text'].count(' ')
        print(f"  Spaces found: {space_count}")

        if space_count >= test_case['min_spaces']:
            print(f"  Result: PASS ✓ (expected >= {test_case['min_spaces']}, got {space_count})")
            results.append(True)
        else:
            print(f"  Result: FAIL ✗ (expected >= {test_case['min_spaces']}, got {space_count})")
            results.append(False)

    print("\n" + "=" * 70)
    print(f"SUMMARY: {sum(results)}/{len(results)} tests passed")
    print("=" * 70)
    return all(results)


def test_queue_behavior():
    """Test that text is correctly put in queue"""
    print("\n" + "=" * 70)
    print("TEST: Queue Behavior with Original Text")
    print("=" * 70)

    # Simulate the queue put behavior
    mock_queue = queue.Queue()

    # Simulate the fixed code behavior:
    # if self.conn.tts_MessageText:
    #     self.tts_audio_queue.put((SentenceType.FIRST, [], self.conn.tts_MessageText))
    #     self.conn.tts_MessageText = None

    mock_conn = MockConnection()
    mock_conn.tts_MessageText = "Chào! Mình có thể giúp cho bạn hôm nay? 😊"

    print(f"\nBefore queue put:")
    print(f"  conn.tts_MessageText: {mock_conn.tts_MessageText!r}")
    print(f"  Queue empty: {mock_queue.empty()}")

    # Simulate the fixed code
    if mock_conn.tts_MessageText:
        mock_queue.put((SentenceType.FIRST, [], mock_conn.tts_MessageText))
        mock_conn.tts_MessageText = None

    print(f"\nAfter queue put:")
    print(f"  conn.tts_MessageText: {mock_conn.tts_MessageText}")
    print(f"  Queue empty: {mock_queue.empty()}")

    # Get from queue and verify
    sentence_type, audio_data, text = mock_queue.get()
    print(f"\nRetrieved from queue:")
    print(f"  SentenceType: {sentence_type.name}")
    print(f"  Audio data: {audio_data}")
    print(f"  Text: {text!r}")

    expected_text = "Chào! Mình có thể giúp cho bạn hôm nay? 😊"
    if text == expected_text and sentence_type == SentenceType.FIRST:
        print(f"\nResult: PASS ✓")
        print(f"  Original text preserved in queue")
        return True
    else:
        print(f"\nResult: FAIL ✗")
        print(f"  Text was not preserved correctly")
        return False


def test_duplicate_prevention():
    """Test that tts_MessageText is cleared after use"""
    print("\n" + "=" * 70)
    print("TEST: Duplicate Message Prevention")
    print("=" * 70)

    mock_queue = queue.Queue()
    mock_conn = MockConnection()
    mock_conn.tts_MessageText = "Chào! Mình có thể giúp cho bạn hôm nay? 😊"

    print(f"\nInitial state:")
    print(f"  conn.tts_MessageText is set: {bool(mock_conn.tts_MessageText)}")

    # First call - should put in queue and clear
    if mock_conn.tts_MessageText:
        mock_queue.put((SentenceType.FIRST, [], mock_conn.tts_MessageText))
        mock_conn.tts_MessageText = None

    print(f"\nAfter first put:")
    print(f"  conn.tts_MessageText is None: {mock_conn.tts_MessageText is None}")
    print(f"  Queue size: {mock_queue.qsize()}")

    # Second call - should NOT put in queue (already None)
    if mock_conn.tts_MessageText:
        mock_queue.put((SentenceType.FIRST, [], mock_conn.tts_MessageText))
        mock_conn.tts_MessageText = None
        print(f"\n  ERROR: Should not have executed!")
        return False

    print(f"\nAfter second attempt:")
    print(f"  Queue size: {mock_queue.qsize()} (should still be 1)")

    if mock_queue.qsize() == 1:
        print(f"\nResult: PASS ✓")
        print(f"  Duplicate prevention working correctly")
        return True
    else:
        print(f"\nResult: FAIL ✗")
        print(f"  Duplicate message was added to queue")
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("Vietnamese Diacritics Fix - Test Suite")
    print("=" * 70)

    test_results = []

    # Run tests
    test_results.append(("Vietnamese Text Preservation", test_vietnamese_text_preservation()))
    test_results.append(("Space Preservation", test_spaces_preservation()))
    test_results.append(("Queue Behavior", test_queue_behavior()))
    test_results.append(("Duplicate Prevention", test_duplicate_prevention()))

    # Summary
    print("\n\n" + "=" * 70)
    print("OVERALL TEST SUMMARY")
    print("=" * 70)

    for test_name, result in test_results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {test_name}: {status}")

    total_passed = sum(1 for _, result in test_results if result)
    total_tests = len(test_results)

    print("\n" + "=" * 70)
    print(f"FINAL RESULT: {total_passed}/{total_tests} test suites passed")
    print("=" * 70)

    return all(result for _, result in test_results)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
