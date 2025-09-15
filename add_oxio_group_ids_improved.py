#!/usr/bin/env python3
"""
Improved script to add OXIO Group IDs to all DOT users who don't have one.
Addresses uniqueness issues by using millisecond timestamps, checking against existing IDs,
and including retry mechanisms.

Usage:
  python add_oxio_group_ids_improved.py --dry-run    # Preview changes
  python add_oxio_group_ids_improved.py --apply      # Apply changes
"""

import os
import psycopg2
import time
import random
import argparse
import sys
from datetime import datetime
from typing import Set

def generate_unique_group_id(existing_ids: Set[str], max_retries: int = 10) -> str:
    """
    Generate a unique OXIO Group ID that doesn't exist in the database.
    Uses millisecond timestamp for better uniqueness.
    
    Args:
        existing_ids: Set of existing group IDs to avoid
        max_retries: Maximum number of attempts to generate unique ID
    
    Returns:
        Unique group ID following DOTM-{millisecond_timestamp}-{random_4_digits} pattern
    
    Raises:
        RuntimeError: If unable to generate unique ID after max_retries
    """
    for attempt in range(max_retries):
        # Use millisecond timestamp for better uniqueness
        timestamp_ms = int(time.time() * 1000)
        random_suffix = random.randint(1000, 9999)
        group_id = f"DOTM-{timestamp_ms}-{random_suffix}"
        
        if group_id not in existing_ids:
            existing_ids.add(group_id)  # Immediately add to prevent intra-run duplicates
            return group_id
            
        # Small delay if collision occurred
        time.sleep(0.001)
    
    raise RuntimeError(f"Unable to generate unique OXIO Group ID after {max_retries} attempts")

def ensure_unique_index(conn):
    """Ensure there's a unique index on oxio_group_id to prevent duplicates"""
    try:
        with conn.cursor() as cur:
            # Check if unique index already exists
            cur.execute("""
                SELECT indexname 
                FROM pg_indexes 
                WHERE tablename = 'users' 
                AND indexdef LIKE '%UNIQUE%' 
                AND indexdef LIKE '%oxio_group_id%'
            """)
            
            existing_unique_index = cur.fetchone()
            
            if not existing_unique_index:
                print("Creating unique index on oxio_group_id...")
                cur.execute("""
                    CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS 
                    idx_users_oxio_group_id_unique ON users(oxio_group_id) 
                    WHERE oxio_group_id IS NOT NULL
                """)
                conn.commit()
                print("✅ Unique index created successfully")
            else:
                print(f"✅ Unique index already exists: {existing_unique_index[0]}")
                
    except Exception as e:
        print(f"⚠️  Warning: Could not create unique index: {str(e)}")
        print("Continuing without unique index (higher risk of duplicates)")

def prefetch_existing_group_ids(conn) -> Set[str]:
    """Load all existing OXIO Group IDs into memory for uniqueness checking"""
    with conn.cursor() as cur:
        cur.execute("SELECT oxio_group_id FROM users WHERE oxio_group_id IS NOT NULL")
        existing_ids = {row[0] for row in cur.fetchall()}
        print(f"Prefetched {len(existing_ids)} existing OXIO Group IDs")
        return existing_ids

