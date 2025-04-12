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
        logging.FileHandler("flight_search.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("flight_search")

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure Gemini API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=GEMINI_API_KEY)

# Initialize the model
model = genai.GenerativeModel('gemini-2.0-flash')

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

    system_prompt = f"""You are a flight search expert with access to multiple flight search APIs. Your task is to:

1. Search for flights from {departure} to {arrival} on {departure_date}{f' with return on {return_date}' if return_date else ''}
2. Consider {passengers} passenger(s)
3. Analyze the results based on:
   - Price competitiveness (compare with historical averages and other options)
   - Flight duration and layovers (prefer shorter total travel time)
   - Airline reputation and reliability (check on-time performance)
   - Overall value proposition (price vs. quality ratio)
   - Connection quality (layover duration, airport facilities)
   - Cabin class and amenities

{tools_description}

REASONING STEPS:
1. Parameter Validation:
   - Verify all input parameters are valid
   - Check date formats and airport codes
   - Validate passenger count

2. Search Strategy:
   - Determine which APIs to query based on route
   - Plan search sequence for optimal results
   - Consider time zones and connection times

3. Analysis Process:
   - Compare prices across providers
   - Evaluate flight durations and connections
   - Assess airline reliability
   - Consider passenger preferences

4. Recommendation Criteria:
   - Price vs. quality balance
   - Total travel time
   - Connection convenience
   - Airline reputation

ERROR HANDLING:
- If an API call fails, try alternative providers
- If no flights found, suggest alternative dates/routes
- If parameters invalid, request clarification
- If analysis incomplete, explain missing data

RESPONSE FORMATS:
1. For API calls:
   {{
     "type": "api_call",
     "reasoning_type": "search_planning",
     "api": "api_name",
     "params": {{
       "param1": "value1",
       "param2": "value2",
       ...
     }},
     "validation": {{
       "param1_valid": true,
       "param2_valid": true,
       "notes": "validation notes"
     }}
   }}
   
   Example: For search_skyscanner(departure, arrival, date), use:
   {{
     "type": "api_call",
     "reasoning_type": "search_planning",
     "api": "search_skyscanner",
     "params": {{
       "departure": "BER",
       "arrival": "DEL",
       "date": "2024-03-15"
     }},
     "validation": {{
       "departure_valid": true,
       "arrival_valid": true,
       "date_valid": true,
       "notes": "All parameters validated"
     }}
   }}

2. For analysis:
   {{
     "type": "analysis",
     "reasoning_type": "comparative_analysis",
     "content": "detailed analysis of flight options",
     "metrics": {{
       "price_range": "min-max",
       "avg_duration": "Xh Ym",
       "direct_options": "count",
       "best_value": "airline name"
     }},
     "validation": {{
       "data_complete": true,
       "sources_verified": true,
       "notes": "analysis validation notes"
     }}
   }}

3. For recommendations:
   {{
     "type": "recommendation",
     "reasoning_type": "decision_making",
     "content": "specific flight recommendation with reasoning",
     "flight_details": {{
       "airline": "name",
       "price": "amount",
       "duration": "Xh Ym",
       "stops": "count",
       "departure": "time",
       "arrival": "time"
     }},
     "reasoning": "detailed explanation of why this is the best option",
     "validation": {{
       "criteria_met": true,
       "alternatives_considered": true,
       "notes": "recommendation validation notes"
     }}
   }}

4. For errors or clarifications:
   {{
     "type": "error",
     "reasoning_type": "error_handling",
     "error_type": "validation|api|analysis|recommendation",
     "message": "detailed error description",
     "suggested_action": "what to do next",
     "validation": {{
       "error_confirmed": true,
       "impact_assessed": true,
       "notes": "error handling notes"
     }}
   }}

CONVERSATION SUPPORT:
- Each response should reference previous context when relevant
- Maintain state of search progress
- Support follow-up questions about specific aspects
- Allow for parameter adjustments and re-analysis

IMPORTANT RULES:
1. DO NOT include multiple responses - give ONE response at a time
2. Validate all parameters before making API calls
3. Handle errors gracefully and report them clearly
4. Ensure all time zones are properly considered
5. After searching, proceed with analysis and recommendations in sequence
6. For return flights, ensure the return journey is also analyzed
7. Consider time zone differences when calculating total travel time
8. Always include validation and reasoning_type in responses
9. Support multi-turn conversations by maintaining context"""

    return system_prompt

