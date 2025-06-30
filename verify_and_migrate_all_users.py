
#!/usr/bin/env python3
"""
Script to verify user count and migrate all Firebase users if needed
"""

import os
import json
import psycopg2
from psycopg2.pool import SimpleConnectionPool
from contextlib import contextmanager
from datetime import datetime
import stripe
from web3 import Web3

# Initialize database connection
database_url = os.environ.get('DATABASE_URL')
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

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

def check_current_user_count():
    """Check how many users are currently in the database"""
    try:
        with get_db_connection() as conn:
            if conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT COUNT(*) FROM users")
                    count = cur.fetchone()[0]
                    return count
        return 0
    except Exception as e:
        print(f"Error checking user count: {str(e)}")
        return 0

def count_users_in_batch_files():
    """Count total users in all batch files"""
    total_users = 0
    batch_files_found = 0
    
    for i in range(1, 40):  # Check up to batch 39
        filename = f"users_batch_{i}.json"
        if os.path.exists(filename):
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
                
                total_users += len(users)
                batch_files_found += 1
                print(f"Batch {i}: {len(users)} users")
                
            except Exception as e:
                print(f"Error reading {filename}: {str(e)}")
    
    print(f"\nTotal users in {batch_files_found} batch files: {total_users}")
    return total_users

def create_stripe_customer(email, display_name, firebase_uid, user_id):
    """Create a Stripe customer for the user"""
    if not stripe.api_key:
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

def migrate_users_from_batch_files():
    """Migrate users from batch files to database"""
    # Load all users from batch files
    all_users = []
    
    for i in range(1, 40):
        filename = f"users_batch_{i}.json"
        if os.path.exists(filename):
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if isinstance(data, list):
                    users = data
                elif isinstance(data, dict) and 'users' in data:
                    users = data['users']
                else:
                    users = [data]
                
                for user in users:
                    if user.get('createdAt'):
                        all_users.append(user)
                        
            except Exception as e:
                print(f"Error loading {filename}: {str(e)}")
                continue
    
    # Sort users by creation date (earliest first)
    all_users.sort(key=lambda x: x.get('createdAt', 0))
    
    print(f"Loaded {len(all_users)} users from batch files")
    
    # Migrate users to database
    with get_db_connection() as conn:
        if conn:
            with conn.cursor() as cur:
                # Ensure users table exists
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
                
                success_count = 0
                skip_count = 0
                error_count = 0
                
                for user in all_users:
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
                            firebase_created_at = datetime.fromtimestamp(user['createdAt'] / 1000000)
                        
                        if user.get('lastSignedInAt'):
                            firebase_last_signin_at = datetime.fromtimestamp(user['lastSignedInAt'] / 1000000)
                        
                        if not firebase_uid or not email:
                            skip_count += 1
                            continue
                        
                        # Check if user already exists
                        cur.execute("SELECT id FROM users WHERE firebase_uid = %s", (firebase_uid,))
                        if cur.fetchone():
                            skip_count += 1
                            continue
                        
                        # Create test wallet
                        web3 = Web3()
                        test_account = web3.eth.account.create()
                        eth_address = test_account.address
                        
                        # Insert user
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
                        
                        if stripe_customer_id:
                            cur.execute(
                                "UPDATE users SET stripe_customer_id = %s WHERE id = %s",
                                (stripe_customer_id, user_id)
                            )
                        
                        conn.commit()
                        success_count += 1
                        
                        if success_count % 1000 == 0:
                            print(f"Migrated {success_count} users...")
                        
                    except Exception as e:
                        print(f"Error processing user {user.get('email', 'unknown')}: {str(e)}")
                        error_count += 1
                        conn.rollback()
                        continue
                
                print(f"\n=== Migration Summary ===")
                print(f"Successfully migrated: {success_count} users")
                print(f"Skipped (already exist): {skip_count} users")
                print(f"Errors: {error_count} users")

def main():
    """Main function"""
    print("User Migration Verification and Import")
    print("=====================================")
    
    # Check current user count in database
    current_count = check_current_user_count()
    print(f"Current users in database: {current_count}")
    
    # Count users in batch files
    batch_file_count = count_users_in_batch_files()
    
    if current_count >= 29000:
        print(f"✓ Database already has {current_count} users - sufficient for membership creation")
        response = input("Proceed anyway to ensure all users are migrated? (y/N): ")
        if response.lower() != 'y':
            return
    elif batch_file_count > 0:
        print(f"Found {batch_file_count} users in batch files")
        response = input(f"Migrate {batch_file_count} users to database? (y/N): ")
        if response.lower() != 'y':
            return
        
        migrate_users_from_batch_files()
    else:
        print("No batch files found. Please ensure user batch files exist.")
        return
    
    # Final count check
    final_count = check_current_user_count()
    print(f"\nFinal user count: {final_count}")
    
    if final_count >= 29000:
        print("✓ Ready to create Basic Memberships for all users")
        print("You can now run: python create_basic_memberships_2099.py")
    else:
        print("⚠ User count is still low. Check batch files and migration process.")

if __name__ == "__main__":
    main()
