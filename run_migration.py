
#!/usr/bin/env python3
"""
Simple script to run Firebase user migration
Run this 36 times for 36 batches of 1000 users each
"""

from firebase_user_migration import FirebaseUserMigration
import sys

def run_single_batch(batch_number: int, file_path: str = None):
    """Run migration for a single batch"""
    try:
        migrator = FirebaseUserMigration()
        
        # If no file path provided, use default pattern
        if not file_path:
            file_path = f"users_batch_{batch_number}.json"
        
        print(f"Starting migration for batch {batch_number}")
        print(f"Loading from: {file_path}")
        
        # Load and migrate users from the specific batch file
        results = migrator.migrate_users_from_single_file(file_path)
        
        if results:
            result = results[0]
            print(f"Batch {batch_number} completed:")
            print(f"  Success: {result.get('success_count', 0)} users")
            print(f"  Failed: {result.get('failure_count', 0)} users")
        else:
            print(f"Batch {batch_number} failed - no results")
            
    except Exception as e:
        print(f"Error running batch {batch_number}: {str(e)}")

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python run_migration.py <batch_number> [file_path]")
        print("Example: python run_migration.py 1")
        print("Example: python run_migration.py 5 custom_batch_5.json")
        sys.exit(1)
    
    try:
        batch_number = int(sys.argv[1])
        file_path = sys.argv[2] if len(sys.argv) > 2 else None
        
        run_single_batch(batch_number, file_path)
        
    except ValueError:
        print("Error: Batch number must be an integer")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
