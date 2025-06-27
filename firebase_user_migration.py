
import os
import json
import firebase_admin
from firebase_admin import credentials, auth
from typing import List, Dict, Any
import time

class FirebaseUserMigration:
    def __init__(self):
        """Initialize Firebase Admin SDK for the target project"""
        try:
            # Check if Firebase credentials are set up
            if os.environ.get('FIREBASE_CREDENTIALS'):
                # Initialize with credentials from environment variable
                cred_json = json.loads(os.environ.get('FIREBASE_CREDENTIALS'))
                cred = credentials.Certificate(cred_json)
            else:
                # Look for credentials file
                cred_path = 'firebase-credentials.json'
                if os.path.exists(cred_path):
                    cred = credentials.Certificate(cred_path)
                else:
                    raise Exception("Firebase credentials not found")

            # Initialize the app for the target project
            if not firebase_admin._apps:
                firebase_admin.initialize_app(cred)
            
            print("Firebase Admin SDK initialized successfully for target project")
            
        except Exception as e:
            print(f"Error initializing Firebase Admin SDK: {str(e)}")
            raise

    def prepare_user_data(self, source_users: List[Dict]) -> List[auth.ImportUserRecord]:
        """Prepare user data for import with hash configuration"""
        import_users = []
        
        for user_data in source_users:
            try:
                # Convert timestamps from milliseconds to seconds if they exist
                creation_timestamp = None
                last_sign_in_timestamp = None
                
                if user_data.get('createdAt'):
                    creation_timestamp = user_data['createdAt'] / 1000
                if user_data.get('lastSignedInAt'):
                    last_sign_in_timestamp = user_data['lastSignedInAt'] / 1000
                
                # Create ImportUserRecord without password data (users will need to reset passwords)
                user_import = auth.ImportUserRecord(
                    uid=user_data.get('uid'),
                    email=user_data.get('email'),
                    email_verified=user_data.get('emailVerified', False),
                    display_name=user_data.get('displayName'),
                    photo_url=user_data.get('photoURL'),
                    phone_number=user_data.get('phoneNumber'),
                    disabled=user_data.get('disabled', False),
                    custom_claims=user_data.get('customClaims'),
                    provider_data=user_data.get('providerData', []),
                    user_metadata=auth.UserMetadata(
                        creation_timestamp=creation_timestamp,
                        last_sign_in_timestamp=last_sign_in_timestamp
                    ) if creation_timestamp or last_sign_in_timestamp else None
                )
                import_users.append(user_import)
                
            except Exception as e:
                print(f"Error preparing user {user_data.get('uid', 'unknown')}: {str(e)}")
                continue
                
        return import_users

    def import_users_batch(self, users: List[auth.ImportUserRecord], batch_number: int) -> Dict[str, Any]:
        """Import a batch of users without password data"""
        try:
            # Import the users without hash configuration (users will need to reset passwords)
            result = auth.import_users(users)
            
            print(f"Batch {batch_number} - Successfully imported {result.success_count} users")
            if result.failure_count > 0:
                print(f"Batch {batch_number} - Failed to import {result.failure_count} users")
                for error in result.errors:
                    print(f"  Error: {error.reason} for user index {error.index}")
            
            return {
                'batch_number': batch_number,
                'success_count': result.success_count,
                'failure_count': result.failure_count,
                'errors': [{'index': e.index, 'reason': e.reason} for e in result.errors]
            }
            
        except Exception as e:
            print(f"Error importing batch {batch_number}: {str(e)}")
            return {
                'batch_number': batch_number,
                'success_count': 0,
                'failure_count': len(users),
                'error': str(e)
            }

    def load_user_data_from_json(self, file_path: str) -> List[Dict]:
        """Load user data from JSON file exported from source Firebase project"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Handle different JSON structures
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and 'users' in data:
                return data['users']
            else:
                print("Warning: Unexpected JSON structure, treating as single user")
                return [data]
                
        except Exception as e:
            print(f"Error loading user data from {file_path}: {str(e)}")
            return []

    def migrate_users_from_files(self, base_file_pattern: str, total_batches: int = 36):
        """Migrate users from multiple JSON files"""
        total_imported = 0
        total_failed = 0
        results = []
        
        for batch_num in range(1, total_batches + 1):
            try:
                # Construct file path (adjust pattern as needed)
                file_path = base_file_pattern.format(batch_num)
                
                if not os.path.exists(file_path):
                    print(f"Warning: File {file_path} not found, skipping batch {batch_num}")
                    continue
                
                print(f"\nProcessing batch {batch_num} from {file_path}")
                
                # Load user data from file
                source_users = self.load_user_data_from_json(file_path)
                
                if not source_users:
                    print(f"No users found in {file_path}")
                    continue
                
                print(f"Loaded {len(source_users)} users from file")
                
                # Prepare users for import
                import_users = self.prepare_user_data(source_users)
                
                if not import_users:
                    print(f"No valid users to import from batch {batch_num}")
                    continue
                
                # Import the batch
                result = self.import_users_batch(import_users, batch_num)
                results.append(result)
                
                total_imported += result.get('success_count', 0)
                total_failed += result.get('failure_count', 0)
                
                # Add delay between batches to avoid rate limiting
                if batch_num < total_batches:
                    print("Waiting 2 seconds before next batch...")
                    time.sleep(2)
                    
            except Exception as e:
                print(f"Error processing batch {batch_num}: {str(e)}")
                continue
        
        # Print summary
        print(f"\n=== Migration Summary ===")
        print(f"Total users successfully imported: {total_imported}")
        print(f"Total users failed: {total_failed}")
        print(f"Batches processed: {len(results)}")
        
        return results

    def migrate_users_from_single_file(self, file_path: str, batch_size: int = 1000):
        """Migrate users from a single large JSON file, processing in batches"""
        try:
            print(f"Loading users from {file_path}")
            all_users = self.load_user_data_from_json(file_path)
            
            if not all_users:
                print("No users found in file")
                return []
            
            print(f"Total users to migrate: {len(all_users)}")
            
            results = []
            total_imported = 0
            total_failed = 0
            
            # Process in batches
            for i in range(0, len(all_users), batch_size):
                batch_num = (i // batch_size) + 1
                batch_users = all_users[i:i + batch_size]
                
                print(f"\nProcessing batch {batch_num} ({len(batch_users)} users)")
                
                # Prepare users for import
                import_users = self.prepare_user_data(batch_users)
                
                if not import_users:
                    print(f"No valid users to import from batch {batch_num}")
                    continue
                
                # Import the batch
                result = self.import_users_batch(import_users, batch_num)
                results.append(result)
                
                total_imported += result.get('success_count', 0)
                total_failed += result.get('failure_count', 0)
                
                # Add delay between batches
                if i + batch_size < len(all_users):
                    print("Waiting 2 seconds before next batch...")
                    time.sleep(2)
            
            # Print summary
            print(f"\n=== Migration Summary ===")
            print(f"Total users successfully imported: {total_imported}")
            print(f"Total users failed: {total_failed}")
            print(f"Batches processed: {len(results)}")
            
            return results
            
        except Exception as e:
            print(f"Error in migration: {str(e)}")
            return []

def main():
    """Main function to run the migration"""
    try:
        migrator = FirebaseUserMigration()
        
        # Option 1: Migrate from multiple files (36 files with 1000 users each)
        # Adjust the file pattern to match your exported files
        # Example: "exported_users_batch_{}.json" will look for exported_users_batch_1.json, exported_users_batch_2.json, etc.
        print("Choose migration method:")
        print("1. Multiple files (batch_1.json, batch_2.json, etc.)")
        print("2. Single large file")
        
        choice = input("Enter choice (1 or 2): ").strip()
        
        if choice == "1":
            file_pattern = input("Enter file pattern (e.g., 'users_batch_{}.json'): ").strip()
            if not file_pattern:
                file_pattern = "users_batch_{}.json"
            
            total_batches = int(input("Enter total number of batches (default 36): ").strip() or "36")
            
            results = migrator.migrate_users_from_files(file_pattern, total_batches)
            
        elif choice == "2":
            file_path = input("Enter file path (e.g., 'all_users.json'): ").strip()
            if not file_path:
                file_path = "all_users.json"
            
            batch_size = int(input("Enter batch size (default 1000): ").strip() or "1000")
            
            results = migrator.migrate_users_from_single_file(file_path, batch_size)
            
        else:
            print("Invalid choice")
            return
        
        # Save results to file
        with open('migration_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\nMigration completed! Results saved to migration_results.json")
        
    except Exception as e:
        print(f"Migration failed: {str(e)}")

if __name__ == "__main__":
    main()
