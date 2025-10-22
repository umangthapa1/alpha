#!/usr/bin/env python3
"""
Entry point script to run Alpha voice assistant.
This script handles the proper module imports and starts Alpha.
"""

import sys
import os

# Add the current directory to Python path so we can import voice_assistant
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Now we can import and run the main function
from voice_assistant.main import main

if __name__ == "__main__":
    main()
