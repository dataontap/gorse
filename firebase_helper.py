import os
import firebase_admin
from firebase_admin import credentials, auth
from functools import wraps
from flask import request, jsonify

# Initialize Firebase Admin SDK
try:
    # Check if Firebase credentials are set up
    if os.environ.get('FIREBASE_CREDENTIALS'):
        # Initialize with credentials from environment variable
        from json import loads
        cred_json = loads(os.environ.get('FIREBASE_CREDENTIALS'))
        cred = credentials.Certificate(cred_json)
    else:
        # Look for credentials file
        cred_path = 'firebase-credentials.json'
        if os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
        else:
            # Default to application default credentials
            cred = credentials.ApplicationDefault()

    firebase_admin.initialize_app(cred)
    print("Firebase Admin SDK initialized successfully")
except Exception as e:
    print(f"Error initializing Firebase Admin SDK: {str(e)}")
    print("Server will continue without Firebase Admin verification")

def verify_firebase_token(request):
    """Verify Firebase authentication token from Authorization header"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None, "No valid authorization header found"

    id_token = auth_header.split('Bearer ')[1]
    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token, None
    except Exception as e:
        return None, str(e)

def get_user_by_firebase_uid(firebase_uid):
    """Get user information from database by Firebase UID"""
    try:
        from main import get_db_connection
        with get_db_connection() as conn:
            if conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT id, email, display_name, firebase_uid
                        FROM users 
                        WHERE firebase_uid = %s
                    """, (firebase_uid,))

                    user = cur.fetchone()
                    if user:
                        # Parse display_name into first_name and last_name
                        display_name = user[2] or ''
                        name_parts = display_name.split(' ', 1) if display_name else []
                        first_name = name_parts[0] if name_parts else ''
                        last_name = name_parts[1] if len(name_parts) > 1 else ''

                        return {
                            'id': user[0],
                            'email': user[1],
                            'first_name': first_name,
                            'last_name': last_name,
                            'display_name': display_name,
                            'firebase_uid': user[3]
                        }
        return None
    except Exception as e:
        print(f"Error getting user by Firebase UID: {str(e)}")
        return None

def firebase_auth_required(f):
    """Decorator for Firebase Authentication on API routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not firebase_admin._apps:
            # Firebase Admin not initialized, proceed without verification (for development)
            print("WARNING: Firebase Admin not initialized, skipping token verification")
            return f(*args, **kwargs)

        decoded_token, error = verify_firebase_token(request)
        if error:
            return jsonify({'error': f'Unauthorized: {error}'}), 401

        # Add the decoded token to request object
        request.firebase_user = decoded_token
        return f(*args, **kwargs)
    return decorated_function