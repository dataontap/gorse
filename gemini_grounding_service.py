import os
import logging
from google import genai
from google.genai import types

# IMPORTANT: KEEP THIS COMMENT
# Follow these instructions when using this blueprint:
# - Using google-genai SDK with grounding for real-time information
# - Grounding with Google Search enables live data retrieval

class GeminiGroundingService:
    """Service for getting real-time local context using Gemini with Google Search grounding"""
    
    def __init__(self):
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            logging.warning("GEMINI_API_KEY not configured")
            self.client = None
        else:
            self.client = genai.Client(api_key=api_key)
            logging.info("Gemini Grounding Service initialized successfully")
    
    def get_local_context(self, city: str, region: str, country: str) -> dict:
        """
        Get real-time local context (weather, traffic, events) for a location using Gemini grounding.
        
        Args:
            city: City name (e.g., "Toronto")
            region: Region/province (e.g., "Ontario")
            country: Country name (e.g., "Canada")
        
        Returns:
            dict with keys:
                - success: bool
                - weather: str (description of current weather)
                - traffic: str (description of current traffic conditions)
                - events: str (description of today's events)
                - summary: str (2-3 sentence summary for voice message)
                - error: str (if failed)
        """
        if not self.client:
            return {
                'success': False,
                'error': 'Gemini API not configured'
            }
        
        try:
            location_str = f"{city}, {region}, {country}"
            
            # Craft a prompt that will trigger Google Search grounding
            prompt = f"""For {location_str} right now, provide current information about:

1. Weather: What is the current weather and temperature?
2. Traffic: What are the current traffic conditions?
3. Events: What events or activities are happening today?

Please provide a concise, natural summary that could be spoken in a welcome message. 
Keep it brief (2-3 sentences) and focus on the most relevant information for someone just joining from this location."""

            # Use Gemini with grounding enabled
            response = self.client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.7,
                    # Enable grounding with Google Search
                    tools=[types.Tool(google_search=types.GoogleSearch())]
                )
            )
            
            if response.text:
                summary = response.text.strip()
                
                # Parse the response to extract components
                # The response will be a natural language summary
                return {
                    'success': True,
                    'summary': summary,
                    'location': location_str,
                    'grounded': True
                }
            else:
                return {
                    'success': False,
                    'error': 'No response from Gemini'
                }
                
        except Exception as e:
            logging.error(f"Error getting local context from Gemini: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_structured_context(self, city: str, region: str, country: str) -> dict:
        """
        Get structured local context with separate fields for weather, traffic, and events.
        
        Returns:
            dict with keys:
                - success: bool
                - weather: dict (temp, condition, description)
                - traffic: dict (status, description)
                - events: list (event names and descriptions)
                - error: str (if failed)
        """
        if not self.client:
            return {
                'success': False,
                'error': 'Gemini API not configured'
            }
        
        try:
            location_str = f"{city}, {region}, {country}"
            
            prompt = f"""For {location_str}, provide current real-time information in the following format:

WEATHER: [Current temperature and conditions]
TRAFFIC: [Current traffic situation]
EVENTS: [Today's notable events, if any]

Be concise and factual. Use actual current data."""

            response = self.client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    tools=[types.Tool(google_search=types.GoogleSearch())]
                )
            )
            
            if response.text:
                result_text = response.text.strip()
                
                # Parse the structured response
                weather = ""
                traffic = ""
                events = ""
                
                lines = result_text.split('\n')
                current_section = None
                
                for line in lines:
                    line = line.strip()
                    if line.startswith('WEATHER:'):
                        current_section = 'weather'
                        weather = line.replace('WEATHER:', '').strip()
                    elif line.startswith('TRAFFIC:'):
                        current_section = 'traffic'
                        traffic = line.replace('TRAFFIC:', '').strip()
                    elif line.startswith('EVENTS:'):
                        current_section = 'events'
                        events = line.replace('EVENTS:', '').strip()
                    elif line and current_section:
                        if current_section == 'weather':
                            weather += ' ' + line
                        elif current_section == 'traffic':
                            traffic += ' ' + line
                        elif current_section == 'events':
                            events += ' ' + line
                
                return {
                    'success': True,
                    'weather': weather.strip(),
                    'traffic': traffic.strip(),
                    'events': events.strip(),
                    'location': location_str,
                    'grounded': True
                }
            else:
                return {
                    'success': False,
                    'error': 'No response from Gemini'
                }
                
        except Exception as e:
            logging.error(f"Error getting structured context from Gemini: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }


# Create singleton instance
gemini_grounding_service = GeminiGroundingService()
