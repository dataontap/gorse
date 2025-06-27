
#!/usr/bin/env python3
"""
Script to sync Firebase users to the Users database table
Orders users by creation date (earliest first) and creates Stripe customers
"""

import os
import json
import psycopg2
from psycopg2.pool import SimpleConnectionPool
from contextlib import contextmanager
import stripe
from datetime import datetime
from web3 import Web3

# Initialize Stripe
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

# Initialize database connection
database_url = os.environ.get('DATABASE_URL')
try:
    pool = SimpleConnectionPool(1, 20, database_url)
    print("Database connection pool initialized successfully")

    @contextmanager
    def get_db_connection():
        connection = pool.getconn()
        try:
            yield connection
        finally:
            pool.putconn(connection)
except Exception as e:
    print(f"Error initializing database connection pool: {str(e)}")
    exit(1)

def load_all_users_from_batches():
    """Load all users from all batch files and sort by creation date"""
    all_users = []
    
    # Find all batch files
    batch_files = []
    for i in range(1, 40):  # Check up to batch 39
        filename = f"users_batch_{i}.json"
        if os.path.exists(filename):
            batch_files.append(filename)
    
    print(f"Found {len(batch_files)} batch files")
    
    # Load users from all batch files
    for filename in batch_files:
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Handle different JSON structures
            if isinstance(data, list):
                users = data
            elif isinstance(data, dict) and 'users' in data:
                users = data['users']
            else:
                users = [data]
            
            for user in users:
                if user.get('createdAt'):
                    all_users.append(user)
            
            print(f"Loaded {len(users)} users from {filename}")
            
        except Exception as e:
            print(f"Error loading {filename}: {str(e)}")
            continue
    
    # Sort users by creation date (earliest first)
    all_users.sort(key=lambda x: x.get('createdAt', 0))
    
    print(f"Total users loaded and sorted: {len(all_users)}")
    return all_users

def create_stripe_customer(email, display_name, firebase_uid, user_id):
    """Create a Stripe customer for the user"""
    if not stripe.api_key:
        print("Stripe API key not configured, skipping Stripe customer creation")
        return None
    
    try:
        customer = stripe.Customer.create(
            email=email,
            name=display_name,
            metadata={
                'firebase_uid': firebase_uid,
                'user_id': str(user_id),
                'source': 'firebase_migration'
            }
        )
        return customer.id
    except Exception as e:
        print(f"Error creating Stripe customer for {email}: {str(e)}")
        return None

