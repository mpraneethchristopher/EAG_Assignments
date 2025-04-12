from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
from dotenv import load_dotenv
import logging
import json
from datetime import datetime
import win32com.client as win32

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("flight_search.log"), logging.StreamHandler()]
)
logger = logging.getLogger("flight_search")

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Email configuration
RECIPIENT_EMAIL = 'mpraneeth.c@gmail.com'

# Define available tools/functions
tools_description = """
Available tools:
- search_skyscanner(departure: string, arrival: string, date: string) -> list: Search flights on Skyscanner
- search_kayak(departure: string, arrival: string, date: string) -> list: Search flights on Kayak
- search_google_flights(departure: string, arrival: string, date: string) -> list: Search flights on Google Flights
- analyze_flights(flights: list) -> dict: Analyze flight options based on price, duration, and stops
- recommend_flights(analysis: dict) -> list: Recommend best flight options based on analysis
"""

def get_system_prompt(params):
    departure = params.get('departure', '')
    arrival = params.get('arrival', '')
    departure_date = params.get('departureDate', '')
    return_date = params.get('returnDate', '')
    passengers = params.get('passengers', 1)
    
    return f"""You are a flight search expert with access to multiple flight search APIs. Your task is to:

1. Search for flights from {departure} to {arrival} on {departure_date}{f' with return on {return_date}' if return_date else ''}
2. Consider {passengers} passenger(s)
3. Analyze the results based on:
   - Price competitiveness
   - Flight duration and layovers
   - Airline reputation and reliability
   - Overall value proposition

{tools_description}

Respond with EXACTLY ONE of these formats:
1. For API calls:
   {{
     "type": "api_call",
     "api": "api_name",
     "params": {{
       "param1": "value1",
       "param2": "value2",
       ...
     }}
   }}
   
   Example: For search_skyscanner(departure, arrival, date), use:
   {{
     "type": "api_call",
     "api": "search_skyscanner",
     "params": {{
       "departure": "BER",
       "arrival": "DEL",
       "date": "2024-03-15"
     }}
   }}

2. For analysis:
   {{
     "type": "analysis",
     "content": "detailed analysis of flight options"
   }}

3. For recommendations:
   {{
     "type": "recommendation",
     "content": "specific flight recommendation with reasoning"
   }}

DO NOT include multiple responses. Give ONE response at a time.
Make sure to provide parameters in the correct order as specified in the API signature.
After searching, proceed with analysis and recommendations in sequence."""

# Flight search API endpoints
FLIGHT_APIS = {
    "skyscanner": "https://partners.api.skyscanner.net/apiservices/v3/flights/live/search/create",
    "kayak": "https://www.kayak.com/h/mobileapis/directory/apisearch",
    "google_flights": "https://www.googleapis.com/qpxExpress/v1/trips/search"
}

def update_system_prompt(prompt_type: str, prompt: str):
    """Update a system prompt"""
    if prompt_type in current_system_prompts:
        current_system_prompts[prompt_type] = prompt
        return True
    return False

def get_system_prompts():
    """Get all current system prompts"""
    return current_system_prompts

def reset_system_prompts():
    """Reset system prompts to defaults"""
    global current_system_prompts
    current_system_prompts = DEFAULT_SYSTEM_PROMPTS.copy()
    return current_system_prompts

def search_skyscanner(params, prompt):
    """Search flights using Skyscanner API"""
    try:
        # In a real implementation, you would use the actual Skyscanner API
        # This is a mock response
        return [
            {
                "airline": "Lufthansa",
                "departureTime": "10:00",
                "arrivalTime": "22:30",
                "duration": "12h 30m",
                "stops": "1 stop",
                "price": "€450",
                "source": "Skyscanner"
            }
        ]
    except Exception as e:
        logger.error(f"Error searching Skyscanner: {str(e)}")
        return []

def search_kayak(params, prompt):
    """Search flights using Kayak API"""
    try:
        # In a real implementation, you would use the actual Kayak API
        # This is a mock response
        return [
            {
                "airline": "Air India",
                "departureTime": "08:00",
                "arrivalTime": "20:00",
                "duration": "12h 00m",
                "stops": "Direct",
                "price": "€480",
                "source": "Kayak"
            }
        ]
    except Exception as e:
        logger.error(f"Error searching Kayak: {str(e)}")
        return []

