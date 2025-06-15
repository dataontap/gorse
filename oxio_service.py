
import os
import requests
import json
from typing import Dict, Any, Optional

class OXIOService:
    def __init__(self):
        self.api_key = os.environ.get('OXIO_API_KEY')
        self.auth_token = os.environ.get('OXIO_AUTH_TOKEN')
        self.base_url = "https://api-staging.brandvno.com"
        
        # Debug information
        print(f"OXIO Service initialized:")
        print(f"  Base URL: {self.base_url}")
        print(f"  API Key configured: {bool(self.api_key)} (length: {len(self.api_key) if self.api_key else 0})")
        print(f"  Auth Token configured: {bool(self.auth_token)} (length: {len(self.auth_token) if self.auth_token else 0})")
        
        if not self.api_key or not self.auth_token:
            raise ValueError("OXIO_API_KEY and OXIO_AUTH_TOKEN must be set in secrets")
    
    def get_headers(self) -> Dict[str, str]:
        """Get standard headers for OXIO API requests"""
        import base64
        
        # Create Basic Auth credentials: username = API_KEY, password = AUTH_TOKEN
        credentials = f"{self.api_key}:{self.auth_token}"
        encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
        
        return {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Basic {encoded_credentials}',
            'User-Agent': 'DOTM-Platform/1.0'
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
            url = f"{self.base_url}/v3/lines/line"
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
            
            # Check if response is JSON
            content_type = response.headers.get('content-type', '').lower()
            response_text = response.text
            
            if 'application/json' in content_type:
                try:
                    response_data = response.json() if response.content else {}
                    print(f"OXIO API Response Body: {json.dumps(response_data, indent=2)}")
                except json.JSONDecodeError:
                    print(f"Failed to parse JSON response: {response_text[:500]}...")
                    response_data = {'error': 'Invalid JSON response', 'raw_response': response_text[:500]}
            else:
                print(f"Non-JSON response received (Content-Type: {content_type})")
                print(f"Response body (first 500 chars): {response_text[:500]}...")
                response_data = {'error': 'Non-JSON response', 'content_type': content_type, 'raw_response': response_text[:500]}
            
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
    
    def test_plans_endpoint(self) -> Dict[str, Any]:
        """Test the plans endpoint for health check"""
        try:
            # Use the v2-internal/plans endpoint for health check
            test_url = "https://api-staging.brandvno.com/v2-internal/plans"
            headers = self.get_headers()
            
            print(f"Testing OXIO plans endpoint: {test_url}")
            auth_masked = f'Basic ...{headers["Authorization"][-8:]}' if 'Authorization' in headers else 'None'
            headers_masked = dict(headers, **{'Authorization': auth_masked})
            print(f"Headers (Basic Auth masked): {headers_masked}")
            
            response = requests.get(test_url, headers=headers, timeout=10)
            print(f"Plans endpoint response status: {response.status_code}")
            print(f"Plans endpoint content-type: {response.headers.get('content-type', 'Unknown')}")
            
            # Log response for debugging
            response_text = response.text[:500]
            print(f"Response preview: {response_text}...")
            
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    return {
                        'success': True,
                        'message': 'OXIO plans endpoint accessible - API connection working',
                        'status_code': response.status_code,
                        'endpoint': test_url,
                        'data': response_data,
                        'api_key_configured': bool(self.api_key),
                        'auth_token_configured': bool(self.auth_token)
                    }
                except json.JSONDecodeError:
                    return {
                        'success': True,
                        'message': 'OXIO plans endpoint accessible but returned non-JSON',
                        'status_code': response.status_code,
                        'response_preview': response_text,
                        'content_type': response.headers.get('content-type', 'Unknown')
                    }
            else:
                return {
                    'success': False,
                    'message': f'Plans endpoint returned status {response.status_code}',
                    'status_code': response.status_code,
                    'endpoint': test_url,
                    'response_preview': response_text,
                    'content_type': response.headers.get('content-type', 'Unknown')
                }
                
        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'message': 'Cannot connect to OXIO plans endpoint - check network',
                'endpoint': test_url
            }
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'message': 'OXIO plans endpoint request timed out',
                'endpoint': test_url
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to test OXIO plans endpoint'
            }

    def test_connection(self) -> Dict[str, Any]:
        """Test connection to OXIO API using plans endpoint"""
        try:
            # First verify our credentials are set
            if not self.api_key or not self.auth_token:
                return {
                    'success': False,
                    'message': 'API credentials not configured',
                    'api_key_configured': bool(self.api_key),
                    'auth_token_configured': bool(self.auth_token)
                }
            
            # Use the plans endpoint for health check
            return self.test_plans_endpoint()
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to test OXIO connection'
            }

# Create a singleton instance
oxio_service = OXIOService()
