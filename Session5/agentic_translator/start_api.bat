@echo off
echo Starting Agentic Translator API...
echo To stop the server, press Ctrl+C

:: Activate virtual environment if it exists, otherwise use system Python
if exist venv\Scripts\activate (
    call venv\Scripts\activate
) else (
    echo No virtual environment found, using system Python...
)

:: Install dependencies if needed
pip install -r requirements.txt

:: Start the API server
python translator_api.py

pause 