import os
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class EventsService:
    """Service for fetching local events using Ticketmaster API"""
    
    def __init__(self):
        self.api_key = os.environ.get('TICKETMASTER_API_KEY')
        self.base_url = "https://app.ticketmaster.com/discovery/v2"
        
        if not self.api_key:
            print("WARNING: TICKETMASTER_API_KEY not configured. Event fetching will not work.")
    
    def get_recent_events(self, city: str, country_code: str = 'US', days_back: int = 30, max_results: int = 5) -> Dict:
        """
        Fetch recent events from a city in the last N days
        
        Args:
            city: City name
            country_code: Two-letter country code (default: US)
            days_back: Number of days to look back (default: 30)
            max_results: Maximum number of events to return (default: 5)
            
        Returns:
            dict with events data
        """
        if not self.api_key:
            return {
                'success': False,
                'error': 'Ticketmaster API key not configured'
            }
        
        try:
            # Calculate date range (last 30 days)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            # Format dates for API (ISO 8601 format)
            start_datetime = start_date.strftime('%Y-%m-%dT%H:%M:%SZ')
            end_datetime = end_date.strftime('%Y-%m-%dT%H:%M:%SZ')
            
            # Build API request
            params = {
                'apikey': self.api_key,
                'city': city,
                'countryCode': country_code,
                'startDateTime': start_datetime,
                'endDateTime': end_datetime,
                'size': max_results,
                'sort': 'date,desc'  # Most recent first
            }
            
            response = requests.get(
                f"{self.base_url}/events.json",
                params=params,
                timeout=5
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Extract events
            events = []
            if '_embedded' in data and 'events' in data['_embedded']:
                for event in data['_embedded']['events']:
                    events.append({
                        'name': event.get('name', ''),
                        'date': event.get('dates', {}).get('start', {}).get('localDate', ''),
                        'time': event.get('dates', {}).get('start', {}).get('localTime', ''),
                        'venue': event.get('_embedded', {}).get('venues', [{}])[0].get('name', ''),
                        'category': event.get('classifications', [{}])[0].get('segment', {}).get('name', ''),
                        'url': event.get('url', '')
                    })
            
            return {
                'success': True,
                'events': events,
                'total': len(events)
            }
            
        except requests.exceptions.Timeout:
            print("Events API timed out")
            return {
                'success': False,
                'error': 'Events lookup timed out'
            }
        except Exception as e:
            print(f"Error fetching events: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def format_events_summary(self, events_data: Dict) -> str:
        """
        Format events into a readable summary for welcome message
        
        Args:
            events_data: dict from get_recent_events()
            
        Returns:
            Formatted events summary string
        """
        if not events_data.get('success') or not events_data.get('events'):
            return ""
        
        events = events_data['events'][:3]  # Top 3 events
        
        if not events:
            return ""
        
        summary_parts = []
        for event in events:
            name = event.get('name', '')
            date = event.get('date', '')
            venue = event.get('venue', '')
            
            if name:
                event_str = f"{name}"
                if date:
                    event_str += f" on {date}"
                if venue:
                    event_str += f" at {venue}"
                summary_parts.append(event_str)
        
        if summary_parts:
            return "Recent local events include: " + "; ".join(summary_parts) + "."
        
        return ""

# Create singleton instance
events_service = EventsService()
