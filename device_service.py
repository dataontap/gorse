import hashlib
from datetime import datetime, timedelta
from user_agents import parse
from typing import Dict, Optional, Tuple
import psycopg2
from psycopg2.extras import RealDictCursor

def get_db_connection():
    """Get database connection"""
    import os
    try:
        conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
        return conn
    except Exception as e:
        print(f"Database connection error: {str(e)}")
        return None

def parse_user_agent(user_agent_string: str) -> Dict:
    """Parse user agent string and extract device information"""
    if not user_agent_string:
        return {
            'device_type': 'unknown',
            'device_brand': 'unknown',
            'device_model': 'unknown',
            'os_family': 'unknown',
            'os_version': 'unknown',
            'browser_family': 'unknown',
            'browser_version': 'unknown'
        }
    
    user_agent = parse(user_agent_string)
    
    device_type = 'desktop'
    if user_agent.is_mobile:
        device_type = 'mobile'
    elif user_agent.is_tablet:
        device_type = 'tablet'
    elif user_agent.is_pc:
        device_type = 'desktop'
    elif user_agent.is_bot:
        device_type = 'bot'
    
    device_brand = user_agent.device.brand or 'unknown'
    device_model = user_agent.device.model or 'unknown'
    
    if device_brand == 'unknown' and device_model == 'unknown':
        if 'iPhone' in user_agent_string:
            device_brand = 'Apple'
            if 'iPhone 14 Pro Max' in user_agent_string:
                device_model = 'iPhone 14 Pro Max'
            elif 'iPhone 14 Pro' in user_agent_string:
                device_model = 'iPhone 14 Pro'
            elif 'iPhone 14' in user_agent_string:
                device_model = 'iPhone 14'
            elif 'iPhone 13' in user_agent_string:
                device_model = 'iPhone 13'
            elif 'iPhone' in user_agent_string:
                device_model = 'iPhone'
        elif 'iPad' in user_agent_string:
            device_brand = 'Apple'
            device_model = 'iPad'
        elif 'Macintosh' in user_agent_string or 'Mac OS' in user_agent_string:
            device_brand = 'Apple'
            device_model = 'Mac'
        elif 'Windows' in user_agent_string:
            device_brand = 'PC'
            device_model = 'Windows Computer'
        elif 'Android' in user_agent_string:
            device_brand = 'Android'
            if 'Samsung' in user_agent_string:
                device_brand = 'Samsung'
            elif 'Google' in user_agent_string or 'Pixel' in user_agent_string:
                device_brand = 'Google'
    
    return {
        'device_type': device_type,
        'device_brand': device_brand,
        'device_model': device_model,
        'os_family': user_agent.os.family,
        'os_version': user_agent.os.version_string,
        'browser_family': user_agent.browser.family,
        'browser_version': user_agent.browser.version_string
    }

def generate_device_fingerprint(user_agent: str, ip_address: str, firebase_uid: str) -> str:
    """Generate a unique device fingerprint"""
    fingerprint_data = f"{user_agent}|{ip_address}|{firebase_uid}"
    return hashlib.sha256(fingerprint_data.encode()).hexdigest()

def estimate_device_value(device_brand: str, device_model: str, os_version: str) -> Optional[float]:
    """Estimate device value based on brand and model"""
    value_map = {
        ('Apple', 'iPhone 14 Pro Max'): 699.00,
        ('Apple', 'iPhone 14 Pro'): 649.00,
        ('Apple', 'iPhone 14'): 599.00,
        ('Apple', 'iPhone 13 Pro Max'): 599.00,
        ('Apple', 'iPhone 13 Pro'): 549.00,
        ('Apple', 'iPhone 13'): 499.00,
        ('Apple', 'iPad'): 399.00,
        ('Apple', 'Mac'): 899.00,
        ('Samsung', 'Galaxy S22'): 450.00,
        ('Samsung', 'Galaxy S21'): 350.00,
        ('Google', 'Pixel 6'): 385.00,
        ('Google', 'Pixel 7'): 450.00,
    }
    
    key = (device_brand, device_model)
    if key in value_map:
        return value_map[key]
    
    if device_brand == 'Apple':
        if 'iPhone' in device_model:
            return 500.00
        elif 'iPad' in device_model:
            return 350.00
        elif 'Mac' in device_model:
            return 800.00
    elif device_brand == 'Samsung':
        return 400.00
    elif device_brand == 'Google':
        return 350.00
    
    return None

