
#!/usr/bin/env python3
"""
Script to export Firebase users from source project and split them into batch files
Run this BEFORE running the migration
"""

import os
import json
import firebase_admin
from firebase_admin import credentials, auth
from typing import List, Dict, Any

class FirebaseUserExporter:
    def __init__(self, source_credentials_path: str):
        """Initialize Firebase Admin SDK for the SOURCE project"""
        try:
            # Initialize with source project credentials
            cred = credentials.Certificate(source_credentials_path)
            self.app = firebase_admin.initialize_app(cred, name='source_project')
            print("Firebase Admin SDK initialized for source project")
        except Exception as e:
            print(f"Error initializing Firebase Admin SDK: {str(e)}")
            raise

    def export_all_users(self, batch_size: int = 1000) -> None:
        """Export all users from Firebase and save to batch files"""
        try:
            print("Starting user export...")
            
            all_users = []
            page_token = None
            batch_number = 1
            
            while True:
                # List users with pagination
                if page_token:
                    page = auth.list_users(page_token=page_token, app=self.app)
                else:
                    page = auth.list_users(app=self.app)
                
                # Convert users to export format
                for user in page.users:
                    user_data = self.convert_user_to_export_format(user)
                    all_users.append(user_data)
                    
                    # Save batch when we reach batch_size
                    if len(all_users) >= batch_size:
                        self.save_batch_file(all_users, batch_number)
                        print(f"Saved batch {batch_number} with {len(all_users)} users")
                        all_users = []
                        batch_number += 1
                
                # Check if there are more users
                if not page.has_next_page:
                    break
                page_token = page.next_page_token
            
            # Save remaining users if any
            if all_users:
                self.save_batch_file(all_users, batch_number)
                print(f"Saved final batch {batch_number} with {len(all_users)} users")
            
            print(f"Export completed! Created {batch_number} batch files")
            
        except Exception as e:
            print(f"Error exporting users: {str(e)}")
            raise

    def convert_user_to_export_format(self, user) -> Dict[str, Any]:
        """Convert Firebase UserRecord to export format"""
        user_data = {
            'uid': user.uid,
            'email': user.email,
            'emailVerified': user.email_verified,
            'displayName': user.display_name,
            'photoURL': user.photo_url,
            'phoneNumber': user.phone_number,
            'disabled': user.disabled,
            'customClaims': user.custom_claims or {},
            'providerData': []
        }
        
        # Add provider data
        for provider in user.provider_data:
            user_data['providerData'].append({
                'uid': provider.uid,
                'email': provider.email,
                'displayName': provider.display_name,
                'photoURL': provider.photo_url,
                'phoneNumber': provider.phone_number,
                'providerId': provider.provider_id
            })
        
        # Add metadata timestamps
        if user.user_metadata:
            if user.user_metadata.creation_timestamp:
                user_data['createdAt'] = int(user.user_metadata.creation_timestamp.timestamp() * 1000)
            if user.user_metadata.last_sign_in_timestamp:
                user_data['lastSignedInAt'] = int(user.user_metadata.last_sign_in_timestamp.timestamp() * 1000)
        
        # Note: Password hashes and salts cannot be exported from Firebase
        # Users will need to reset their passwords after migration
        # You would need these from a database backup if available
        
        return user_data

    def save_batch_file(self, users: List[Dict], batch_number: int) -> None:
        """Save users to a batch file"""
        filename = f"users_batch_{batch_number}.json"
        batch_data = {
            "users": users,
            "batch_number": batch_number,
            "total_users": len(users)
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(batch_data, f, indent=2, ensure_ascii=False)

def main():
    """Main function"""
    print("Firebase User Exporter")
    print("======================")
    
    # You need to provide the path to your SOURCE Firebase project credentials
    source_creds = input("Enter path to source Firebase credentials JSON file: ").strip()
    
    if not os.path.exists(source_creds):
        print(f"Error: Credentials file not found: {source_creds}")
        return
    
    batch_size = int(input("Enter batch size (default 1000): ").strip() or "1000")
    
    try:
        exporter = FirebaseUserExporter(source_creds)
        exporter.export_all_users(batch_size)
        
    except Exception as e:
        print(f"Export failed: {str(e)}")

if __name__ == "__main__":
    main()
