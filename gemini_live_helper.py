import os
import json
import time
import uuid
from datetime import datetime, timedelta

class GeminiLiveHelper:
    def __init__(self):
        self.api_key = os.environ.get('GEMINI_API_KEY')
        self.active_sessions = {}

    def create_ephemeral_token(self, uses=10, expire_time_minutes=60):
        """Create an ephemeral token for Gemini Live"""
        try:
            if not self.api_key:
                return {
                    'success': False,
                    'error': 'Gemini API key not configured'
                }

            # Generate a unique token
            token = f"gemini_live_{uuid.uuid4().hex}_{int(time.time())}"
            expiry = datetime.now() + timedelta(minutes=expire_time_minutes)

            return {
                'success': True,
                'token': token,
                'expiry': expiry.isoformat(),
                'uses_remaining': uses
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def start_live_session(self, ephemeral_token, user_context):
        """Start a Gemini Live session"""
        try:
            session_id = user_context.get('session_id')

            # Create mock WebSocket URL and config for now
            ws_url = f"wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1alpha.GenerativeService.BidiGenerateContent"

            config = {
                "setup": {
                    "model": "models/gemini-2.0-flash-exp",
                    "generation_config": {
                        "response_modalities": ["TEXT"],
                        "speech_config": {
                            "voice_config": {
                                "prebuilt_voice_config": {
                                    "voice_name": "Puck"
                                }
                            }
                        }
                    },
                    "system_instruction": {
                        "parts": [{
                            "text": "You are a helpful customer support assistant for a mobile eSIM service. Provide helpful, concise assistance focused on eSIM activation, mobile data, subscriptions, and general account management."
                        }]
                    },
                    "tools": []
                }
            }

            # Store session info
            self.active_sessions[session_id] = {
                'token': ephemeral_token,
                'started_at': datetime.now(),
                'user_context': user_context,
                'conversation_history': []
            }

            return {
                'success': True,
                'ws_url': ws_url,
                'config': config,
                'session_id': session_id
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def get_conversation_history(self, session_id):
        """Get conversation history for a session"""
        try:
            if session_id in self.active_sessions:
                return {
                    'success': True,
                    'history': self.active_sessions[session_id]['conversation_history']
                }
            else:
                return {
                    'success': False,
                    'error': 'Session not found'
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

# Initialize the service
gemini_live = GeminiLiveHelper()