
#!/usr/bin/env python3
"""
Script to check for duplicates between import files and current Firebase users
"""

import os
import json
import firebase_admin
from firebase_admin import credentials, auth
from collections import defaultdict
from typing import Dict, List, Set

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

def get_all_firebase_users() -> Dict[str, Dict]:
    """Get all users currently in Firebase"""
    firebase_users = {}
    
    try:
        page_token = None
        while True:
            if page_token:
                page = auth.list_users(page_token=page_token)
            else:
                page = auth.list_users()
            
            for user in page.users:
                firebase_users[user.uid] = {
                    'uid': user.uid,
                    'email': user.email,
                    'display_name': user.display_name,
                    'created_at': user.user_metadata.creation_timestamp if user.user_metadata else None
                }
            
            if not page.has_next_page:
                break
            page_token = page.next_page_token
        
        print(f"Found {len(firebase_users)} users in Firebase")
        return firebase_users
        
    except Exception as e:
        print(f"Error getting Firebase users: {str(e)}")
        return {}

def get_all_import_file_users() -> Dict[str, Dict]:
    """Get all users from import batch files"""
    import_users = {}
    uid_duplicates = defaultdict(list)
    email_duplicates = defaultdict(list)
    
    for i in range(1, 40):  # Check batches 1-39
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
            
            print(f"Processing {filename}: {len(users)} users")
            
            for user in users:
                uid = user.get('uid')
                email = user.get('email')
                
                if not uid or not email:
                    continue
                
                # Track duplicates by UID
                if uid in import_users:
                    uid_duplicates[uid].append({
                        'existing_batch': import_users[uid]['batch_file'],
                        'duplicate_batch': filename,
                        'email': email
                    })
                else:
                    import_users[uid] = {
                        'uid': uid,
                        'email': email,
                        'batch_file': filename,
                        'batch_number': i,
                        'user_data': user
                    }
                
                # Track duplicates by email
                for existing_uid, existing_user in import_users.items():
                    if existing_uid != uid and existing_user['email'] == email:
                        email_duplicates[email].append({
                            'uid1': existing_uid,
                            'batch1': existing_user['batch_file'],
                            'uid2': uid,
                            'batch2': filename
                        })
                        
        except Exception as e:
            print(f"Error reading {filename}: {str(e)}")
            continue
    
    print(f"Found {len(import_users)} unique users in import files")
    return import_users, uid_duplicates, email_duplicates

def check_firebase_vs_import_duplicates(firebase_users: Dict, import_users: Dict) -> Dict:
    """Check for duplicates between Firebase and import files"""
    duplicates = {
        'uid_duplicates': [],
        'email_duplicates': []
    }
    
    for uid, import_user in import_users.items():
        # Check UID duplicates
        if uid in firebase_users:
            duplicates['uid_duplicates'].append({
                'uid': uid,
                'firebase_email': firebase_users[uid]['email'],
                'import_email': import_user['email'],
                'import_batch': import_user['batch_file']
            })
        
        # Check email duplicates
        import_email = import_user['email']
        for fb_uid, fb_user in firebase_users.items():
            if fb_user['email'] == import_email and fb_uid != uid:
                duplicates['email_duplicates'].append({
                    'email': import_email,
                    'firebase_uid': fb_uid,
                    'import_uid': uid,
                    'import_batch': import_user['batch_file']
                })
    
    return duplicates

def main():
    """Main function to check for duplicates"""
    print("=" * 60)
    print("DUPLICATE DETECTION ANALYSIS")
    print("=" * 60)
    
    # Initialize Firebase
    if not init_firebase():
        return
    
    # Get all Firebase users
    print("\n1. Getting current Firebase users...")
    firebase_users = get_all_firebase_users()
    
    # Get all import file users
    print("\n2. Getting users from import files...")
    import_users, uid_duplicates, email_duplicates = get_all_import_file_users()
    
    # Check for duplicates between Firebase and import files
    print("\n3. Checking for duplicates between Firebase and import files...")
    fb_import_duplicates = check_firebase_vs_import_duplicates(firebase_users, import_users)
    
    # Generate report
    print("\n" + "=" * 60)
    print("DUPLICATE ANALYSIS REPORT")
    print("=" * 60)
    
    print(f"Total users in Firebase: {len(firebase_users):,}")
    print(f"Total unique users in import files: {len(import_users):,}")
    
    # Report UID duplicates within import files
    print(f"\nUID DUPLICATES WITHIN IMPORT FILES: {len(uid_duplicates)}")
    if uid_duplicates:
        for uid, dups in uid_duplicates.items():
            for dup in dups:
                print(f"  UID {uid}: {dup['existing_batch']} vs {dup['duplicate_batch']} (email: {dup['email']})")
    
    # Report email duplicates within import files
    print(f"\nEMAIL DUPLICATES WITHIN IMPORT FILES: {len(email_duplicates)}")
    if email_duplicates:
        for email, dups in email_duplicates.items():
            for dup in dups:
                print(f"  Email {email}: {dup['uid1']} ({dup['batch1']}) vs {dup['uid2']} ({dup['batch2']})")
    
    # Report UID duplicates between Firebase and import files
    print(f"\nUID DUPLICATES (Firebase vs Import): {len(fb_import_duplicates['uid_duplicates'])}")
    if fb_import_duplicates['uid_duplicates']:
        for dup in fb_import_duplicates['uid_duplicates']:
            print(f"  UID {dup['uid']}: Firebase({dup['firebase_email']}) vs Import({dup['import_email']}) from {dup['import_batch']}")
    
    # Report email duplicates between Firebase and import files
    print(f"\nEMAIL DUPLICATES (Firebase vs Import): {len(fb_import_duplicates['email_duplicates'])}")
    if fb_import_duplicates['email_duplicates']:
        for dup in fb_import_duplicates['email_duplicates']:
            print(f"  Email {dup['email']}: Firebase UID({dup['firebase_uid']}) vs Import UID({dup['import_uid']}) from {dup['import_batch']}")
    
    # Calculate potential explanation for user count difference
    firebase_only = len(firebase_users) - len(import_users)
    if firebase_only > 0:
        print(f"\nUsers in Firebase but not in import files: {firebase_only:,}")
        print("This could explain why Firebase has more users than expected.")
    
    # Save detailed report
    report = {
        'firebase_user_count': len(firebase_users),
        'import_user_count': len(import_users),
        'uid_duplicates_in_imports': dict(uid_duplicates),
        'email_duplicates_in_imports': dict(email_duplicates),
        'firebase_vs_import_duplicates': fb_import_duplicates,
        'users_in_firebase_not_in_imports': firebase_only
    }
    
    with open('duplicate_analysis_report.json', 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\nDetailed report saved to: duplicate_analysis_report.json")

if __name__ == "__main__":
    main()
