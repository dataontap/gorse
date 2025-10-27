"""
MCP API Key Authentication and Rate Limiting System
Provides secure API key management for MCP endpoints
"""

import os
import secrets
import hashlib
import time
from datetime import datetime, timedelta
from functools import wraps
from typing import Optional, Tuple, Dict
from flask import request, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor

# Constants
API_KEY_PREFIX = "mcp_"
API_KEY_LENGTH = 48  # Total length including prefix
RATE_LIMIT_WINDOW = 3600  # 1 hour in seconds
DEFAULT_RATE_LIMIT = 1000  # requests per hour


def generate_api_key() -> str:
    """
    Generate a cryptographically secure API key
    Format: mcp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    """
    # Generate 42 random characters (48 - 4 for prefix - 2 for underscore buffer)
    random_part = secrets.token_urlsafe(32)[:42]
    return f"{API_KEY_PREFIX}{random_part}"


def hash_api_key(api_key: str) -> str:
    """
    Hash an API key for secure storage using SHA-256
    """
    return hashlib.sha256(api_key.encode('utf-8')).hexdigest()


class MCPAuthManager:
    """Manages MCP API key authentication and rate limiting"""
    
    def __init__(self, get_db_connection):
        self.get_db_connection = get_db_connection
        self._ensure_table_exists()
    
    def _ensure_table_exists(self):
        """Create mcp_api_keys table if it doesn't exist"""
        try:
            with self.get_db_connection() as conn:
                if conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            CREATE TABLE IF NOT EXISTS mcp_api_keys (
                                id SERIAL PRIMARY KEY,
                                key_hash VARCHAR(64) UNIQUE NOT NULL,
                                key_name VARCHAR(255) NOT NULL,
                                description TEXT,
                                rate_limit INTEGER DEFAULT 1000,
                                is_active BOOLEAN DEFAULT TRUE,
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                last_used_at TIMESTAMP,
                                total_requests BIGINT DEFAULT 0,
                                firebase_uid VARCHAR(128),
                                allowed_origins TEXT[],
                                metadata JSONB
                            );
                            
                            CREATE INDEX IF NOT EXISTS idx_mcp_api_keys_key_hash 
                                ON mcp_api_keys(key_hash);
                            CREATE INDEX IF NOT EXISTS idx_mcp_api_keys_is_active 
                                ON mcp_api_keys(is_active);
                            CREATE INDEX IF NOT EXISTS idx_mcp_api_keys_firebase_uid 
                                ON mcp_api_keys(firebase_uid);
                        """)
                        
                        # Create rate limiting tracking table
                        cur.execute("""
                            CREATE TABLE IF NOT EXISTS mcp_api_requests (
                                id SERIAL PRIMARY KEY,
                                key_hash VARCHAR(64) NOT NULL,
                                request_path VARCHAR(255),
                                request_method VARCHAR(10),
                                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                ip_address INET,
                                user_agent TEXT,
                                response_status INTEGER
                            );
                            
                            CREATE INDEX IF NOT EXISTS idx_mcp_api_requests_key_hash_timestamp 
                                ON mcp_api_requests(key_hash, timestamp);
                        """)
                        
                        conn.commit()
                        print("MCP API keys tables created/verified successfully")
        except Exception as e:
            print(f"Error creating MCP API keys tables: {str(e)}")
    
    def create_api_key(
        self, 
        key_name: str, 
        description: str = "", 
        rate_limit: int = DEFAULT_RATE_LIMIT,
        firebase_uid: Optional[str] = None,
        allowed_origins: Optional[list] = None
    ) -> Tuple[bool, str, str]:
        """
        Create a new API key
        Returns: (success, api_key or error_message, message)
        """
        try:
            # Generate new API key
            api_key = generate_api_key()
            key_hash = hash_api_key(api_key)
            
            with self.get_db_connection() as conn:
                if not conn:
                    return False, "Database connection unavailable", ""
                
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO mcp_api_keys 
                        (key_hash, key_name, description, rate_limit, firebase_uid, allowed_origins)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (key_hash, key_name, description, rate_limit, firebase_uid, allowed_origins))
                    
                    result = cur.fetchone()
                    conn.commit()
                    
                    if result:
                        return True, api_key, f"API key '{key_name}' created successfully"
            
            return False, "Failed to create API key", ""
            
        except Exception as e:
            return False, f"Error creating API key: {str(e)}", ""
    
    def validate_api_key(self, api_key: str) -> Tuple[bool, Optional[Dict]]:
        """
        Validate an API key and return key details
        Returns: (is_valid, key_info_dict or None)
        """
        if not api_key or not api_key.startswith(API_KEY_PREFIX):
            return False, None
        
        try:
            key_hash = hash_api_key(api_key)
            
            with self.get_db_connection() as conn:
                if not conn:
                    return False, None
                
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT id, key_name, description, rate_limit, is_active, 
                               firebase_uid, allowed_origins, total_requests
                        FROM mcp_api_keys
                        WHERE key_hash = %s AND is_active = TRUE
                    """, (key_hash,))
                    
                    key_info = cur.fetchone()
                    
                    if key_info:
                        # Update last_used_at
                        cur.execute("""
                            UPDATE mcp_api_keys 
                            SET last_used_at = CURRENT_TIMESTAMP,
                                total_requests = total_requests + 1
                            WHERE key_hash = %s
                        """, (key_hash,))
                        conn.commit()
                        
                        return True, dict(key_info)
            
            return False, None
            
        except Exception as e:
            print(f"Error validating API key: {str(e)}")
            return False, None
    
    def check_rate_limit(self, api_key: str, key_info: Dict) -> Tuple[bool, Dict]:
        """
        Check if API key is within rate limit
        Returns: (is_allowed, rate_limit_info)
        """
        try:
            key_hash = hash_api_key(api_key)
            rate_limit = key_info.get('rate_limit', DEFAULT_RATE_LIMIT)
            
            with self.get_db_connection() as conn:
                if not conn:
                    return True, {}  # Allow if DB unavailable
                
                with conn.cursor() as cur:
                    # Count requests in the last hour
                    one_hour_ago = datetime.now() - timedelta(hours=1)
                    
                    cur.execute("""
                        SELECT COUNT(*) 
                        FROM mcp_api_requests
                        WHERE key_hash = %s AND timestamp > %s
                    """, (key_hash, one_hour_ago))
                    
                    current_usage = cur.fetchone()[0]
                    
                    # Clean up old request logs (keep last 24 hours)
                    cur.execute("""
                        DELETE FROM mcp_api_requests
                        WHERE timestamp < NOW() - INTERVAL '24 hours'
                    """)
                    conn.commit()
                    
                    is_allowed = current_usage < rate_limit
                    
                    rate_info = {
                        "allowed": is_allowed,
                        "current_usage": current_usage,
                        "limit": rate_limit,
                        "percentage": round((current_usage / rate_limit) * 100, 1),
                        "reset_at": (datetime.now() + timedelta(hours=1)).isoformat()
                    }
                    
                    return is_allowed, rate_info
                    
        except Exception as e:
            print(f"Error checking rate limit: {str(e)}")
            return True, {}  # Allow on error to prevent blocking
    
    def log_request(
        self, 
        api_key: str, 
        request_path: str,
        request_method: str,
        ip_address: str,
        user_agent: str,
        response_status: int
    ):
        """Log an API request for rate limiting and analytics"""
        try:
            key_hash = hash_api_key(api_key)
            
            with self.get_db_connection() as conn:
                if conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            INSERT INTO mcp_api_requests 
                            (key_hash, request_path, request_method, ip_address, 
                             user_agent, response_status)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """, (key_hash, request_path, request_method, 
                              ip_address, user_agent, response_status))
                        conn.commit()
        except Exception as e:
            print(f"Error logging MCP request: {str(e)}")
    
    def list_api_keys(self, firebase_uid: Optional[str] = None) -> list:
        """List all API keys (optionally filtered by Firebase UID)"""
        try:
            with self.get_db_connection() as conn:
                if not conn:
                    return []
                
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    if firebase_uid:
                        cur.execute("""
                            SELECT id, key_name, description, rate_limit, is_active,
                                   created_at, last_used_at, total_requests
                            FROM mcp_api_keys
                            WHERE firebase_uid = %s
                            ORDER BY created_at DESC
                        """, (firebase_uid,))
                    else:
                        cur.execute("""
                            SELECT id, key_name, description, rate_limit, is_active,
                                   created_at, last_used_at, total_requests, firebase_uid
                            FROM mcp_api_keys
                            ORDER BY created_at DESC
                        """)
                    
                    return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            print(f"Error listing API keys: {str(e)}")
            return []
    
    def revoke_api_key(self, key_id: int) -> Tuple[bool, str]:
        """Revoke (deactivate) an API key"""
        try:
            with self.get_db_connection() as conn:
                if not conn:
                    return False, "Database connection unavailable"
                
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE mcp_api_keys
                        SET is_active = FALSE
                        WHERE id = %s
                        RETURNING key_name
                    """, (key_id,))
                    
                    result = cur.fetchone()
                    conn.commit()
                    
                    if result:
                        return True, f"API key '{result[0]}' revoked successfully"
                    return False, "API key not found"
        except Exception as e:
            return False, f"Error revoking API key: {str(e)}"


