#!/usr/bin/env python3
"""
Test ElevenLabs WebSocket connection stability
Usage: python test_elevenlabs_connection.py
"""
import asyncio
import websockets
import json

# Test configuration - IMPORTANT: Update with valid credentials
# Get API_KEY from https://elevenlabs.io/app/settings/api-keys
API_KEY = "sk_d455b25f6ef58bfd92d81ded5ffe7cd58ba235c3bb1174e5"
# Get VOICE_ID from https://elevenlabs.io/voice-library
VOICE_ID = "558B1EcdabtcSdleer40"
MODEL_ID = "eleven_multilingual_v2"
OUTPUT_FORMAT = "pcm_16000"

# Note: This test focuses on connection keepalive, not audio generation
# If you get "voice_id does not exist" errors, that's expected
# The important test is that the WebSocket connection stays OPEN


async def test_connection_without_keepalive():
    """Test connection WITHOUT keepalive (should fail after ~60s)"""
    print("=" * 60)
    print("TEST 1: Connection WITHOUT keepalive")
    print("=" * 60)

    url = (
        f"wss://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}/"
        f"stream-input?model_id={MODEL_ID}&output_format={OUTPUT_FORMAT}"
    )

    headers = {"xi-api-key": API_KEY}

    try:
        ws = await websockets.connect(url, additional_headers=headers, max_size=10000000)
        print("✓ Connection established")

        # Send BOS
        bos = {"text": " ", "xi_api_key": API_KEY}
        await ws.send(json.dumps(bos))
        print("✓ BOS sent")

        # Wait 90 seconds (should timeout)
        print("Waiting 90 seconds to test idle timeout...")
        for i in range(9):
            await asyncio.sleep(10)
            state = ws.state.name if hasattr(ws.state, 'name') else str(ws.state)
            print(f"  {(i+1)*10}s elapsed... (connection state={state})")

        # Try to send text
        if ws.state.value == 1:  # OPEN state
            await ws.send(json.dumps({"text": "Test"}))
            print("✓ Text sent after 90s - UNEXPECTED!")
        else:
            print("✗ Connection closed after idle - EXPECTED")

        await ws.close()
    except Exception as e:
        print(f"✗ Error: {e}")

    print()


async def test_connection_with_keepalive():
    """Test connection WITH keepalive (should survive 90s+)"""
    print("=" * 60)
    print("TEST 2: Connection WITH keepalive")
    print("=" * 60)

    url = (
        f"wss://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}/"
        f"stream-input?model_id={MODEL_ID}&output_format={OUTPUT_FORMAT}"
    )

    headers = {"xi-api-key": API_KEY}

    try:
        # WITH keepalive parameters
        ws = await websockets.connect(
            url,
            additional_headers=headers,
            max_size=10000000,
            ping_interval=30,
            ping_timeout=10,
            close_timeout=10,
        )
        print("✓ Connection established with keepalive")

        # Send BOS
        bos = {"text": " ", "xi_api_key": API_KEY}
        await ws.send(json.dumps(bos))
        print("✓ BOS sent")

        # Wait 90 seconds (should NOT timeout)
        print("Waiting 90 seconds to test keepalive...")
        for i in range(9):
            await asyncio.sleep(10)
            state_name = (
                ws.state.name
                if hasattr(ws.state, "name")
                else str(ws.state)
            )
            print(f"  {(i+1)*10}s elapsed... (state={state_name})")

        # Try to send text
        if ws.state.value == 1:  # OPEN state
            msg = {
                "text": "Test message",
                "try_trigger_generation": True,
            }
            await ws.send(json.dumps(msg))
            print("✓ Text sent after 90s - SUCCESS!")

            # Send EOS
            await ws.send(json.dumps({"text": ""}))
            print("✓ EOS sent")

            # Wait for response
            try:
                response = await asyncio.wait_for(
                    ws.recv(), timeout=5.0
                )
                data = json.loads(response)
                if "audio" in data:
                    print("✓ Received audio response")
            except asyncio.TimeoutError:
                print("⚠ No immediate response (API processing)")

        else:
            print("✗ Connection closed - keepalive FAILED")

        await ws.close()
        print("✓ Connection closed gracefully")
    except Exception as e:
        print(f"✗ Error: {e}")

    print()


async def main():
    print("\n" + "=" * 60)
    print("ElevenLabs WebSocket Connection Stability Test")
    print("=" * 60)
    print()

    # Test without keepalive first (expect failure)
    await test_connection_without_keepalive()

    # Wait a bit between tests
    await asyncio.sleep(5)

    # Test with keepalive (expect success)
    await test_connection_with_keepalive()

    print("=" * 60)
    print("Test complete!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
