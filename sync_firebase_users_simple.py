
#!/usr/bin/env python3
"""
Simple script to sync Firebase users to database in chronological order
Creates Stripe customers for all users
"""

import os
import json
import psycopg2
from contextlib import contextmanager
import stripe
from datetime import datetime

# Database setup
database_url = os.environ.get('DATABASE_URL')
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

@contextmanager
def get_db_connection():
    connection = psycopg2.connect(database_url)
    try:
        yield connection
    finally:
        connection.close()

def load_and_sort_users():
    """Load all users and sort by creation date"""
    all_users = []
    
    for i in range(1, 40):
        filename = f"users_batch_{i}.json"
        if os.path.exists(filename):
            try:
                with open(filename, 'r') as f:
                    data = json.load(f)
                    users = data.get('users', data) if isinstance(data, dict) else data
                    all_users.extend(users)
                print(f"Loaded batch {i}")
            except Exception as e:
                print(f"Error loading {filename}: {e}")
    
    # Sort by creation date (earliest first)
    all_users.sort(key=lambda x: x.get('createdAt', 0))
    print(f"Total users sorted: {len(all_users)}")
    return all_users

def sync_users():
    """Sync users to database with Stripe customers"""
    users = load_and_sort_users()
    
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            synced = 0
            
            for user in users:
                try:
                    firebase_uid = user.get('uid')
                    email = user.get('email')
                    display_name = user.get('displayName')
                    
                    if not firebase_uid or not email:
                        continue
                    
                    # Check if user exists
                    cur.execute("SELECT id FROM users WHERE firebase_uid = %s", (firebase_uid,))
                    if cur.fetchone():
                        continue
                    
                    # Create user in database
                    cur.execute("""
                        INSERT INTO users (email, firebase_uid, display_name, created_at)
                        VALUES (%s, %s, %s, %s) RETURNING id
                    """, (email, firebase_uid, display_name, 
                          datetime.fromtimestamp(user.get('createdAt', 0) / 1000000)))
                    
                    user_id = cur.fetchone()[0]
                    
                    # Create Stripe customer
                    if stripe.api_key:
                        try:
                            customer = stripe.Customer.create(
                                email=email,
                                name=display_name,
                                metadata={'firebase_uid': firebase_uid, 'user_id': str(user_id)}
                            )
                            
                            # Update with Stripe ID
                            cur.execute(
                                "UPDATE users SET stripe_customer_id = %s WHERE id = %s",
                                (customer.id, user_id)
                            )
                        except Exception as stripe_err:
                            print(f"Stripe error for {email}: {stripe_err}")
                    
                    conn.commit()
                    synced += 1
                    
                    if synced % 50 == 0:
                        print(f"Synced {synced} users...")
                        
                except Exception as e:
                    print(f"Error with user {user.get('email')}: {e}")
                    conn.rollback()
            
            print(f"Successfully synced {synced} users with Stripe customers")

if __name__ == "__main__":
    sync_users()
