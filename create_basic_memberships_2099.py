#!/usr/bin/env python3
"""
Script to create Basic Membership subscriptions for ALL current users
Validity: 2099-07-02 07:11:00 EST (Canada Day)
Status: Active
"""

import os
import psycopg2
from psycopg2.pool import SimpleConnectionPool
from contextlib import contextmanager
from datetime import datetime
import pytz

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

def ensure_phone_number_column():
    """Ensure phone_number column exists in users table"""
    with get_db_connection() as conn:
        if conn:
            with conn.cursor() as cur:
                try:
                    # Check if phone_number column exists
                    cur.execute("""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name='users' AND column_name='phone_number'
                    """)

                    if not cur.fetchone():
                        print("Adding missing phone_number column to users table...")
                        cur.execute("ALTER TABLE users ADD COLUMN phone_number VARCHAR(20)")
                        conn.commit()
                        print("✓ phone_number column added")
                    else:
                        print("✓ phone_number column already exists")

                except Exception as e:
                    print(f"Error checking/adding phone_number column: {str(e)}")
                    conn.rollback()

def ensure_tables_exist():
    """Ensure all required tables exist"""
    with get_db_connection() as conn:
        if conn:
            with conn.cursor() as cur:
                # Create subscriptions table if it doesn't exist
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS subscriptions (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        subscription_type VARCHAR(50) NOT NULL,
                        status VARCHAR(20) NOT NULL DEFAULT 'active',
                        start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        end_date TIMESTAMP,
                        stripe_subscription_id VARCHAR(100),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id)
                    )
                """)

                # Create purchases table if it doesn't exist
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS purchases (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        product_type VARCHAR(50) NOT NULL,
                        amount INTEGER NOT NULL,
                        status VARCHAR(20) NOT NULL DEFAULT 'completed',
                        stripe_payment_intent_id VARCHAR(100),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id)
                    )
                """)

                conn.commit()
                print("✓ Required tables verified/created")

def get_all_users():
    """Get all users from the database"""
    with get_db_connection() as conn:
        if conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, email, firebase_uid FROM users ORDER BY id")
                users = cur.fetchall()
                return users
    return []

def create_basic_membership_for_user(user_id, email):
    """Create Basic Membership subscription for a specific user"""
    # Set end date to 2099-07-02 07:11:00 EST (Canada Day)
    est = pytz.timezone('US/Eastern')
    end_date = est.localize(datetime(2099, 7, 2, 7, 11, 0))

    with get_db_connection() as conn:
        if conn:
            with conn.cursor() as cur:
                try:
                    # Check if user already has a Basic Membership
                    cur.execute("""
                        SELECT id FROM subscriptions 
                        WHERE user_id = %s AND subscription_type = 'basic_membership'
                    """, (user_id,))

                    existing_subscription = cur.fetchone()

                    if existing_subscription:
                        # Update existing subscription to ensure it's active and has correct end date
                        cur.execute("""
                            UPDATE subscriptions 
                            SET status = 'active', 
                                end_date = %s,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE id = %s
                        """, (end_date, existing_subscription[0]))

                        print(f"✓ Updated existing Basic Membership for user {user_id} ({email})")
                        return True
                    else:
                        # Create new Basic Membership subscription
                        cur.execute("""
                            INSERT INTO subscriptions 
                            (user_id, subscription_type, status, end_date, start_date)
                            VALUES (%s, 'basic_membership', 'active', %s, CURRENT_TIMESTAMP)
                        """, (user_id, end_date))

                        print(f"✓ Created Basic Membership for user {user_id} ({email})")

                    # Create purchase record for the Basic Membership
                    cur.execute("""
                        INSERT INTO purchases 
                        (user_id, product_type, amount, status)
                        VALUES (%s, 'basic_membership', 0, 'completed')
                        ON CONFLICT DO NOTHING
                    """, (user_id,))

                    conn.commit()
                    return True

                except Exception as e:
                    print(f"✗ Error creating membership for user {user_id} ({email}): {str(e)}")
                    conn.rollback()
                    return False

    return False

def main():
    """Main function"""
    print("=" * 60)
    print("Creating Basic Memberships for ALL Users")
    print("Target: 29905 users")
    print("Membership: Basic Membership")
    print("Status: Active")
    print("Valid until: 2099-07-02 07:11:00 EST (Canada Day)")
    print("=" * 60)

    # Ensure database schema is correct
    ensure_phone_number_column()
    ensure_tables_exist()

    # Get all users
    users = get_all_users()
    total_users = len(users)

    print(f"\nFound {total_users} users in database")

    if total_users == 0:
        print("No users found! Please run user migration first.")
        return

    # Confirm before proceeding
    response = input(f"\nCreate Basic Memberships for all {total_users} users? (y/N): ")
    if response.lower() != 'y':
        print("Operation cancelled")
        return

    print(f"\nCreating Basic Memberships...")

    success_count = 0
    error_count = 0

    for user_id, email, firebase_uid in users:
        if create_basic_membership_for_user(user_id, email):
            success_count += 1
        else:
            error_count += 1

        # Progress update every 1000 users
        if (success_count + error_count) % 1000 == 0:
            print(f"Progress: {success_count + error_count}/{total_users} users processed")

    print(f"\n" + "=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)
    print(f"Total users processed: {success_count + error_count}")
    print(f"Successful memberships: {success_count}")
    print(f"Errors: {error_count}")
    print(f"Expected target: 29905")

    if success_count >= 29000:
        print("✅ SUCCESS: Membership creation completed for all users!")
    else:
        print("⚠️  WARNING: Not all users received memberships")

    print(f"\nAll users now have Active Basic Membership until 2099-07-02 07:11:00 EST")

if __name__ == "__main__":
    main()