
#!/usr/bin/env python3
"""
Script to identify exactly which users didn't make it to the database
and create a retry migration for those specific users
"""

import os
import json
import psycopg2
from datetime import datetime
from typing import List, Dict, Set

def get_database_connection():
    """Get database connection"""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL not set")
    return psycopg2.connect(database_url)

def get_all_firebase_uids_from_database() -> Set[str]:
    """Get all Firebase UIDs currently in the database"""
    conn = get_database_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT firebase_uid FROM users WHERE firebase_uid IS NOT NULL")
            results = cur.fetchall()
            return {row[0] for row in results}
    finally:
        conn.close()

def get_all_uids_from_batch_files() -> Dict[str, Dict]:
    """Get all UIDs from batch files with their user data"""
    all_users = {}
    
    for i in range(1, 40):  # Batches 1-39
        filename = f"users_batch_{i}.json"
        if not os.path.exists(filename):
            continue
            
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle different JSON structures
            if isinstance(data, list):
                users = data
            elif isinstance(data, dict) and 'users' in data:
                users = data['users']
            else:
                users = [data] if data else []
            
            for user in users:
                uid = user.get('uid')
                email = user.get('email')
                
                # Only include users with valid data
                if uid and email and user.get('createdAt'):
                    all_users[uid] = {
                        'uid': uid,
                        'email': email,
                        'batch_file': filename,
                        'batch_number': i,
                        'user_data': user
                    }
                    
        except Exception as e:
            print(f"Error reading {filename}: {str(e)}")
            continue
    
    return all_users

def identify_missing_users():
    """Identify which users are missing from the database"""
    print("Identifying missing users...")
    
    # Get all UIDs from database
    db_uids = get_all_firebase_uids_from_database()
    print(f"Found {len(db_uids)} users in database")
    
    # Get all UIDs from batch files
    batch_users = get_all_uids_from_batch_files()
    print(f"Found {len(batch_users)} valid users in batch files")
    
    # Find missing users
    missing_uids = set(batch_users.keys()) - db_uids
    missing_users = [batch_users[uid] for uid in missing_uids]
    
    print(f"\nMissing users: {len(missing_users)}")
    
    # Group by batch file for analysis
    missing_by_batch = {}
    for user in missing_users:
        batch = user['batch_number']
        if batch not in missing_by_batch:
            missing_by_batch[batch] = []
        missing_by_batch[batch].append(user)
    
    print("\nMissing users by batch:")
    for batch in sorted(missing_by_batch.keys()):
        print(f"Batch {batch}: {len(missing_by_batch[batch])} missing users")
    
    return missing_users, missing_by_batch