def sync_users_to_database(users):
    """Sync users to the database with proper ordering"""
    
    with get_db_connection() as conn:
        if conn:
            with conn.cursor() as cur:
                # Ensure users table exists with all required columns
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        email VARCHAR(255) NOT NULL,
                        firebase_uid VARCHAR(128) UNIQUE NOT NULL,
                        stripe_customer_id VARCHAR(100),
                        display_name VARCHAR(255),
                        photo_url TEXT,
                        imei VARCHAR(100),
                        eth_address VARCHAR(42),
                        email_verified BOOLEAN DEFAULT FALSE,
                        phone_number VARCHAR(20),
                        disabled BOOLEAN DEFAULT FALSE,
                        firebase_created_at TIMESTAMP,
                        firebase_last_signin_at TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Check how many users already exist
                cur.execute("SELECT COUNT(*) FROM users")
                existing_count = cur.fetchone()[0]
                print(f"Existing users in database: {existing_count}")
                
                # Process users in order
                success_count = 0
                skip_count = 0
                error_count = 0
                
                for user in users:
                    try:
                        firebase_uid = user.get('uid')
                        email = user.get('email')
                        display_name = user.get('displayName')
                        photo_url = user.get('photoURL')
                        phone_number = user.get('phoneNumber')
                        email_verified = user.get('emailVerified', False)
                        disabled = user.get('disabled', False)
                        
                        # Convert timestamps
                        firebase_created_at = None
                        firebase_last_signin_at = None
                        
                        if user.get('createdAt'):
                            # Convert from microseconds to seconds, then to datetime
                            firebase_created_at = datetime.fromtimestamp(user['createdAt'] / 1000000)
                        
                        if user.get('lastSignedInAt'):
                            firebase_last_signin_at = datetime.fromtimestamp(user['lastSignedInAt'] / 1000000)
                        
                        if not firebase_uid or not email:
                            print(f"Skipping user with missing UID or email: {firebase_uid}")
                            skip_count += 1
                            continue
                        
                        # Check if user already exists
                        cur.execute("SELECT id, stripe_customer_id FROM users WHERE firebase_uid = %s", (firebase_uid,))
                        existing_user = cur.fetchone()
                        
                        if existing_user:
                            print(f"User {email} already exists, skipping")
                            skip_count += 1
                            continue
                        
                        # Create test wallet for the user
                        web3 = Web3()
                        test_account = web3.eth.account.create()
                        eth_address = test_account.address
                        
                        # Insert user into database
                        cur.execute("""
                            INSERT INTO users 
                            (email, firebase_uid, display_name, photo_url, phone_number, 
                             email_verified, disabled, eth_address, firebase_created_at, 
                             firebase_last_signin_at)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            RETURNING id
                        """, (
                            email, firebase_uid, display_name, photo_url, phone_number,
                            email_verified, disabled, eth_address, firebase_created_at,
                            firebase_last_signin_at
                        ))
                        
                        user_id = cur.fetchone()[0]
                        
                        # Create Stripe customer
                        stripe_customer_id = create_stripe_customer(
                            email, display_name, firebase_uid, user_id
                        )
                        
                        # Update user with Stripe customer ID if created
                        if stripe_customer_id:
                            cur.execute(
                                "UPDATE users SET stripe_customer_id = %s WHERE id = %s",
                                (stripe_customer_id, user_id)
                            )
                        
                        conn.commit()
                        success_count += 1
                        
                        if success_count % 100 == 0:
                            print(f"Processed {success_count} users...")
                        
                        # Award 100.33 DOTM tokens to each new user
                        try:
                            from ethereum_helper import award_new_member_token
                            success, result = award_new_member_token(eth_address)
                            if success:
                                print(f"Awarded 100.33 DOTM tokens to {email}. TX: {result}")
                            else:
                                print(f"Failed to award tokens to {email}: {result}")
                        except Exception as token_err:
                            print(f"Error awarding tokens to {email}: {str(token_err)}")
                        
                    except Exception as e:
                        print(f"Error processing user {user.get('email', 'unknown')}: {str(e)}")
                        error_count += 1
                        conn.rollback()
                        continue
                
                print(f"\n=== Sync Summary ===")
                print(f"Successfully synced: {success_count} users")
                print(f"Skipped (already exist): {skip_count} users")
                print(f"Errors: {error_count} users")
                print(f"Total processed: {len(users)} users")

def main():
    """Main function"""
    print("Firebase Users to Database Sync")
    print("===============================")
    
    # Load all users from batch files
    users = load_all_users_from_batches()
    
    if not users:
        print("No users found in batch files")
        return
    
    # Show earliest and latest users for verification
    earliest_user = users[0]
    latest_user = users[-1]
    
    print(f"Earliest user: {earliest_user.get('email')} (created: {datetime.fromtimestamp(earliest_user['createdAt'] / 1000000)})")
    print(f"Latest user: {latest_user.get('email')} (created: {datetime.fromtimestamp(latest_user['createdAt'] / 1000000)})")
    
    # Confirm before proceeding
    response = input(f"\nSync {len(users)} users to database? (y/N): ")
    if response.lower() != 'y':
        print("Sync cancelled")
        return
    
    # Sync users to database
    sync_users_to_database(users)
    
    print("\nSync completed!")

if __name__ == "__main__":
    main()
