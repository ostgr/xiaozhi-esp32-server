#!/usr/bin/env python3
"""
Test script for LLM provider
Tests LLM response with a simple prompt
"""
import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import yaml
from config.logger import setup_logging
from core.providers.llm.openai.openai import LLMProvider

# Setup logging
logger = setup_logging()
TAG = "LLM_TEST"


def load_config():
    """Load configuration from config.yaml"""
    config_path = os.path.join(os.path.dirname(__file__), "config.yaml")

    # Check for override config
    override_config_path = os.path.join(os.path.dirname(__file__), "data", ".config.yaml")

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # Apply override config if exists
    if os.path.exists(override_config_path):
        with open(override_config_path, "r", encoding="utf-8") as f:
            override_config = yaml.safe_load(f)
            if override_config:
                # Deep merge override config
                config.update(override_config)

    return config


def test_llm_response():
    """Test LLM with a simple prompt"""
    try:
        # Load config
        config = load_config()

        # Get selected LLM module name
        llm_module_name = config["selected_module"]["LLM"]
        logger.bind(tag=TAG).info(f"Selected LLM module: {llm_module_name}")

        # Get LLM configuration
        llm_config = config["LLM"][llm_module_name]
        logger.bind(tag=TAG).info(f"LLM config: {llm_config['model_name']} @ {llm_config.get('base_url', llm_config.get('url'))}")

        # Initialize LLM provider
        llm_provider = LLMProvider(llm_config)

        # Test prompt
        user_prompt = "Hãy nhắc lại toàn bộ câu sau: 'Chào bạn, tôi là Tú Nguyễn, là 1 Software Engineer'"
        system_prompt = config.get("prompt", "You are a helpful assistant.")

        logger.bind(tag=TAG).info("=" * 60)
        logger.bind(tag=TAG).info("Testing LLM Response")
        logger.bind(tag=TAG).info("=" * 60)
        logger.bind(tag=TAG).info(f"System Prompt: {system_prompt[:100]}...")
        logger.bind(tag=TAG).info(f"User Prompt: {user_prompt}")
        logger.bind(tag=TAG).info("=" * 60)

        # Create dialogue
        dialogue = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        # Get response (streaming)
        print("\n[LLM Response]:")
        print("-" * 60)
        full_response = ""
        for token in llm_provider.response("test_session_001", dialogue):
            print(token, end="", flush=True)
            full_response += token
        print("\n" + "-" * 60)

        logger.bind(tag=TAG).info(f"Full response length: {len(full_response)} characters")
        logger.bind(tag=TAG).info("Test completed successfully!")

        return full_response

    except Exception as e:
        logger.bind(tag=TAG).error(f"Error testing LLM: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_llm_no_stream():
    """Test LLM with no streaming (complete response)"""
    try:
        # Load config
        config = load_config()

        # Get selected LLM module name
        llm_module_name = config["selected_module"]["LLM"]

        # Get LLM configuration
        llm_config = config["LLM"][llm_module_name]

        # Initialize LLM provider
        llm_provider = LLMProvider(llm_config)

        # Test prompt
        user_prompt = "Hãy nhắc lại toàn bộ câu sau: 'Chào bạn, tôi là Tú Nguyễn, là 1 Software Engineer'"
        system_prompt = config.get("prompt", "You are a helpful assistant.")

        logger.bind(tag=TAG).info("=" * 60)
        logger.bind(tag=TAG).info("Testing LLM Response (No Stream)")
        logger.bind(tag=TAG).info("=" * 60)

        # Get response (no streaming)
        result = llm_provider.response_no_stream(system_prompt, user_prompt)

        print("\n[LLM Response (No Stream)]:")
        print("-" * 60)
        print(result)
        print("-" * 60)

        logger.bind(tag=TAG).info("Test completed successfully!")

        return result

    except Exception as e:
        logger.bind(tag=TAG).error(f"Error testing LLM (no stream): {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("LLM Provider Test Script")
    print("=" * 60 + "\n")

    # Test 1: Streaming response
    print("\n[Test 1] Streaming Response")
    result1 = test_llm_response()

    print("\n" + "=" * 60)

    # Test 2: No stream response
    print("\n[Test 2] No Stream Response")
    result2 = test_llm_no_stream()

    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60 + "\n")
