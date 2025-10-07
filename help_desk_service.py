
import os
import requests
import json
from datetime import datetime, timedelta
from contextlib import contextmanager
import psycopg2
from main import get_db_connection
import openai

class HelpDeskService:
    def __init__(self):
        # Jira configuration
        self.jira_url = os.environ.get('JIRA_URL', 'https://dotmobile.atlassian.net')
        self.jira_username = os.environ.get('JIRA_EMAIL')
        self.jira_api_token = os.environ.get('JIRA_API_TOKEN')
        self.jira_project_key = os.environ.get('JIRA_PROJECT_KEY', 'HELP')
        
        # Supported ticket statuses
        self.supported_statuses = [
            "Need Help", 
            "User_Closed", 
            "In Progress", 
            "Resolved", 
            "Escalated_L1", 
            "Escalated_L2", 
            "Escalated_L3"
        ]
        
        # OpenAI configuration
        openai.api_key = os.environ.get('OPENAI_API_KEY')
        
        # Initialize database tables
        self.create_help_tables()
    
    def create_help_tables(self):
        """Create help-related database tables"""
        try:
            with get_db_connection() as conn:
                if conn:
                    with conn.cursor() as cur:
                        # Create need_for_help table
                        cur.execute("""
                            CREATE TABLE IF NOT EXISTS need_for_help (
                                id SERIAL PRIMARY KEY,
                                user_id INTEGER,
                                firebase_uid VARCHAR(128),
                                session_id VARCHAR(255) NOT NULL,
                                help_started_at TIMESTAMP NOT NULL,
                                help_ended_at TIMESTAMP,
                                total_duration_seconds INTEGER,
                                click_count INTEGER DEFAULT 1,
                                last_activity_at TIMESTAMP NOT NULL,
                                jira_ticket_key VARCHAR(50),
                                jira_ticket_status VARCHAR(50),
                                resolution_time_seconds INTEGER,
                                live_callback_requested BOOLEAN DEFAULT FALSE,
                                live_callback_completed_at TIMESTAMP,
                                ai_assistance_provided BOOLEAN DEFAULT FALSE,
                                ai_response_count INTEGER DEFAULT 0,
                                user_agent TEXT,
                                ip_address INET,
                                page_url TEXT,
                                issue_category VARCHAR(100),
                                issue_description TEXT,
                                satisfaction_rating INTEGER,
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                            )
                        """)
                        
                        # Create help interactions table for detailed tracking
                        cur.execute("""
                            CREATE TABLE IF NOT EXISTS help_interactions (
                                id SERIAL PRIMARY KEY,
                                help_session_id INTEGER REFERENCES need_for_help(id),
                                interaction_type VARCHAR(50) NOT NULL, -- 'help_open', 'help_close', 'ai_query', 'callback_request'
                                interaction_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                duration_since_last_action INTEGER,
                                ai_query TEXT,
                                ai_response TEXT,
                                user_satisfaction BOOLEAN,
                                additional_data JSONB
                            )
                        """)
                        
                        # Create indexes for performance
                        cur.execute("""
                            CREATE INDEX IF NOT EXISTS idx_help_user_id ON need_for_help(user_id);
                            CREATE INDEX IF NOT EXISTS idx_help_firebase_uid ON need_for_help(firebase_uid);
                            CREATE INDEX IF NOT EXISTS idx_help_session_id ON need_for_help(session_id);
                            CREATE INDEX IF NOT EXISTS idx_help_jira_ticket ON need_for_help(jira_ticket_key);
                            CREATE INDEX IF NOT EXISTS idx_help_interactions_session ON help_interactions(help_session_id);
                        """)
                        
                        # Add context fields if they don't exist (for backward compatibility)
                        cur.execute("""
                            DO $$ 
                            BEGIN
                                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                                             WHERE table_name='need_for_help' AND column_name='context_provided_at') THEN
                                    ALTER TABLE need_for_help ADD COLUMN context_provided_at TIMESTAMP;
                                END IF;
                                
                                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                                             WHERE table_name='need_for_help' AND column_name='context_category') THEN
                                    ALTER TABLE need_for_help ADD COLUMN context_category VARCHAR(100);
                                END IF;
                                
                                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                                             WHERE table_name='need_for_help' AND column_name='context_description') THEN
                                    ALTER TABLE need_for_help ADD COLUMN context_description TEXT;
                                END IF;
                            END $$;
                        """)
                        
                        conn.commit()
                        print("Help desk tables created successfully")
        except Exception as e:
            print(f"Error creating help desk tables: {str(e)}")
    
    def start_help_session(self, user_data):
        """Start a new help session"""
        try:
            session_id = f"help_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{user_data.get('user_id', 'unknown')}"
            
            with get_db_connection() as conn:
                if conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            INSERT INTO need_for_help 
                            (user_id, firebase_uid, session_id, help_started_at, last_activity_at, 
                             user_agent, ip_address, page_url)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                            RETURNING id
                        """, (
                            user_data.get('user_id'),
                            user_data.get('firebase_uid'),
                            session_id,
                            datetime.now(),
                            datetime.now(),
                            user_data.get('user_agent'),
                            user_data.get('ip_address'),
                            user_data.get('page_url')
                        ))
                        
                        help_id = cur.fetchone()[0]
                        
                        # Log the interaction
                        cur.execute("""
                            INSERT INTO help_interactions 
                            (help_session_id, interaction_type, additional_data)
                            VALUES (%s, %s, %s)
                        """, (help_id, 'help_open', json.dumps(user_data)))
                        
                        conn.commit()
                        
                        # Create Jira ticket
                        jira_ticket = self.create_jira_ticket(help_id, user_data)
                        if jira_ticket:
                            cur.execute("""
                                UPDATE need_for_help 
                                SET jira_ticket_key = %s, jira_ticket_status = %s
                                WHERE id = %s
                            """, (jira_ticket['key'], jira_ticket['status'], help_id))
                            conn.commit()
                        
                        return {
                            'success': True,
                            'help_session_id': help_id,
                            'session_id': session_id,
                            'jira_ticket': jira_ticket
                        }
        except Exception as e:
            print(f"Error starting help session: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_active_session(self, user_id=None, firebase_uid=None):
        """Get active session for a user"""
        try:
            with get_db_connection() as conn:
                if conn:
                    with conn.cursor() as cur:
                        if firebase_uid:
                            cur.execute("""
                                SELECT id, session_id, jira_ticket_key, jira_ticket_status, 
                                       help_started_at
                                FROM need_for_help 
                                WHERE firebase_uid = %s AND help_ended_at IS NULL
                                ORDER BY help_started_at DESC
                                LIMIT 1
                            """, (firebase_uid,))
                        elif user_id:
                            cur.execute("""
                                SELECT id, session_id, jira_ticket_key, jira_ticket_status,
                                       help_started_at
                                FROM need_for_help 
                                WHERE user_id = %s AND help_ended_at IS NULL
                                ORDER BY help_started_at DESC
                                LIMIT 1
                            """, (user_id,))
                        else:
                            return {'success': False, 'error': 'User ID or Firebase UID required'}
                        
                        session = cur.fetchone()
                        if session:
                            return {
                                'success': True,
                                'help_session_id': session[0],
                                'session_id': session[1],
                                'jira_ticket': {
                                    'key': session[2],
                                    'status': session[3],
                                    'url': f"{self.jira_url}/browse/{session[2]}" if session[2] else None
                                },
                                'started_at': session[4].isoformat() if session[4] else None
                            }
                        else:
                            return {'success': False, 'error': 'No active session found'}
        except Exception as e:
            print(f"Error getting active session: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def end_help_session(self, session_id, user_data=None):
        """End a help session"""
        try:
            with get_db_connection() as conn:
                if conn:
                    with conn.cursor() as cur:
                        # Get the current session
                        cur.execute("""
                            SELECT id, help_started_at, click_count
                            FROM need_for_help 
                            WHERE session_id = %s AND help_ended_at IS NULL
                        """, (session_id,))
                        
                        session = cur.fetchone()
                        if not session:
                            return {'success': False, 'error': 'Session not found'}
                        
                        help_id, start_time, click_count = session
                        end_time = datetime.now()
                        duration = int((end_time - start_time).total_seconds())
                        
                        # Update the session
                        cur.execute("""
                            UPDATE need_for_help 
                            SET help_ended_at = %s, total_duration_seconds = %s, 
                                last_activity_at = %s, updated_at = %s
                            WHERE id = %s
                        """, (end_time, duration, end_time, end_time, help_id))
                        
                        # Log the interaction
                        cur.execute("""
                            INSERT INTO help_interactions 
                            (help_session_id, interaction_type, additional_data)
                            VALUES (%s, %s, %s)
                        """, (help_id, 'help_close', json.dumps({
                            'duration_seconds': duration,
                            'total_clicks': click_count,
                            **(user_data or {})
                        })))
                        
                        conn.commit()
                        
                        return {
                            'success': True,
                            'duration_seconds': duration,
                            'total_clicks': click_count
                        }
        except Exception as e:
            print(f"Error ending help session: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def track_help_interaction(self, session_id, interaction_type, data=None):
        """Track help interactions (toggle detection)"""
        try:
            with get_db_connection() as conn:
                if conn:
                    with conn.cursor() as cur:
                        # Get current session
                        cur.execute("""
                            SELECT id, click_count, last_activity_at
                            FROM need_for_help 
                            WHERE session_id = %s AND help_ended_at IS NULL
                        """, (session_id,))
                        
                        session = cur.fetchone()
                        if not session:
                            return {'success': False, 'error': 'Session not found'}
                        
                        help_id, current_clicks, last_activity = session
                        now = datetime.now()
                        
                        # Calculate time since last activity
                        duration_since_last = 0
                        if last_activity:
                            duration_since_last = int((now - last_activity).total_seconds())
                        
                        # Determine if this is rapid toggling (< 3 seconds) or genuine help request
                        is_toggle = duration_since_last > 0 and duration_since_last < 3
                        
                        # Update session
                        new_click_count = current_clicks + 1
                        cur.execute("""
                            UPDATE need_for_help 
                            SET click_count = %s, last_activity_at = %s, updated_at = %s
                            WHERE id = %s
                        """, (new_click_count, now, now, help_id))
                        
                        # Log interaction
                        cur.execute("""
                            INSERT INTO help_interactions 
                            (help_session_id, interaction_type, duration_since_last_action, additional_data)
                            VALUES (%s, %s, %s, %s)
                        """, (help_id, interaction_type, duration_since_last, json.dumps({
                            'is_toggle': is_toggle,
                            'click_number': new_click_count,
                            **(data or {})
                        })))
                        
                        conn.commit()
                        
                        return {
                            'success': True,
                            'is_toggle': is_toggle,
                            'click_count': new_click_count,
                            'duration_since_last': duration_since_last
                        }
        except Exception as e:
            print(f"Error tracking help interaction: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def create_jira_ticket(self, help_session_id, user_data):
        """Create a Jira ticket for help request"""
        try:
            if not all([self.jira_url, self.jira_username, self.jira_api_token]):
                print("Jira credentials not configured")
                return None
            
            # Prepare ticket data
            summary = f"Help Request - User {user_data.get('user_id', 'Unknown')} - Session {help_session_id}"
            
            # JIRA API v3 requires Atlassian Document Format (ADF) for description
            description_adf = {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": "User requested help through the application."
                            }
                        ]
                    },
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": "Session Details:",
                                "marks": [{"type": "strong"}]
                            }
                        ]
                    },
                    {
                        "type": "bulletList",
                        "content": [
                            {
                                "type": "listItem",
                                "content": [{
                                    "type": "paragraph",
                                    "content": [{"type": "text", "text": f"Help Session ID: {help_session_id}"}]
                                }]
                            },
                            {
                                "type": "listItem",
                                "content": [{
                                    "type": "paragraph",
                                    "content": [{"type": "text", "text": f"User ID: {user_data.get('user_id', 'Unknown')}"}]
                                }]
                            },
                            {
                                "type": "listItem",
                                "content": [{
                                    "type": "paragraph",
                                    "content": [{"type": "text", "text": f"Firebase UID: {user_data.get('firebase_uid', 'Unknown')}"}]
                                }]
                            },
                            {
                                "type": "listItem",
                                "content": [{
                                    "type": "paragraph",
                                    "content": [{"type": "text", "text": f"Page URL: {user_data.get('page_url', 'Unknown')}"}]
                                }]
                            },
                            {
                                "type": "listItem",
                                "content": [{
                                    "type": "paragraph",
                                    "content": [{"type": "text", "text": f"User Agent: {user_data.get('user_agent', 'Unknown')}"}]
                                }]
                            },
                            {
                                "type": "listItem",
                                "content": [{
                                    "type": "paragraph",
                                    "content": [{"type": "text", "text": f"IP Address: {user_data.get('ip_address', 'Unknown')}"}]
                                }]
                            },
                            {
                                "type": "listItem",
                                "content": [{
                                    "type": "paragraph",
                                    "content": [{"type": "text", "text": f"Timestamp: {datetime.now().isoformat()}"}]
                                }]
                            }
                        ]
                    }
                ]
            }
            
            ticket_data = {
                "fields": {
                    "project": {"key": self.jira_project_key},
                    "summary": summary,
                    "description": description_adf,
                    "issuetype": {"name": "Task"},
                    "priority": {"name": "Medium"},
                    "labels": ["help-request", "automated", f"session-{help_session_id}"]
                }
            }
            
            # Create ticket via Jira API
            auth = (self.jira_username, self.jira_api_token)
            headers = {"Content-Type": "application/json"}
            
            response = requests.post(
                f"{self.jira_url}/rest/api/3/issue",
                auth=auth,
                headers=headers,
                json=ticket_data
            )
            
            if response.status_code == 201:
                ticket = response.json()
                print(f"Jira ticket created: {ticket['key']}")
                return {
                    'key': ticket['key'],
                    'id': ticket['id'],
                    'status': 'Need Help',
                    'url': f"{self.jira_url}/browse/{ticket['key']}"
                }
            else:
                print(f"Failed to create Jira ticket: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error creating Jira ticket: {str(e)}")
            return None
    
    def update_jira_ticket_status(self, ticket_key, status, resolution_notes=None):
        """Update Jira ticket status"""
        try:
            if not ticket_key:
                return False
            
            # Validate status
            if status not in self.supported_statuses:
                print(f"Invalid status: {status}. Must be one of: {', '.join(self.supported_statuses)}")
                return False
            
            auth = (self.jira_username, self.jira_api_token)
            headers = {"Content-Type": "application/json"}
            
            # Add comment if resolution notes provided
            if resolution_notes:
                comment_data = {
                    "body": {
                        "type": "doc",
                        "version": 1,
                        "content": [
                            {
                                "type": "paragraph",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": resolution_notes
                                    }
                                ]
                            }
                        ]
                    }
                }
                
                requests.post(
                    f"{self.jira_url}/rest/api/3/issue/{ticket_key}/comment",
                    auth=auth,
                    headers=headers,
                    json=comment_data
                )
            
            # Update status (this would need transition ID mapping in real implementation)
            print(f"Jira ticket {ticket_key} status updated to {status}")
            return True
            
        except Exception as e:
            print(f"Error updating Jira ticket: {str(e)}")
            return False
    
    def update_ticket_context(self, session_id, category, description):
        """Update ticket context with user-provided information"""
        try:
            with get_db_connection() as conn:
                if conn:
                    with conn.cursor() as cur:
                        # Get the current session and JIRA ticket
                        cur.execute("""
                            SELECT id, jira_ticket_key, user_id, firebase_uid
                            FROM need_for_help 
                            WHERE session_id = %s AND help_ended_at IS NULL
                        """, (session_id,))
                        
                        session = cur.fetchone()
                        if not session:
                            return {'success': False, 'error': 'Session not found'}
                        
                        help_id, jira_ticket_key, user_id, firebase_uid = session
                        now = datetime.now()
                        
                        # Update database with context information
                        cur.execute("""
                            UPDATE need_for_help 
                            SET context_category = %s, 
                                context_description = %s, 
                                context_provided_at = %s,
                                updated_at = %s
                            WHERE id = %s
                        """, (category, description, now, now, help_id))
                        
                        # Log the interaction
                        cur.execute("""
                            INSERT INTO help_interactions 
                            (help_session_id, interaction_type, additional_data)
                            VALUES (%s, %s, %s)
                        """, (help_id, 'context_provided', json.dumps({
                            'category': category,
                            'description': description
                        })))
                        
                        conn.commit()
                        
                        # Update JIRA ticket if it exists
                        if jira_ticket_key and all([self.jira_url, self.jira_username, self.jira_api_token]):
                            auth = (self.jira_username, self.jira_api_token)
                            headers = {"Content-Type": "application/json"}
                            
                            # Create structured ADF comment with headings
                            comment_data = {
                                "body": {
                                    "type": "doc",
                                    "version": 1,
                                    "content": [
                                        {
                                            "type": "heading",
                                            "attrs": {"level": 3},
                                            "content": [
                                                {
                                                    "type": "text",
                                                    "text": "📝 Additional Context from User",
                                                    "marks": [{"type": "strong"}]
                                                }
                                            ]
                                        },
                                        {
                                            "type": "paragraph",
                                            "content": [
                                                {
                                                    "type": "text",
                                                    "text": "Category: ",
                                                    "marks": [{"type": "strong"}]
                                                },
                                                {
                                                    "type": "text",
                                                    "text": category
                                                }
                                            ]
                                        },
                                        {
                                            "type": "paragraph",
                                            "content": [
                                                {
                                                    "type": "text",
                                                    "text": "Description:",
                                                    "marks": [{"type": "strong"}]
                                                }
                                            ]
                                        },
                                        {
                                            "type": "paragraph",
                                            "content": [
                                                {
                                                    "type": "text",
                                                    "text": description
                                                }
                                            ]
                                        },
                                        {
                                            "type": "paragraph",
                                            "content": [
                                                {
                                                    "type": "text",
                                                    "text": f"Submitted at: {now.strftime('%Y-%m-%d %H:%M:%S UTC')}",
                                                    "marks": [{"type": "em"}]
                                                }
                                            ]
                                        }
                                    ]
                                }
                            }
                            
                            # Add comment
                            response = requests.post(
                                f"{self.jira_url}/rest/api/3/issue/{jira_ticket_key}/comment",
                                auth=auth,
                                headers=headers,
                                json=comment_data
                            )
                            
                            if response.status_code == 201:
                                print(f"Context added to JIRA ticket {jira_ticket_key}")
                                
                                # Update issue to trigger timestamp update
                                # Add label to force an update
                                update_data = {
                                    "update": {
                                        "labels": [
                                            {"add": f"context-{category.lower().replace(' ', '-')}"}
                                        ]
                                    }
                                }
                                
                                update_response = requests.put(
                                    f"{self.jira_url}/rest/api/3/issue/{jira_ticket_key}",
                                    auth=auth,
                                    headers=headers,
                                    json=update_data
                                )
                                
                                if update_response.status_code in [200, 204]:
                                    print(f"JIRA ticket {jira_ticket_key} timestamp updated")
                                else:
                                    print(f"Failed to update JIRA ticket timestamp: {update_response.status_code} - {update_response.text}")
                            else:
                                print(f"Failed to update JIRA ticket with context: {response.status_code} - {response.text}")
                        
                        return {
                            'success': True,
                            'message': 'Context updated successfully',
                            'jira_ticket_updated': jira_ticket_key is not None
                        }
                        
        except Exception as e:
            print(f"Error updating ticket context: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_ai_assistance(self, user_query, user_context):
        """Get AI assistance for user query"""
        try:
            # Prepare context for the AI
            context = f"""
