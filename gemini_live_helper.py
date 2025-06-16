
import os
import json
import asyncio
import websockets
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

class GeminiLiveHelper:
    def __init__(self):
        self.api_key = os.environ.get('GEMINI_API_KEY')
        self.base_url = "https://generativelanguage.googleapis.com"
        self.live_api_url = "wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1alpha.GenerativeService.BidiGenerateContent"
        
    def create_ephemeral_token(self, uses: int = 1, expire_time_minutes: int = 30) -> Optional[Dict]:
        """Create ephemeral token for Gemini Live API"""
        try:
            expire_time = datetime.now() + timedelta(minutes=expire_time_minutes)
            
            token_config = {
                "config": {
                    "uses": uses,
                    "expireTime": expire_time.isoformat() + "Z",
                    "newSessionExpirationTime": (datetime.now() + timedelta(minutes=1)).isoformat() + "Z"
                },
                "httpOptions": {
                    "apiVersion": "v1alpha"
                }
            }
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                f"{self.base_url}/v1alpha/authTokens:create",
                headers=headers,
                json=token_config
            )
            
            if response.status_code == 200:
                token_data = response.json()
                return {
                    "success": True,
                    "token": token_data.get("authToken"),
                    "expiry": expire_time.isoformat()
                }
            else:
                print(f"Failed to create ephemeral token: {response.status_code} - {response.text}")
                return {"success": False, "error": f"API Error: {response.status_code}"}
                
        except Exception as e:
            print(f"Error creating ephemeral token: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def start_live_session(self, ephemeral_token: str, user_context: Dict) -> Dict:
        """Start a live conversation session with Gemini"""
        try:
            # WebSocket URL with ephemeral token
            ws_url = f"{self.live_api_url}?token={ephemeral_token}"
            
            # System instruction for help desk context
            system_instruction = f"""
You are a helpful customer support assistant for a mobile eSIM service. 
You are currently helping a user in a live conversation session.

User context:
- User ID: {user_context.get('user_id')}
- Current page: {user_context.get('page_url')}
- Session ID: {user_context.get('session_id')}

Provide helpful, conversational assistance focused on:
- eSIM activation and setup
- Mobile data troubleshooting
- Account management
- Billing questions
- Technical support

Be conversational, empathetic, and provide clear step-by-step guidance when needed.
Ask clarifying questions if you need more information to help effectively.
            """
            
            # Initial configuration message
            config_message = {
                "setup": {
                    "model": "models/gemini-2.0-flash-exp",
                    "generation_config": {
                        "response_modalities": ["TEXT"],
                        "speech_config": {
                            "voice_config": {"prebuilt_voice_config": {"voice_name": "Aoede"}}
                        }
                    },
                    "system_instruction": {"parts": [{"text": system_instruction}]},
                    "tools": []
                }
            }
            
            return {
                "success": True,
                "ws_url": ws_url,
                "config": config_message,
                "system_instruction": system_instruction
            }
            
        except Exception as e:
            print(f"Error starting live session: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def handle_live_conversation(self, ws_url: str, config_message: Dict, message_handler=None):
        """Handle live WebSocket conversation"""
        try:
            async with websockets.connect(ws_url) as websocket:
                # Send initial setup
                await websocket.send(json.dumps(config_message))
                
                # Listen for messages
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        
                        if message_handler:
                            await message_handler(data)
                        else:
                            print(f"Received: {data}")
                            
                    except json.JSONDecodeError:
                        print(f"Invalid JSON received: {message}")
                        
        except Exception as e:
            print(f"WebSocket error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_conversation_history(self, session_id: str) -> Dict:
        """Get conversation history for a session"""
        try:
            from main import get_db_connection
            
            with get_db_connection() as conn:
                if conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            SELECT ai_query, ai_response, interaction_timestamp
                            FROM help_interactions 
                            WHERE help_session_id = (
                                SELECT id FROM need_for_help WHERE session_id = %s
                            )
                            AND interaction_type = 'gemini_live'
                            ORDER BY interaction_timestamp ASC
                        """, (session_id,))
                        
                        history = []
                        for row in cur.fetchall():
                            history.append({
                                "query": row[0],
                                "response": row[1],
                                "timestamp": row[2].isoformat() if row[2] else None
                            })
                        
                        return {"success": True, "history": history}
            
            return {"success": False, "error": "Database connection failed"}
            
        except Exception as e:
            print(f"Error getting conversation history: {str(e)}")
            return {"success": False, "error": str(e)}

# Initialize the helper
gemini_live = GeminiLiveHelper()
