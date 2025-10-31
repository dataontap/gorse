import requests
from typing import Dict, Optional

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

# Create singleton instance
location_service = LocationService()
