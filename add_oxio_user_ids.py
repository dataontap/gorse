#!/usr/bin/env python3
"""
Production-ready script to create OXIO User IDs for all DOT users who don't have one.
Uses OXIO API to create users and handles existing users appropriately.

Usage:
  python add_oxio_user_ids.py --dry-run    # Preview changes
  python add_oxio_user_ids.py --apply      # Apply changes
"""

import os
import psycopg2
from psycopg2 import errors
import argparse
import sys
import time
from datetime import datetime
from typing import List, Tuple, Optional, Dict, Any

# Import OXIO service 
from oxio_service import OXIOService

def get_users_without_oxio_user_ids(conn, batch_size: int, last_id: int = 0) -> List[Tuple[int, str, str, str, str]]:
    """
    Get next batch of users without OXIO User IDs using keyset pagination.
    
    Args:
        conn: Database connection
        batch_size: Number of users to fetch
        last_id: Last user ID from previous batch (for pagination)
        
    Returns:
        List of (user_id, email, display_name, oxio_group_id, firebase_uid) tuples
    """
    with conn.cursor() as cur:
        cur.execute("""
            SELECT id, email, display_name, oxio_group_id, firebase_uid
            FROM users 
            WHERE oxio_user_id IS NULL AND id > %s
            ORDER BY id 
            LIMIT %s
        """, (last_id, batch_size))
        
        return cur.fetchall()

def parse_display_name(display_name: str) -> Tuple[str, str]:
    """Parse display name into first and last name"""
    if not display_name:
        return "Anonymous", "Anonymous"
    
    name_parts = display_name.split(' ', 1)
    first_name = name_parts[0] if name_parts else "Anonymous"
    last_name = name_parts[1] if len(name_parts) > 1 else "Anonymous"
    
    return first_name, last_name

def create_or_find_oxio_user(oxio_service: OXIOService, email: str, display_name: str, oxio_group_id: str, firebase_uid: str) -> Dict[str, Any]:
    """
    Create a new OXIO user or find existing one
    
    Args:
        oxio_service: OXIO service instance
        email: User email
        display_name: User display name
        oxio_group_id: OXIO Group ID (if available)
        firebase_uid: Firebase UID
    
    Returns:
        Dictionary with success status and oxio_user_id if successful
    """
    first_name, last_name = parse_display_name(display_name)
    
    try:
        # Try to create new OXIO user
        result = oxio_service.create_oxio_user(
            first_name=first_name,
            last_name=last_name,
            email=email,
            firebase_uid=firebase_uid,
            oxio_group_id=oxio_group_id
        )
        
        if result.get('success'):
            return {
                'success': True,
                'oxio_user_id': result.get('oxio_user_id'),
                'method': 'created',
                'message': 'OXIO user created successfully',
                'api_response': result
            }
        else:
            # Check if user already exists (error code 6805)
            if (result.get('status_code') == 400 and 
                result.get('data', {}).get('code') == 6805):
                
                print(f"      User already exists, finding existing OXIO User ID for {email}")
                
                # Try to find existing OXIO user by email
                find_result = oxio_service.find_user_by_email(email)
                if find_result.get('success'):
                    return {
                        'success': True,
                        'oxio_user_id': find_result.get('oxio_user_id'),
                        'method': 'found',
                        'message': 'Found existing OXIO user',
                        'api_response': find_result,
                        'original_error': result
                    }
                else:
                    return {
                        'success': False,
                        'error': 'User exists but could not find existing user ID',
                        'message': find_result.get('message', 'Unknown error'),
                        'api_response': find_result,
                        'original_error': result
                    }
            else:
                return {
                    'success': False,
                    'error': f"OXIO API error: {result.get('status_code')}",
                    'message': result.get('message', 'Unknown error'),
                    'api_response': result
                }
                
    except Exception as e:
        return {
            'success': False,
            'error': 'Exception during OXIO user creation',
            'message': str(e),
            'exception_details': str(e)
        }