@app.route('/api/search-flights', methods=['POST'])
def search_flights():
    """Search for flights using Gemini API"""
    try:
        # Log request details
        logger.info("\n" + "="*50)
        logger.info("Starting new flight search request")
        logger.info("="*50)
        
        data = request.json
        logger.info(f"\nRequest Parameters:")
        logger.info(f"Departure: {data.get('departure', '')}")
        logger.info(f"Arrival: {data.get('arrival', '')}")
        logger.info(f"Departure Date: {data.get('departureDate', '')}")
        logger.info(f"Return Date: {data.get('returnDate', '')}")
        logger.info(f"Passengers: {data.get('passengers', 1)}")
        
        # Get system prompt
        logger.info("\nGenerating system prompt...")
        system_prompt = get_system_prompt(data)
        logger.info("System prompt generated successfully")
        
        # Prepare the prompt for Gemini
        logger.info("\nPreparing Gemini API request...")
        prompt = f"""
        {system_prompt}
        
        Please search for flights with the following details:
        - Departure: {data.get('departure', '')}
        - Arrival: {data.get('arrival', '')}
        - Departure Date: {data.get('departureDate', '')}
        - Return Date: {data.get('returnDate', '')}
        - Passengers: {data.get('passengers', 1)}
        
        IMPORTANT: You must respond with ONLY a valid JSON object in the following format:
        {{
            "results": [
                {{
                    "airline": "string",
                    "price": "string",
                    "departureTime": "string",
                    "arrivalTime": "string",
                    "duration": "string",
                    "stops": "string",
                    "source": "string",
                    "recommendation": "string"
                }}
            ]
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
            
            # Check if the response has the expected structure
            if "results" not in results:
                # Try to find flight information in the response
                flight_info = []
                for key, value in results.items():
                    logger.info(f"\nChecking key: {key}")
                    logger.info(f"Value type: {type(value)}")
                    
                    if isinstance(value, list):
                        for item in value:
                            if isinstance(item, dict):
                                logger.info(f"Item keys: {item.keys()}")
                                if any(field in item for field in ['airline', 'price', 'departureTime']):
                                    flight_info.append(item)
                
                if flight_info:
                    logger.info(f"\nFound {len(flight_info)} flight options in alternative format")
                    results = {"results": flight_info}
                else:
                    raise ValueError("Response missing 'results' key and no flight information found")
            
            if not isinstance(results["results"], list):
                raise ValueError("'results' is not a list")
            
            # Validate each flight entry
            valid_flights = []
            for flight in results["results"]:
                if isinstance(flight, dict):
                    valid_flight = {
                        "airline": flight.get("airline", "Unknown"),
                        "price": flight.get("price", "N/A"),
                        "departureTime": flight.get("departureTime", "N/A"),
                        "arrivalTime": flight.get("arrivalTime", "N/A"),
                        "duration": flight.get("duration", "N/A"),
                        "stops": flight.get("stops", "N/A"),
                        "source": flight.get("source", "N/A"),
                        "recommendation": flight.get("recommendation", "N/A")
                    }
                    valid_flights.append(valid_flight)
            
            results["results"] = valid_flights
            
            logger.info("\nSuccessfully parsed flight results:")
            for flight in results["results"]:
                logger.info(f"\nFlight Option:")
                logger.info(f"Airline: {flight['airline']}")
                logger.info(f"Price: {flight['price']}")
                logger.info(f"Departure: {flight['departureTime']}")
                logger.info(f"Arrival: {flight['arrivalTime']}")
                logger.info(f"Duration: {flight['duration']}")
                logger.info(f"Stops: {flight['stops']}")
                logger.info(f"Source: {flight['source']}")
                logger.info(f"Recommendation: {flight['recommendation']}")
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"\nFailed to parse Gemini API response: {str(e)}")
            logger.error(f"Response that failed to parse: {response_text}")
            logger.info("\nUsing mock data as fallback...")
            
            # If parsing fails, use mock data
            results = {
                "results": [
                    {
                        "airline": "Lufthansa",
                        "price": "INR 45,000",
                        "departureTime": "10:00 AM",
                        "arrivalTime": "11:30 PM",
                        "duration": "9h 30m",
                        "stops": "Non-stop",
                        "source": "Skyscanner",
                        "recommendation": "Best direct flight option with good service"
                    },
                    {
                        "airline": "Emirates",
                        "price": "INR 42,500",
                        "departureTime": "2:30 PM",
                        "arrivalTime": "6:00 AM (next day)",
                        "duration": "8h 30m",
                        "stops": "1 stop in Dubai",
                        "source": "Skyscanner",
                        "recommendation": "Good value with short layover in Dubai"
                    }
                ]
            }
            
            logger.info("\nMock flight results:")
            for flight in results["results"]:
                logger.info(f"\nFlight Option:")
                logger.info(f"Airline: {flight['airline']}")
                logger.info(f"Price: {flight['price']}")
                logger.info(f"Departure: {flight['departureTime']}")
                logger.info(f"Arrival: {flight['arrivalTime']}")
                logger.info(f"Duration: {flight['duration']}")
                logger.info(f"Stops: {flight['stops']}")
                logger.info(f"Source: {flight['source']}")
                logger.info(f"Recommendation: {flight['recommendation']}")
        
        logger.info("\nSending flight search results to client...")
        logger.info("="*50 + "\n")
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"\nError in flight search: {str(e)}")
        logger.error("="*50 + "\n")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) 