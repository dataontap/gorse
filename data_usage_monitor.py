"""
Real-Time Data Usage Monitoring Service
Tracks network data consumption with detailed metrics for Stripe metered billing
"""

import os
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import stripe
from decimal import Decimal

# Initialize Stripe
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

# Pricing configuration
DATA_COST_PER_GB = 0.10  # $0.10 per GB


class DataUsageMonitor:
    """Monitor and track real-time network data usage with detailed metrics"""
    
    def __init__(self, get_db_connection):
        self.get_db_connection = get_db_connection
        self._ensure_table_exists()
    
    def _ensure_table_exists(self):
        """Create data_usage_metrics table if it doesn't exist"""
        try:
            with self.get_db_connection() as conn:
                if conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            CREATE TABLE IF NOT EXISTS data_usage_metrics (
                                id SERIAL PRIMARY KEY,
                                firebase_uid VARCHAR(128) NOT NULL,
                                stripe_customer_id VARCHAR(255),
                                
                                -- Network type and connection
                                network_type VARCHAR(10) NOT NULL,  -- '4G' or '5G'
                                connection_type VARCHAR(20) NOT NULL,  -- 'Mobile', 'Home', or 'WiFi'
                                
                                -- Performance metrics
                                speed_mbps DECIMAL(10, 2) NOT NULL,
                                priority VARCHAR(20),  -- 'High', 'Medium', 'Low'
                                provider VARCHAR(100),
                                
                                -- Usage data
                                data_used_mb DECIMAL(15, 6) NOT NULL,
                                data_used_gb DECIMAL(10, 3) NOT NULL,
                                cost_usd DECIMAL(10, 2) NOT NULL,
                                
                                -- Session tracking
                                session_id VARCHAR(64),
                                session_start TIMESTAMP,
                                session_duration_seconds INTEGER,
                                
                                -- Metadata
                                device_id VARCHAR(128),
                                ip_address VARCHAR(45),
                                location VARCHAR(100),
                                
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                
                                CONSTRAINT check_network_type CHECK (network_type IN ('4G', '5G')),
                                CONSTRAINT check_connection_type CHECK (connection_type IN ('Mobile', 'Home', 'WiFi'))
                            );
                            
                            -- Indexes for fast queries
                            CREATE INDEX IF NOT EXISTS idx_data_usage_firebase_uid 
                                ON data_usage_metrics(firebase_uid);
                            CREATE INDEX IF NOT EXISTS idx_data_usage_created_at 
                                ON data_usage_metrics(created_at);
                            CREATE INDEX IF NOT EXISTS idx_data_usage_session 
                                ON data_usage_metrics(session_id);
                            
                            -- Aggregated usage view for faster real-time queries
                            CREATE TABLE IF NOT EXISTS data_usage_realtime (
                                firebase_uid VARCHAR(128) PRIMARY KEY,
                                current_session_id VARCHAR(64),
                                
                                -- Current metrics
                                network_type VARCHAR(10),
                                connection_type VARCHAR(20),
                                speed_mbps DECIMAL(10, 2),
                                priority VARCHAR(20),
                                provider VARCHAR(100),
                                
                                -- Real-time usage (last hour)
                                data_used_gb_hour DECIMAL(10, 1),
                                cost_usd_hour DECIMAL(10, 1),
                                
                                -- Cumulative today
                                data_used_gb_today DECIMAL(10, 1),
                                cost_usd_today DECIMAL(10, 2),
                                
                                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                            );
                            
                            CREATE INDEX IF NOT EXISTS idx_data_usage_realtime_updated 
                                ON data_usage_realtime(last_updated);
                        """)
                        conn.commit()
                        print("Data usage monitoring tables created/verified successfully")
        except Exception as e:
            print(f"Error creating data usage monitoring tables: {str(e)}")
    
    def log_usage_event(
        self,
        firebase_uid: str,
        network_type: str,
        connection_type: str,
        speed_mbps: float,
        data_used_mb: float,
        priority: Optional[str] = None,
        provider: Optional[str] = None,
        session_id: Optional[str] = None,
        device_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        location: Optional[str] = None,
        stripe_customer_id: Optional[str] = None
    ) -> Dict:
        """
        Log a data usage event
        
        Args:
            firebase_uid: User's Firebase UID
            network_type: '4G' or '5G'
            connection_type: 'Mobile', 'Home', or 'WiFi'
            speed_mbps: Current connection speed in Mbps
            data_used_mb: Data consumed in megabytes
            priority: Connection priority (High/Medium/Low)
            provider: Internet service provider name
            session_id: Unique session identifier
            device_id: Device identifier
            ip_address: User's IP address
            location: Geographic location
            stripe_customer_id: Stripe customer ID for billing
            
        Returns:
            dict: Result of the operation
        """
        try:
            # Calculate usage in GB and cost
            data_used_gb = data_used_mb / 1024
            cost_usd = data_used_gb * DATA_COST_PER_GB
            
            with self.get_db_connection() as conn:
                if not conn:
                    return {'success': False, 'error': 'Database unavailable'}
                
                with conn.cursor() as cur:
                    # Insert usage event
                    cur.execute("""
                        INSERT INTO data_usage_metrics (
                            firebase_uid, stripe_customer_id, network_type, connection_type,
                            speed_mbps, priority, provider, data_used_mb, data_used_gb,
                            cost_usd, session_id, device_id, ip_address, location
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        firebase_uid, stripe_customer_id, network_type, connection_type,
                        speed_mbps, priority, provider, data_used_mb, data_used_gb,
                        cost_usd, session_id, device_id, ip_address, location
                    ))
                    
                    event_id = cur.fetchone()[0]
                    conn.commit()
                    
                    # Update real-time aggregates
                    self._update_realtime_metrics(firebase_uid)
                    
                    # Report to Stripe if customer ID available
                    if stripe_customer_id:
                        self._report_to_stripe(
                            stripe_customer_id,
                            data_used_gb,
                            network_type,
                            connection_type,
                            provider
                        )
                    
                    return {
                        'success': True,
                        'event_id': event_id,
                        'data_gb': round(data_used_gb, 3),
                        'cost_usd': round(cost_usd, 2)
                    }
                    
        except Exception as e:
            print(f"Error logging usage event: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _update_realtime_metrics(self, firebase_uid: str):
        """Update real-time aggregated metrics for a user"""
        try:
            with self.get_db_connection() as conn:
                if conn:
                    with conn.cursor() as cur:
                        # Calculate hourly usage
                        one_hour_ago = datetime.now() - timedelta(hours=1)
                        
                        cur.execute("""
                            WITH hourly_data AS (
                                SELECT 
                                    SUM(data_used_gb) as gb_hour,
                                    SUM(cost_usd) as cost_hour
                                FROM data_usage_metrics
                                WHERE firebase_uid = %s
                                    AND created_at >= %s
                            ),
                            daily_data AS (
                                SELECT 
                                    SUM(data_used_gb) as gb_today,
                                    SUM(cost_usd) as cost_today
                                FROM data_usage_metrics
                                WHERE firebase_uid = %s
                                    AND created_at >= DATE_TRUNC('day', CURRENT_TIMESTAMP)
                            ),
                            latest_metrics AS (
                                SELECT 
                                    network_type, connection_type, speed_mbps,
                                    priority, provider, session_id
                                FROM data_usage_metrics
                                WHERE firebase_uid = %s
                                ORDER BY created_at DESC
                                LIMIT 1
                            )
                            INSERT INTO data_usage_realtime (
                                firebase_uid, current_session_id, network_type, 
                                connection_type, speed_mbps, priority, provider,
                                data_used_gb_hour, cost_usd_hour,
                                data_used_gb_today, cost_usd_today, last_updated
                            )
                            SELECT 
                                %s, lm.session_id, lm.network_type,
                                lm.connection_type, lm.speed_mbps, lm.priority, lm.provider,
                                COALESCE(hd.gb_hour, 0), COALESCE(hd.cost_hour, 0),
                                COALESCE(dd.gb_today, 0), COALESCE(dd.cost_today, 0),
                                CURRENT_TIMESTAMP
                            FROM latest_metrics lm
                            CROSS JOIN hourly_data hd
                            CROSS JOIN daily_data dd
                            ON CONFLICT (firebase_uid) 
                            DO UPDATE SET
                                current_session_id = EXCLUDED.current_session_id,
                                network_type = EXCLUDED.network_type,
                                connection_type = EXCLUDED.connection_type,
                                speed_mbps = EXCLUDED.speed_mbps,
                                priority = EXCLUDED.priority,
                                provider = EXCLUDED.provider,
                                data_used_gb_hour = EXCLUDED.data_used_gb_hour,
                                cost_usd_hour = EXCLUDED.cost_usd_hour,
                                data_used_gb_today = EXCLUDED.data_used_gb_today,
                                cost_usd_today = EXCLUDED.cost_usd_today,
                                last_updated = CURRENT_TIMESTAMP
                        """, (firebase_uid, one_hour_ago, firebase_uid, firebase_uid, firebase_uid))
                        
                        conn.commit()
        except Exception as e:
            print(f"Error updating real-time metrics: {str(e)}")
    
    def _report_to_stripe(
        self,
        customer_id: str,
        data_gb: float,
        network_type: str,
        connection_type: str,
        provider: Optional[str]
    ):
        """Report usage to Stripe with detailed metadata"""
        try:
            event = stripe.billing.MeterEvent.create(
                event_name='data_usage',
                payload={
                    'stripe_customer_id': customer_id,
                    'value': str(data_gb),
                    'network_type': network_type,
                    'connection_type': connection_type,
                    'provider': provider or 'Unknown'
                },
                timestamp=int(time.time())
            )
            print(f"✅ Reported {data_gb:.3f} GB ({network_type} {connection_type}) to Stripe for {customer_id}")
        except Exception as e:
            print(f"Error reporting to Stripe: {str(e)}")
    
    def get_realtime_metrics(self, firebase_uid: str) -> Dict:
        """Get real-time metrics for a user"""
        try:
            with self.get_db_connection() as conn:
                if not conn:
                    return {'success': False, 'error': 'Database unavailable'}
                
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT 
                            network_type, connection_type, speed_mbps,
                            priority, provider,
                            data_used_gb_hour, cost_usd_hour,
                            data_used_gb_today, cost_usd_today,
                            last_updated
                        FROM data_usage_realtime
                        WHERE firebase_uid = %s
                    """, (firebase_uid,))
                    
                    row = cur.fetchone()
                    
                    if not row:
                        return {
                            'success': True,
                            'metrics': {
                                'network_type': 'N/A',
                                'connection_type': 'N/A',
                                'speed_mbps': 0,
                                'priority': 'N/A',
                                'provider': 'N/A',
                                'data_gb_hour': 0.0,
                                'cost_usd_hour': 0.0,
                                'data_gb_today': 0.0,
                                'cost_usd_today': 0.0
                            }
                        }
                    
                    return {
                        'success': True,
                        'metrics': {
                            'network_type': row[0] or 'N/A',
                            'connection_type': row[1] or 'N/A',
                            'speed_mbps': float(row[2]) if row[2] else 0,
                            'priority': row[3] or 'N/A',
                            'provider': row[4] or 'N/A',
                            'data_gb_hour': float(row[5]) if row[5] else 0.0,
                            'cost_usd_hour': float(row[6]) if row[6] else 0.0,
                            'data_gb_today': float(row[7]) if row[7] else 0.0,
                            'cost_usd_today': float(row[8]) if row[8] else 0.0,
                            'last_updated': row[9].isoformat() if row[9] else None
                        }
                    }
                    
        except Exception as e:
            print(f"Error getting real-time metrics: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_usage_history(
        self,
        firebase_uid: str,
        hours: int = 24,
        interval_minutes: int = 5
    ) -> Dict:
        """
        Get historical usage data for charting
        
        Args:
            firebase_uid: User's Firebase UID
            hours: Number of hours of history to retrieve
            interval_minutes: Data aggregation interval in minutes
            
        Returns:
            dict: Historical usage data with timestamps
        """
        try:
            with self.get_db_connection() as conn:
                if not conn:
                    return {'success': False, 'error': 'Database unavailable'}
                
                with conn.cursor() as cur:
                    start_time = datetime.now() - timedelta(hours=hours)
                    
                    cur.execute("""
                        SELECT 
                            DATE_TRUNC('minute', created_at) as time_bucket,
                            SUM(data_used_gb) as total_gb,
                            AVG(speed_mbps) as avg_speed,
                            MAX(network_type) as network_type
                        FROM data_usage_metrics
                        WHERE firebase_uid = %s
                            AND created_at >= %s
                        GROUP BY DATE_TRUNC('minute', created_at)
                        ORDER BY time_bucket ASC
                    """, (firebase_uid, start_time))
                    
                    history = []
                    for row in cur.fetchall():
                        history.append({
                            'timestamp': row[0].isoformat() if row[0] else None,
                            'data_gb': float(row[1]) if row[1] else 0,
                            'speed_mbps': float(row[2]) if row[2] else 0,
                            'network_type': row[3] or '4G'
                        })
                    
                    return {
                        'success': True,
                        'history': history,
                        'interval_minutes': interval_minutes,
                        'hours': hours
                    }
                    
        except Exception as e:
            print(f"Error getting usage history: {str(e)}")
            return {'success': False, 'error': str(e)}
