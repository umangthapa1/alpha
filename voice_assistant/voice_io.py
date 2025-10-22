# Voice Input/Output module
# Handles speech recognition and text-to-speech functionality

import speech_recognition as sr
import subprocess
import platform
import logging
import time
import win32com.client as wincl

try:
    from .config import TTS_RATE, TTS_VOLUME, WAKE_WORD
except ImportError:
    from config import TTS_RATE, TTS_VOLUME, WAKE_WORD

logger = logging.getLogger(__name__)

# Initialize speech recognizer with optimized settings
r = sr.Recognizer()
r.energy_threshold = 300  # Microphone sensitivity threshold
r.pause_threshold = 1.2   # Silence duration before command completion

# Text-to-speech engine instance
tts_engine = None


def initialize_tts():
    """Initializes the win32com SAPI Text-to-Speech engine for Windows."""
    global tts_engine
    if tts_engine is None and platform.system() == "Windows":
        try:
            tts_engine = wincl.Dispatch("SAPI.SpVoice")
            
            sapi_rate = int((TTS_RATE - 175) / 12.5) 
            tts_engine.Rate = max(-10, min(10, sapi_rate))
            
            tts_engine.Volume = int(TTS_VOLUME * 100) 
            
            logger.info("win32com SAPI TTS engine initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize win32com SAPI: {e}. Falling back to print.")
            tts_engine = None
    elif tts_engine is None:
        logger.warning("TTS not initialized. Running on non-Windows OS or initialization failed.")

def speak(text):
    """Speaks the given text using the win32com SAPI engine."""
    global tts_engine
    logger.info(f"Alpha: {text}")
    
    if tts_engine:
        try:
            tts_engine.Speak(text, 0) # Synchronous flag (blocks until done)
        except Exception as e:
            logger.error(f"Error speaking with win32com: {e}")
            print(f"Alpha (TTS FAILED): {text}") 
    else:
        print(f"Alpha (TTS ENGINE OFFLINE): {text}")


def listen_for_wake_word():
    """Continuously listens for the wake word."""
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source, duration=1.0) 
        logger.info(f"Waiting for wake word: '{WAKE_WORD}'...")

        try:
            audio = r.listen(source, timeout=None, phrase_time_limit=5)
            text = r.recognize_google(audio).lower()
            logger.debug(f"Wake word attempt heard: '{text}'")

            if WAKE_WORD.lower() in text:
                logger.info("Wake word detected!")
                return True
        
        except sr.WaitTimeoutError:
            pass
        except sr.UnknownValueError:
            logger.debug("Speech not clear or no speech detected.")
        except sr.RequestError as e:
            logger.error(f"Could not request results from Google Speech Recognition service: {e}")

    return False

def listen_for_command():
    """Listens for a command after the wake word is detected."""
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source, duration=0.5) 
        logger.info("Listening for command...")

        try:
            audio = r.listen(source, timeout=8, phrase_time_limit=30)
            
            command = r.recognize_google(audio)
            logger.info(f"Command received: '{command}'")
            return command
            
        except sr.WaitTimeoutError:
            speak("I didn't hear a command. Returning to sleep mode.")
            return None
        except sr.UnknownValueError:
            speak("Sorry, I could not understand the audio. Please speak clearly.")
            return None
        except sr.RequestError as e:
            speak("Sorry, my speech service is currently unavailable.")
            logger.error(f"Speech service error: {e}")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred during listening: {e}")
            speak("An internal error occurred. Please check the logs.")
            return None


def listen_for_short_response(timeout: float = 4.0, phrase_time_limit: float = 3.0):
    """Listen for a short yes/no response with tighter time limits.

    This helper reduces the phrase_time_limit and timeout to better capture
    single-word replies like 'yes' or 'no'. It returns the recognized text
    (string) or None if nothing understandable was heard.
    """
    with sr.Microphone() as source:
        # Short ambient adjustment for quick responses
        r.adjust_for_ambient_noise(source, duration=0.4)
        logger.info("Listening for short response...")

        try:
            audio = r.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
            response = r.recognize_google(audio)
            logger.info(f"Short response received: '{response}'")
            return response
        except sr.WaitTimeoutError:
            logger.debug("Short response: wait timeout")
            return None
        except sr.UnknownValueError:
            logger.debug("Short response: could not understand audio")
            return None
        except sr.RequestError as e:
            logger.error(f"Short response: speech service error: {e}")
            return None
        except Exception as e:
            logger.error(f"Short response: unexpected error: {e}")
            return None