def add_oxio_group_ids_to_users(dry_run: bool = True, batch_size: int = 500):
    """
    Add OXIO Group IDs to all users who don't have one
    
    Args:
        dry_run: If True, only show what would be updated without making changes
        batch_size: Number of users to process in each batch
    """
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("ERROR: DATABASE_URL not set")
        return False
    
    try:
        conn = psycopg2.connect(database_url)
        
        # Ensure unique index exists (only if not dry run)
        if not dry_run:
            ensure_unique_index(conn)
        
        # Prefetch existing group IDs for uniqueness checking
        existing_group_ids = prefetch_existing_group_ids(conn)
        
        with conn.cursor() as cur:
            # Get current statistics
            print("=== OXIO GROUP ID STATISTICS ===")
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
            print(f"Coverage: {(users_with_group_id / total_users * 100):.1f}%")
            
            if users_without_group_id == 0:
                print("\n✅ All users already have OXIO Group IDs!")
                return True
            
            # Process users in batches
            mode_text = "DRY RUN - PREVIEW" if dry_run else "APPLYING UPDATES"
            print(f"\n=== {mode_text} ===")
            print(f"Processing {users_without_group_id:,} users in batches of {batch_size}")
            
            offset = 0
            total_processed = 0
            total_retries = 0
            
            while offset < users_without_group_id:
                # Get batch of users without group ID
                cur.execute("""
                    SELECT id, email 
                    FROM users 
                    WHERE oxio_group_id IS NULL 
                    ORDER BY id 
                    LIMIT %s OFFSET %s
                """, (batch_size, offset))
                
                batch_users = cur.fetchall()
                
                if not batch_users:
                    break
                
                batch_updates = []
                batch_retries = 0
                
                # Generate unique group IDs for this batch
                for user_id, email in batch_users:
                    try:
                        group_id = generate_unique_group_id(existing_group_ids)
                        batch_updates.append((group_id, user_id))
                    except RuntimeError as e:
                        print(f"❌ Failed to generate unique ID for user {user_id}: {str(e)}")
                        return False
                
                # Execute batch update with retry mechanism
                if not dry_run:
                    success = False
                    for retry_attempt in range(3):
                        try:
                            cur.executemany("""
                                UPDATE users 
                                SET oxio_group_id = %s 
                                WHERE id = %s AND oxio_group_id IS NULL
                            """, batch_updates)
                            conn.commit()
                            success = True
                            break
                        except psycopg2.IntegrityError as e:
                            if 'duplicate key' in str(e).lower():
                                batch_retries += 1
                                conn.rollback()
                                print(f"  Collision detected in batch, regenerating IDs (attempt {retry_attempt + 1}/3)...")
                                
                                # Regenerate IDs for the entire batch
                                batch_updates = []
                                for user_id, email in batch_users:
                                    try:
                                        group_id = generate_unique_group_id(existing_group_ids)
                                        batch_updates.append((group_id, user_id))
                                    except RuntimeError as e:
                                        print(f"❌ Failed to regenerate unique ID: {str(e)}")
                                        return False
                            else:
                                raise  # Re-raise if it's not a uniqueness error
                    
                    if not success:
                        print("❌ Failed to resolve uniqueness conflicts after 3 attempts")
                        return False
                
                # Log batch completion
                batch_num = offset // batch_size + 1
                total_batches = (users_without_group_id + batch_size - 1) // batch_size
                progress_pct = (total_processed + len(batch_updates)) / users_without_group_id * 100
                
                if dry_run:
                    print(f"Batch {batch_num}/{total_batches}: Would update {len(batch_updates)} users ({progress_pct:.1f}%)")
                else:
                    retry_text = f" ({batch_retries} retries)" if batch_retries > 0 else ""
                    print(f"Batch {batch_num}/{total_batches}: Updated {len(batch_updates)} users{retry_text} ({progress_pct:.1f}%)")
                
                total_processed += len(batch_updates)
                total_retries += batch_retries
                offset += batch_size
                
                # Small throttle between batches
                time.sleep(0.1)
            
            # Final summary
            if dry_run:
                print(f"\n📝 DRY RUN SUMMARY:")
                print(f"Would update {total_processed:,} users with unique OXIO Group IDs")
                print(f"Run with --apply to execute these changes")
            else:
                print(f"\n✅ UPDATE COMPLETE:")
                print(f"Successfully updated {total_processed:,} users")
                if total_retries > 0:
                    print(f"Total uniqueness conflicts resolved: {total_retries}")
                
                # Final verification
                cur.execute("""
                    SELECT 
                        COUNT(*) as total_users,
                        COUNT(oxio_group_id) as users_with_group_id,
                        COUNT(*) - COUNT(oxio_group_id) as users_without_group_id
                    FROM users
                """)
                
                final_stats = cur.fetchone()
                final_total, final_with, final_without = final_stats
                
                print(f"\nFINAL STATISTICS:")
                print(f"Total users: {final_total:,}")
                print(f"Users with OXIO Group ID: {final_with:,}")
                print(f"Coverage: {(final_with / final_total * 100):.1f}%")
                
                if final_without == 0:
                    print("🎉 SUCCESS: All users now have OXIO Group IDs!")
                else:
                    print(f"⚠️  {final_without} users still missing OXIO Group IDs")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False

def main():
    """Main function with command-line argument parsing"""
    parser = argparse.ArgumentParser(
        description="Add OXIO Group IDs to DOT users who don't have them"
    )
    parser.add_argument(
        '--apply', 
        action='store_true', 
        help='Apply changes to database (default is dry-run mode)'
    )
    parser.add_argument(
        '--dry-run', 
        action='store_true', 
        help='Preview changes without applying them (default)'
    )
    parser.add_argument(
        '--batch-size', 
        type=int, 
        default=500, 
        help='Number of users to process per batch (default: 500)'
    )
    
    args = parser.parse_args()
    
    # Determine mode
    if args.apply and args.dry_run:
        print("ERROR: Cannot use both --apply and --dry-run. Choose one.")
        sys.exit(1)
    
    dry_run = not args.apply  # Default to dry-run unless --apply is specified
    
    print("OXIO Group ID Assignment Script")
    print("=" * 50)
    print(f"Mode: {'DRY RUN (preview only)' if dry_run else 'APPLY CHANGES'}")
    print(f"Batch size: {args.batch_size}")
    print()
    
    success = add_oxio_group_ids_to_users(dry_run=dry_run, batch_size=args.batch_size)
    
    if not success:
        print("\n❌ Script failed. Please check error messages above.")
        sys.exit(1)
    
    print(f"\n✅ Script completed successfully.")

if __name__ == "__main__":
    main()