def search_google_flights(params, prompt):
    """Search flights using Google Flights API"""
    try:
        # In a real implementation, you would use the actual Google Flights API
        # This is a mock response
        return [
            {
                "airline": "Qatar Airways",
                "departureTime": "09:30",
                "arrivalTime": "23:00",
                "duration": "13h 30m",
                "stops": "1 stop",
                "price": "€490",
                "source": "Google Flights"
            }
        ]
    except Exception as e:
        logger.error(f"Error searching Google Flights: {str(e)}")
        return []

def analyze_and_recommend(flights, prompts):
    """Analyze and recommend flights based on the prompts"""
    try:
        # Sort flights by price
        flights.sort(key=lambda x: int(x['price'].replace('€', '')))
        
        # Add recommendations based on analysis
        for i, flight in enumerate(flights):
            if i == 0:
                flight['recommendation'] = "Best value option - Lowest price with good duration"
            elif flight['stops'] == "Direct":
                flight['recommendation'] = "Recommended for direct flight preference"
        
        return flights
    except Exception as e:
        logger.error(f"Error analyzing flights: {str(e)}")
        return flights

def send_email(subject, body, results):
    try:
        # Create Outlook application instance
        outlook = win32.Dispatch('outlook.application')
        mail = outlook.CreateItem(0)  # 0 represents a mail item

        # Set email properties
        mail.To = RECIPIENT_EMAIL
        mail.Subject = subject

        # Create HTML content
        html = f"""
        <html>
            <body>
                <h2>Flight Search Results</h2>
                <p>{body}</p>
                <h3>Flight Options:</h3>
                <table border="1" style="border-collapse: collapse; width: 100%;">
                    <tr>
                        <th>Airline</th>
                        <th>Price</th>
                        <th>Departure</th>
                        <th>Arrival</th>
                        <th>Duration</th>
                        <th>Stops</th>
                        <th>Source</th>
                        <th>Recommendation</th>
                    </tr>
        """
        
        for flight in results:
            html += f"""
                    <tr>
                        <td>{flight['airline']}</td>
                        <td>{flight['price']}</td>
                        <td>{flight['departureTime']}</td>
                        <td>{flight['arrivalTime']}</td>
                        <td>{flight['duration']}</td>
                        <td>{flight['stops']}</td>
                        <td>{flight['source']}</td>
                        <td>{flight.get('recommendation', '')}</td>
                    </tr>
            """
        
        html += """
                </table>
            </body>
        </html>
        """

        # Set HTML body
        mail.HTMLBody = html

        # Send email
        mail.Send()
        
        logger.info("Email sent successfully")
        return True
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        return False

@app.route('/api/system-prompts', methods=['GET'])
def get_system_prompts_endpoint():
    """Get all current system prompts"""
    return jsonify(get_system_prompts())

@app.route('/api/system-prompts', methods=['POST'])
def update_system_prompt_endpoint():
    """Update a system prompt"""
    data = request.json
    prompt_type = data.get('type')
    prompt = data.get('prompt')
    
    if not prompt_type or not prompt:
        return jsonify({"error": "Missing prompt type or prompt text"}), 400
    
    success = update_system_prompt(prompt_type, prompt)
    if success:
        return jsonify({"status": "success", "message": "System prompt updated"})
    return jsonify({"error": "Invalid prompt type"}), 400

@app.route('/api/system-prompts/reset', methods=['POST'])
def reset_system_prompts_endpoint():
    """Reset system prompts to defaults"""
    reset_system_prompts()
    return jsonify({"status": "success", "message": "System prompts reset to defaults"})

@app.route('/api/search-flights', methods=['POST'])
def search_flights():
    """Search for flights using multiple APIs"""
    try:
        data = request.json
        system_prompt = get_system_prompt(data)
        
        # Here you would:
        # 1. Process the system prompt
        # 2. Make API calls based on the prompt
        # 3. Analyze results
        # 4. Return recommendations
        
        # For now, return mock data
        results = [
            {
                "airline": "Air India",
                "price": "₹25,000",
                "departureTime": "10:00 AM",
                "arrivalTime": "1:00 PM",
                "duration": "3h 0m",
                "stops": "Non-stop",
                "source": "Skyscanner",
                "recommendation": "Best value for money with direct flight"
            }
        ]
        
        # Send email with results
        subject = f"Flight Search Results: {data.get('departure', '')} to {data.get('arrival', '')}"
        body = f"Here are the flight options from {data.get('departure', '')} to {data.get('arrival', '')} on {data.get('departureDate', '')}"
        send_email(subject, body, results)
        
        return jsonify({"results": results})
        
    except Exception as e:
        logger.error(f"Error in flight search: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) 