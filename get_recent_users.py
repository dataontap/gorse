
#!/usr/bin/env python3
"""
Script to get the last 5 users that joined
"""

import os
import psycopg2
from datetime import datetime

database_url = os.environ.get('DATABASE_URL')

def get_recent_users():
    """Get the last 5 users that joined"""
    try:
        conn = psycopg2.connect(database_url)
        with conn.cursor() as cur:
            # Get last 5 users ordered by creation date
            cur.execute("""
                SELECT 
                    id,
                    email,
                    firebase_uid,
                    display_name,
                    stripe_customer_id,
                    oxio_user_id,
                    eth_address,
                    created_at
                FROM users 
                ORDER BY created_at DESC 
                LIMIT 5
            """)
            
            users = cur.fetchall()
            
            print("=" * 80)
            print("LAST 5 USERS THAT JOINED")
            print("=" * 80)
            print()
            
            for i, user in enumerate(users, 1):
                user_id, email, firebase_uid, display_name, stripe_customer_id, \
                oxio_user_id, eth_address, created_at = user
                
                print(f"User #{i}:")
                print(f"  ID: {user_id}")
                print(f"  Email: {email}")
                print(f"  Display Name: {display_name or 'N/A'}")
                print(f"  Firebase UID: {firebase_uid}")
                print(f"  Stripe Customer ID: {stripe_customer_id or 'N/A'}")
                print(f"  OXIO User ID: {oxio_user_id or 'N/A'}")
                print(f"  ETH Address: {eth_address or 'N/A'}")
                print(f"  Database Created: {created_at}")
                print()
            
            # Get additional stats
            cur.execute("""
                SELECT 
                    COUNT(*) as total_users,
                    COUNT(stripe_customer_id) as users_with_stripe,
                    COUNT(oxio_user_id) as users_with_oxio,
                    MIN(created_at) as earliest_user,
                    MAX(created_at) as latest_user
                FROM users
            """)
            
            stats = cur.fetchone()
            total, with_stripe, with_oxio, earliest, latest = stats
            
            print("=" * 80)
            print("DATABASE STATISTICS")
            print("=" * 80)
            print(f"Total Users: {total}")
            print(f"Users with Stripe: {with_stripe}")
            print(f"Users with OXIO: {with_oxio}")
            print(f"Earliest User: {earliest}")
            print(f"Latest User: {latest}")
            print()
            
        conn.close()
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    get_recent_users()
