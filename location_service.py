import requests
from typing import Dict, Optional
from datetime import datetime
import pytz

class LocationService:
    """Service for IP-based location and ISP detection"""
    
    def __init__(self):
        self.ip_api_url = "http://ip-api.com/json/{ip}"
    
    def get_location_data(self, ip_address: Optional[str] = None) -> Dict:
        """
        Get location and ISP data from IP address using IP-API.com
        
        Args:
            ip_address: IP address to lookup (optional, will use requester's IP if not provided)
            
        Returns:
            dict with location and ISP information
        """
        try:
            # If no IP provided, IP-API will use the requester's IP
            url = self.ip_api_url.format(ip=ip_address if ip_address else '')
            
            # Request specific fields for efficiency
            params = {
                'fields': 'status,message,country,countryCode,region,regionName,city,zip,lat,lon,timezone,isp,org,as,query'
            }
            
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status') == 'success':
                return {
                    'success': True,
                    'city': data.get('city', 'Unknown'),
                    'region': data.get('regionName', ''),
                    'country': data.get('country', 'Unknown'),
                    'country_code': data.get('countryCode', ''),
                    'timezone': data.get('timezone', ''),
                    'latitude': data.get('lat'),
                    'longitude': data.get('lon'),
                    'isp': data.get('isp', 'Unknown ISP'),
                    'organization': data.get('org', ''),
                    'as_number': data.get('as', ''),
                    'ip': data.get('query', ip_address)
                }
            else:
                error_msg = data.get('message', 'Unknown error')
                print(f"Location lookup failed: {error_msg}")
                return {
                    'success': False,
                    'error': error_msg
                }
                
        except requests.exceptions.Timeout:
            print("Location lookup timed out")
            return {
                'success': False,
                'error': 'Location lookup timed out'
            }
        except Exception as e:
            print(f"Error fetching location data: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_location_string(self, location_data: Dict) -> str:
        """
        Format location data into a friendly string
        
        Args:
            location_data: dict from get_location_data()
            
        Returns:
            Formatted location string
        """
        if not location_data.get('success'):
            return "your location"
        
        city = location_data.get('city', '')
        region = location_data.get('region', '')
        country = location_data.get('country', '')
        
        # Build location string
        parts = []
        if city:
            parts.append(city)
        if region and region != city:
            parts.append(region)
        if country:
            parts.append(country)
        
        return ', '.join(parts) if parts else "your location"
    
    def get_local_time(self, timezone_str: str) -> Dict:
        """
        Get current local time for a given timezone
        
        Args:
            timezone_str: Timezone string (e.g., 'America/Toronto')
            
        Returns:
            dict with local time information
        """
        try:
            if not timezone_str:
                return {
                    'success': False,
                    'error': 'No timezone provided'
                }
            
            # Get timezone object
            tz = pytz.timezone(timezone_str)
            
            # Get current time in that timezone
            now = datetime.now(tz)
            
            # Format time for voice message
            hour = now.hour
            minute = now.minute
            
            # Determine time of day
            if 5 <= hour < 12:
                time_of_day = "morning"
            elif 12 <= hour < 17:
                time_of_day = "afternoon"
            elif 17 <= hour < 21:
                time_of_day = "evening"
            else:
                time_of_day = "night"
            
            # Format time string
            time_12h = now.strftime("%I:%M %p").lstrip('0')  # Remove leading zero
            time_24h = now.strftime("%H:%M")
            
            return {
                'success': True,
                'timezone': timezone_str,
                'datetime': now.isoformat(),
                'time_12h': time_12h,
                'time_24h': time_24h,
                'hour': hour,
                'minute': minute,
                'time_of_day': time_of_day,
                'date': now.strftime("%B %d, %Y"),  # e.g., "October 31, 2025"
                'day_of_week': now.strftime("%A")  # e.g., "Friday"
            }
            
        except Exception as e:
            print(f"Error getting local time: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

# Create singleton instance
location_service = LocationService()
