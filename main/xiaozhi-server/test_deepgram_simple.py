#!/usr/bin/env python3
"""
Simple standalone test for Deepgram providers (no xiaozhi dependencies)
"""
import sys
import os

def test_deepgram_sdk():
    """Test that Deepgram SDK is installed"""
    print("Testing Deepgram SDK installation...")
    try:
        import deepgram
        from deepgram import DeepgramClient, LiveOptions, LiveTranscriptionEvents
        print(f"✓ Deepgram SDK installed: version {deepgram.__version__ if hasattr(deepgram, '__version__') else 'unknown'}")
        return True
    except ImportError as e:
        print(f"✗ Deepgram SDK not installed: {e}")
        return False


def test_file_structure():
    """Test that all required files exist"""
    print("\nTesting file structure...")

    files = [
        "core/providers/shared/__init__.py",
        "core/providers/shared/deepgram_client.py",
        "core/providers/asr/deepgram_stream.py",
        "core/providers/vad/deepgram_vad.py",
    ]

    all_exist = True
    for file_path in files:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"✓ {file_path} exists ({size} bytes)")
        else:
            print(f"✗ {file_path} not found")
            all_exist = False

    return all_exist


def test_python_syntax():
    """Test that Python files have valid syntax"""
    print("\nTesting Python syntax...")

    files = [
        "core/providers/shared/deepgram_client.py",
        "core/providers/asr/deepgram_stream.py",
        "core/providers/vad/deepgram_vad.py",
    ]

    all_valid = True
    for file_path in files:
        try:
            with open(file_path, 'r') as f:
                code = f.read()
            compile(code, file_path, 'exec')
            print(f"✓ {file_path} syntax valid")
        except SyntaxError as e:
            print(f"✗ {file_path} syntax error: {e}")
            all_valid = False
        except FileNotFoundError:
            print(f"✗ {file_path} not found")
            all_valid = False

    return all_valid


def test_config_syntax():
    """Test config.yaml syntax"""
    print("\nTesting config.yaml syntax...")

    try:
        from ruamel.yaml import YAML
        yaml = YAML()

        with open("config.yaml", "r") as f:
            config = yaml.load(f)

        # Check Deepgram sections exist
        has_vad = "DeepgramVAD" in config.get("VAD", {})
        has_asr = "DeepgramStreamASR" in config.get("ASR", {})

        if has_vad and has_asr:
            print("✓ config.yaml valid with Deepgram sections")

            # Show config details
            asr_config = config["ASR"]["DeepgramStreamASR"]
            print(f"  Model: {asr_config.get('model')}")
            print(f"  Language: {asr_config.get('language')}")
            print(f"  Encoding: {asr_config.get('encoding')}")
            print(f"  Endpointing: {asr_config.get('endpointing')}ms")

            if asr_config.get("api_key") == "YOUR_DEEPGRAM_API_KEY":
                print("  ⚠️  API key needs configuration")
            else:
                print("  ✓ API key configured")

            return True
        else:
            print(f"✗ Missing sections: VAD={has_vad}, ASR={has_asr}")
            return False

    except Exception as e:
        print(f"✗ config.yaml error: {e}")
        return False


def test_class_structure():
    """Test that classes are defined correctly"""
    print("\nTesting class structure...")

    try:
        # Test ASR provider class name
        with open("core/providers/asr/deepgram_stream.py", 'r') as f:
            content = f.read()
            if "class ASRProvider(" in content:
                print("✓ ASR provider uses correct class name 'ASRProvider'")
            else:
                print("✗ ASR provider should have class named 'ASRProvider'")
                return False

        # Test VAD provider class name
        with open("core/providers/vad/deepgram_vad.py", 'r') as f:
            content = f.read()
            if "class VADProvider(" in content:
                print("✓ VAD provider uses correct class name 'VADProvider'")
            else:
                print("✗ VAD provider should have class named 'VADProvider'")
                return False

        # Test connection manager
        with open("core/providers/shared/deepgram_client.py", 'r') as f:
            content = f.read()
            if "class DeepgramConnectionManager" in content:
                print("✓ Connection manager class defined")
            else:
                print("✗ DeepgramConnectionManager not found")
                return False

        return True
    except Exception as e:
        print(f"✗ Class structure test failed: {e}")
        return False


def main():
    """Run all standalone tests"""
    print("=" * 70)
    print("Deepgram Provider Simple Test Suite")
    print("=" * 70)

    results = []

    # Run tests that don't require full environment
    results.append(("Deepgram SDK", test_deepgram_sdk()))
    results.append(("File Structure", test_file_structure()))
    results.append(("Python Syntax", test_python_syntax()))
    results.append(("Config Syntax", test_config_syntax()))
    results.append(("Class Structure", test_class_structure()))

    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:8s} {name}")

    print(f"\nResults: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All standalone tests passed!")
        print("\nDeepgram providers are correctly installed and configured.")
        print("\nTo use Deepgram:")
        print("1. Get API key from: https://console.deepgram.com/")
        print("2. Edit config.yaml and replace 'YOUR_DEEPGRAM_API_KEY' with your key")
        print("3. Update selected_module.VAD to 'DeepgramVAD'")
        print("4. Update selected_module.ASR to 'DeepgramStreamASR'")
        print("5. Run: python app.py")
        return 0
    else:
        print("\n❌ Some tests failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