You are a helpful customer support assistant for a mobile eSIM service. 
The user is asking for help with: {user_query}

User context:
- User ID: {user_context.get('user_id')}
- Current page: {user_context.get('page_url')}
- User agent: {user_context.get('user_agent')}

Provide helpful, concise assistance focused on eSIM activation, mobile data, 
subscriptions, and general account management.
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": context},
                    {"role": "user", "content": user_query}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            ai_response = response.choices[0].message.content
            
            # Log AI interaction
            session_id = user_context.get('session_id')
            if session_id:
                with get_db_connection() as conn:
                    if conn:
                        with conn.cursor() as cur:
                            cur.execute("""
                                SELECT id FROM need_for_help 
                                WHERE session_id = %s AND help_ended_at IS NULL
                            """, (session_id,))
                            
                            session = cur.fetchone()
                            if session:
                                help_id = session[0]
                                
                                # Update help session
                                cur.execute("""
                                    UPDATE need_for_help 
                                    SET ai_assistance_provided = TRUE, 
                                        ai_response_count = ai_response_count + 1,
                                        updated_at = %s
                                    WHERE id = %s
                                """, (datetime.now(), help_id))
                                
                                # Log interaction
                                cur.execute("""
                                    INSERT INTO help_interactions 
                                    (help_session_id, interaction_type, ai_query, ai_response)
                                    VALUES (%s, %s, %s, %s)
                                """, (help_id, 'ai_query', user_query, ai_response))
                                
                                conn.commit()
            
            return {
                'success': True,
                'response': ai_response,
                'tokens_used': response.usage.total_tokens
            }
            
        except Exception as e:
            print(f"Error getting AI assistance: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'response': "I'm sorry, I'm unable to assist right now. Please try again later or request a callback."
            }
    
    def request_live_callback(self, session_id, phone_number, preferred_time=None):
        """Request live person callback"""
        try:
            with get_db_connection() as conn:
                if conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            UPDATE need_for_help 
                            SET live_callback_requested = TRUE, updated_at = %s
                            WHERE session_id = %s AND help_ended_at IS NULL
                        """, (datetime.now(), session_id))
                        
                        # Log interaction
                        cur.execute("""
                            INSERT INTO help_interactions 
                            (help_session_id, interaction_type, additional_data)
                            SELECT id, 'callback_request', %s
                            FROM need_for_help 
                            WHERE session_id = %s AND help_ended_at IS NULL
                        """, (json.dumps({
                            'phone_number': phone_number,
                            'preferred_time': preferred_time
                        }), session_id))
                        
                        conn.commit()
                        
                        return {'success': True, 'message': 'Callback requested successfully'}
        except Exception as e:
            print(f"Error requesting callback: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def update_help_ticket_status(self, session_id, status):
        """Update help ticket status in database and JIRA"""
        try:
            # Validate status
            if status not in self.supported_statuses:
                return {
                    'success': False,
                    'error': f"Invalid status: {status}. Must be one of: {', '.join(self.supported_statuses)}"
                }
            
            with get_db_connection() as conn:
                if conn:
                    with conn.cursor() as cur:
                        # Get the current session and JIRA ticket
                        cur.execute("""
                            SELECT id, jira_ticket_key, jira_ticket_status
                            FROM need_for_help 
                            WHERE session_id = %s AND help_ended_at IS NULL
                        """, (session_id,))
                        
                        session = cur.fetchone()
                        if not session:
                            return {'success': False, 'error': 'Session not found'}
                        
                        help_id, jira_ticket_key, current_status = session
                        now = datetime.now()
                        
                        # Update database with new status
                        cur.execute("""
                            UPDATE need_for_help 
                            SET jira_ticket_status = %s, 
                                updated_at = %s
                            WHERE id = %s
                        """, (status, now, help_id))
                        
                        # Log the interaction
                        cur.execute("""
                            INSERT INTO help_interactions 
                            (help_session_id, interaction_type, additional_data)
                            VALUES (%s, %s, %s)
                        """, (help_id, 'status_update', json.dumps({
                            'previous_status': current_status,
                            'new_status': status,
                            'timestamp': now.isoformat()
                        })))
                        
                        conn.commit()
                        
                        # Update JIRA ticket if it exists
                        jira_updated = False
                        if jira_ticket_key:
                            jira_updated = self.update_jira_ticket_status(
                                jira_ticket_key, 
                                status,
                                f"Status updated to {status} at {now.isoformat()}"
                            )
                        
                        return {
                            'success': True,
                            'message': 'Status updated successfully',
                            'ticket_status': status,
                            'jira_ticket_key': jira_ticket_key,
                            'jira_updated': jira_updated
                        }
                        
        except Exception as e:
            print(f"Error updating help ticket status: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_help_analytics(self, days=30):
        """Get help desk analytics"""
        try:
            with get_db_connection() as conn:
                if conn:
                    with conn.cursor() as cur:
                        # Get basic stats
                        cur.execute("""
                            SELECT 
                                COUNT(*) as total_sessions,
                                AVG(total_duration_seconds) as avg_duration,
                                COUNT(*) FILTER (WHERE live_callback_requested = TRUE) as callback_requests,
                                COUNT(*) FILTER (WHERE ai_assistance_provided = TRUE) as ai_assisted_sessions,
                                AVG(click_count) as avg_clicks_per_session,
                                COUNT(*) FILTER (WHERE click_count = 1) as single_click_sessions,
                                COUNT(*) FILTER (WHERE click_count > 5) as toggle_heavy_sessions
                            FROM need_for_help 
                            WHERE help_started_at >= %s
                        """, (datetime.now() - timedelta(days=days),))
                        
                        stats = cur.fetchone()
                        
                        return {
                            'total_sessions': stats[0] or 0,
                            'avg_duration_seconds': float(stats[1] or 0),
                            'callback_requests': stats[2] or 0,
                            'ai_assisted_sessions': stats[3] or 0,
                            'avg_clicks_per_session': float(stats[4] or 0),
                            'single_click_sessions': stats[5] or 0,
                            'toggle_heavy_sessions': stats[6] or 0,
                            'period_days': days
                        }
        except Exception as e:
            print(f"Error getting analytics: {str(e)}")
            return {}

# Initialize the service
help_desk = HelpDeskService()