def add_oxio_user_ids(dry_run: bool = True, batch_size: int = 100) -> bool:
    """
    Add OXIO User IDs to all users who don't have one using OXIO API
    
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
    
    # Initialize OXIO service
    try:
        oxio_service = OXIOService()
    except Exception as e:
        print(f"❌ ERROR: Failed to initialize OXIO service: {str(e)}")
        print("Make sure OXIO_API_KEY and OXIO_AUTH_TOKEN are set in secrets")
        return False
    
    conn = None
    try:
        conn = psycopg2.connect(database_url)
        
        with conn.cursor() as cur:
            # Get current statistics
            print("=== OXIO USER ID STATISTICS ===")
            cur.execute("""
                SELECT 
                    COUNT(*) as total_users,
                    COUNT(oxio_user_id) as users_with_user_id,
                    COUNT(oxio_group_id) as users_with_group_id,
                    COUNT(*) - COUNT(oxio_user_id) as users_without_user_id
                FROM users
            """)
            
            stats = cur.fetchone()
            total_users, users_with_user_id, users_with_group_id, users_without_user_id = stats
            
            print(f"Total users: {total_users:,}")
            print(f"Users with OXIO User ID: {users_with_user_id:,}")
            print(f"Users with OXIO Group ID: {users_with_group_id:,}")
            print(f"Users without OXIO User ID: {users_without_user_id:,}")
            print(f"Coverage: {(users_with_user_id / total_users * 100):.1f}%")
            
            if users_without_user_id == 0:
                print("\n✅ All users already have OXIO User IDs!")
                return True
            
            # Process users using keyset pagination
            mode_text = "DRY RUN - PREVIEW" if dry_run else "APPLYING UPDATES"
            print(f"\n=== {mode_text} ===")
            print(f"Processing users in batches of {batch_size}")
            print("⚠️  NOTE: This involves API calls to OXIO - will be slower than Group ID assignment")
            
            total_processed = 0
            total_created = 0
            total_found = 0
            total_errors = 0
            batch_num = 0
            last_processed_id = 0
            
            while True:
                # Get next batch using keyset pagination
                batch_users = get_users_without_oxio_user_ids(conn, batch_size, last_processed_id)
                
                if not batch_users:
                    break  # No more users to process
                
                batch_num += 1
                batch_updates = []
                batch_created = 0
                batch_found = 0
                batch_errors = 0
                
                print(f"\nBatch {batch_num}: Processing {len(batch_users)} users...")
                
                # Process each user in the batch
                for user_id, email, display_name, oxio_group_id, firebase_uid in batch_users:
                    if not dry_run:
                        # Make API call to create/find OXIO user
                        result = create_or_find_oxio_user(
                            oxio_service, email, display_name, oxio_group_id, firebase_uid
                        )
                        
                        # Store the API response in database for tracking
                        try:
                            with conn.cursor() as response_cur:
                                # Create oxio_api_responses table if it doesn't exist
                                response_cur.execute("""
                                    CREATE TABLE IF NOT EXISTS oxio_api_responses (
                                        id SERIAL PRIMARY KEY,
                                        user_id INTEGER NOT NULL,
                                        firebase_uid VARCHAR(128),
                                        email VARCHAR(255),
                                        operation_type VARCHAR(50),
                                        success BOOLEAN,
                                        oxio_user_id VARCHAR(100),
                                        method VARCHAR(20),
                                        error_code VARCHAR(50),
                                        error_message TEXT,
                                        api_response_json TEXT,
                                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                                    )
                                """)
                                
                                # Insert the response record
                                import json
                                response_cur.execute("""
                                    INSERT INTO oxio_api_responses 
                                    (user_id, firebase_uid, email, operation_type, success, 
                                     oxio_user_id, method, error_code, error_message, api_response_json)
                                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                """, (
                                    user_id,
                                    firebase_uid,
                                    email,
                                    'create_or_find_user',
                                    result.get('success', False),
                                    result.get('oxio_user_id'),
                                    result.get('method'),
                                    result.get('error'),
                                    result.get('message'),
                                    json.dumps(result, default=str)
                                ))
                                conn.commit()
                        except Exception as db_err:
                            print(f"  ⚠️ Failed to store API response for user {user_id}: {str(db_err)}")
                        
                        if result.get('success'):
                            oxio_user_id = result.get('oxio_user_id')
                            method = result.get('method')
                            batch_updates.append((oxio_user_id, user_id))
                            
                            if method == 'created':
                                batch_created += 1
                                print(f"  ✅ User {user_id} ({email}): Created OXIO User ID {oxio_user_id}")
                            elif method == 'found':
                                batch_found += 1  
                                print(f"  🔍 User {user_id} ({email}): Found existing OXIO User ID {oxio_user_id}")
                        else:
                            batch_errors += 1
                            error_msg = result.get('message', 'Unknown error')
                            print(f"  ❌ User {user_id} ({email}): {error_msg}")
                        
                        # Small delay between API calls to avoid rate limiting
                        time.sleep(0.2)
                    else:
                        # Dry run - just show what would be processed
                        batch_updates.append((f"[would-create-or-find]", user_id))
                        print(f"  📝 User {user_id} ({email or 'no email'}): Would create/find OXIO User ID")
                
                # Execute batch database update
                if batch_updates and not dry_run:
                    try:
                        cur.executemany("""
                            UPDATE users 
                            SET oxio_user_id = %s 
                            WHERE id = %s AND oxio_user_id IS NULL
                        """, [(oxio_user_id, user_id) for oxio_user_id, user_id in batch_updates if oxio_user_id != f"[would-create-or-find]"])
                        conn.commit()
                        print(f"  💾 Database: Updated {len([u for u in batch_updates if u[0] != '[would-create-or-find]'])} users")
                    except Exception as e:
                        print(f"  ❌ Database error: {str(e)}")
                        conn.rollback()
                        return False
                
                # Update progress tracking
                successful_updates = len([u for u in batch_updates if u[0] != '[would-create-or-find]']) if not dry_run else len(batch_updates)
                total_processed += successful_updates
                total_created += batch_created
                total_found += batch_found
                total_errors += batch_errors
                last_processed_id = max(user_id for user_id, _, _, _, _ in batch_users)
                
                # Progress reporting
                progress_pct = (total_processed / users_without_user_id * 100) if users_without_user_id > 0 else 100
                
                if dry_run:
                    print(f"Batch {batch_num}: Would process {len(batch_updates)} users ({progress_pct:.1f}%)")
                else:
                    print(f"Batch {batch_num}: Processed {successful_updates}/{len(batch_users)} users - Created: {batch_created}, Found: {batch_found}, Errors: {batch_errors} ({progress_pct:.1f}%)")
                
                # Throttle between batches
                time.sleep(1.0)
            
            # Final summary and verification
            if dry_run:
                print(f"\n📝 DRY RUN SUMMARY:")
                print(f"Would process {total_processed:,} users with OXIO API calls")
                print(f"Each user would be created in OXIO or found if already existing")
                print(f"Run with --apply to execute these changes")
            else:
                print(f"\n✅ UPDATE COMPLETE:")
                print(f"Successfully processed {total_processed:,} users")
                print(f"  - Created new: {total_created:,}")
                print(f"  - Found existing: {total_found:,}")
                print(f"  - Errors: {total_errors:,}")
                
                # Final verification
                cur.execute("""
                    SELECT 
                        COUNT(*) as total_users,
                        COUNT(oxio_user_id) as users_with_user_id,
                        COUNT(*) - COUNT(oxio_user_id) as users_without_user_id
                    FROM users
                """)
                
                final_stats = cur.fetchone()
                final_total, final_with, final_without = final_stats
                
                print(f"\nFINAL STATISTICS:")
                print(f"Total users: {final_total:,}")
                print(f"Users with OXIO User ID: {final_with:,}")
                print(f"Coverage: {(final_with / final_total * 100):.1f}%")
                
                # Check if API responses table exists and show response statistics
                try:
                    cur.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_name = 'oxio_api_responses'
                        )
                    """)
                    if cur.fetchone()[0]:
                        cur.execute("""
                            SELECT 
                                COUNT(*) as total_responses,
                                COUNT(CASE WHEN success = true THEN 1 END) as successful_responses,
                                COUNT(CASE WHEN method = 'created' THEN 1 END) as created_responses,
                                COUNT(CASE WHEN method = 'found' THEN 1 END) as found_responses,
                                COUNT(CASE WHEN success = false THEN 1 END) as failed_responses
                            FROM oxio_api_responses
                            WHERE operation_type = 'create_or_find_user'
                        """)
                        
                        response_stats = cur.fetchone()
                        if response_stats:
                            total_resp, success_resp, created_resp, found_resp, failed_resp = response_stats
                            print(f"\nAPI RESPONSE STATISTICS:")
                            print(f"Total API responses logged: {total_resp:,}")
                            print(f"  - Successful: {success_resp:,}")
                            print(f"  - New users created: {created_resp:,}")
                            print(f"  - Existing users found: {found_resp:,}")
                            print(f"  - Failed: {failed_resp:,}")
                except Exception as stats_err:
                    print(f"Could not retrieve API response statistics: {str(stats_err)}")
                
                if final_without == 0:
                    print("🎉 SUCCESS: All users now have OXIO User IDs!")
                elif total_errors == 0:
                    print("✅ SUCCESS: No errors occurred during processing")
                else:
                    print(f"⚠️  {final_without} users still missing OXIO User IDs ({total_errors} had errors)")
                    print("💡 Check oxio_api_responses table for detailed error analysis")
        
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
        description="Create OXIO User IDs for DOT users who don't have them"
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
        default=50, 
        help='Number of users to process per batch (default: 50, smaller due to API calls)'
    )
    
    args = parser.parse_args()
    
    # Determine mode
    if args.apply and args.dry_run:
        print("ERROR: Cannot use both --apply and --dry-run. Choose one.")
        sys.exit(1)
    
    dry_run = not args.apply  # Default to dry-run unless --apply is specified
    
    print("OXIO User ID Creation Script (Production Ready)")
    print("=" * 55)
    print(f"Mode: {'DRY RUN (preview only)' if dry_run else 'APPLY CHANGES'}")
    print(f"Batch size: {args.batch_size}")
    print("⚠️  NOTE: This script makes API calls to OXIO - process will be slower")
    print()
    
    success = add_oxio_user_ids(dry_run=dry_run, batch_size=args.batch_size)
    
    if not success:
        print("\n❌ Script failed. Please check error messages above.")
        sys.exit(1)
    
    print(f"\n✅ Script completed successfully.")

if __name__ == "__main__":
    main()