
#!/usr/bin/env python3
"""
Simple script to check how many DOT users don't have OXIO User IDs
"""

import os
import psycopg2
from psycopg2.pool import SimpleConnectionPool
from contextlib import contextmanager

# Initialize database connection
database_url = os.environ.get('DATABASE_URL')
if not database_url:
    print("❌ ERROR: DATABASE_URL not set")
    exit(1)

try:
    pool = SimpleConnectionPool(1, 5, database_url)
    print("✅ Database connection initialized")

    @contextmanager
    def get_db_connection():
        connection = pool.getconn()
        try:
            yield connection
        finally:
            pool.putconn(connection)
except Exception as e:
    print(f"❌ Error initializing database connection: {str(e)}")
    exit(1)

def check_oxio_uid_coverage():
    """Check OXIO User ID coverage statistics"""
    
    with get_db_connection() as conn:
        if conn:
            with conn.cursor() as cur:
                print("=== DOT USERS OXIO UID COVERAGE ===")
                print()
                
                # Get basic statistics
                cur.execute("""
                    SELECT 
                        COUNT(*) as total_users,
                        COUNT(oxio_user_id) as users_with_oxio_uid,
                        COUNT(oxio_group_id) as users_with_oxio_group_id,
                        COUNT(*) - COUNT(oxio_user_id) as users_without_oxio_uid
                    FROM users
                """)
                
                stats = cur.fetchone()
                if not stats:
                    print("❌ No data found")
                    return
                
                total_users, users_with_uid, users_with_group_id, users_without_uid = stats
                
                coverage_percent = (users_with_uid / total_users * 100) if total_users > 0 else 0
                
                print(f"📊 STATISTICS:")
                print(f"   Total DOT users: {total_users:,}")
                print(f"   Users WITH OXIO User ID: {users_with_uid:,}")
                print(f"   Users WITHOUT OXIO User ID: {users_without_uid:,}")
                print(f"   Users with OXIO Group ID: {users_with_group_id:,}")
                print(f"   Coverage: {coverage_percent:.1f}%")
                print()
                
                # Show some examples of users without OXIO UIDs
                if users_without_uid > 0:
                    print(f"📋 SAMPLE USERS WITHOUT OXIO UID (showing first 10):")
                    cur.execute("""
                        SELECT id, email, display_name, firebase_uid, created_at
                        FROM users 
                        WHERE oxio_user_id IS NULL
                        ORDER BY created_at DESC
                        LIMIT 10
                    """)
                    
                    missing_users = cur.fetchall()
                    print(f"{'ID':<5} | {'Email':<25} | {'Name':<20} | {'Created':<12}")
                    print("-" * 70)
                    
                    for user in missing_users:
                        user_id, email, display_name, firebase_uid, created_at = user
                        email_short = email[:22] + "..." if email and len(email) > 22 else email or "N/A"
                        name_short = (display_name[:17] + "...") if display_name and len(display_name) > 17 else display_name or "N/A"
                        date_str = created_at.strftime('%Y-%m-%d') if created_at else "N/A"
                        print(f"{user_id:<5} | {email_short:<25} | {name_short:<20} | {date_str:<12}")
                    
                    print()
                else:
                    print("✅ ALL USERS HAVE OXIO USER IDS!")
                    print()
                
                # Check for users with invalid OXIO UIDs (should contain hyphens for UUID format)
                cur.execute("""
                    SELECT COUNT(*) 
                    FROM users 
                    WHERE oxio_user_id IS NOT NULL 
                    AND oxio_user_id NOT LIKE '%-%'
                """)
                
                invalid_uids = cur.fetchone()[0]
                if invalid_uids > 0:
                    print(f"⚠️  Found {invalid_uids} users with potentially invalid OXIO UIDs (missing hyphens)")
                    print()
                
                # Show recent activity
                cur.execute("""
                    SELECT COUNT(*) 
                    FROM users 
                    WHERE oxio_user_id IS NOT NULL 
                    AND created_at > CURRENT_TIMESTAMP - INTERVAL '7 days'
                """)
                
                recent_with_uid = cur.fetchone()[0]
                print(f"📈 RECENT ACTIVITY (last 7 days):")
                print(f"   Users created with OXIO UID: {recent_with_uid:,}")
                print()
                
                # Recommendation
                if users_without_uid > 0:
                    print(f"💡 RECOMMENDATION:")
                    print(f"   Run 'python add_oxio_user_ids.py --dry-run' to see what would be updated")
                    print(f"   Then run 'python add_oxio_user_ids.py --apply' to create OXIO UIDs")
                else:
                    print(f"🎉 ALL USERS HAVE OXIO USER IDS - NO ACTION NEEDED!")

def main():
    """Main function"""
    try:
        check_oxio_uid_coverage()
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    finally:
        if 'pool' in globals():
            pool.closeall()

if __name__ == "__main__":
    main()
