
import os
import requests
import json
from typing import Dict, Any, Optional

class OXIOService:
    def __init__(self):
        self.api_key = os.environ.get('OXIO_API_KEY')
        self.auth_token = os.environ.get('OXIO_AUTH_TOKEN')
        self.base_url = "https://api-staging.brandvno.com/v3"
        
        if not self.api_key or not self.auth_token:
            raise ValueError("OXIO_API_KEY and OXIO_AUTH_TOKEN must be set in secrets")
    
    def get_headers(self) -> Dict[str, str]:
        """Get standard headers for OXIO API requests"""
        return {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.auth_token}',
            'X-API-Key': self.api_key
        }
    
    def activate_line(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Activate a line using OXIO API
        
        Args:
            payload: Line activation payload
            
        Returns:
            API response as dictionary
        """
        try:
            url = f"{self.base_url}/lines/line"
            headers = self.get_headers()
            
            print(f"OXIO API Request URL: {url}")
            print(f"OXIO API Request Headers: {headers}")
            print(f"OXIO API Request Payload: {json.dumps(payload, indent=2)}")
            
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            print(f"OXIO API Response Status: {response.status_code}")
            print(f"OXIO API Response Headers: {dict(response.headers)}")
            
            response_data = response.json() if response.content else {}
            print(f"OXIO API Response Body: {json.dumps(response_data, indent=2)}")
            
            if response.status_code >= 200 and response.status_code < 300:
                return {
                    'success': True,
                    'status_code': response.status_code,
                    'data': response_data,
                    'message': 'Line activation successful'
                }
            else:
                return {
                    'success': False,
                    'status_code': response.status_code,
                    'data': response_data,
                    'error': f'OXIO API error: {response.status_code}',
                    'message': response_data.get('message', 'Unknown error')
                }
                
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': 'Request timeout',
                'message': 'OXIO API request timed out'
            }
        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'error': 'Connection error',
                'message': 'Could not connect to OXIO API'
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': 'Request error',
                'message': f'Request failed: {str(e)}'
            }
        except json.JSONDecodeError:
            return {
                'success': False,
                'error': 'Invalid JSON response',
                'message': 'OXIO API returned invalid JSON'
            }
        except Exception as e:
            return {
                'success': False,
                'error': 'Unexpected error',
                'message': f'Unexpected error: {str(e)}'
            }
    
    def test_connection(self) -> Dict[str, Any]:
        """Test connection to OXIO API"""
        try:
            # You can implement a health check endpoint here if OXIO provides one
            # For now, we'll just verify our credentials are set
            if not self.api_key or not self.auth_token:
                return {
                    'success': False,
                    'message': 'API credentials not configured'
                }
            
            return {
                'success': True,
                'message': 'OXIO service configured successfully',
                'base_url': self.base_url,
                'api_key_configured': bool(self.api_key),
                'auth_token_configured': bool(self.auth_token)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to initialize OXIO service'
            }

# Create a singleton instance
oxio_service = OXIOService()
