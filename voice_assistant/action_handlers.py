# voice_assistant/action_handlers.py

import os
import sys
import subprocess
import webbrowser
import logging
import urllib.parse
import pyautogui 

# Import necessary libraries for volume control
# Check if running on Windows to safely import pycaw
if sys.platform.startswith('win'):
    try:
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        from comtypes import CLSCTX_ALL
        from ctypes import cast, POINTER
        import math
    except ImportError:
        logging.warning("pycaw not installed. Volume control on Windows will be disabled.")

try:
    from .config import DEFAULT_WEB_ENGINE, DEFAULT_VOLUME_STEP
    from .voice_io import speak, listen_for_command, listen_for_short_response
except ImportError:
    from config import DEFAULT_WEB_ENGINE, DEFAULT_VOLUME_STEP
    from voice_io import speak, listen_for_command, listen_for_short_response

logger = logging.getLogger(__name__)

# --- Helper Functions for Cross-Platform Execution ---

def _open_app_cross_platform(app_name):
    """Opens an application based on the current OS."""
    app_name = app_name.lower().replace(' ', '')
    
    # Common application mappings for cross-platform convenience
    mapping = {
        'vscode': 'code',
        'calculator': 'calc',
        'notepad': 'notepad',
        'chrome': 'google-chrome' if sys.platform.startswith('linux') else 'chrome',
        'spotify': 'spotify',
        'cmd': 'cmd' if sys.platform.startswith('win') else 'terminal',
        'camera': 'start microsoft.windows.camera:' if sys.platform.startswith('win') else 'webcam'
    }
    command = mapping.get(app_name, app_name) # Use mapped name or original
    
    try:
        if sys.platform.startswith('win'):
            # Use 'start' to run in a separate command window and not block the assistant
            subprocess.Popen(['start', command], shell=True)
        elif sys.platform.startswith('darwin'):
            # On macOS, use 'open'
            subprocess.Popen(['open', '-a', command])
        else:
            # On Linux, run directly (assuming the command is in PATH)
            subprocess.Popen([command])
        return True
    except FileNotFoundError:
        return False
    except Exception as e:
        logger.error(f"App Open Error for {app_name}: {e}")
        return False

