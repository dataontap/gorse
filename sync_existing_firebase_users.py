
#!/usr/bin/env python3
"""
Script to sync existing Firebase users to the PostgreSQL database
This handles users who exist in Firebase but not in the database
"""

import os
import json
import psycopg2
import firebase_admin
from firebase_admin import credentials, auth
from datetime import datetime
import time

def init_firebase():
    """Initialize Firebase Admin SDK"""
    try:
        if os.environ.get('FIREBASE_CREDENTIALS'):
            cred_json = json.loads(os.environ.get('FIREBASE_CREDENTIALS'))
            cred = credentials.Certificate(cred_json)
        else:
            cred_path = 'firebase-credentials.json'
            if os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
            else:
                raise Exception("Firebase credentials not found")

        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)
        
        print("Firebase Admin SDK initialized successfully")
        return True
    except Exception as e:
        print(f"Error initializing Firebase: {str(e)}")
        return False

def get_database_connection():
    """Get database connection"""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL not set")
    return psycopg2.connect(database_url)

def get_existing_firebase_uids_in_db():
    """Get all Firebase UIDs that already exist in database"""
    conn = get_database_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT firebase_uid FROM users WHERE firebase_uid IS NOT NULL")
            return {row[0] for row in cur.fetchall()}
    finally:
        conn.close()

def get_missing_uids_from_file():
    """Get missing UIDs from the retry file"""
    retry_file = "retry_users_batch_20250701_082727.json"
    
    if not os.path.exists(retry_file):
        print(f"Retry file {retry_file} not found")
        return []
    
    with open(retry_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    users = data.get('users', [])
    return [user['uid'] for user in users if user.get('uid')]

def sync_firebase_user_to_db(firebase_user, cursor):
    """Sync a single Firebase user to the database"""
    try:
        # Check if user already exists in database
        cursor.execute("SELECT id FROM users WHERE firebase_uid = %s", (firebase_user.uid,))
        existing = cursor.fetchone()
        
        if existing:
            print(f"User {firebase_user.uid} already exists in database, skipping")
            return False
        
        # Insert new user
        cursor.execute("""
            INSERT INTO users (
                firebase_uid, 
                email, 
                display_name, 
                email_verified, 
                phone_number, 
                photo_url,
                disabled,
                created_at,
                updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            firebase_user.uid,
            firebase_user.email,
            firebase_user.display_name,
            firebase_user.email_verified,
            firebase_user.phone_number,
            firebase_user.photo_url,
            firebase_user.disabled,
            datetime.now(),
            datetime.now()
        ))
        
        user_id = cursor.fetchone()[0]
        print(f"✓ Synced user {firebase_user.uid} ({firebase_user.email}) to database as user_id {user_id}")
        return True
        
    except Exception as e:
        print(f"✗ Error syncing user {firebase_user.uid}: {str(e)}")
        return False

def sync_missing_users():
    """Sync missing Firebase users to database"""
    if not init_firebase():
        return
    
    print("Getting missing UIDs from retry file...")
    missing_uids = get_missing_uids_from_file()
    
    if not missing_uids:
        print("No missing UIDs found in retry file")
        return
    
    print(f"Found {len(missing_uids)} missing UIDs to sync")
    
    # Get existing UIDs in database
    print("Checking existing UIDs in database...")
    existing_db_uids = get_existing_firebase_uids_in_db()
    
    # Filter out UIDs that already exist in database
    uids_to_sync = [uid for uid in missing_uids if uid not in existing_db_uids]
    
    print(f"UIDs to sync: {len(uids_to_sync)} (filtered out {len(missing_uids) - len(uids_to_sync)} already in DB)")
    
    if not uids_to_sync:
        print("All users are already synced!")
        return
    
    # Sync users in batches
    conn = get_database_connection()
    synced_count = 0
    failed_count = 0
    
    try:
        with conn.cursor() as cursor:
            for i, uid in enumerate(uids_to_sync):
                try:
                    # Get user from Firebase
                    firebase_user = auth.get_user(uid)
                    
                    # Sync to database
                    if sync_firebase_user_to_db(firebase_user, cursor):
                        synced_count += 1
                    else:
                        failed_count += 1
                    
                    # Commit every 10 users
                    if (i + 1) % 10 == 0:
                        conn.commit()
                        print(f"Progress: {i + 1}/{len(uids_to_sync)} users processed")
                    
                    # Rate limiting
                    if (i + 1) % 100 == 0:
                        print("Pausing for rate limiting...")
                        time.sleep(1)
                        
                except auth.UserNotFoundError:
                    print(f"✗ User {uid} not found in Firebase")
                    failed_count += 1
                except Exception as e:
                    print(f"✗ Error processing user {uid}: {str(e)}")
                    failed_count += 1
            
            # Final commit
            conn.commit()
            
    finally:
        conn.close()
    
    print(f"\n=== Sync Summary ===")
    print(f"Total UIDs to sync: {len(uids_to_sync)}")
    print(f"Successfully synced: {synced_count}")
    print(f"Failed: {failed_count}")
    print(f"Success rate: {(synced_count / len(uids_to_sync) * 100):.1f}%")

def main():
    """Main function"""
    print("=" * 60)
    print("SYNCING EXISTING FIREBASE USERS TO DATABASE")
    print("=" * 60)
    
    sync_missing_users()

if __name__ == "__main__":
    main()
