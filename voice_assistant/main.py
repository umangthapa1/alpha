# Main module for Alpha Voice Assistant
# Orchestrates voice recognition, NLU processing, and command execution

import logging
import time
from typing import Optional

try:
    from .config import LOG_FILE, WAKE_WORD, LISTENING_PROMPT, GEMINI_API_KEY
    from .voice_io import initialize_tts, listen_for_wake_word, listen_for_command, speak
    from .gemini_nlu import parse_command_with_gemini
    from .action_handlers import execute_action
    from .gui import AlphaGUI
except ImportError:
    from config import LOG_FILE, WAKE_WORD, LISTENING_PROMPT, GEMINI_API_KEY
    from voice_io import initialize_tts, listen_for_wake_word, listen_for_command, speak
    from gemini_nlu import parse_command_with_gemini
    from action_handlers import execute_action
    from gui import AlphaGUI

STOP_REQUESTED = False  # Control flag for graceful shutdown

def _request_stop() -> None:
    global STOP_REQUESTED
    STOP_REQUESTED = True

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(module)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()  # This adds console output
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Main function to run the voice assistant application loop."""
    print("👋 Alpha Voice Assistant Starting Up...")
    logger.info("--- Alpha Voice Assistant Starting Up ---")
    
    if not GEMINI_API_KEY:
        # Configuration file should check for this, but added here for safety.
        print("CRITICAL ERROR: GEMINI_API_KEY not found. Please check config.py or environment.")
        return

    # 1. Initialize TTS Engine
    print("🔊 Initializing TTS Engine...")
    initialize_tts()
    
    print(f"✅ Alpha activated. Listening for wake word: '{WAKE_WORD}'")
    print("🎙️ Say 'Alpha' followed by your command to interact with the assistant")
    print("❌ Press Ctrl+C to stop Alpha")
    print("-" * 60)
    
    speak(f"Alpha activated. I am listening for the wake word: {WAKE_WORD}.")
    
    # Start GUI (if available)
    gui = None
    try:
        gui = AlphaGUI(on_quit=_request_stop)
        gui.start()
        gui.log_text("TTS initialized. Starting assistant...")
    except Exception as e:
        logger.warning(f"Failed to start GUI: {e}")
        gui = None

    try:
        # 2. Main Listening Loop
        while True:
            # Allow GUI to request stop
            if STOP_REQUESTED:
                logger.info("Stop requested by GUI. Shutting down main loop.")
                break

            if listen_for_wake_word():
                # Assistant is awake
                if gui:
                    gui.set_listening(True)
                    gui.update_status("Status: Wake word detected — Listening for command")
                    gui.log_text("Wake word detected.")

                speak(LISTENING_PROMPT)
                
                # 3. Listen for Initial Command
                command_text = listen_for_command()
                
                if command_text:
                    if gui:
                        gui.log_text(f"User command: {command_text}")
                    # Inner loop for follow-up commands/conversational turn
                    while True:
                        # 4. Process Command with Gemini NLU
                        nlu_result = parse_command_with_gemini(command_text)
                        
                        # 5. Execute Action
                        # execute_action now returns True if a follow-up listen is needed
                        should_relisten = execute_action(nlu_result, command_text) 
                        
                        if should_relisten:
                            # 6. Listen for Follow-up Command
                            print("System prompted user. Listening for follow-up...")
                            if gui:
                                gui.log_text(f"Prompted follow-up: {command_text}")
                            command_text = listen_for_command()
                            if not command_text:
                                # User didn't respond to the prompt, break out to wake word mode
                                speak("No response heard. Returning to wake word detection.")
                                break 
                        else:
                            # Action complete (or failed but required no follow-up), exit inner loop
                            break 

                if gui:
                    gui.set_listening(False)
                    gui.update_status("Status: Idle")

            time.sleep(0.1) # Small delay to prevent high CPU usage

    except KeyboardInterrupt:
        logger.info("Alpha manually stopped by user (Ctrl+C).")
        speak("Goodbye.")
    except Exception as e:
        logger.critical(f"A fatal unhandled error occurred: {e}")
        speak("A critical error has occurred and Alpha is shutting down.")
        
    logger.info("--- Alpha Voice Assistant Shut Down ---")

    # Ensure GUI is closed
    try:
        if gui:
            gui.log_text("Assistant shutting down...")
            gui.stop()
    except Exception:
        pass

if __name__ == '__main__':
    main()