
#!/usr/bin/env python3
"""
Debug script to check how OXIO user IDs are stored in the database
"""

import os
import psycopg2
from contextlib import contextmanager
import json

# Initialize database connection
database_url = os.environ.get('DATABASE_URL')

@contextmanager
def get_db_connection():
    connection = psycopg2.connect(database_url)
    try:
        yield connection
    finally:
        connection.close()

def check_oxio_storage():
    """Check how OXIO user IDs are stored in the database"""
    print("=== OXIO User ID Storage Analysis ===")
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Check users table structure
                cur.execute("""
                    SELECT column_name, data_type, character_maximum_length 
                    FROM information_schema.columns 
                    WHERE table_name = 'users' AND column_name IN ('oxio_user_id', 'eth_address')
                    ORDER BY column_name
                """)
                columns = cur.fetchall()
                
                print("Users table OXIO-related columns:")
                for col in columns:
                    print(f"  {col[0]}: {col[1]} ({col[2]} chars max)")
                
                # Get sample of users with OXIO data
                cur.execute("""
                    SELECT id, email, oxio_user_id, eth_address, firebase_uid
                    FROM users 
                    WHERE oxio_user_id IS NOT NULL 
                    ORDER BY id 
                    LIMIT 10
                """)
                users = cur.fetchall()
                
                print(f"\nFound {len(users)} users with OXIO user IDs:")
                print("ID | Email | OXIO User ID | ETH Address | Firebase UID")
                print("-" * 120)
                
                for user in users:
                    user_id, email, oxio_user_id, eth_address, firebase_uid = user
                    # Truncate long fields for display
                    email_short = email[:20] + "..." if len(email) > 20 else email
                    oxio_short = oxio_user_id[:36] if oxio_user_id else "None"
                    eth_short = eth_address[:10] + "..." if eth_address else "None"
                    firebase_short = firebase_uid[:20] + "..." if firebase_uid else "None"
                    
                    print(f"{user_id:3} | {email_short:23} | {oxio_short:36} | {eth_short:13} | {firebase_short}")
                
                # Check for hyphens specifically
                cur.execute("""
                    SELECT COUNT(*) as total,
                           COUNT(CASE WHEN oxio_user_id LIKE '%-%' THEN 1 END) as with_hyphens,
                           COUNT(CASE WHEN oxio_user_id NOT LIKE '%-%' AND oxio_user_id IS NOT NULL THEN 1 END) as without_hyphens
                    FROM users 
                    WHERE oxio_user_id IS NOT NULL
                """)
                hyphen_stats = cur.fetchone()
                
                print(f"\nHyphen Analysis:")
                print(f"  Total OXIO user IDs: {hyphen_stats[0]}")
                print(f"  With hyphens: {hyphen_stats[1]}")
                print(f"  Without hyphens: {hyphen_stats[2]}")
                
                # Check recent OXIO activations
                cur.execute("""
                    SELECT COUNT(*) FROM information_schema.tables 
                    WHERE table_name = 'oxio_activations'
                """)
                
                if cur.fetchone()[0] > 0:
                    cur.execute("""
                        SELECT o.id, o.user_id, u.email, o.product_id, o.activation_status, 
                               o.created_at, o.oxio_response
                        FROM oxio_activations o
                        JOIN users u ON o.user_id = u.id
                        ORDER BY o.created_at DESC
                        LIMIT 5
                    """)
                    activations = cur.fetchall()
                    
                    print(f"\nRecent OXIO Activations ({len(activations)}):")
                    for activation in activations:
                        activation_id, user_id, email, product_id, status, created_at, response = activation
                        print(f"  ID {activation_id}: User {user_id} ({email[:20]}...) - {product_id} - {status}")
                        
                        # Parse OXIO response to see what was sent
                        if response:
                            try:
                                response_data = json.loads(response)
                                if 'request_payload' in response_data:
                                    payload = response_data['request_payload']
                                    if 'endUser' in payload:
                                        brand_id = payload['endUser'].get('brandId', 'Not found')
                                        end_user_id = payload['endUser'].get('endUserId', 'Not found')
                                        print(f"    Payload brandId: {brand_id}")
                                        print(f"    Payload endUserId: {end_user_id}")
                            except Exception as e:
                                print(f"    Could not parse response: {str(e)}")
                
                # Check what's in the purchases table for recent Basic Membership purchases
                cur.execute("""
                    SELECT p.PurchaseID, p.StripeProductID, p.UserID, p.FirebaseUID, 
                           u.email, u.oxio_user_id, p.DateCreated
                    FROM purchases p
                    JOIN users u ON p.UserID = u.id
                    WHERE p.StripeProductID = 'basic_membership'
                    ORDER BY p.DateCreated DESC
                    LIMIT 5
                """)
                recent_purchases = cur.fetchall()
                
                print(f"\nRecent Basic Membership Purchases ({len(recent_purchases)}):")
                for purchase in recent_purchases:
                    purchase_id, product_id, user_id, firebase_uid, email, oxio_user_id, date_created = purchase
                    print(f"  Purchase {purchase_id}: User {user_id} ({email[:20]}...)")
                    print(f"    OXIO User ID: {oxio_user_id}")
                    print(f"    Date: {date_created}")
                
    except Exception as e:
        print(f"Error checking OXIO storage: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_oxio_storage()
