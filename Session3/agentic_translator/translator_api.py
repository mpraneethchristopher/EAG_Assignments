from flask import Flask, request, jsonify
import os
import requests
from dotenv import load_dotenv
import logging
import json
import time

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("translation_logs.log"), logging.StreamHandler()]
)
logger = logging.getLogger("translator_api")

app = Flask(__name__)

# Try to get API key from environment variables
# If you have a working API key, place it in the .env file
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# If no API key in .env, try the one from Session2 that was known to work
if not GEMINI_API_KEY:
    GEMINI_API_KEY = 'AIzaSyBkQ6LwyF3omfQkDL-RywZ-BZ2uVl28WKM'  # Try a different API key from Session3 notebook
    logger.info(f"Using fallback API key from Session3 notebook")

logger.info(f"API Key being used (first few chars): {GEMINI_API_KEY[:8]}...")

# Add a root route for testing
@app.route('/', methods=['GET'])
def root():
    """Simple test endpoint to verify the server is running"""
    return jsonify({
        "status": "ok",
        "message": "Agentic Translator API is running",
        "api_key_status": "API key is set" if GEMINI_API_KEY else "API key is missing",
        "endpoints": [
            {"path": "/", "method": "GET", "description": "This test endpoint"},
            {"path": "/api/translate", "method": "POST", "description": "Translate text to German"},
            {"path": "/api/direct-translate", "method": "POST", "description": "Direct translation without agent steps"},
            {"path": "/api/logs", "method": "GET", "description": "Get translation logs"},
            {"path": "/api/clear_logs", "method": "POST", "description": "Clear translation logs"}
        ]
    })

# Store logs for the translation process
translation_logs = []

def log_function_call(function_name, params, result=None):
    """Log function calls in the format similar to the notebook"""
    log_entry = {
        "type": "function_call",
        "function": function_name,
        "params": params
    }
    
    if result is not None:
        log_entry["result"] = result
    
    translation_logs.append(log_entry)
    logger.info(f"FUNCTION_CALL: {function_name}|{params}")
    if result:
        logger.info(f"Result: {result}")
    
    return log_entry

def log_final_answer(translation):
    """Log the final translation answer"""
    log_entry = {
        "type": "final_answer",
        "translation": translation
    }
    translation_logs.append(log_entry)
    logger.info(f"FINAL_ANSWER: {translation}")
    return log_entry

@app.route('/api/logs', methods=['GET'])
def get_logs():
    """Return all logged function calls and results"""
    return jsonify(translation_logs)

@app.route('/api/clear_logs', methods=['POST'])
def clear_logs():
    """Clear all logged function calls and results"""
    global translation_logs
    translation_logs = []
    return jsonify({"status": "success", "message": "Logs cleared"})

def preprocess_text(text):
    """Clean and format the input text"""
    log_function_call("preprocessText", text)
    
    # Simple preprocessing - remove extra spaces and format text
    cleaned_text = text.strip().replace("  ", " ")
    
    log_function_call("preprocessText", text, cleaned_text)
    return cleaned_text

def detect_language(text):
    """Detect the language of the text using Gemini API"""
    log_function_call("detectLanguage", text)
    
    try:
        # Using the exact format from the working Session2 code
        payload = {
            "contents": [{
                "parts": [{
                    "text": f'You are a language detection agent. Detect the language of this text and respond with only the language name: "{text}"'
                }]
            }],
            "safetySettings": [{
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_NONE"
            }]
        }
        
        logger.info(f"Language detection request payload: {json.dumps(payload)}")
        
        response = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        logger.info(f"Language detection response status: {response.status_code}")
        
        if not response.ok:
            logger.error(f"Language detection API Error: {response.text}")
            raise Exception(f"API Error: {response.status_code} - {response.text}")
        
        data = response.json()
        logger.info(f"Language detection response: {json.dumps(data)}")
        
        # Extract language name from response
        language_name = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        
        log_function_call("detectLanguage", text, language_name)
        return language_name
    
    except Exception as e:
        error_message = f"Error: {str(e)}"
        logger.error(f"Language detection error: {error_message}")
        logger.error(f"Response: {response.text if 'response' in locals() else 'No response'}")
        log_function_call("detectLanguage", text, error_message)
        return "Unknown"

def translate_to_german(text):
    """Translate text to German using Gemini API"""
    log_function_call("translateToGerman", text)
    
    try:
        # Using the exact format from the working Session2 code
        payload = {
            "contents": [{
                "parts": [{
                    "text": f'You are a translator. Translate this English text to German: "{text}". Only respond with the German translation, nothing else.'
                }]
            }],
            "safetySettings": [{
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_NONE"
            }]
        }
        
        logger.info(f"Translation request payload: {json.dumps(payload)}")
        
        response = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        logger.info(f"Translation response status: {response.status_code}")
        
        if not response.ok:
            logger.error(f"Translation API Error: {response.text}")
            raise Exception(f"API Error: {response.status_code} - {response.text}")
        
        data = response.json()
        logger.info(f"Translation response: {json.dumps(data)}")
        
        # Extract translation from response
        translation = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        
        log_function_call("translateToGerman", text, translation)
        return translation
    
    except Exception as e:
        error_message = f"Error: {str(e)}"
        logger.error(f"Translation error: {error_message}")
        logger.error(f"Response: {response.text if 'response' in locals() else 'No response'}")
        log_function_call("translateToGerman", text, error_message)
        return f"Translation error: {str(e)}"

