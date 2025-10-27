"""
MCP Usage Tracking Service
Integrates MCP API usage with Stripe metered billing
"""

import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import stripe
from stripe_metering import report_data_usage

# Initialize Stripe
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

# MCP usage calculation constants
REQUESTS_PER_MB = 1000  # Approximate: 1000 API requests = 1 MB of data usage


class MCPUsageService:
    """Track and report MCP API usage to Stripe for billing"""
    
    def __init__(self, get_db_connection):
        self.get_db_connection = get_db_connection
    
    def report_mcp_usage_to_stripe(
        self, 
        firebase_uid: str,
        request_count: int = 1
    ) -> Dict:
        """
        Report MCP API usage to Stripe metered billing
        
        Args:
            firebase_uid: User's Firebase UID
            request_count: Number of API requests (default: 1)
            
        Returns:
            dict: Result of the usage report
        """
        try:
            # Get user's Stripe customer ID
            with self.get_db_connection() as conn:
                if not conn:
                    return {'success': False, 'error': 'Database unavailable'}
                
                with conn.cursor() as cur:
                    # Get Stripe customer ID from users table
                    cur.execute("""
                        SELECT stripe_customer_id, email
                        FROM users
                        WHERE firebase_uid = %s
                    """, (firebase_uid,))
                    
                    result = cur.fetchone()
                    
                    if not result or not result[0]:
                        print(f"No Stripe customer ID found for user {firebase_uid}")
                        return {
                            'success': False,
                            'error': 'No Stripe customer ID',
                            'user_email': result[1] if result else None
                        }
                    
                    stripe_customer_id = result[0]
                    user_email = result[1]
            
            # Convert API requests to megabytes for billing
            megabytes_used = request_count / REQUESTS_PER_MB
            
            # Report to Stripe
            result = report_data_usage(
                customer_id=stripe_customer_id,
                megabytes_used=megabytes_used,
                timestamp=datetime.now()
            )
            
            if result.get('success'):
                # Log the billing event
                self._log_billing_event(
                    firebase_uid=firebase_uid,
                    stripe_customer_id=stripe_customer_id,
                    request_count=request_count,
                    megabytes_used=megabytes_used,
                    stripe_event_id=result.get('event_id')
                )
                
                print(f"✅ Reported {request_count} MCP requests ({megabytes_used:.4f} MB) "
                      f"for {user_email} to Stripe")
            
            return result
            
        except Exception as e:
            print(f"Error reporting MCP usage to Stripe: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _log_billing_event(
        self,
        firebase_uid: str,
        stripe_customer_id: str,
        request_count: int,
        megabytes_used: float,
        stripe_event_id: str
    ):
        """Log billing event to database for tracking"""
        try:
            with self.get_db_connection() as conn:
                if conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            INSERT INTO mcp_billing_events 
                            (firebase_uid, stripe_customer_id, request_count, 
                             megabytes_used, stripe_event_id, created_at)
                            VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                        """, (firebase_uid, stripe_customer_id, request_count, 
                              megabytes_used, stripe_event_id))
                        conn.commit()
        except Exception as e:
            print(f"Error logging billing event: {str(e)}")
    
    def get_user_usage_stats(
        self, 
        firebase_uid: str,
        days: int = 30
    ) -> Dict:
        """
        Get usage statistics for a user
        
        Args:
            firebase_uid: User's Firebase UID
            days: Number of days to look back (default: 30)
            
        Returns:
            dict: Usage statistics
        """
        try:
            with self.get_db_connection() as conn:
                if not conn:
                    return {'success': False, 'error': 'Database unavailable'}
                
                with conn.cursor() as cur:
                    # Get total usage from MCP API requests table
                    start_date = datetime.now() - timedelta(days=days)
                    
                    # Get usage by day
                    cur.execute("""
                        SELECT 
                            DATE(mar.timestamp) as date,
                            COUNT(*) as request_count,
                            COUNT(DISTINCT mak.key_name) as unique_keys
                        FROM mcp_api_requests mar
                        LEFT JOIN mcp_api_keys mak ON mar.key_hash = mak.key_hash
                        WHERE mak.firebase_uid = %s
                            AND mar.timestamp >= %s
                        GROUP BY DATE(mar.timestamp)
                        ORDER BY date DESC
                    """, (firebase_uid, start_date))
                    
                    daily_usage = []
                    for row in cur.fetchall():
                        daily_usage.append({
                            'date': row[0].isoformat() if row[0] else None,
                            'request_count': row[1],
                            'megabytes': row[1] / REQUESTS_PER_MB,
                            'unique_keys': row[2]
                        })
                    
                    # Get total stats
                    cur.execute("""
                        SELECT 
                            COUNT(*) as total_requests,
                            COUNT(DISTINCT DATE(mar.timestamp)) as active_days,
                            COUNT(DISTINCT mak.id) as total_keys
                        FROM mcp_api_requests mar
                        LEFT JOIN mcp_api_keys mak ON mar.key_hash = mak.key_hash
                        WHERE mak.firebase_uid = %s
                            AND mar.timestamp >= %s
                    """, (firebase_uid, start_date))
                    
                    total_row = cur.fetchone()
                    total_requests = total_row[0] if total_row else 0
                    active_days = total_row[1] if total_row else 0
                    total_keys = total_row[2] if total_row else 0
                    
                    # Get current billing period usage
                    cur.execute("""
                        SELECT 
                            SUM(request_count) as period_requests,
                            SUM(megabytes_used) as period_megabytes
                        FROM mcp_billing_events
                        WHERE firebase_uid = %s
                            AND created_at >= DATE_TRUNC('month', CURRENT_TIMESTAMP)
                    """, (firebase_uid,))
                    
                    billing_row = cur.fetchone()
                    period_requests = billing_row[0] if billing_row and billing_row[0] else 0
                    period_megabytes = float(billing_row[1]) if billing_row and billing_row[1] else 0.0
                    
                    return {
                        'success': True,
                        'period_days': days,
                        'total_requests': total_requests,
                        'total_megabytes': total_requests / REQUESTS_PER_MB,
                        'active_days': active_days,
                        'total_keys': total_keys,
                        'avg_requests_per_day': total_requests / max(active_days, 1),
                        'daily_usage': daily_usage,
                        'current_billing_period': {
                            'requests': int(period_requests),
                            'megabytes': round(period_megabytes, 4)
                        }
                    }
                    
        except Exception as e:
            print(f"Error getting user usage stats: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_usage_by_endpoint(
        self,
        firebase_uid: str,
        days: int = 7
    ) -> Dict:
        """Get usage breakdown by endpoint"""
        try:
            with self.get_db_connection() as conn:
                if not conn:
                    return {'success': False, 'error': 'Database unavailable'}
                
                with conn.cursor() as cur:
                    start_date = datetime.now() - timedelta(days=days)
                    
                    cur.execute("""
                        SELECT 
                            mar.request_path,
                            mar.request_method,
                            COUNT(*) as request_count,
                            AVG(CASE WHEN mar.response_status = 200 THEN 1 ELSE 0 END) * 100 as success_rate
                        FROM mcp_api_requests mar
                        LEFT JOIN mcp_api_keys mak ON mar.key_hash = mak.key_hash
                        WHERE mak.firebase_uid = %s
                            AND mar.timestamp >= %s
                        GROUP BY mar.request_path, mar.request_method
                        ORDER BY request_count DESC
                        LIMIT 20
                    """, (firebase_uid, start_date))
                    
                    endpoints = []
                    for row in cur.fetchall():
                        endpoints.append({
                            'path': row[0],
                            'method': row[1],
                            'count': row[2],
                            'success_rate': round(float(row[3]), 2) if row[3] else 0
                        })
                    
                    return {
                        'success': True,
                        'endpoints': endpoints
                    }
                    
        except Exception as e:
            print(f"Error getting endpoint usage: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def ensure_billing_table_exists(self):
        """Create billing events table if it doesn't exist"""
        try:
            with self.get_db_connection() as conn:
                if conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            CREATE TABLE IF NOT EXISTS mcp_billing_events (
                                id SERIAL PRIMARY KEY,
                                firebase_uid VARCHAR(128) NOT NULL,
                                stripe_customer_id VARCHAR(255) NOT NULL,
                                request_count INTEGER NOT NULL,
                                megabytes_used DECIMAL(10, 6) NOT NULL,
                                stripe_event_id VARCHAR(255),
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                            );
                            
                            CREATE INDEX IF NOT EXISTS idx_mcp_billing_events_firebase_uid 
                                ON mcp_billing_events(firebase_uid);
                            CREATE INDEX IF NOT EXISTS idx_mcp_billing_events_created_at 
                                ON mcp_billing_events(created_at);
                        """)
                        conn.commit()
                        print("MCP billing events table created/verified successfully")
        except Exception as e:
            print(f"Error creating MCP billing events table: {str(e)}")
