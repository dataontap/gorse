import os
import requests
import json
from typing import Dict, Any, Optional
import time

class OXIOService:
    def __init__(self):
        self.api_key = os.environ.get('OXIO_API_KEY')
        self.auth_token = os.environ.get('OXIO_AUTH_TOKEN')
        self.base_url = "https://api-staging.brandvno.com"

        # Debug information
        print(f"OXIO Service initialized:")
        print(f"  Base URL: {self.base_url}")
        print(f"  API Key configured: {bool(self.api_key)}")
        print(f"  Auth Token configured: {bool(self.auth_token)}")

        if not self.api_key or not self.auth_token:
            raise ValueError("OXIO_API_KEY and OXIO_AUTH_TOKEN must be set in secrets")

    def get_headers(self) -> Dict[str, str]:
        """Get standard headers for OXIO API requests"""
        import base64

        # Create Basic Auth credentials: username = API_KEY, password = AUTH_TOKEN
        credentials = f"{self.api_key}:{self.auth_token}"
        encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')

        # Credentials configured and encoded for authorization

        return {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Basic {encoded_credentials}',
            'User-Agent': 'DOTM-Platform/1.0'
        }

    def activate_line(self, oxio_user_id: str) -> Dict[str, Any]:
        """
        Activate a line using simplified OXIO API payload with only OXIO user ID

        Args:
            oxio_user_id: OXIO user ID for line activation

        Returns:
            API response as dictionary
        """
        try:
            url = f"{self.base_url}/v3/lines/line"
            headers = self.get_headers()

            # Validate that OXIO user ID is provided
            if not oxio_user_id:
                return {
                    'success': False,
                    'error': 'Missing OXIO user ID',
                    'message': 'OXIO user ID is required for line activation'
                }

            # Create simplified payload as requested - only these 4 fields
            payload = {
                "lineType": "LINE_TYPE_MOBILITY",
                "countryCode": "US",
                "sim": { "simType": "EMBEDDED" },
                "endUserId": oxio_user_id
            }

            print(f"OXIO API Request URL: {url}")
            print(f"OXIO API Request Headers (Auth masked): {dict(headers, **{'Authorization': '***'})}")
            print(f"OXIO API Request Payload: {json.dumps(payload, indent=2)}")

            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=30
            )

            print(f"OXIO API Response Status: {response.status_code}")
            print(f"OXIO API Response Headers: {dict(response.headers)}")

            # Get response text first
            response_text = response.text
            print(f"Raw response body: {response_text}")

            # Check if response is JSON
            content_type = response.headers.get('content-type', '').lower()

            if 'application/json' in content_type:
                try:
                    response_data = response.json() if response.content else {}
                    print(f"OXIO API Response Body (parsed): {json.dumps(response_data, indent=2)}")
                except json.JSONDecodeError as json_err:
                    print(f"Failed to parse JSON response: {str(json_err)}")
                    print(f"Raw response (first 1000 chars): {response_text[:1000]}...")
                    response_data = {
                        'error': 'Invalid JSON response', 
                        'json_error': str(json_err),
                        'raw_response': response_text[:1000]
                    }
            else:
                print(f"Non-JSON response received (Content-Type: {content_type})")
                print(f"Response body (first 1000 chars): {response_text[:1000]}...")
                response_data = {
                    'error': 'Non-JSON response', 
                    'content_type': content_type, 
                    'raw_response': response_text[:1000]
                }

            if response.status_code >= 200 and response.status_code < 300:
                return {
                    'success': True,
                    'status_code': response.status_code,
                    'data': response_data,
                    'message': 'Line activation successful',
                    'request_payload': payload
                }
            else:
                error_details = {
                    'success': False,
                    'status_code': response.status_code,
                    'data': response_data,
                    'error': f'OXIO API error: {response.status_code}',
                    'message': response_data.get('message', f'HTTP {response.status_code} error'),
                    'request_payload': payload,
                    'response_headers': dict(response.headers)
                }

                # Add specific error details if available
                if isinstance(response_data, dict):
                    if 'error' in response_data:
                        error_details['oxio_error'] = response_data['error']
                    if 'details' in response_data:
                        error_details['oxio_details'] = response_data['details']
                    if 'validation_errors' in response_data:
                        error_details['validation_errors'] = response_data['validation_errors']

                return error_details

        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': 'Request timeout',
                'message': 'OXIO API request timed out after 30 seconds',
                'request_payload': payload
            }
        except requests.exceptions.ConnectionError as conn_err:
            return {
                'success': False,
                'error': 'Connection error',
                'message': f'Could not connect to OXIO API: {str(conn_err)}',
                'request_payload': payload
            }
        except requests.exceptions.RequestException as req_err:
            return {
                'success': False,
                'error': 'Request error',
                'message': f'Request failed: {str(req_err)}',
                'request_payload': payload
            }
        except json.JSONDecodeError as json_err:
            return {
                'success': False,
                'error': 'Invalid JSON response',
                'message': f'OXIO API returned invalid JSON: {str(json_err)}',
                'request_payload': payload
            }
        except Exception as e:
            return {
                'success': False,
                'error': 'Unexpected error',
                'message': f'Unexpected error: {str(e)}',
                'request_payload': payload
            }

    def create_oxio_user(self, first_name=None, last_name=None, email=None, firebase_uid=None) -> Dict[str, Any]:
        """
        Create a new OXIO end user

        Args:
            first_name: User's first name (optional, defaults to "Anonymous")
            last_name: User's last name (optional, defaults to "Anonymous")
            email: User's email address (optional)
            firebase_uid: Firebase UID for tracking (optional)

        Returns:
            API response as dictionary
        """
        try:
            url = f"{self.base_url}/v2/end-users"
            headers = self.get_headers()

            payload = {
                "sex": "UNSPECIFIED",
                "firstName": first_name or "Anonymous",
                "lastName": last_name or "Anonymous"
            }

            # Add email if provided
            if email:
                payload["email"] = email

            print(f"OXIO Create User Request URL: {url}")
            print(f"OXIO Create User Headers (Auth masked): {dict(headers, **{'Authorization': '***'})}")
            print(f"OXIO Create User Payload: {json.dumps(payload, indent=2)}")

            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=30
            )

            print(f"OXIO Create User Response Status: {response.status_code}")
            print(f"OXIO Create User Response Headers: {dict(response.headers)}")

            # Get response text first
            response_text = response.text
            print(f"Raw response body: {response_text}")

            # Check if response is JSON
            content_type = response.headers.get('content-type', '').lower()

            if 'application/json' in content_type:
                try:
                    response_data = response.json() if response.content else {}
                    print(f"OXIO Create User Response Body (parsed): {json.dumps(response_data, indent=2)}")
                except json.JSONDecodeError as json_err:
                    print(f"Failed to parse JSON response: {str(json_err)}")
                    response_data = {
                        'error': 'Invalid JSON response',
                        'json_error': str(json_err),
                        'raw_response': response_text[:1000]
                    }
            else:
                print(f"Non-JSON response received (Content-Type: {content_type})")
                response_data = {
                    'error': 'Non-JSON response',
                    'content_type': content_type,
                    'raw_response': response_text[:1000]
                }

            if response.status_code >= 200 and response.status_code < 300:
                # Get OXIO user ID from response - try different possible field names
                oxio_user_id = response_data.get('endUserId') or response_data.get('id') or response_data.get('userId')
                
                return {
                    'success': True,
                    'status_code': response.status_code,
                    'data': response_data,
                    'message': 'OXIO user created successfully',
                    'oxio_user_id': oxio_user_id,
                    'request_payload': payload,
                    'firebase_uid': firebase_uid
                }
            else:
                error_details = {
                    'success': False,
                    'status_code': response.status_code,
                    'data': response_data,
                    'error': f'OXIO API error: {response.status_code}',
                    'message': response_data.get('message', f'HTTP {response.status_code} error'),
                    'request_payload': payload,
                    'firebase_uid': firebase_uid
                }

                return error_details

        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': 'Request timeout',
                'message': 'OXIO API request timed out after 30 seconds',
                'request_payload': payload,
                'firebase_uid': firebase_uid
            }
        except requests.exceptions.ConnectionError as conn_err:
            return {
                'success': False,
                'error': 'Connection error',
                'message': f'Could not connect to OXIO API: {str(conn_err)}',
                'request_payload': payload,
                'firebase_uid': firebase_uid
            }
        except requests.exceptions.RequestException as req_err:
            return {
                'success': False,
                'error': 'Request error',
                'message': f'Request failed: {str(req_err)}',
                'request_payload': payload,
                'firebase_uid': firebase_uid
            }
        except Exception as e:
            return {
                'success': False,
                'error': 'Unexpected error',
                'message': f'Unexpected error: {str(e)}',
                'request_payload': payload,
                'firebase_uid': firebase_uid
            }

    def get_user_lines(self, oxio_user_id: str) -> Dict[str, Any]:
        """
        Get existing lines for an OXIO user

        Args:
            oxio_user_id: OXIO user ID to check lines for

        Returns:
            API response as dictionary with user's existing lines
        """
        try:
            url = f"{self.base_url}/v3/end-users/{oxio_user_id}/lines"
            headers = self.get_headers()

            print(f"OXIO Get User Lines URL: {url}")
            print(f"OXIO Get User Lines Headers (Auth masked): {dict(headers, **{'Authorization': '***'})}")

            response = requests.get(
                url,
                headers=headers,
                timeout=30
            )

            print(f"OXIO Get User Lines Response Status: {response.status_code}")
            print(f"OXIO Get User Lines Response Headers: {dict(response.headers)}")

            # Get response text first
            response_text = response.text
            print(f"Raw response body: {response_text}")

            # Check if response is JSON
            content_type = response.headers.get('content-type', '').lower()

            if 'application/json' in content_type:
                try:
                    response_data = response.json() if response.content else {}
                    print(f"OXIO Get User Lines Response Body (parsed): {json.dumps(response_data, indent=2)}")
                except json.JSONDecodeError as json_err:
                    print(f"Failed to parse JSON response: {str(json_err)}")
                    response_data = {
                        'error': 'Invalid JSON response',
                        'json_error': str(json_err),
                        'raw_response': response_text[:1000]
                    }
            else:
                print(f"Non-JSON response received (Content-Type: {content_type})")
                response_data = {
                    'error': 'Non-JSON response',
                    'content_type': content_type,
                    'raw_response': response_text[:1000]
                }

            if response.status_code >= 200 and response.status_code < 300:
                return {
                    'success': True,
                    'status_code': response.status_code,
                    'data': response_data,
                    'message': 'User lines retrieved successfully',
                    'oxio_user_id': oxio_user_id
                }
            else:
                return {
                    'success': False,
                    'status_code': response.status_code,
                    'data': response_data,
                    'error': f'OXIO API error: {response.status_code}',
                    'message': response_data.get('message', f'HTTP {response.status_code} error'),
                    'oxio_user_id': oxio_user_id
                }

        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': 'Request timeout',
                'message': 'OXIO API request timed out after 30 seconds',
                'oxio_user_id': oxio_user_id
            }
        except requests.exceptions.ConnectionError as conn_err:
            return {
                'success': False,
                'error': 'Connection error',
                'message': f'Could not connect to OXIO API: {str(conn_err)}',
                'oxio_user_id': oxio_user_id
            }
        except requests.exceptions.RequestException as req_err:
            return {
                'success': False,
                'error': 'Request error',
                'message': f'Request failed: {str(req_err)}',
                'oxio_user_id': oxio_user_id
            }
        except Exception as e:
            return {
                'success': False,
                'error': 'Unexpected error',
                'message': f'Unexpected error: {str(e)}',
                'oxio_user_id': oxio_user_id
            }

    def create_custom_plan(self, user_email, plan_name, duration_seconds, data_limit_kb):
        """Create a custom plan for beta users"""
        if not self.api_key:
            print("OXIO API key not configured - simulating plan creation")
            return {
                'success': True,
                'plan_id': f'sim_demo_plan_{int(time.time())}',
                'profile_id': f'profile_{int(time.time())}',
                'message': 'Demo plan created (simulated)',
                'duration_seconds': duration_seconds,
                'data_limit_kb': data_limit_kb
            }

        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }

            payload = {
                'email': user_email,
                'plan_name': plan_name,
                'duration_seconds': duration_seconds,
                'data_limit_kb': data_limit_kb,
                'auto_activate': True,
                'region': 'global'
            }

            url = f"{self.base_url}/v3/plans/custom"

            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=30
            )

            print(f"OXIO API Response Status: {response.status_code}")
            print(f"OXIO API Response Headers: {dict(response.headers)}")

            # Get response text first
            response_text = response.text
            print(f"Raw response body: {response_text}")

            # Check if response is JSON
            content_type = response.headers.get('content-type', '').lower()

            if 'application/json' in content_type:
                try:
                    response_data = response.json() if response.content else {}
                    print(f"OXIO API Response Body (parsed): {json.dumps(response_data, indent=2)}")
                except json.JSONDecodeError as json_err:
                    print(f"Failed to parse JSON response: {str(json_err)}")
                    print(f"Raw response (first 1000 chars): {response_text[:1000]}...")
                    response_data = {
                        'error': 'Invalid JSON response',
                        'json_error': str(json_err),
                        'raw_response': response_text[:1000]
                    }
            else:
                print(f"Non-JSON response received (Content-Type: {content_type})")
                print(f"Response body (first 1000 chars): {response_text[:1000]}...")
                response_data = {
                    'error': 'Non-JSON response',
                    'content_type': content_type,
                    'raw_response': response_text[:1000]
                }

            if response.status_code in [200, 201]:
                result = response_data
                return {
                    'success': True,
                    'plan_id': result.get('plan_id'),
                    'profile_id': result.get('profile_id'),
                    'message': 'Custom plan created successfully',
                    'response': result
                }
            else:
                return {
                    'success': False,
                    'error': f'OXIO API error: {response.status_code}',
                    'details': response_data,
                    'raw_response': response_text
                }

        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': 'Request timeout',
                'message': 'OXIO API request timed out after 30 seconds',
                'request_payload': payload
            }
        except requests.exceptions.ConnectionError as conn_err:
            return {
                'success': False,
                'error': 'Connection error',
                'message': f'Could not connect to OXIO API: {str(conn_err)}',
                'request_payload': payload
            }
        except requests.exceptions.RequestException as req_err:
            return {
                'success': False,
                'error': 'Request error',
                'message': f'Request failed: {str(req_err)}',
                'request_payload': payload
            }
        except json.JSONDecodeError as json_err:
            return {
                'success': False,
                'error': 'Invalid JSON response',
                'message': f'OXIO API returned invalid JSON: {str(json_err)}',
                'request_payload': payload
            }
        except Exception as e:
            return {
                'success': False,
                'error': 'Unexpected error',
                'message': f'Unexpected error: {str(e)}',
                'request_payload': payload
            }

    def test_plans_endpoint(self) -> Dict[str, Any]:
        """Test the plans endpoint for health check"""
        try:
            # Use the v3 endpoint for health check
            test_url = f"{self.base_url}/v3"
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
        """Test connection to OXIO API using specific SIM endpoint"""
        try:
            # First verify our credentials are set
            if not self.api_key or not self.auth_token:
                return {
                    'success': False,
                    'message': 'API credentials not configured',
                    'api_key_configured': bool(self.api_key),
                    'auth_token_configured': bool(self.auth_token)
                }

            # Use the specific SIM endpoint for authentication test
            test_url = f"{self.base_url}/v3/sims/8910650420001501340F"
            headers = self.get_headers()

            print(f"Testing OXIO SIM endpoint: {test_url}")
            auth_masked = f'Basic ...{headers["Authorization"][-8:]}' if 'Authorization' in headers else 'None'
            headers_masked = dict(headers, **{'Authorization': auth_masked})
            print(f"Headers (Basic Auth masked): {headers_masked}")

            response = requests.get(test_url, headers=headers, timeout=10)
            print(f"SIM endpoint response status: {response.status_code}")
            print(f"SIM endpoint content-type: {response.headers.get('content-type', 'Unknown')}")

            # Log response for debugging
            response_text = response.text[:500]
            print(f"Response preview: {response_text}...")

            if response.status_code == 200:
                try:
                    response_data = response.json()
                    return {
                        'success': True,
                        'message': 'OXIO SIM endpoint accessible - API connection working',
                        'status_code': response.status_code,
                        'endpoint': test_url,
                        'data': response_data,
                        'api_key_configured': bool(self.api_key),
                        'auth_token_configured': bool(self.auth_token)
                    }
                except json.JSONDecodeError:
                    return {
                        'success': True,
                        'message': 'OXIO SIM endpoint accessible but returned non-JSON',
                        'status_code': response.status_code,
                        'response_preview': response_text,
                        'content_type': response.headers.get('content-type', 'Unknown'),
                        'endpoint': test_url
                    }
            else:
                return {
                    'success': False,
                    'message': f'SIM endpoint returned status {response.status_code}',
                    'status_code': response.status_code,
                    'endpoint': test_url,
                    'response_preview': response_text,
                    'content_type': response.headers.get('content-type', 'Unknown')
                }

        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'message': 'Cannot connect to OXIO SIM endpoint - check network',
                'endpoint': test_url
            }
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'message': 'OXIO SIM endpoint request timed out',
                'endpoint': test_url
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to test OXIO SIM endpoint'
            }

# Create a singleton instance
oxio_service = OXIOService()