def postprocess_translation(translation):
    """Apply any post-processing to the translation"""
    log_function_call("postprocessTranslation", translation)
    
    # Simple post-processing - ensure proper formatting
    processed_translation = translation.strip()
    
    log_function_call("postprocessTranslation", translation, processed_translation)
    return processed_translation

@app.route('/api/translate', methods=['POST'])
def translate():
    """Main endpoint for translating text"""
    data = request.json
    text = data.get('text', '')
    
    if not text:
        return jsonify({"error": "No text provided for translation"}), 400
    
    try:
        # Clear previous logs for this translation
        global translation_logs
        translation_logs = []
        
        logger.info(f"Received translation request for text: {text}")
        
        # Step 1: Preprocess the text
        preprocessed_text = preprocess_text(text)
        
        # Step 2: Detect the language
        detected_language = detect_language(preprocessed_text)
        
        # Step 3: Translate to German (only if not already German)
        if detected_language.lower() in ['german', 'deutsch']:
            translation = "Der Text ist bereits auf Deutsch."
            log_function_call("translateToGerman", preprocessed_text, translation)
        else:
            translation = translate_to_german(preprocessed_text)
        
        # Step 4: Post-process the translation
        final_translation = postprocess_translation(translation)
        
        # Log the final result
        log_final_answer(final_translation)
        
        return jsonify({
            "translation": final_translation,
            "logs": translation_logs,
            "detected_language": detected_language
        })
    
    except Exception as e:
        error_message = f"Error during translation: {str(e)}"
        logger.error(error_message)
        return jsonify({"error": error_message}), 500

@app.route('/api/test', methods=['GET'])
def test_api():
    """Test endpoint that doesn't require any parameters"""
    return jsonify({
        "status": "success", 
        "message": "API is working correctly"
    })

# Simple endpoint that directly uses the Session2 code approach for translation
@app.route('/api/direct-translate', methods=['POST'])
def direct_translate():
    """Translate text using the direct Session2 approach (no agentic steps)"""
    data = request.json
    text = data.get('text', '')
    
    if not text:
        return jsonify({"error": "No text provided for translation"}), 400
    
    try:
        logger.info(f"Direct translation request for: {text}")
        
        # First detect the language
        language_detection_payload = {
            "contents": [{
                "parts": [{
                    "text": f'You are a language detection agent. Detect the language of this text and respond with only the language name: "{text}"'
                }]
            }],
            "safetySettings": [{
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_NONE"
            }]
        }
        
        language_response = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}",
            json=language_detection_payload,
            headers={"Content-Type": "application/json"}
        )
        
        detected_language = "Unknown"
        if language_response.ok:
            language_data = language_response.json()
            detected_language = language_data["candidates"][0]["content"]["parts"][0]["text"].strip()
            logger.info(f"Detected language: {detected_language}")
        else:
            logger.warning(f"Language detection failed, proceeding with translation anyway")
        
        # Check if already German
        if detected_language.lower() in ['german', 'deutsch']:
            logger.info(f"Text is already in German, no translation needed")
            return jsonify({
                "translation": "Der Text ist bereits auf Deutsch.",
                "detected_language": detected_language
            })
            
        # Then translate to German
        translation_payload = {
            "contents": [{
                "parts": [{
                    "text": f'You are a translator. Translate this English text to German: "{text}". Only respond with the German translation, nothing else.'
                }]
            }],
            "safetySettings": [{
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_NONE"
            }]
        }
        
        logger.info(f"Direct translation request payload: {json.dumps(translation_payload)}")
        
        response = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}",
            json=translation_payload,
            headers={"Content-Type": "application/json"}
        )
        
        logger.info(f"Direct translation response status: {response.status_code}")
        
        if not response.ok:
            logger.error(f"Direct translation API Error: {response.text}")
            return jsonify({"error": f"API Error: {response.status_code} - {response.text}"}), 500
        
        data = response.json()
        logger.info(f"Direct translation API Response: {json.dumps(data)}")
        
        if data.get("candidates") and data["candidates"][0].get("content") and data["candidates"][0]["content"].get("parts"):
            translation = data["candidates"][0]["content"]["parts"][0]["text"].strip()
            logger.info(f"Direct translation result: {translation}")
            
            # Create simple logs for display in the popup
            logs = [
                {
                    "type": "function_call",
                    "function": "detectLanguage",
                    "params": text,
                    "result": detected_language,
                    "timestamp": int(time.time() * 1000)
                },
                {
                    "type": "function_call",
                    "function": "translateToGerman",
                    "params": text,
                    "result": translation,
                    "timestamp": int(time.time() * 1000)
                },
                {
                    "type": "final_answer",
                    "translation": translation,
                    "timestamp": int(time.time() * 1000)
                }
            ]
            
            return jsonify({
                "translation": translation,
                "detected_language": detected_language,
                "logs": logs
            })
        else:
            logger.error(f"Invalid API response format: {json.dumps(data)}")
            return jsonify({"error": "Invalid API response format"}), 500
            
    except Exception as e:
        error_message = f"Error during direct translation: {str(e)}"
        logger.error(error_message)
        return jsonify({"error": error_message}), 500

@app.after_request
def after_request(response):
    """Add CORS headers to allow requests from Chrome extension"""
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    return response

if __name__ == '__main__':
    # Print a message to show the server has started
    logger.info(f"Starting Agentic Translator API server on http://localhost:5000")
    print("="*80)
    print("Agentic Translator API server is running on http://localhost:5000")
    print(f"Using API key (first few chars): {GEMINI_API_KEY[:8]}...")
    print("Try accessing http://localhost:5000/ in your browser to verify")
    print("="*80)
    
    # Run the Flask app
    app.run(debug=True, port=5000) 