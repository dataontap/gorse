
from flask import request, jsonify
from help_desk_service import help_desk
from main import app
import uuid

@app.route('/api/help/start', methods=['POST'])
def start_help_session():
    """Start a new help session"""
    try:
        data = request.get_json() or {}
        
        user_data = {
            'user_id': data.get('userId'),
            'firebase_uid': data.get('firebaseUid'),
            'user_agent': request.headers.get('User-Agent'),
            'ip_address': request.remote_addr,
            'page_url': data.get('pageUrl', request.referrer)
        }
        
        result = help_desk.start_help_session(user_data)
        
        if result['success']:
            return jsonify({
                'status': 'success',
                'session_id': result['session_id'],
                'help_session_id': result['help_session_id'],
                'jira_ticket': result.get('jira_ticket'),
                'message': 'Help session started successfully'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': result.get('error', 'Failed to start help session')
            }), 500
            
    except Exception as e:
        return jsonify({
            'status': 'error', 
            'message': str(e)
        }), 500

@app.route('/api/help/end', methods=['POST'])
def end_help_session():
    """End a help session"""
    try:
        data = request.get_json() or {}
        session_id = data.get('sessionId')
        
        if not session_id:
            return jsonify({'status': 'error', 'message': 'Session ID required'}), 400
        
        result = help_desk.end_help_session(session_id, data)
        
        if result['success']:
            return jsonify({
                'status': 'success',
                'duration_seconds': result['duration_seconds'],
                'total_clicks': result['total_clicks'],
                'message': 'Help session ended successfully'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': result.get('error', 'Failed to end help session')
            }), 500
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/help/interact', methods=['POST'])
def track_help_interaction():
    """Track help interactions"""
    try:
        data = request.get_json() or {}
        session_id = data.get('sessionId')
        interaction_type = data.get('type', 'help_toggle')
        
        if not session_id:
            return jsonify({'status': 'error', 'message': 'Session ID required'}), 400
        
        result = help_desk.track_help_interaction(session_id, interaction_type, data)
        
        if result['success']:
            return jsonify({
                'status': 'success',
                'is_toggle': result['is_toggle'],
                'click_count': result['click_count'],
                'duration_since_last': result['duration_since_last']
            })
        else:
            return jsonify({
                'status': 'error',
                'message': result.get('error', 'Failed to track interaction')
            }), 500
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/help/ai-assist', methods=['POST'])
def get_ai_assistance():
    """Get AI assistance"""
    try:
        data = request.get_json() or {}
        query = data.get('query')
        session_id = data.get('sessionId')
        
        if not query:
            return jsonify({'status': 'error', 'message': 'Query required'}), 400
        
        user_context = {
            'session_id': session_id,
            'user_id': data.get('userId'),
            'firebase_uid': data.get('firebaseUid'),
            'page_url': data.get('pageUrl'),
            'user_agent': request.headers.get('User-Agent')
        }
        
        result = help_desk.get_ai_assistance(query, user_context)
        
        return jsonify({
            'status': 'success' if result['success'] else 'error',
            'response': result['response'],
            'tokens_used': result.get('tokens_used'),
            'error': result.get('error')
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/help/request-callback', methods=['POST'])
def request_callback():
    """Request live person callback"""
    try:
        data = request.get_json() or {}
        session_id = data.get('sessionId')
        phone_number = data.get('phoneNumber')
        preferred_time = data.get('preferredTime')
        
        if not session_id or not phone_number:
            return jsonify({
                'status': 'error', 
                'message': 'Session ID and phone number required'
            }), 400
        
        result = help_desk.request_live_callback(session_id, phone_number, preferred_time)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/help/gemini-token', methods=['POST'])
def create_gemini_token():
    """Create ephemeral token for Gemini Live"""
    try:
        from gemini_live_helper import gemini_live
        
        data = request.get_json() or {}
        session_id = data.get('sessionId')
        
        if not session_id:
            return jsonify({'status': 'error', 'message': 'Session ID required'}), 400
        
        # Create ephemeral token
        token_result = gemini_live.create_ephemeral_token(
            uses=10,  # Allow multiple uses in the session
            expire_time_minutes=60  # 1 hour expiry
        )
        
        if token_result['success']:
            return jsonify({
                'status': 'success',
                'token': token_result['token'],
                'expiry': token_result['expiry']
            })
        else:
            return jsonify({
                'status': 'error',
                'message': token_result.get('error', 'Failed to create token')
            }), 500
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/help/gemini-live-start', methods=['POST'])
def start_gemini_live():
    """Start Gemini Live session"""
    try:
        from gemini_live_helper import gemini_live
        
        data = request.get_json() or {}
        session_id = data.get('sessionId')
        ephemeral_token = data.get('ephemeralToken')
        
        if not session_id or not ephemeral_token:
            return jsonify({
                'status': 'error', 
                'message': 'Session ID and ephemeral token required'
            }), 400
        
        user_context = {
            'session_id': session_id,
            'user_id': data.get('userId'),
            'firebase_uid': data.get('firebaseUid'),
            'page_url': data.get('pageUrl'),
            'user_agent': request.headers.get('User-Agent')
        }
        
        # Start live session
        session_result = await gemini_live.start_live_session(ephemeral_token, user_context)
        
        if session_result['success']:
            # Log the start of live session
            help_desk.track_help_interaction(session_id, 'gemini_live_start', {
                'ephemeral_token_created': True,
                'live_session_started': True
            })
            
            return jsonify({
                'status': 'success',
                'ws_url': session_result['ws_url'],
                'config': session_result['config']
            })
        else:
            return jsonify({
                'status': 'error',
                'message': session_result.get('error', 'Failed to start live session')
            }), 500
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/help/gemini-conversation', methods=['GET'])
def get_gemini_conversation():
    """Get Gemini conversation history"""
    try:
        from gemini_live_helper import gemini_live
        
        session_id = request.args.get('sessionId')
        
        if not session_id:
            return jsonify({'status': 'error', 'message': 'Session ID required'}), 400
        
        history_result = gemini_live.get_conversation_history(session_id)
        
        return jsonify({
            'status': 'success' if history_result['success'] else 'error',
            'history': history_result.get('history', []),
            'message': history_result.get('error')
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/help/analytics', methods=['GET'])
def get_help_analytics():
    """Get help desk analytics"""
    try:
        days = int(request.args.get('days', 30))
        analytics = help_desk.get_help_analytics(days)
        
        return jsonify({
            'status': 'success',
            'analytics': analytics
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/help/sessions', methods=['GET'])
def get_help_sessions():
    """Get help sessions for admin dashboard"""
    try:
        from main import get_db_connection
        
        with get_db_connection() as conn:
            if conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT 
                            h.id, h.session_id, h.user_id, h.firebase_uid,
                            h.help_started_at, h.help_ended_at, h.total_duration_seconds,
                            h.click_count, h.jira_ticket_key, h.jira_ticket_status,
                            h.live_callback_requested, h.ai_assistance_provided,
                            h.ai_response_count, h.page_url, h.issue_category
                        FROM need_for_help h
                        ORDER BY h.help_started_at DESC
                        LIMIT 100
                    """)
                    
                    sessions = []
                    for row in cur.fetchall():
                        sessions.append({
                            'id': row[0],
                            'session_id': row[1],
                            'user_id': row[2],
                            'firebase_uid': row[3],
                            'started_at': row[4].isoformat() if row[4] else None,
                            'ended_at': row[5].isoformat() if row[5] else None,
                            'duration_seconds': row[6],
                            'click_count': row[7],
                            'jira_ticket_key': row[8],
                            'jira_ticket_status': row[9],
                            'callback_requested': row[10],
                            'ai_assisted': row[11],
                            'ai_response_count': row[12],
                            'page_url': row[13],
                            'issue_category': row[14]
                        })
                    
                    return jsonify({
                        'status': 'success',
                        'sessions': sessions
                    })
        
        return jsonify({
            'status': 'error',
            'message': 'Database connection error'
        }), 500
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