def _close_app_cross_platform(app_name):
    """Closes an application based on the current OS."""
    app_name = app_name.lower().replace(' ', '')
    
    try:
        if sys.platform.startswith('win'):
            # Taskkill is the standard way to terminate a process by name or window title
            # /F forces termination, /IM specifies image name
            subprocess.run(['taskkill', '/F', '/IM', f'{app_name}.exe'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        elif sys.platform.startswith('darwin'):
            # On macOS, use osascript to tell the application to quit
            subprocess.run(['osascript', '-e', f'quit app "{app_name}"'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        else:
            # On Linux, use pkill
            subprocess.run(['pkill', '-f', app_name], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
    except subprocess.CalledProcessError:
        logger.warning(f"Failed to close or find app: {app_name}")
        return False
    except Exception as e:
        logger.error(f"App Close Error for {app_name}: {e}")
        return False

def _system_control_cross_platform(command):
    """Executes a system-level command (shutdown, lock, restart)."""
    command = command.lower()
    
    try:
        if command == 'lock':
            if sys.platform.startswith('win'):
                subprocess.run('rundll32.exe user32.dll,LockWorkStation', check=True)
            elif sys.platform.startswith('darwin'):
                subprocess.run(['/System/Library/CoreServices/Menu Extras/User.menu/Contents/Resources/CGSession', '-suspend'], check=True)
            else: # Linux (Ubuntu/Gnome often uses this)
                subprocess.run(['gnome-screensaver-command', '-l'], check=True)
            speak("System locked.")
            return True
        elif command == 'shutdown':
            if sys.platform.startswith('win'):
                subprocess.run('shutdown /s /t 1', check=True)
            elif sys.platform.startswith('darwin'):
                subprocess.run(['shutdown', '-h', 'now'], check=True)
            else:
                subprocess.run(['shutdown', 'now'], check=True)
            speak("System shutting down.")
            return True
        elif command == 'restart':
            if sys.platform.startswith('win'):
                subprocess.run('shutdown /r /t 1', check=True)
            elif sys.platform.startswith('darwin'):
                subprocess.run(['shutdown', '-r', 'now'], check=True)
            else:
                subprocess.run(['reboot'], check=True)
            speak("System restarting.")
            return True
        elif command == 'sleep':
            if sys.platform.startswith('win'):
                # This is an unreliable system command, often requiring third-party tools or admin rights
                speak("I need administrative rights or a specific utility to put the system to sleep.")
                return False 
            elif sys.platform.startswith('darwin'):
                subprocess.run(['pmset', 'sleepnow'], check=True)
            else:
                subprocess.run(['systemctl', 'suspend'], check=True)
            speak("System entering sleep mode.")
            return True
        else:
            return False
    except Exception as e:
        logger.error(f"System Control Error: {e}")
        speak(f"Could not execute system command: {command}")
        return False

def _volume_control_windows(operation, value):
    """Handles volume control using pycaw on Windows."""
    try:
        devices = AudioUtilities.GetDefaultAudioEndpoint()
        interface = devices.Activate(
            IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        
        current_volume_scalar = volume.GetMasterVolumeLevelScalar()
        
        if operation == 'set':
            target_scalar = min(1.0, max(0.0, value / 100.0))
            volume.SetMasterVolumeLevelScalar(target_scalar, None)
            return True
        elif operation == 'increase':
            target_scalar = min(1.0, current_volume_scalar + (DEFAULT_VOLUME_STEP / 100.0))
            volume.SetMasterVolumeLevelScalar(target_scalar, None)
            return True
        elif operation == 'decrease':
            target_scalar = max(0.0, current_volume_scalar - (DEFAULT_VOLUME_STEP / 100.0))
            volume.SetMasterVolumeLevelScalar(target_scalar, None)
            return True
        elif operation == 'mute':
            volume.SetMute(1, None)
            return True
        elif operation == 'unmute':
            volume.SetMute(0, None)
            return True
    except NameError:
        logger.warning("pycaw components not imported. Volume control on Windows disabled.")
        return False
    except Exception as e:
        logger.error(f"Windows Volume Control Error: {e}")
        return False

def _volume_control_mac_linux(operation, value):
    """Handles volume control using 'osascript' (Mac) or 'amixer' (Linux)."""
    try:
        if sys.platform.startswith('darwin'):
            if operation == 'set':
                subprocess.run(['osascript', '-e', f'set volume output volume {value}'], check=True, stdout=subprocess.DEVNULL)
            elif operation == 'increase':
                subprocess.run(['osascript', '-e', f'set volume output volume ((output volume of (get volume settings)) + {DEFAULT_VOLUME_STEP})'], check=True, stdout=subprocess.DEVNULL)
            elif operation == 'decrease':
                subprocess.run(['osascript', '-e', f'set volume output volume ((output volume of (get volume settings)) - {DEFAULT_VOLUME_STEP})'], check=True, stdout=subprocess.DEVNULL)
            elif operation == 'mute':
                subprocess.run(['osascript', '-e', 'set volume with output muted'], check=True, stdout=subprocess.DEVNULL)
            elif operation == 'unmute':
                subprocess.run(['osascript', '-e', 'set volume without output muted'], check=True, stdout=subprocess.DEVNULL)
            else:
                return False
            return True
        elif sys.platform.startswith('linux'):
            if operation == 'set':
                subprocess.run(['amixer', 'set', 'Master', f'{value}%'], check=True, stdout=subprocess.DEVNULL)
            elif operation == 'increase':
                subprocess.run(['amixer', 'set', 'Master', f'{DEFAULT_VOLUME_STEP}%+'], check=True, stdout=subprocess.DEVNULL)
            elif operation == 'decrease':
                subprocess.run(['amixer', 'set', 'Master', f'{DEFAULT_VOLUME_STEP}%-'], check=True, stdout=subprocess.DEVNULL)
            elif operation == 'mute':
                subprocess.run(['amixer', 'set', 'Master', 'mute'], check=True, stdout=subprocess.DEVNULL)
            elif operation == 'unmute':
                subprocess.run(['amixer', 'set', 'Master', 'unmute'], check=True, stdout=subprocess.DEVNULL)
            else:
                return False
            return True
        else:
            return False
    except Exception as e:
        logger.error(f"Mac/Linux Volume Control Error: {e}")
        return False


# --- Action Handler Functions ---

def handle_gemini_reply(params, original_command=None):
    """Handles the 'gemini_reply' action by speaking the provided answer.

    After speaking the answer, asks the user if they'd like to save the
    response for later. If the user confirms, appends a nicely formatted
    entry (timestamp, question, answer) to voice_assistant/responses.txt.
    """
    answer = params.get('answer')
    if not answer:
        speak("I received an empty response from the knowledge engine.")
        return False

    # Speak the answer first
    speak(answer)

    # Prompt the user to save the response
    speak("Would you like me to save this response for later? Please say yes or no.")

    # Listen for a short yes/no response (one retry if unclear)
    try:
        # Use the short-response helper for quick yes/no answers
        reply = listen_for_short_response()
    except Exception as e:
        logger.debug(f"Error while listening for save confirmation: {e}")
        reply = None

    if not reply:
        # Try one more time briefly
        speak("I didn't catch that. Do you want me to save it? Say yes or no.")
        try:
            reply = listen_for_short_response()
        except Exception:
            reply = None

    affirmative = False
    if reply:
        low = reply.lower()
        if any(w in low for w in ['yes', 'yeah', 'yup', 'sure', 'save', 'please save', 'ok']):
            affirmative = True

    if not affirmative:
        speak("Okay, I won't save it.")
        return False

    # Save the response to voice_assistant/responses.txt with a nice format
    try:
        responses_path = os.path.join(os.path.dirname(__file__), 'responses.txt')
        from datetime import datetime

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        question = original_command or params.get('question') or 'User query'

        entry_lines = [
            '=' * 60,
            f"Saved: {timestamp}",
            f"Question: {question}",
            '-' * 60,
            answer.strip(),
            "",
        ]

        with open(responses_path, 'a', encoding='utf-8') as f:
            f.write('\n'.join(entry_lines) + '\n')

        speak("Saved the response to my memory.")
    except Exception as e:
        logger.error(f"Failed to save response: {e}")
        speak("Sorry, I couldn't save the response due to an error.")

    return False

def handle_open_website(params):
    """Handles the 'open_website' action."""
    url = params.get('url')
    if url:
        # Ensure URL has a scheme for correct opening
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url.lstrip('www.')
        speak(f"Opening {url}")
        webbrowser.open(url)
    else:
        speak("I need a website address to open.")

def handle_open_application(params):
    """Handles the 'open_application' action."""
    app_name = params.get('app_name')
    if app_name:
        speak(f"Launching {app_name}.")
        if not _open_app_cross_platform(app_name):
            speak(f"Sorry, I couldn't find the application: {app_name}.")
    else:
        speak("I need an application name to open.")

def handle_close_application(params):
    """Handles the 'close_application' action."""
    app_name = params.get('app_name')
    if app_name:
        speak(f"Attempting to close {app_name}.")
        if not _close_app_cross_platform(app_name):
            speak(f"Sorry, I couldn't close the application or it wasn't running: {app_name}.")
        else:
            speak(f"{app_name} closed successfully.")
    else:
        speak("I need an application name to close.")

def handle_youtube_search(params):
    """Handles the 'youtube_search' action."""
    query = params.get('query')
    if query:
        url = f"https://www.youtube.com/results?search_query={urllib.parse.quote_plus(query)}"
        speak(f"Searching YouTube for: {query}")
        webbrowser.open(url)
    else:
        speak("I need a search query for YouTube.")

def handle_youtube_play(params):
    """Handles the 'youtube_play' action."""
    song_name = params.get('song_name')
    artist = params.get('artist')
    if song_name:
        query = f"{song_name} {artist}" if artist else song_name
        url = f"https://www.youtube.com/results?search_query={urllib.parse.quote_plus(query)}"
        speak(f"Playing {query} on YouTube.")
        webbrowser.open(url)
    else:
        speak("I need a song or video name to play.")

def handle_web_search(params):
    """Handles the 'web_search' action."""
    query = params.get('query')
    engine = params.get('engine', DEFAULT_WEB_ENGINE)
    
    if query:
        search_urls = {
            "google": f"https://www.google.com/search?q={urllib.parse.quote_plus(query)}",
            "duckduckgo": f"https://duckduckgo.com/?q={urllib.parse.quote_plus(query)}",
            "bing": f"https://www.bing.com/search?q={urllib.parse.quote_plus(query)}"
        }
        
        url = search_urls.get(engine.lower(), search_urls[DEFAULT_WEB_ENGINE])
        
        speak(f"Searching {engine.capitalize()} for: {query}")
        webbrowser.open(url)
    else:
        speak("I need a query for a web search.")

def handle_system_control(params):
    """Handles the 'system_control' action."""
    command = params.get('command')
    if command:
        if not _system_control_cross_platform(command):
            speak(f"Sorry, the system control command '{command}' failed.")
    else:
        speak("I need a command like shutdown, restart, or lock.")

def handle_volume_control(params):
    """Handles the 'volume_control' action."""
    operation = params.get('operation')
    value = params.get('value')
    
    if sys.platform.startswith('win'):
        success = _volume_control_windows(operation, value)
    else:
        success = _volume_control_mac_linux(operation, value)

    if success:
        if operation == 'set':
            speak(f"Volume set to {value} percent.")
        elif operation == 'increase' or operation == 'decrease':
            speak(f"Volume {operation}d by {DEFAULT_VOLUME_STEP} percent.")
        elif operation == 'mute' or operation == 'unmute':
            speak(f"Volume {operation}d.")
        else:
            speak("Volume control executed.")
    else:
        speak("I'm sorry, I couldn't control the system volume. Check your pycaw installation on Windows, or permissions on other operating systems.")


def handle_window_control(params):
    """Handles commands to minimize or maximize the active window using pyautogui."""
    command = params.get('command')
    
    try:
        if command == 'minimize':
            if sys.platform.startswith('win'):
                pyautogui.hotkey('win', 'down')
            elif sys.platform.startswith('darwin'):
                pyautogui.hotkey('command', 'm')
            else: # Linux/General
                pyautogui.hotkey('alt', 'f9') # Common minimize shortcut
            speak("Window minimized.")
        
        elif command == 'maximize':
            if sys.platform.startswith('win'):
                pyautogui.hotkey('win', 'up')
            elif sys.platform.startswith('darwin'):
                # Note: No single, reliable universal Mac maximize shortcut via hotkey.
                speak("Attempting to maximize window.")
                pyautogui.hotkey('win', 'up') # Using an attempt
            else: # Linux/General
                pyautogui.hotkey('alt', 'f10') # Common maximize shortcut
            speak("Window maximized.")
            
        else:
            speak(f"Unknown window control command: {command}")
            
    except Exception as e:
        logger.error(f"Window Control Error: {e}")
        speak("I had trouble controlling the window. Check your system's keyboard shortcuts.")


def handle_file_io(params):
    """
    Handles advanced file operations: create, append, read, delete, and list directory contents.
    Includes logic to ensure list/note files default to .txt extension for consistency.
    """
    operation = params.get('operation')
    file_path = params.get('file_name', '.') 
    content = params.get('content') or ''
    
    # --- FILE NAME STANDARDIZATION FIX ---
    # If the operation is related to notes/lists/content, ensure a .txt extension exists
    if operation in ['create', 'append', 'read', 'delete'] and file_path != '.':
        # Check if file_path is already a directory name without an extension
        if not os.path.splitext(file_path)[1] and not os.path.isdir(file_path):
            file_path = f"{file_path}.txt"
    # -------------------------------------

    # If a file operation is requested, ensure a path is provided unless it's a 'list' of the current dir
    if operation in ['create', 'append', 'read', 'delete'] and file_path == '.':
        speak(f"Please specify a file name for the '{operation}' operation.")
        return

    try:
        if operation == 'create':
            with open(file_path, 'w') as f:
                f.write(content)
            speak(f"Successfully created or overwritten file {file_path}.")

        elif operation == 'append':
            # Append a newline for clarity if content already exists
            # The 'a' mode ensures the file is created if it doesn't exist.
            with open(file_path, 'a') as f:
                # Add content on a new line if the file is not empty and content is provided
                if os.path.getsize(file_path) > 0 and content.strip():
                     f.write('\n' + content)
                else:
                    f.write(content)
            speak(f"Successfully added {content} to {file_path}.")

        elif operation == 'read':
            with open(file_path, 'r') as f:
                file_content = f.read()
            if file_content:
                # Truncate content for speaking to avoid long responses
                display_content = file_content[:200] + ('...' if len(file_content) > 200 else '')
                speak(f"The content of {file_path} is: {display_content}")
            else:
                speak(f"File {file_path} is empty.")
                
        elif operation == 'delete':
            # ADVANCED: Delete file
            os.remove(file_path)
            speak(f"File {file_path} has been permanently deleted.")

        elif operation == 'list':
            # ADVANCED: List directory contents
            items = os.listdir(file_path)
            # Filter out hidden files/folders for cleaner output
            items = [item for item in items if not item.startswith('.') and item not in ['..', '.']]
            
            if not items:
                speak(f"The directory {file_path} is empty or doesn't exist.")
            else:
                speak(f"The contents of {file_path} are: {', '.join(items)}")

        else:
            speak(f"The file operation '{operation}' is not supported.")

    except FileNotFoundError:
        speak(f"Error: The file or directory '{file_path}' was not found.")
    except PermissionError:
        speak(f"Error: I do not have permission to access or modify '{file_path}'.")
    except IsADirectoryError:
        speak(f"Error: '{file_path}' is a directory. Please use the 'list' operation to view its contents.")
    except Exception as e:
        logger.error(f"File I/O Error: {e}")
        speak(f"A general error occurred during the file operation on {file_path}.")


def handle_unknown_action(params, original_command: str) -> bool:
    """
    Handles the 'unknown' action by analyzing the original command for missing info
    and issuing a context-aware follow-up prompt.
    Returns True if a follow-up listen is required, False otherwise.
    """
    reason = params.get('reason', 'Command not understood.')
    
    # Normalize command for easier keyword search
    clean_command = original_command.lower().strip()

    # --- Context-Aware Prompts ---
    if 'explain about' in clean_command or 'tell me about' in clean_command:
        speak("What do you want me to explain about?")
        return True # Listen again
    
    elif 'play' in clean_command and ('song' in clean_command or 'video' in clean_command or 'on youtube' in clean_command):
        speak("What song or video should I play?")
        return True # Listen again
        
    elif 'open' in clean_command or 'go to' in clean_command:
        speak("What application or website do you want me to open?")
        return True # Listen again

    # If the command is truly vague, use the generic response
    speak(f"I'm sorry, I didn't understand the command. The NLU reason was: {reason}")
    logger.warning(f"Unknown Command Handled. Reason: {reason}. Original: {original_command}")
    return False # Action finished

# --- Action Mapping Dictionary ---
ACTION_MAP = {
    "gemini_reply": lambda p, c: handle_gemini_reply(p),
    "open_website": lambda p, c: handle_open_website(p),
    "open_application": lambda p, c: handle_open_application(p),
    "close_application": lambda p, c: handle_close_application(p),
    "youtube_search": lambda p, c: handle_youtube_search(p),
    "youtube_play": lambda p, c: handle_youtube_play(p),
    "web_search": lambda p, c: handle_web_search(p),
    "system_control": lambda p, c: handle_system_control(p),
    "volume_control": lambda p, c: handle_volume_control(p),
    "window_control": lambda p, c: handle_window_control(p), 
    "file_io": lambda p, c: handle_file_io(p),             
    "unknown": handle_unknown_action,
}

def execute_action(nlu_result, original_command: str) -> bool:
    """
    Looks up the action handler and executes it with the provided parameters.
    Returns True if a follow-up listen is required (only for the 'unknown' action).
    """
    action_type = nlu_result.get('action')
    params = nlu_result.get('parameters', {})
    confidence = nlu_result.get('confidence', 0.0)
    
    logger.info(f"NLU Result: Action='{action_type}', Params={params}, Confidence={confidence}")

    handler = ACTION_MAP.get(action_type, handle_unknown_action)
    
    # Execute the handler function and capture the relisten flag
    relisten_needed = handler(params, original_command)
        
    return relisten_needed