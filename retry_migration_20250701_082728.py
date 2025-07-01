#!/usr/bin/env python3
"""
Retry migration script for missing users
Generated on 2025-07-01T08:27:28.206784
"""

from firebase_user_migration import FirebaseUserMigration
import json

def retry_missing_users():
    """Retry migration for users that didn't make it to the database"""
    retry_file = "retry_users_batch_20250701_082727.json"
    
    print(f"Starting retry migration from: {retry_file}")
    
    try:
        # Load retry data
        with open(retry_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        users = data.get('users', [])
        print(f"Found {len(users)} users to retry")
        
        if not users:
            print("No users to retry!")
            return
        
        # Initialize migrator
        migrator = FirebaseUserMigration()
        
        # Prepare users for import
        import_users = migrator.prepare_user_data(users)
        print(f"Prepared {len(import_users)} users for import")
        
        # Import in smaller batches to avoid issues
        batch_size = 100
        total_success = 0
        total_failed = 0
        
        for i in range(0, len(import_users), batch_size):
            batch_users = import_users[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            
            print(f"\nProcessing retry batch {batch_num} ({len(batch_users)} users)")
            
            result = migrator.import_users_batch(batch_users, f"retry_{batch_num}")
            
            success_count = result.get('success_count', 0)
            failure_count = result.get('failure_count', 0)
            
            total_success += success_count
            total_failed += failure_count
            
            print(f"Retry batch {batch_num} completed:")
            print(f"  Success: {success_count} users")
            print(f"  Failed: {failure_count} users")
            
            # Show errors if any
            errors = result.get('errors', [])
            if errors:
                print(f"  Errors in batch {batch_num}:")
                for error in errors[:5]:  # Show first 5 errors
                    print(f"    Index {error['index']}: {error['reason']}")
        
        print(f"\n=== Retry Migration Summary ===")
        print(f"Total users retried: {len(import_users)}")
        print(f"Successfully imported: {total_success}")
        print(f"Failed: {total_failed}")
        print(f"Success rate: {(total_success / len(import_users) * 100):.1f}%")
        
    except Exception as e:
        print(f"Error in retry migration: {str(e)}")

if __name__ == "__main__":
    retry_missing_users()