def get_device_storage_and_color(device_model: str) -> Tuple[Optional[str], Optional[str]]:
    """Extract storage capacity and color from device model if available"""
    storage = None
    color = None
    
    if 'iPhone 14 Pro Max' in device_model:
        storage = '256GB'
        color = 'Sierra Blue'
    elif 'iPhone 14 Pro' in device_model:
        storage = '256GB'
        color = 'Deep Purple'
    elif 'iPhone 13 Pro' in device_model:
        storage = '256GB'
        color = 'Graphite'
    elif 'Galaxy S22' in device_model:
        storage = '128GB'
        color = 'Phantom Black'
    elif 'Pixel 6' in device_model:
        storage = '256GB'
        color = 'Sorta Seafoam'
    
    return storage, color

def register_or_update_device(
    user_id: int,
    firebase_uid: str,
    user_agent: str,
    ip_address: str
) -> Dict:
    """Register a new device or update existing device information"""
    
    device_info = parse_user_agent(user_agent)
    fingerprint = generate_device_fingerprint(user_agent, ip_address, firebase_uid)
    estimated_value = estimate_device_value(device_info['device_brand'], device_info['device_model'], device_info['os_version'])
    storage, color = get_device_storage_and_color(device_info['device_model'])
    
    conn = get_db_connection()
    if not conn:
        return {'success': False, 'error': 'Database connection failed'}
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT id, last_active FROM devices 
                WHERE device_fingerprint = %s
                """,
                (fingerprint,)
            )
            existing_device = cur.fetchone()
            
            if existing_device:
                cur.execute(
                    """
                    UPDATE devices SET
                        last_active = CURRENT_TIMESTAMP,
                        device_status = 'online',
                        ip_address = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE device_fingerprint = %s
                    RETURNING id
                    """,
                    (ip_address, fingerprint)
                )
                device_id = cur.fetchone()['id']
                conn.commit()
                
                return {
                    'success': True,
                    'device_id': device_id,
                    'action': 'updated',
                    'message': 'Device information updated'
                }
            else:
                cur.execute(
                    """
                    INSERT INTO devices (
                        user_id, firebase_uid, device_type, device_brand, device_model,
                        os_family, os_version, browser_family, browser_version,
                        user_agent, device_fingerprint, ip_address,
                        estimated_value, storage_capacity, color, condition, device_status
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'online'
                    )
                    RETURNING id
                    """,
                    (
                        user_id, firebase_uid, device_info['device_type'],
                        device_info['device_brand'], device_info['device_model'],
                        device_info['os_family'], device_info['os_version'],
                        device_info['browser_family'], device_info['browser_version'],
                        user_agent, fingerprint, ip_address,
                        estimated_value, storage, color, 'excellent'
                    )
                )
                device_id = cur.fetchone()['id']
                conn.commit()
                
                return {
                    'success': True,
                    'device_id': device_id,
                    'action': 'created',
                    'message': 'New device registered'
                }
    
    except Exception as e:
        conn.rollback()
        print(f"Error registering device: {str(e)}")
        return {'success': False, 'error': str(e)}
    finally:
        conn.close()

def get_user_devices(firebase_uid: str) -> Dict:
    """Get all devices associated with a user"""
    conn = get_db_connection()
    if not conn:
        return {'success': False, 'error': 'Database connection failed'}
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT 
                    id, device_type, device_brand, device_model,
                    os_family, os_version, browser_family, browser_version,
                    last_active, first_seen, device_status,
                    estimated_value, storage_capacity, color, condition,
                    is_primary
                FROM devices
                WHERE firebase_uid = %s
                ORDER BY last_active DESC
                """,
                (firebase_uid,)
            )
            devices = cur.fetchall()
            
            for device in devices:
                time_diff = datetime.now() - device['last_active']
                if time_diff < timedelta(minutes=5):
                    device['device_status'] = 'online'
                else:
                    device['device_status'] = 'offline'
            
            return {
                'success': True,
                'devices': devices,
                'count': len(devices)
            }
    
    except Exception as e:
        print(f"Error fetching devices: {str(e)}")
        return {'success': False, 'error': str(e)}
    finally:
        conn.close()

def mark_devices_offline(firebase_uid: str, exclude_fingerprint: Optional[str] = None):
    """Mark all devices as offline except the current one"""
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        with conn.cursor() as cur:
            if exclude_fingerprint:
                cur.execute(
                    """
                    UPDATE devices 
                    SET device_status = 'offline'
                    WHERE firebase_uid = %s 
                    AND device_fingerprint != %s
                    AND last_active < NOW() - INTERVAL '5 minutes'
                    """,
                    (firebase_uid, exclude_fingerprint)
                )
            else:
                cur.execute(
                    """
                    UPDATE devices 
                    SET device_status = 'offline'
                    WHERE firebase_uid = %s
                    AND last_active < NOW() - INTERVAL '5 minutes'
                    """,
                    (firebase_uid,)
                )
            conn.commit()
    except Exception as e:
        print(f"Error marking devices offline: {str(e)}")
        conn.rollback()
    finally:
        conn.close()
