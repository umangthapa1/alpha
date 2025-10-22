# Configuration module for Alpha Voice Assistant
# Centralized settings and environment variables

import os

# Gemini API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")  # Get API key from environment variable

# Voice Assistant Settings
WAKE_WORD = "assistant"  # Activation keyword

# The prompt for the assistant to listen for a command after the wake word.
LISTENING_PROMPT = "How can I help you?"

# --- Text-to-Speech (TTS) Settings ---
TTS_RATE = 200  # ADVANCE TWEAK: Increased speed from 150 to 200 WPM
TTS_VOLUME = 1.0 # Volume (0.0 to 1.0)

# --- System Defaults ---
# Default search engine to use when 'web_search' is requested without a specific engine.
DEFAULT_WEB_ENGINE = "google"

# Default volume change percentage for 'increase'/'decrease' operations.
DEFAULT_VOLUME_STEP = 10

# --- File Paths ---
# Log file location
LOG_FILE = "voice_assistant.log"

# --- Validation ---
if not GEMINI_API_KEY:
    print("CRITICAL ERROR: GEMINI_API_KEY not found.")
    print("Please set the GEMINI_API_KEY environment variable.")

# --- GUI Theme Settings ---
# Simple theme selection for the Tkinter HUD. Set GUI_THEME to one of the keys
# in GUI_THEMES to change the appearance. Themes provide colors and a suggested
# font name used by the HUD.
GUI_THEME = "ironman"

GUI_THEMES = {
    "ironman": {
        "bg": "#071020",         # window background
        "accent": "#ff2d00",     # primary accent (Iron Man red)
        "accent_alt": "#ffd700", # accent alt (gold)
        "secondary": "#9be7ff",  # status text
        "canvas_bg": "#0b1a2b",  # HUD canvas background
        "text": "#a7f0ff",       # main text color
        "title": "#ffb86b",      # title color
        "font": "Segoe UI"
    },
    "default": {
        "bg": "#071020",
        "accent": "#00ffcc",
        "accent_alt": "#9be7ff",
        "secondary": "#9be7ff",
        "canvas_bg": "#0b1a2b",
        "text": "#a7f0ff",
        "title": "#00ffcc",
        "font": "Segoe UI"
    }
}