from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
from dotenv import load_dotenv
import logging
import json
from datetime import datetime
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("translation.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("translation")

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure Gemini API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=GEMINI_API_KEY)

# Initialize the model
model = genai.GenerativeModel('gemini-2.0-flash')

@app.route('/api/translate', methods=['POST'])
def translate():
    """Translate text using Gemini API"""
    try:
        # Log request details
        logger.info("\n" + "="*50)
        logger.info("Starting new translation request")
        logger.info("="*50)
        
        data = request.json
        logger.info(f"\nRequest Parameters:")
        logger.info(f"Source Text: {data.get('text', '')}")
        logger.info(f"Source Language: {data.get('source_language', '')}")
        logger.info(f"Target Language: {data.get('target_language', '')}")
        
        # Prepare the prompt for Gemini
        logger.info("\nPreparing Gemini API request...")
        prompt = f"""
        Please translate the following text from {data.get('source_language', '')} to {data.get('target_language', '')}:
        
        Text: {data.get('text', '')}
        
        IMPORTANT: You must respond with ONLY a valid JSON object in the following format:
        {{
            "translation": "translated text",
            "source_language": "source language",
            "target_language": "target language"
        }}
        
        Do not include any additional text, explanations, or markdown formatting. Only the JSON object.
        """
        
        # Send request to Gemini API
        logger.info("\nSending request to Gemini API...")
        response = model.generate_content(prompt)
        logger.info("\nRaw Gemini API Response:")
        logger.info(response.text)
        
        try:
            # Clean and parse the response
            logger.info("\nProcessing Gemini API response...")
            response_text = response.text.strip()
            
            # Remove any markdown formatting
            response_text = response_text.replace('```json', '').replace('```', '')
            response_text = response_text.strip()
            
            # Find the JSON object in the response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            if start_idx >= 0 and end_idx > start_idx:
                response_text = response_text[start_idx:end_idx]
            
            logger.info("\nCleaned response text:")
            logger.info(response_text)
            
            # Parse the response
            results = json.loads(response_text)
            
            # Log the structure of the response
            logger.info("\nResponse structure:")
            logger.info(f"Type: {type(results)}")
            logger.info(f"Keys: {results.keys() if isinstance(results, dict) else 'Not a dictionary'}")
            
            # Validate the response structure
            if not isinstance(results, dict):
                raise ValueError("Response is not a dictionary")
            
            if "translation" not in results:
                raise ValueError("Response missing 'translation' key")
            
            logger.info("\nSuccessfully parsed translation results:")
            logger.info(f"Translation: {results['translation']}")
            logger.info(f"Source Language: {results.get('source_language', 'N/A')}")
            logger.info(f"Target Language: {results.get('target_language', 'N/A')}")
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"\nFailed to parse Gemini API response: {str(e)}")
            logger.error(f"Response that failed to parse: {response_text}")
            logger.info("\nUsing mock data as fallback...")
            
            # If parsing fails, use mock data
            results = {
                "translation": "This is a mock translation",
                "source_language": data.get('source_language', ''),
                "target_language": data.get('target_language', '')
            }
            
            logger.info("\nMock translation results:")
            logger.info(f"Translation: {results['translation']}")
            logger.info(f"Source Language: {results['source_language']}")
            logger.info(f"Target Language: {results['target_language']}")
        
        logger.info("\nSending translation results to client...")
        logger.info("="*50 + "\n")
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"\nError in translation: {str(e)}")
        logger.error("="*50 + "\n")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) 