def require_mcp_api_key(auth_manager: MCPAuthManager):
    """
    Decorator to require MCP API key authentication
    Usage: @require_mcp_api_key(auth_manager)
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Extract API key from Authorization header
            auth_header = request.headers.get('Authorization', '')
            
            if not auth_header.startswith('Bearer '):
                return jsonify({
                    "error": "Unauthorized",
                    "message": "Missing or invalid Authorization header. Use: Authorization: Bearer mcp_..."
                }), 401
            
            api_key = auth_header.replace('Bearer ', '').strip()
            
            # Validate API key
            is_valid, key_info = auth_manager.validate_api_key(api_key)
            
            if not is_valid:
                auth_manager.log_request(
                    api_key, request.path, request.method,
                    request.remote_addr, request.headers.get('User-Agent', ''),
                    401
                )
                return jsonify({
                    "error": "Unauthorized",
                    "message": "Invalid or inactive API key"
                }), 401
            
            # Check rate limit
            is_allowed, rate_info = auth_manager.check_rate_limit(api_key, key_info)
            
            if not is_allowed:
                auth_manager.log_request(
                    api_key, request.path, request.method,
                    request.remote_addr, request.headers.get('User-Agent', ''),
                    429
                )
                return jsonify({
                    "error": "Rate Limit Exceeded",
                    "message": "API key has exceeded rate limit",
                    "rate_limit": rate_info
                }), 429
            
            # Add key info to request context
            request.mcp_key_info = key_info
            request.mcp_rate_info = rate_info
            
            # Execute the route
            response = f(*args, **kwargs)
            
            # Log successful request
            status_code = response.status_code if hasattr(response, 'status_code') else 200
            auth_manager.log_request(
                api_key, request.path, request.method,
                request.remote_addr, request.headers.get('User-Agent', ''),
                status_code
            )
            
            # Add rate limit headers to response
            if hasattr(response, 'headers'):
                response.headers['X-RateLimit-Limit'] = str(rate_info.get('limit', DEFAULT_RATE_LIMIT))
                response.headers['X-RateLimit-Remaining'] = str(
                    rate_info.get('limit', DEFAULT_RATE_LIMIT) - rate_info.get('current_usage', 0)
                )
                response.headers['X-RateLimit-Reset'] = rate_info.get('reset_at', '')
            
            return response
        
        return decorated_function
    return decorator
