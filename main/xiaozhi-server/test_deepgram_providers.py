#!/usr/bin/env python3
"""
Test script to verify Deepgram providers load correctly
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all Deepgram modules can be imported"""
    print("Testing imports...")

    try:
        from core.providers.shared.deepgram_client import DeepgramConnectionManager
        print("✓ DeepgramConnectionManager imported successfully")
    except Exception as e:
        print(f"✗ Failed to import DeepgramConnectionManager: {e}")
        return False

    try:
        from core.providers.asr.deepgram_stream import ASRProvider as DeepgramASR
        print("✓ Deepgram ASR provider imported successfully")
    except Exception as e:
        print(f"✗ Failed to import Deepgram ASR: {e}")
        return False

    try:
        from core.providers.vad.deepgram_vad import VADProvider as DeepgramVAD
        print("✓ Deepgram VAD provider imported successfully")
    except Exception as e:
        print(f"✗ Failed to import Deepgram VAD: {e}")
        return False

    return True


def test_provider_initialization():
    """Test that providers can be initialized"""
    print("\nTesting provider initialization...")

    # Test config
    config = {
        "api_key": "test_key",
        "model": "nova-2",
        "language": "multi",
        "endpointing": 300,
        "encoding": "opus",
        "sample_rate": 16000,
        "channels": 1,
        "smart_format": True,
        "output_dir": "tmp/"
    }

    try:
        from core.providers.asr.deepgram_stream import ASRProvider as DeepgramASR
        asr = DeepgramASR(config, delete_audio_file=True)
        print(f"✓ ASR provider initialized: interface_type={asr.interface_type}")
    except Exception as e:
        print(f"✗ Failed to initialize ASR provider: {e}")
        return False

    try:
        from core.providers.vad.deepgram_vad import VADProvider as DeepgramVAD
        vad = DeepgramVAD(config)
        print("✓ VAD provider initialized")
    except Exception as e:
        print(f"✗ Failed to initialize VAD provider: {e}")
        return False

    return True


def test_factory_pattern():
    """Test that factory functions can create providers"""
    print("\nTesting factory pattern...")

    config = {
        "api_key": "test_key",
        "model": "nova-2",
        "language": "multi",
        "endpointing": 300,
        "encoding": "opus",
        "sample_rate": 16000,
        "channels": 1,
        "smart_format": True,
        "output_dir": "tmp/",
        "type": "deepgram_stream"
    }

    try:
        from core.utils import asr
        provider = asr.create_instance("deepgram_stream", config, True)
        print(f"✓ ASR factory created provider: {type(provider).__name__}")
    except Exception as e:
        print(f"✗ Failed to create ASR via factory: {e}")
        import traceback
        traceback.print_exc()
        return False

    try:
        from core.utils import vad
        provider = vad.create_instance("deepgram_vad", config)
        print(f"✓ VAD factory created provider: {type(provider).__name__}")
    except Exception as e:
        print(f"✗ Failed to create VAD via factory: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


def test_config_loading():
    """Test that config.yaml has Deepgram sections"""
    print("\nTesting configuration...")

    try:
        from ruamel.yaml import YAML
        yaml = YAML()

        with open("config.yaml", "r") as f:
            config = yaml.load(f)

        # Check VAD section
        if "DeepgramVAD" in config.get("VAD", {}):
            print("✓ DeepgramVAD section found in config.yaml")
        else:
            print("✗ DeepgramVAD section not found in config.yaml")
            return False

        # Check ASR section
        if "DeepgramStreamASR" in config.get("ASR", {}):
            asr_config = config["ASR"]["DeepgramStreamASR"]
            print(f"✓ DeepgramStreamASR section found in config.yaml")
            print(f"  - model: {asr_config.get('model')}")
            print(f"  - language: {asr_config.get('language')}")
            print(f"  - endpointing: {asr_config.get('endpointing')}ms")

            if asr_config.get("api_key") == "YOUR_DEEPGRAM_API_KEY":
                print("  ⚠ Warning: API key not configured (still placeholder)")
        else:
            print("✗ DeepgramStreamASR section not found in config.yaml")
            return False

        return True
    except Exception as e:
        print(f"✗ Failed to load config: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("Deepgram Provider Test Suite")
    print("=" * 60)

    results = []

    # Run tests
    results.append(("Import Test", test_imports()))
    results.append(("Initialization Test", test_provider_initialization()))
    results.append(("Factory Pattern Test", test_factory_pattern()))
    results.append(("Configuration Test", test_config_loading()))

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:8s} {name}")

    print(f"\nResults: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Deepgram providers are ready to use.")
        print("\nNext steps:")
        print("1. Configure your Deepgram API key in config.yaml")
        print("2. Update selected_module.VAD to 'DeepgramVAD'")
        print("3. Update selected_module.ASR to 'DeepgramStreamASR'")
        print("4. Run: python app.py")
        return 0
    else:
        print("\n❌ Some tests failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
