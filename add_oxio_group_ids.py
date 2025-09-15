#!/usr/bin/env python3
"""
Script to add OXIO Group IDs to all DOT users who don't have one.
Each user gets a unique group ID following the pattern: DOTM-{timestamp}-{random_4_digits}
"""

import os
import psycopg2
import time
import random
from datetime import datetime

def generate_unique_group_id():
    """Generate a unique OXIO Group ID following the DOTM pattern"""
    timestamp = int(time.time())
    random_suffix = random.randint(1000, 9999)
    return f"DOTM-{timestamp}-{random_suffix}"

def add_oxio_group_ids_to_users(batch_size=100, dry_run=True):
    """
    Add OXIO Group IDs to all users who don't have one
    
    Args:
        batch_size: Number of users to process in each batch
        dry_run: If True, only show what would be updated without making changes
    """
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("ERROR: DATABASE_URL not set")
        return False
    
    try:
        conn = psycopg2.connect(database_url)
        with conn.cursor() as cur:
            # First, check current statistics
            print("=== CURRENT OXIO GROUP ID STATISTICS ===")
            cur.execute("""
                SELECT 
                    COUNT(*) as total_users,
                    COUNT(oxio_group_id) as users_with_group_id,
                    COUNT(*) - COUNT(oxio_group_id) as users_without_group_id
                FROM users
            """)
            
            stats = cur.fetchone()
            total_users, users_with_group_id, users_without_group_id = stats
            
            print(f"Total users: {total_users:,}")
            print(f"Users with OXIO Group ID: {users_with_group_id:,}")
            print(f"Users without OXIO Group ID: {users_without_group_id:,}")
            print(f"Percentage missing: {(users_without_group_id / total_users * 100):.1f}%")
            
            if users_without_group_id == 0:
                print("\n✅ All users already have OXIO Group IDs!")
                return True
            
            # Get users without OXIO Group ID in batches
            print(f"\n=== {'DRY RUN - ' if dry_run else ''}PROCESSING USERS ===")
            print(f"Processing {users_without_group_id:,} users in batches of {batch_size}")
            
            offset = 0
            total_processed = 0
            
            while offset < users_without_group_id:
                # Get batch of users without group ID
                cur.execute("""
                    SELECT id, email, display_name, firebase_uid 
                    FROM users 
                    WHERE oxio_group_id IS NULL 
                    ORDER BY id 
                    LIMIT %s OFFSET %s
                """, (batch_size, offset))
                
                batch_users = cur.fetchall()
                
                if not batch_users:
                    break
                    
                print(f"\nProcessing batch {offset // batch_size + 1}: users {offset + 1}-{min(offset + len(batch_users), users_without_group_id)}")
                
                batch_updates = []
                
                for user_id, email, display_name, firebase_uid in batch_users:
                    # Generate unique group ID
                    group_id = generate_unique_group_id()
                    
                    # Add small random delay to ensure uniqueness
                    time.sleep(0.001)
                    
                    batch_updates.append((group_id, user_id))
                    
                    if dry_run:
                        print(f"  Would update User {user_id} ({email or 'no email'}): {group_id}")
                    else:
                        print(f"  Updating User {user_id} ({email or 'no email'}): {group_id}")
                
                # Execute batch update
                if not dry_run:
                    cur.executemany("""
                        UPDATE users 
                        SET oxio_group_id = %s 
                        WHERE id = %s
                    """, batch_updates)
                    conn.commit()
                    print(f"  ✅ Updated {len(batch_updates)} users in this batch")
                else:
                    print(f"  📝 Would update {len(batch_updates)} users in this batch")
                
                total_processed += len(batch_updates)
                offset += batch_size
                
                # Show progress
                progress_pct = (total_processed / users_without_group_id * 100)
                print(f"  Progress: {total_processed:,}/{users_without_group_id:,} ({progress_pct:.1f}%)")
                
                # Small delay to prevent overwhelming the database
                time.sleep(0.1)
            
            # Final statistics
            if not dry_run:
                print("\n=== FINAL STATISTICS ===")
                cur.execute("""
                    SELECT 
                        COUNT(*) as total_users,
                        COUNT(oxio_group_id) as users_with_group_id,
                        COUNT(*) - COUNT(oxio_group_id) as users_without_group_id
                    FROM users
                """)
                
                final_stats = cur.fetchone()
                final_total, final_with, final_without = final_stats
                
                print(f"Total users: {final_total:,}")
                print(f"Users with OXIO Group ID: {final_with:,}")
                print(f"Users without OXIO Group ID: {final_without:,}")
                
                if final_without == 0:
                    print("🎉 SUCCESS: All users now have OXIO Group IDs!")
                else:
                    print(f"⚠️  WARNING: {final_without} users still missing OXIO Group IDs")
            else:
                print(f"\n📝 DRY RUN COMPLETE: Would have updated {total_processed:,} users")
                print("To actually apply changes, run with dry_run=False")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False

def main():
    """Main function with different execution modes"""
    print("OXIO Group ID Assignment Script")
    print("="*50)
    
    # First run a dry run to see what would be changed
    print("Step 1: Running DRY RUN to preview changes...")
    success = add_oxio_group_ids_to_users(batch_size=100, dry_run=True)
    
    if not success:
        print("❌ Dry run failed. Exiting.")
        return
    
    # Ask for confirmation to proceed
    print("\n" + "="*50)
    response = input("Do you want to proceed with the actual updates? (y/N): ").strip().lower()
    
    if response in ['y', 'yes']:
        print("\nStep 2: Running ACTUAL UPDATE...")
        success = add_oxio_group_ids_to_users(batch_size=100, dry_run=False)
        
        if success:
            print("\n🎉 OXIO Group ID assignment completed successfully!")
        else:
            print("\n❌ Update failed. Please check the error messages above.")
    else:
        print("\n📝 Update cancelled by user.")

if __name__ == "__main__":
    main()