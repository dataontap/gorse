
#!/usr/bin/env python3
"""
One-time script to populate the founders table with all existing users
All current users will be marked as founding members (Y)
"""

import os
import psycopg2
from psycopg2.pool import SimpleConnectionPool
from contextlib import contextmanager
from datetime import datetime

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

def create_founders_table():
    """Create the founders table if it doesn't exist"""
    try:
        with get_db_connection() as conn:
            if conn:
                with conn.cursor() as cur:
                    # Read and execute the SQL file
                    with open('create_founders_table.sql', 'r') as f:
                        sql_script = f.read()
                    
                    cur.execute(sql_script)
                    conn.commit()
                    print("✓ Founders table created successfully")
                    return True
    except Exception as e:
        print(f"✗ Error creating founders table: {str(e)}")
        return False

def populate_founders_table():
    """Populate founders table with all existing users marked as founders"""
    try:
        with get_db_connection() as conn:
            if conn:
                with conn.cursor() as cur:
                    # Get all existing users
                    cur.execute("""
                        SELECT id, firebase_uid, email, display_name 
                        FROM users 
                        WHERE firebase_uid IS NOT NULL
                        ORDER BY created_at ASC
                    """)
                    
                    users = cur.fetchall()
                    print(f"Found {len(users)} users to mark as founding members")
                    
                    if not users:
                        print("No users found in database")
                        return False
                    
                    # Insert all users as founding members
                    success_count = 0
                    error_count = 0
                    
                    for user in users:
                        user_id, firebase_uid, email, display_name = user
                        
                        try:
                            # Check if already exists
                            cur.execute("""
                                SELECT id FROM founders 
                                WHERE firebase_uid = %s
                            """, (firebase_uid,))
                            
                            if cur.fetchone():
                                print(f"⚠ User {email} already in founders table, skipping")
                                continue
                            
                            # Insert as founding member
                            cur.execute("""
                                INSERT INTO founders (user_id, firebase_uid, founder)
                                VALUES (%s, %s, 'Y')
                            """, (user_id, firebase_uid))
                            
                            success_count += 1
                            print(f"✓ Added founding member: {email} ({display_name or 'No name'})")
                            
                        except Exception as e:
                            error_count += 1
                            print(f"✗ Error adding user {email}: {str(e)}")
                            continue
                    
                    conn.commit()
                    
                    print(f"\n" + "=" * 60)
                    print("FOUNDERS TABLE POPULATION COMPLETE")
                    print("=" * 60)
                    print(f"Total users processed: {len(users)}")
                    print(f"Successfully added: {success_count}")
                    print(f"Errors: {error_count}")
                    print(f"All added users are marked as Founding Members (Y)")
                    
                    return True
                    
    except Exception as e:
        print(f"✗ Error populating founders table: {str(e)}")
        return False

def verify_founders_table():
    """Verify the founders table was populated correctly"""
    try:
        with get_db_connection() as conn:
            if conn:
                with conn.cursor() as cur:
                    # Count total founders
                    cur.execute("SELECT COUNT(*) FROM founders WHERE founder = 'Y'")
                    founder_count = cur.fetchone()[0]
                    
                    # Count total users
                    cur.execute("SELECT COUNT(*) FROM users WHERE firebase_uid IS NOT NULL")
                    user_count = cur.fetchone()[0]
                    
                    print(f"\nVerification Results:")
                    print(f"Users in database: {user_count}")
                    print(f"Founding members: {founder_count}")
                    
                    if founder_count == user_count:
                        print("✓ All users successfully marked as founding members")
                    else:
                        print("⚠ Mismatch between user count and founder count")
                    
                    # Show sample of founders
                    cur.execute("""
                        SELECT u.email, u.display_name, f.founder, f.created_at
                        FROM founders f
                        JOIN users u ON f.user_id = u.id
                        ORDER BY f.created_at ASC
                        LIMIT 5
                    """)
                    
                    sample_founders = cur.fetchall()
                    print(f"\nFirst 5 founding members:")
                    for founder in sample_founders:
                        email, name, status, created = founder
                        print(f"  {email} ({name or 'No name'}) - Status: {status} - Added: {created}")
                    
                    return True
    except Exception as e:
        print(f"✗ Error verifying founders table: {str(e)}")
        return False

def main():
    """Main function"""
    print("=" * 60)
    print("FOUNDING MEMBERS TABLE SETUP")
    print("=" * 60)
    print("This script will:")
    print("1. Create the founders table")
    print("2. Mark all existing users as founding members (Y)")
    print("3. Verify the setup")
    print("=" * 60)
    
    response = input("Continue? (y/N): ")
    if response.lower() != 'y':
        print("Setup cancelled")
        return
    
    # Step 1: Create table
    print("\nStep 1: Creating founders table...")
    if not create_founders_table():
        print("Failed to create founders table")
        return
    
    # Step 2: Populate table
    print("\nStep 2: Populating founders table...")
    if not populate_founders_table():
        print("Failed to populate founders table")
        return
    
    # Step 3: Verify
    print("\nStep 3: Verifying setup...")
    verify_founders_table()
    
    print(f"\n" + "=" * 60)
    print("FOUNDING MEMBERS SETUP COMPLETE!")
    print("=" * 60)
    print("All existing users have been marked as Founding Members.")
    print("Future users will need to be manually added to founders table")
    print("if they should have founding member status.")

if __name__ == "__main__":
    main()
