"""
Authentication helpers for secure API endpoints
"""

import os
import functools
from flask import request, jsonify
from contextlib import contextmanager

def get_db_connection():
    """Import and return database connection context"""
    # Import here to avoid circular imports
    from main import get_db_connection as get_conn
    return get_conn()

def verify_admin_token(token: str) -> bool:
    """Verify admin token against environment variable"""
    # Only accept dedicated admin token for security
    admin_token = os.environ.get('ADMIN_TOKEN')
    if admin_token and token == admin_token:
        return True
        
    return False

def verify_firebase_uid(firebase_uid: str) -> bool:
    """Verify Firebase UID exists in database"""
    if not firebase_uid:
        return False
    
    try:
        with get_db_connection() as conn:
            if conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT id FROM users WHERE firebase_uid = %s", (firebase_uid,))
                    return cur.fetchone() is not None
    except Exception as e:
        print(f"Error verifying Firebase UID: {str(e)}")
        return False
    
    return False

def require_auth(f):
    """Decorator to require authentication for endpoints"""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        # Check for admin token first
        admin_token = request.headers.get('X-Admin-Token')
        if admin_token and verify_admin_token(admin_token):
            return f(*args, **kwargs)
        
        # Check for Firebase authentication
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            firebase_uid = auth_header[7:]  # Remove 'Bearer ' prefix
            if verify_firebase_uid(firebase_uid):
                return f(*args, **kwargs)
        
        # Check for Firebase UID in request body (for backward compatibility)
        if request.is_json:
            data = request.get_json()
            firebase_uid = data.get('firebaseUid') if data else None
            if firebase_uid and verify_firebase_uid(firebase_uid):
                return f(*args, **kwargs)
        
        return jsonify({
            'success': False,
            'error': 'Authentication required',
            'message': 'Provide valid admin token or Firebase authentication'
        }), 401
    
    return decorated_function

def require_admin_auth(f):
    """Decorator to require admin authentication for sensitive endpoints"""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        admin_token = request.headers.get('X-Admin-Token')
        if not admin_token or not verify_admin_token(admin_token):
            return jsonify({
                'success': False,
                'error': 'Admin authentication required',
                'message': 'Provide valid admin token in X-Admin-Token header'
            }), 403
        
        return f(*args, **kwargs)
    
    return decorated_function