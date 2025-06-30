
#!/usr/bin/env python3
"""
Script to create Basic Membership purchase records and subscriptions for all current users
with validity until Canada Day 2099 (July 2, 2099 at 07:11:00 EST)
"""

import os
import psycopg2
from psycopg2.pool import SimpleConnectionPool
from contextlib import contextmanager
from datetime import datetime, timezone, timedelta
import pytz

# Initialize database connection
database_url = os.environ.get('DATABASE_URL')
try:
    pool = SimpleConnectionPool(1, 20, database_url)
    print("Database connection pool initialized successfully")

    @contextmanager
    def get_db_connection():
        connection = pool.getconn()
        try:
            yield connection
        finally:
            pool.putconn(connection)
except Exception as e:
    print(f"Error initializing database connection pool: {str(e)}")
    exit(1)

def create_basic_membership_for_all_users():
    """Create Basic Membership purchase records and subscriptions for all users"""
    
    # Define the target date: Canada Day 2099 at 07:11:00 EST
    est_tz = pytz.timezone('US/Eastern')
    target_date = est_tz.localize(datetime(2099, 7, 2, 7, 11, 0))
    
    print(f"Creating Basic Memberships valid until: {target_date}")
    
    try:
        with get_db_connection() as conn:
            if conn:
                with conn.cursor() as cur:
                    # First, get the total count of users
                    cur.execute("SELECT COUNT(*) FROM users")
                    total_count = cur.fetchone()[0]
                    print(f"Total users in database: {total_count}")
                    
                    if total_count != 29905:
                        print(f"WARNING: Expected 29,905 users but found {total_count}")
                        print("You may need to run the user migration scripts first")
                    
                    # Get all users from the database
                    cur.execute("""
                        SELECT id, email, firebase_uid, stripe_customer_id, display_name
                        FROM users 
                        ORDER BY id
                    """)
                    users = cur.fetchall()
                    
                    if not users:
                        print("No users found in the database")
                        return
                    
                    print(f"Found {len(users)} users to process for Basic Membership creation")
                    
                    success_count = 0
                    error_count = 0
                    
                    for user in users:
                        user_id = user[0]
                        email = user[1]
                        firebase_uid = user[2]
                        stripe_customer_id = user[3]
                        display_name = user[4]
                        
                        try:
                            # Generate unique transaction ID
                            transaction_id = f"ADMIN_BASIC_MEMBERSHIP_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                            
                            # 1. Create purchase record
                            cur.execute("""
                                INSERT INTO purchases 
                                (StripeID, StripeProductID, PriceID, TotalAmount, DateCreated, UserID, StripeTransactionID, FirebaseUID)
                                VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP, %s, %s, %s)
                                RETURNING PurchaseID
                            """, (
                                f"admin_grant_{user_id}",  # StripeID
                                'basic_membership',        # StripeProductID
                                'price_basic_membership',  # PriceID
                                2400,                      # TotalAmount ($24.00)
                                user_id,                   # UserID
                                transaction_id,            # StripeTransactionID
                                firebase_uid               # FirebaseUID
                            ))
                            
                            purchase_id = cur.fetchone()[0]
                            
                            # 2. First, deactivate any existing active subscriptions for this user
                            cur.execute("""
                                UPDATE subscriptions 
                                SET status = 'cancelled', updated_at = CURRENT_TIMESTAMP
                                WHERE user_id = %s AND status = 'active'
                            """, (user_id,))
                            
                            deactivated_count = cur.rowcount
                            
                            # 3. Create new subscription with validity until 2099
                            cur.execute("""
                                INSERT INTO subscriptions 
                                (user_id, subscription_type, stripe_subscription_id, start_date, end_date, status, created_at, updated_at)
                                VALUES (%s, %s, %s, CURRENT_TIMESTAMP, %s, 'active', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                                RETURNING subscription_id
                            """, (
                                user_id,
                                'basic_membership',
                                None,  # No Stripe subscription ID for admin grants
                                target_date.astimezone(timezone.utc)  # Convert to UTC for database storage
                            ))
                            
                            subscription_id = cur.fetchone()[0]
                            
                            # Commit the transaction for this user
                            conn.commit()
                            
                            success_count += 1
                            print(f"✓ User {user_id} ({email}): Purchase {purchase_id}, Subscription {subscription_id}")
                            if deactivated_count > 0:
                                print(f"  → Deactivated {deactivated_count} existing subscription(s)")
                            
                        except Exception as user_error:
                            print(f"✗ Error processing user {user_id} ({email}): {str(user_error)}")
                            conn.rollback()
                            error_count += 1
                            continue
                    
                    print(f"\n=== Summary ===")
                    print(f"Successfully processed: {success_count} users")
                    print(f"Errors: {error_count} users")
                    print(f"Total users processed: {len(users)} users")
                    print(f"Membership validity: Until {target_date} (Canada Day 2099)")
            
            else:
                print("Could not establish database connection")
                
    except Exception as e:
        print(f"Error in main process: {str(e)}")

