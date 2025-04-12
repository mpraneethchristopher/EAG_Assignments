#!/bin/bash
echo "Starting Agentic Translator API..."
echo "To stop the server, press Ctrl+C"

# Activate virtual environment if it exists, otherwise use system Python
if [ -d "venv" ] && [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo "Virtual environment activated"
else
    echo "No virtual environment found, using system Python..."
fi

# Install dependencies if needed
pip install -r requirements.txt

# Start the API server
python translator_api.py 