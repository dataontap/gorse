#!/usr/bin/env python3
"""
Production-ready script to add OXIO Group IDs to all DOT users who don't have one.
Addresses all uniqueness and safety issues for production deployment.

Usage:
  python add_oxio_group_ids_final.py --dry-run    # Preview changes
  python add_oxio_group_ids_final.py --apply      # Apply changes
"""

import os
import psycopg2
from psycopg2 import errors
import time
import random
import argparse
import sys
from datetime import datetime
from typing import Set, List, Tuple, Optional

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

def ensure_unique_index(conn) -> bool:
    """
    Ensure there's a unique index on oxio_group_id to prevent duplicates.
    Creates index outside transaction to avoid Postgres restrictions.
    
    Returns:
        True if index exists or was created successfully, False otherwise
    """
    try:
        # First check if unique index already exists
        with conn.cursor() as cur:
            cur.execute("""
                SELECT indexname, indexdef
                FROM pg_indexes 
                WHERE tablename = 'users' 
                AND indexdef LIKE '%UNIQUE%' 
                AND indexdef LIKE '%oxio_group_id%'
            """)
            
            existing_index = cur.fetchone()
            if existing_index:
                print(f"✅ Unique index already exists: {existing_index[0]}")
                return True
        
        print("Creating unique index on oxio_group_id...")
        
        # Create index outside transaction using autocommit
        old_autocommit = conn.autocommit
        conn.autocommit = True
        
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS 
                    idx_users_oxio_group_id_unique ON users(oxio_group_id) 
                    WHERE oxio_group_id IS NOT NULL
                """)
            
            # Verify the index was created
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT indexname 
                    FROM pg_indexes 
                    WHERE tablename = 'users' 
                    AND indexname = 'idx_users_oxio_group_id_unique'
                """)
                
                if cur.fetchone():
                    print("✅ Unique index created successfully")
                    return True
                else:
                    print("❌ Failed to create unique index")
                    return False
                    
        finally:
            conn.autocommit = old_autocommit
            
    except Exception as e:
        print(f"❌ Error creating unique index: {str(e)}")
        return False

def prefetch_existing_group_ids(conn) -> Set[str]:
    """Load all existing OXIO Group IDs into memory for uniqueness checking"""
    with conn.cursor() as cur:
        cur.execute("SELECT oxio_group_id FROM users WHERE oxio_group_id IS NOT NULL")
        existing_ids = {row[0] for row in cur.fetchall()}
        print(f"Prefetched {len(existing_ids)} existing OXIO Group IDs")
        return existing_ids

def get_users_without_group_ids(conn, batch_size: int, last_id: int = 0) -> List[Tuple[int, str]]:
    """
    Get next batch of users without OXIO Group IDs using keyset pagination.
    This avoids the OFFSET skip problem when updating rows during iteration.
    
    Args:
        conn: Database connection
        batch_size: Number of users to fetch
        last_id: Last user ID from previous batch (for pagination)
        
    Returns:
        List of (user_id, email) tuples
    """
    with conn.cursor() as cur:
        cur.execute("""
            SELECT id, email 
            FROM users 
            WHERE oxio_group_id IS NULL AND id > %s
            ORDER BY id 
            LIMIT %s
        """, (last_id, batch_size))
        
        return cur.fetchall()

def verify_no_duplicates(conn) -> bool:
    """Check for any duplicate OXIO Group IDs in the database"""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT oxio_group_id, COUNT(*) as count
            FROM users 
            WHERE oxio_group_id IS NOT NULL
            GROUP BY oxio_group_id 
            HAVING COUNT(*) > 1
            ORDER BY count DESC
        """)
        
        duplicates = cur.fetchall()
        if duplicates:
            print(f"❌ Found {len(duplicates)} duplicate OXIO Group IDs:")
            for group_id, count in duplicates[:5]:  # Show first 5
                print(f"  {group_id}: {count} users")
            return False
        else:
            print("✅ No duplicate OXIO Group IDs found")
            return True

def add_oxio_group_ids_to_users(dry_run: bool = True, batch_size: int = 500) -> bool:
    """
    Add OXIO Group IDs to all users who don't have one using safe keyset pagination
    
    Args:
        dry_run: If True, only show what would be updated without making changes
        batch_size: Number of users to process in each batch
        
    Returns:
        True if successful, False if errors occurred
    """
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("ERROR: DATABASE_URL not set")
        return False
    
    conn = None
    try:
        conn = psycopg2.connect(database_url)
        
        # Ensure unique index exists (critical for production safety)
        if not dry_run:
            if not ensure_unique_index(conn):
                print("❌ CRITICAL: Cannot proceed without unique index on oxio_group_id")
                print("   This is required to prevent duplicate group IDs.")
                return False
        
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
            
            # Process users using keyset pagination (avoids OFFSET skip problem)
            mode_text = "DRY RUN - PREVIEW" if dry_run else "APPLYING UPDATES"
            print(f"\n=== {mode_text} ===")
            print(f"Processing users in batches of {batch_size}")
            
            total_processed = 0
            total_retries = 0
            batch_num = 0
            last_processed_id = 0
            
            while True:
                # Get next batch using keyset pagination
                batch_users = get_users_without_group_ids(conn, batch_size, last_processed_id)
                
                if not batch_users:
                    break  # No more users to process
                
                batch_num += 1
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
                
                # Execute batch update with collision handling
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
                            
                        except errors.UniqueViolation:
                            batch_retries += 1
                            conn.rollback()
                            print(f"  Collision detected in batch {batch_num}, regenerating IDs (attempt {retry_attempt + 1}/3)...")
                            
                            # Regenerate IDs for the entire batch
                            batch_updates = []
                            for user_id, email in batch_users:
                                try:
                                    group_id = generate_unique_group_id(existing_group_ids)
                                    batch_updates.append((group_id, user_id))
                                except RuntimeError as e:
                                    print(f"❌ Failed to regenerate unique ID: {str(e)}")
                                    return False
                    
                    if not success:
                        print("❌ Failed to resolve uniqueness conflicts after 3 attempts")
                        return False
                
                # Update progress tracking
                total_processed += len(batch_updates)
                total_retries += batch_retries
                last_processed_id = max(user_id for user_id, _ in batch_users)
                
                # Progress reporting
                progress_pct = (total_processed / users_without_group_id * 100) if users_without_group_id > 0 else 100
                
                if dry_run:
                    print(f"Batch {batch_num}: Would update {len(batch_updates)} users ({progress_pct:.1f}%)")
                else:
                    retry_text = f" ({batch_retries} retries)" if batch_retries > 0 else ""
                    print(f"Batch {batch_num}: Updated {len(batch_updates)} users{retry_text} ({progress_pct:.1f}%)")
                
                # Small throttle between batches
                time.sleep(0.05)
            
            # Final summary and verification
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
                
                # Check for duplicates
                verify_no_duplicates(conn)
                
                if final_without == 0:
                    print("🎉 SUCCESS: All users now have OXIO Group IDs!")
                else:
                    print(f"⚠️  {final_without} users still missing OXIO Group IDs")
                    return False
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False
        
    finally:
        if conn:
            conn.close()

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
        default=1000, 
        help='Number of users to process per batch (default: 1000)'
    )
    
    args = parser.parse_args()
    
    # Determine mode
    if args.apply and args.dry_run:
        print("ERROR: Cannot use both --apply and --dry-run. Choose one.")
        sys.exit(1)
    
    dry_run = not args.apply  # Default to dry-run unless --apply is specified
    
    print("OXIO Group ID Assignment Script (Production Ready)")
    print("=" * 55)
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