
#!/usr/bin/env python3
"""
Script to analyze the gap between expected and actual migrated users
"""

import os
import json
from datetime import datetime

def analyze_batch_files():
    """Analyze all batch files to understand the user count discrepancy"""
    
    total_users_in_files = 0
    valid_users = 0
    invalid_users = 0
    duplicate_uids = set()
    duplicate_emails = set()
    users_missing_required_fields = 0
    
    batch_summary = []
    all_uids = set()
    all_emails = set()
    
    print("Analyzing batch files...")
    print("=" * 60)
    
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
            
            batch_valid = 0
            batch_invalid = 0
            batch_duplicates = 0
            batch_missing_fields = 0
            
            for user in users:
                total_users_in_files += 1
                
                uid = user.get('uid')
                email = user.get('email')
                
                # Check for missing required fields
                if not uid or not email:
                    batch_missing_fields += 1
                    users_missing_required_fields += 1
                    continue
                
                # Check for duplicates
                if uid in all_uids:
                    duplicate_uids.add(uid)
                    batch_duplicates += 1
                    continue
                    
                if email in all_emails:
                    duplicate_emails.add(email)
                    batch_duplicates += 1
                    continue
                
                # Check for valid creation timestamp
                if user.get('createdAt'):
                    batch_valid += 1
                    valid_users += 1
                    all_uids.add(uid)
                    all_emails.add(email)
                else:
                    batch_invalid += 1
                    invalid_users += 1
            
            batch_info = {
                'batch': i,
                'total': len(users),
                'valid': batch_valid,
                'invalid': batch_invalid,
                'duplicates': batch_duplicates,
                'missing_fields': batch_missing_fields
            }
            batch_summary.append(batch_info)
            
            print(f"Batch {i:2d}: {len(users):4d} total, {batch_valid:4d} valid, {batch_invalid:2d} invalid, {batch_duplicates:2d} dupes, {batch_missing_fields:2d} missing fields")
            
        except Exception as e:
            print(f"Error reading {filename}: {str(e)}")
            continue
    
    print("\n" + "=" * 60)
    print("ANALYSIS SUMMARY")
    print("=" * 60)
    print(f"Total users in batch files: {total_users_in_files:,}")
    print(f"Valid users for migration: {valid_users:,}")
    print(f"Invalid users (no createdAt): {invalid_users:,}")
    print(f"Users missing UID/email: {users_missing_required_fields:,}")
    print(f"Duplicate UIDs found: {len(duplicate_uids):,}")
    print(f"Duplicate emails found: {len(duplicate_emails):,}")
    
    total_excluded = invalid_users + users_missing_required_fields + len(duplicate_uids) + len(duplicate_emails)
    print(f"Total excluded from migration: {total_excluded:,}")
    print(f"Expected migrated users: {valid_users:,}")
    
    # Show some examples of problematic users
    if duplicate_uids:
        print(f"\nExample duplicate UIDs: {list(duplicate_uids)[:5]}")
    if duplicate_emails:
        print(f"Example duplicate emails: {list(duplicate_emails)[:5]}")
    
    return {
        'total_in_files': total_users_in_files,
        'valid_users': valid_users,
        'invalid_users': invalid_users,
        'missing_fields': users_missing_required_fields,
        'duplicate_uids': len(duplicate_uids),
        'duplicate_emails': len(duplicate_emails),
        'batch_summary': batch_summary
    }

def check_database_count():
    """Check how many users are actually in the database"""
    try:
        import psycopg2
        from contextlib import contextmanager
        
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            print("DATABASE_URL not set - cannot check database count")
            return None
        
        conn = psycopg2.connect(database_url)
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM users")
            db_count = cur.fetchone()[0]
            
            # Get some details about the users
            cur.execute("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN firebase_uid IS NOT NULL THEN 1 END) as with_firebase_uid,
                    COUNT(CASE WHEN stripe_customer_id IS NOT NULL THEN 1 END) as with_stripe,
                    COUNT(CASE WHEN eth_address IS NOT NULL THEN 1 END) as with_eth_address
                FROM users
            """)
            details = cur.fetchone()
            
        conn.close()
        
        print(f"\nDATABASE ANALYSIS")
        print("=" * 60)
        print(f"Total users in database: {db_count:,}")
        print(f"Users with Firebase UID: {details[1]:,}")
        print(f"Users with Stripe customer: {details[2]:,}")
        print(f"Users with ETH address: {details[3]:,}")
        
        return db_count
        
    except Exception as e:
        print(f"Error checking database: {str(e)}")
        return None

def main():
    """Main analysis function"""
    print("Firebase User Migration Gap Analysis")
    print("=" * 60)
    
    # Analyze batch files
    analysis = analyze_batch_files()
    
    # Check database
    db_count = check_database_count()
    
    if db_count:
        gap = analysis['valid_users'] - db_count
        print(f"\nGAP ANALYSIS")
        print("=" * 60)
        print(f"Expected users (from files): {analysis['valid_users']:,}")
        print(f"Actual users (in database): {db_count:,}")
        print(f"Gap: {gap:,} users")
        
        if gap > 0:
            print(f"\nPossible reasons for the gap:")
            print(f"- Migration errors during processing")
            print(f"- Database connection issues")
            print(f"- Users that failed validation during import")
            print(f"- Stripe customer creation failures")
            print(f"- ETH address generation failures")
    
    # Save detailed analysis
    with open('migration_gap_analysis.json', 'w') as f:
        json.dump({
            'analysis_timestamp': datetime.now().isoformat(),
            'file_analysis': analysis,
            'database_count': db_count
        }, f, indent=2)
    
    print(f"\nDetailed analysis saved to: migration_gap_analysis.json")

if __name__ == "__main__":
    main()
