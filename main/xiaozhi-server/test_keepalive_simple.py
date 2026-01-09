#!/usr/bin/env python3
"""
Simple keepalive test - Tests WebSocket keepalive functionality
without requiring valid ElevenLabs credentials.
Usage: python test_keepalive_simple.py
"""
import asyncio
import websockets


async def test_without_keepalive():
    """Test WITHOUT keepalive (connection may timeout)"""
    print("=" * 60)
    print("TEST 1: Echo WebSocket WITHOUT keepalive")
    print("=" * 60)

    try:
        # Using public echo server
        ws = await websockets.connect("wss://echo.websocket.org/")
        print("✓ Connection established")
        print(f"  Initial state: {ws.state.name}")

        # Send a message
        await ws.send("test")
        response = await ws.recv()
        print(f"✓ Message sent and received: {response}")

        # Now wait 30 seconds idle
        print("Waiting 30 seconds (idle, no pings)...")
        for i in range(3):
            await asyncio.sleep(10)
            print(f"  {(i+1)*10}s elapsed (state: {ws.state.name})")

        # Try to send again
        if ws.state.value == 1:  # OPEN
            await ws.send("still alive?")
            response = await ws.recv()
            print(f"✓ Still connected after 30s: {response}")
        else:
            print(f"✗ Connection lost (state: {ws.state.name})")

        await ws.close()
    except Exception as e:
        print(f"✗ Error: {e}")

    print()


async def test_with_keepalive():
    """Test WITH keepalive (should survive idle time)"""
    print("=" * 60)
    print("TEST 2: Echo WebSocket WITH keepalive")
    print("=" * 60)

    try:
        # WITH keepalive parameters
        ws = await websockets.connect(
            "wss://echo.websocket.org/",
            ping_interval=10,
            ping_timeout=5,
            close_timeout=10,
        )
        print("✓ Connection established with keepalive")
        print(f"  Initial state: {ws.state.name}")

        # Send a message
        await ws.send("test with keepalive")
        response = await ws.recv()
        print(f"✓ Message sent and received: {response}")

        # Now wait 40 seconds idle (pings every 10s)
        print("Waiting 40 seconds (with pings every 10s)...")
        for i in range(4):
            await asyncio.sleep(10)
            state_name = ws.state.name
            print(
                f"  {(i+1)*10}s elapsed "
                f"(state: {state_name})"
            )

        # Try to send again
        if ws.state.value == 1:  # OPEN
            await ws.send("still alive after 40s?")
            response = await ws.recv()
            print(f"✓ Still connected after 40s: {response}")
        else:
            print(f"✗ Connection lost (state: {ws.state.name})")

        await ws.close()
        print("✓ Connection closed gracefully")
    except Exception as e:
        print(f"✗ Error: {e}")

    print()


async def main():
    print("\n" + "=" * 60)
    print("WebSocket Keepalive Test (Generic)")
    print("=" * 60)
    print()

    # Test without keepalive first
    await test_without_keepalive()

    # Wait between tests
    await asyncio.sleep(5)

    # Test with keepalive
    await test_with_keepalive()

    print("=" * 60)
    print("Test complete!")
    print("=" * 60)
    print()
    print("Summary:")
    print("- TEST 1: Connection without keepalive may timeout")
    print("- TEST 2: Connection with keepalive survives idle time")
    print()
    print("The fix in elevenlabs_stream.py implements TEST 2 behavior")
    print("by adding ping_interval=30, ping_timeout=10, close_timeout=10")
    print()


if __name__ == "__main__":
    asyncio.run(main())