def save_missing_users_data(missing_users: List[Dict]):
    """Save missing users data to files for retry"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save detailed missing users list
    missing_file = f"missing_users_{timestamp}.json"
    with open(missing_file, 'w', encoding='utf-8') as f:
        json.dump(missing_users, f, indent=2, ensure_ascii=False)
    
    print(f"Saved detailed missing users to: {missing_file}")
    
    # Save just the UIDs for quick reference
    uids_file = f"missing_uids_{timestamp}.txt"
    with open(uids_file, 'w') as f:
        for user in missing_users:
            f.write(f"{user['uid']}\n")
    
    print(f"Saved missing UIDs list to: {uids_file}")
    
    # Create retry batch file with full user data
    retry_batch_file = f"retry_users_batch_{timestamp}.json"
    retry_users = []
    
    for user in missing_users:
        retry_users.append(user['user_data'])
    
    retry_data = {"users": retry_users}
    
    with open(retry_batch_file, 'w', encoding='utf-8') as f:
        json.dump(retry_data, f, indent=2, ensure_ascii=False)
    
    print(f"Saved retry batch file to: {retry_batch_file}")
    
    return missing_file, uids_file, retry_batch_file

def create_retry_migration_script(retry_batch_file: str):
    """Create a script to retry migration for missing users"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    retry_script = f"retry_migration_{timestamp}.py"
    
    script_content = f'''#!/usr/bin/env python3
"""
Retry migration script for missing users
Generated on {datetime.now().isoformat()}
"""

from firebase_user_migration import FirebaseUserMigration
import json

def retry_missing_users():
    """Retry migration for users that didn't make it to the database"""
    retry_file = "{retry_batch_file}"
    
    print(f"Starting retry migration from: {{retry_file}}")
    
    try:
        # Load retry data
        with open(retry_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        users = data.get('users', [])
        print(f"Found {{len(users)}} users to retry")
        
        if not users:
            print("No users to retry!")
            return
        
        # Initialize migrator
        migrator = FirebaseUserMigration()
        
        # Prepare users for import
        import_users = migrator.prepare_user_data(users)
        print(f"Prepared {{len(import_users)}} users for import")
        
        # Import in smaller batches to avoid issues
        batch_size = 100
        total_success = 0
        total_failed = 0
        
        for i in range(0, len(import_users), batch_size):
            batch_users = import_users[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            
            print(f"\\nProcessing retry batch {{batch_num}} ({{len(batch_users)}} users)")
            
            result = migrator.import_users_batch(batch_users, f"retry_{{batch_num}}")
            
            success_count = result.get('success_count', 0)
            failure_count = result.get('failure_count', 0)
            
            total_success += success_count
            total_failed += failure_count
            
            print(f"Retry batch {{batch_num}} completed:")
            print(f"  Success: {{success_count}} users")
            print(f"  Failed: {{failure_count}} users")
            
            # Show errors if any
            errors = result.get('errors', [])
            if errors:
                print(f"  Errors in batch {{batch_num}}:")
                for error in errors[:5]:  # Show first 5 errors
                    print(f"    Index {{error['index']}}: {{error['reason']}}")
        
        print(f"\\n=== Retry Migration Summary ===")
        print(f"Total users retried: {{len(import_users)}}")
        print(f"Successfully imported: {{total_success}}")
        print(f"Failed: {{total_failed}}")
        print(f"Success rate: {{(total_success / len(import_users) * 100):.1f}}%")
        
    except Exception as e:
        print(f"Error in retry migration: {{str(e)}}")

if __name__ == "__main__":
    retry_missing_users()
'''
    
    with open(retry_script, 'w') as f:
        f.write(script_content)
    
    # Make script executable
    os.chmod(retry_script, 0o755)
    
    print(f"Created retry migration script: {retry_script}")
    return retry_script

def main():
    """Main function"""
    print("=" * 60)
    print("IDENTIFYING MISSING USERS FROM MIGRATION")
    print("=" * 60)
    
    try:
        # Identify missing users
        missing_users, missing_by_batch = identify_missing_users()
        
        if not missing_users:
            print("✓ No missing users found! All users successfully migrated.")
            return
        
        # Save missing users data
        missing_file, uids_file, retry_batch_file = save_missing_users_data(missing_users)
        
        # Create retry script
        retry_script = create_retry_migration_script(retry_batch_file)
        
        print(f"\n" + "=" * 60)
        print("ANALYSIS COMPLETE")
        print("=" * 60)
        print(f"Missing users identified: {len(missing_users)}")
        print(f"Files created:")
        print(f"  - {missing_file} (detailed missing users)")
        print(f"  - {uids_file} (UIDs only)")
        print(f"  - {retry_batch_file} (retry batch data)")
        print(f"  - {retry_script} (retry migration script)")
        
        print(f"\nTo retry migration, run:")
        print(f"  python {retry_script}")
        
        # Show some sample missing UIDs
        print(f"\nSample missing UIDs:")
        for i, user in enumerate(missing_users[:10]):
            print(f"  {user['uid']} ({user['email']}) - from {user['batch_file']}")
        
        if len(missing_users) > 10:
            print(f"  ... and {len(missing_users) - 10} more")
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
