# 🤖 Alpha - Smart Voice Assistant

A powerful, cross-platform voice assistant built in Python that uses Google's Gemini API for Natural Language Understanding (NLU). Features smart command interpretation without hardcoded rules.

## ✨ Features

- **Natural Language Understanding:** Uses Gemini API to intelligently parse and understand voice commands
- **Wake Word Activation:** Customizable wake word to start listening for commands
- **Cross-Platform Support:** Works on Windows, macOS, and Linux
- **GUI Interface:** Clean, modern interface showing assistant status
- **Extensible Design:** Easy to add new capabilities through the NLU system

## 🛠️ Setup Instructions

### Prerequisites

1. Python 3.8 or higher
2. Microphone for voice input
3. Speaker for voice output
4. [Gemini API key](https://aistudio.google.com/)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/alpha-voice-assistant.git
cd alpha-voice-assistant
```

2. Set up your Gemini API key as an environment variable:
```bash
# Linux/macOS
export GEMINI_API_KEY='your-api-key'

# Windows (PowerShell)
$env:GEMINI_API_KEY='your-api-key'
```

3. Create and activate a virtual environment:
```bash
python -m venv venv

# Linux/macOS
source venv/bin/activate

# Windows
.\venv\Scripts\activate
```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

5. Run the assistant:
```bash
python run_alpha.py
```

Note: PyAudio installation might require additional system packages:
- **Linux:** `sudo apt-get install portaudio19-dev`
- **macOS:** `brew install portaudio`
- **Windows:** Usually works out of the box

## 🗣️ Example Commands

Alpha understands natural language commands across various categories:

- **Web Navigation:** "Open YouTube", "Go to GitHub"
- **Applications:** "Launch VS Code", "Close Chrome"
- **Media:** "Play Bohemian Rhapsody", "Search for cooking videos"
- **System Control:** "Set volume to 50", "Lock the computer"
- **Web Search:** "Search for weather today", "Find pizza places nearby"
- **File Management:** "Create a shopping list", "Read my notes"

## ⚙️ Configuration

The assistant can be customized by editing `config.py`:
- Wake word (default: "assistant")
- Speech rate and volume
- Default web search engine
- GUI theme and appearance

## 🏗️ Project Structure

```
voice_assistant/
├── main.py          # Main application loop
├── voice_io.py      # Speech recognition and TTS
├── gemini_nlu.py    # Natural language understanding
├── action_handlers.py # Command execution
├── config.py        # Configuration settings
└── gui.py          # GUI interface
```

## 🔧 How It Works

1. Listens for wake word ("assistant")
2. Captures voice command
3. Processes command through Gemini API
4. Executes corresponding action
5. Provides voice feedback

## 🤝 Contributing

Contributions are welcome! Here are some ways you can help:

1. Report bugs and suggest features
2. Improve documentation
3. Add new command capabilities
4. Enhance cross-platform support

## � License

This project is licensed under the MIT License - see the LICENSE file for details.

## ✨ Acknowledgments

- Google Gemini API for natural language understanding
- SpeechRecognition library for voice input
- PyCAW for Windows volume control
