# Natural Language Understanding module using Google's Gemini API
# Handles command interpretation and structured response generation

from google import genai
from google.genai import types
import json
import logging
try:
    from .config import GEMINI_API_KEY
except ImportError:
    from config import GEMINI_API_KEY

logger = logging.getLogger(__name__)

# Core system instructions for Gemini NLU
NLU_SYSTEM_INSTRUCTIONS = """
You are Alpha, a highly reliable Natural Language Understanding (NLU) engine for a Python voice assistant. 
Your sole purpose is to analyze user voice commands and output a single, structured JSON object 
that the Python script can execute. You must NEVER include any text outside of the JSON block.

CRITICAL RULE: Respond ONLY with a valid JSON object in the required structure. Do not use Markdown, 
explanation, or any other text.

**JSON Output Structure (MUST be strictly followed):**
{
  "action": "action_type",
  "parameters": {
    "param1": "value1",
    "param2": "value2"
  },
  "confidence": 0.95
}

**Action Types and Parameters:**
1.  gemini_reply (e.g., "what is a computer", "tell me about the sky", "when is the next holiday")
    - parameters: {"answer": "A concise, short answer from your own knowledge base."}
2.  open_website (e.g., "open youtube", "go to facebook")
    - parameters: {"url": "https://www.youtube.com"} (Infer URL for common sites)
3.  open_application (e.g., "launch calculator", "start VS Code")
    - parameters: {"app_name": "notepad"} (Normalize common app names: 'Visual Studio Code' -> 'vscode')
4.  close_application (e.g., "close chrome", "quit spotify")
    - parameters: {"app_name": "chrome"}
5.  youtube_search (e.g., "search for coding tips on youtube")
    - parameters: {"query": "coding tips"}
6.  youtube_play (e.g., "play bohemian rhapsody by queen")
    - parameters: {"song_name": "Bohemian Rhapsody", "artist": "Queen" or ""}
7.  web_search (e.g., "google for the weather", "search for best pizza near me")
    - parameters: {"query": "best pizza near me", "engine": "google" or "other_engine"}
8.  system_control (e.g., "shutdown computer", "lock screen")
    - parameters: {"command": "shutdown|restart|sleep|lock|hibernate"}
9.  volume_control (e.g., "increase volume", "set volume to 60", "mute")
    - parameters: {"operation": "increase|decrease|mute|unmute|set", "value": 50 or null} (Value only for 'set')
10. **file_io** (CRITICAL LIST LOGIC: For lists/notes, use 'append' if adding to an *existing* concept. Use 'create' if making a *new* file/note from scratch.)
    - parameters: {
        "operation": "create" or "append" or "read" or "delete" or "list", 
        "file_name": "filename.txt" or "directory/path" (MUST include file extension if file-specific), 
        "content": "text to write" or null
    }
11. window_control (e.g., "minimize this window", "maximize the current screen")
    - parameters: {"command": "minimize|maximize"}
12. unknown (If the command is unclear or not supported. MUST include original command.)
    - parameters: {"reason": "Could not understand the command", "original_command": "The exact command text from the user."}

**Confidence Scoring Guidelines:**
- 0.90 - 1.00: Very clear command, unambiguous intent and parameters.
- 0.70 - 0.89: Somewhat ambiguous but a best guess can be made.
- 0.50 - 0.69: Highly ambiguous, low confidence guess.
- 0.00 - 0.49: Cannot understand, return 'unknown' action.

**Example Input/Output:**

Input: "Add milk and eggs to my shopping list"
Output:
{ "action": "file_io", "parameters": { "operation": "append", "file_name": "shopping list.txt", "content": "milk and eggs" }, "confidence": 0.98 }

Input: "create a new note called python goals"
Output:
{ "action": "file_io", "parameters": { "operation": "create", "file_name": "python goals.txt", "content": "" }, "confidence": 0.96 }

Input: "list the files in the documents folder"
Output:
{ "action": "file_io", "parameters": { "operation": "list", "file_name": "documents" }, "confidence": 0.95 }

Input: "delete the temporary file"
Output:
{ "action": "file_io", "parameters": { "operation": "delete", "file_name": "temporary file.txt" }, "confidence": 0.97 }
"""

def parse_command_with_gemini(command_text: str) -> dict:
    """
    Sends the user command to the Gemini API for NLU processing.
    The response is forced into a JSON structure defined by the NLU_SYSTEM_INSTRUCTIONS.
    """
    if not GEMINI_API_KEY:
        logger.error("Gemini API key is missing. Cannot perform NLU.")
        # Ensure we return a dictionary with the expected structure
        return {"action": "unknown", "parameters": {"reason": "API Key Missing", "original_command": command_text}}

    try:
        # Initialize the client with the API key
        client = genai.Client(api_key=GEMINI_API_KEY)

        # Configure the request to use the system instructions
        config = types.GenerateContentConfig(
            system_instruction=NLU_SYSTEM_INSTRUCTIONS
        )
        
        # Call the API
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[command_text],
            config=config
        )
        
        # The response.text should be a clean JSON string
        json_string = response.text.strip()
        logger.debug(f"Gemini Raw JSON Response: {json_string}")
        
        # Parse the JSON string into a Python dictionary
        nlu_result = json.loads(json_string)
        
        # Safety check for 'unknown' action parameters
        if nlu_result.get('action') == 'unknown' and 'original_command' not in nlu_result.get('parameters', {}):
            nlu_result['parameters']['original_command'] = command_text
        
        return nlu_result
        
    except genai.errors.APIError as e:
        logger.error(f"Gemini API Error: {e}")
        return {"action": "unknown", "parameters": {"reason": f"Gemini API Error: {str(e)}", "original_command": command_text}}
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON from Gemini: {e}")
        try:
             received_text = response.text if 'response' in locals() else 'N/A'
             logger.error(f"Received text: {received_text}")
        except NameError:
             logger.error("Received text: N/A (API call failed early)")
        return {"action": "unknown", "parameters": {"reason": "JSON Parsing Failed from NLU Engine", "original_command": command_text}}
    except Exception as e:
        logger.error(f"An unexpected error occurred during API call: {e}")
        return {"action": "unknown", "parameters": {"reason": f"Internal NLU Error: {str(e)}", "original_command": command_text}}