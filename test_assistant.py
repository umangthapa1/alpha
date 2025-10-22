#!/usr/bin/env python3
"""
Simple test script to verify the voice assistant components work correctly.
Run this before using the full assistant to check for basic issues.
"""

import os
import sys

def test_imports():
    """Test that all modules can be imported successfully."""
    print("Testing imports...")
    
    try:
        from voice_assistant import config
        print("✓ config.py imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import config.py: {e}")
        return False
    
    try:
        from voice_assistant import voice_io
        print("✓ voice_io.py imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import voice_io.py: {e}")
        return False
    
    try:
        from voice_assistant import gemini_nlu
        print("✓ gemini_nlu.py imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import gemini_nlu.py: {e}")
        return False
    
    try:
        from voice_assistant import action_handlers
        print("✓ action_handlers.py imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import action_handlers.py: {e}")
        return False
    
    return True

def test_config():
    """Test configuration loading."""
    print("\nTesting configuration...")
    
    from voice_assistant.config import GEMINI_API_KEY, WAKE_WORD, TTS_RATE
    
    if GEMINI_API_KEY:
        print("✓ GEMINI_API_KEY is set")
    else:
        print("✗ GEMINI_API_KEY is not set - please set your environment variable")
        return False
    
    print(f"✓ Wake word: {WAKE_WORD}")
    print(f"✓ TTS Rate: {TTS_RATE}")
    
    return True

def test_dependencies():
    """Test that required dependencies are available."""
    print("\nTesting dependencies...")
    
    required_modules = [
        'speech_recognition',
        'google.genai',
        'webbrowser',
        'subprocess'
    ]
    
    optional_modules = [
        'pycaw',  # For Windows volume control
        'comtypes'  # For Windows volume control
    ]
    
    all_good = True
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"✓ {module} is available")
        except ImportError:
            print(f"✗ {module} is missing - required dependency")
            all_good = False
    
    for module in optional_modules:
        try:
            __import__(module)
            print(f"✓ {module} is available (optional)")
        except ImportError:
            print(f"⚠ {module} is missing (optional - volume control may not work)")
    
    return all_good

def main():
    """Run all tests."""
    print("🤖 Alpha Voice Assistant Test Suite")
    print("=" * 40)
    
    tests = [
        test_imports,
        test_config, 
        test_dependencies
    ]
    
    all_passed = True
    
    for test in tests:
        if not test():
            all_passed = False
    
    print("\n" + "=" * 40)
    if all_passed:
        print("🎉 All tests passed! Alpha should work correctly.")
        print("\nTo run Alpha:")
        print("  python voice_assistant/main.py")
    else:
        print("❌ Some tests failed. Please fix the issues above before running Alpha.")
        sys.exit(1)

if __name__ == "__main__":
    main()