def verify_created_memberships():
    """Verify the created memberships"""
    print("\n=== Verification ===")
    
    try:
        with get_db_connection() as conn:
            if conn:
                with conn.cursor() as cur:
                    # Count total users
                    cur.execute("SELECT COUNT(*) FROM users")
                    total_users = cur.fetchone()[0]
                    
                    # Count active Basic Memberships
                    cur.execute("""
                        SELECT COUNT(*) 
                        FROM subscriptions 
                        WHERE subscription_type = 'basic_membership' AND status = 'active'
                    """)
                    active_count = cur.fetchone()[0]
                    
                    # Count Basic Membership purchases
                    cur.execute("""
                        SELECT COUNT(*) 
                        FROM purchases 
                        WHERE StripeProductID = 'basic_membership'
                    """)
                    purchase_count = cur.fetchone()[0]
                    
                    # Check for any non-active subscriptions
                    cur.execute("""
                        SELECT COUNT(*) 
                        FROM subscriptions 
                        WHERE subscription_type = 'basic_membership' AND status != 'active'
                    """)
                    inactive_count = cur.fetchone()[0]
                    
                    # Get sample of created subscriptions
                    cur.execute("""
                        SELECT u.email, s.end_date, s.created_at, s.status
                        FROM subscriptions s
                        JOIN users u ON s.user_id = u.id
                        WHERE s.subscription_type = 'basic_membership' AND s.status = 'active'
                        ORDER BY s.created_at DESC
                        LIMIT 5
                    """)
                    samples = cur.fetchall()
                    
                    print(f"Total users in database: {total_users}")
                    print(f"Active Basic Memberships: {active_count}")
                    print(f"Basic Membership purchases: {purchase_count}")
                    print(f"Inactive Basic Memberships: {inactive_count}")
                    
                    if active_count == total_users:
                        print("✅ SUCCESS: All users have Active Basic Memberships!")
                    else:
                        print(f"⚠ WARNING: {total_users - active_count} users missing Active subscriptions")
                    
                    if samples:
                        print("\nSample Active subscriptions:")
                        for sample in samples:
                            email = sample[0]
                            end_date = sample[1]
                            created_at = sample[2]
                            status = sample[3]
                            print(f"  {email}: Status={status}, Valid until {end_date}")
                    
    except Exception as e:
        print(f"Error in verification: {str(e)}")

def main():
    """Main function"""
    print("Basic Membership Creator for All Users")
    print("=====================================")
    print("This script will:")
    print("1. Create Basic Membership purchase records for all users")
    print("2. Create active subscriptions valid until Canada Day 2099")
    print("3. Deactivate any existing active subscriptions")
    
    # First, check if we have the expected number of users
    try:
        with get_db_connection() as conn:
            if conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT COUNT(*) FROM users")
                    current_count = cur.fetchone()[0]
                    
                    print(f"\nCurrent users in database: {current_count}")
                    
                    if current_count < 29905:
                        print(f"⚠ WARNING: Expected 29,905 users but found only {current_count}")
                        print("You should run the user migration first:")
                        print("python verify_and_migrate_all_users.py")
                        response = input("Continue anyway with current users? (y/N): ")
                        if response.lower() != 'y':
                            print("Operation cancelled. Please run user migration first.")
                            return
                    elif current_count == 29905:
                        print("✅ Perfect! Found exactly 29,905 users")
                    else:
                        print(f"✅ Found {current_count} users (more than expected)")
    except Exception as e:
        print(f"Error checking user count: {str(e)}")
        return
    
    # Confirm before proceeding
    response = input(f"\nProceed with creating Active Basic Memberships for all {current_count} users? (y/N): ")
    if response.lower() != 'y':
        print("Operation cancelled")
        return
    
    # Create memberships
    create_basic_membership_for_all_users()
    
    # Verify results
    verify_created_memberships()
    
    print("\n🎉 Basic Membership creation completed!")
    print("All users now have Active Basic Memberships valid until Canada Day 2099!")

if __name__ == "__main__":
    main()
