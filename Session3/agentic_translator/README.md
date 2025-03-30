# Agentic German Translator

This Chrome extension uses an agentic approach to translate text to German. Instead of a direct translation, it shows the step-by-step process and functions used during translation, mimicking the agent-based approach shown in the Session3.ipynb notebook.

## Features

- Translate selected text to German using an agentic approach
- View logs of function calls in the translation process
- See the step-by-step processing of your text
- Dark/light theme detection for better UI integration
- Python backend for handling API calls and logging

## Files

### Chrome Extension
- `manifest.json`: Chrome extension manifest file
- `background.js`: Background script that communicates with the Python backend
- `content.js`: Content script for webpage integration
- `popup.html`: Popup UI for the extension
- `popup.js`: Script for handling logs in the popup
- `images/`: Directory for extension icons

### Python Backend
- `translator_api.py`: Flask API server that handles translation requests
- `requirements.txt`: Python dependencies
- `.env`: Environment variables (contains API key)
- `start_api.bat`/`start_api.sh`: Scripts to start the API server
- `translation_logs.log`: Log file (created when running the API)

## Installation

### Set Up the Python Backend
1. Make sure you have Python 3.7+ installed
2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file with your Google Gemini API key (or use the included one):
   ```
   GEMINI_API_KEY=your_api_key_here
   ```
4. Start the Python backend:
   - On Windows: Run `start_api.bat`
   - On Linux/macOS: Run `./start_api.sh` (make it executable first with `chmod +x start_api.sh`)

### Set Up the Chrome Extension
1. Make sure you have icon files in the images directory (icon16.png, icon48.png, icon128.png)
2. Open Chrome and navigate to `chrome://extensions/`
3. Enable "Developer mode" in the top right corner
4. Click "Load unpacked" and select the `agentic_translator` folder
5. The extension should now be installed and visible in your toolbar

## Usage

1. Start the Python backend server (should be running on localhost:5000)
2. Select any text on a webpage
3. Right-click and choose "Translate to German" from the context menu
4. A popup will appear with the German translation
5. Click "View translation logs" to see the function calls in the translation process
6. You can also click the extension icon in the toolbar to view the most recent logs

## Agentic Translation Process

The extension breaks down the translation process into distinct function calls:

1. `preprocessText`: Cleans and formats the input text
2. `detectLanguage`: Identifies the language of the source text
3. `translateToGerman`: Translates the text to German
4. `postprocessTranslation`: Performs any final formatting on the translation
5. `FINAL_ANSWER`: Displays the final translation result

All these functions are implemented in the Python backend, and their logs are displayed in the extension popup.

## API Key

The extension uses the Gemini API for translation. To use your own API key:

1. Get an API key from the Google AI Studio (https://makersuite.google.com/)
2. Replace the `GEMINI_API_KEY` value in the `.env` file with your key

## Troubleshooting

- **Extension shows "Translation error"**: Make sure the Python backend is running (check for the terminal window running the API server)
- **API server won't start**: Check that you have all required Python packages installed
- **Logs not showing**: The logs are stored in Chrome's local storage. Try clearing and reloading the extension

## License

MIT 