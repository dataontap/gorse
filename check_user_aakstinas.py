
#!/usr/bin/env python3
"""
Script to check user data for aakstinas+7@oxio.io
"""

import os
import psycopg2
from contextlib import contextmanager

# Initialize connection
database_url = os.environ.get('DATABASE_URL')

@contextmanager
def get_db_connection():
    connection = psycopg2.connect(database_url)
    try:
        yield connection
    finally:
        connection.close()

def check_user_aakstinas():
    """Check the specific user aakstinas+7@oxio.io"""
    email = "aakstinas+7@oxio.io"
    
    print(f"=== CHECKING USER: {email} ===")
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Get user data
                cur.execute("""
                    SELECT id, email, firebase_uid, display_name, stripe_customer_id, 
                           oxio_user_id, eth_address, created_at
                    FROM users 
                    WHERE email = %s
                """, (email,))
                user_data = cur.fetchone()
                
                if user_data:
                    print(f"✅ USER FOUND!")
                    print(f"User ID: {user_data[0]}")
                    print(f"Email: {user_data[1]}")
                    print(f"Firebase UID: {user_data[2]}")
                    print(f"Display Name: {user_data[3]}")
                    print(f"Stripe Customer ID: {user_data[4]}")
                    print(f"OXIO User ID: {user_data[5]}")
                    print(f"ETH Address: {user_data[6]}")
                    print(f"Created At: {user_data[7]}")
                    
                    # Check subscriptions
                    cur.execute("""
                        SELECT subscription_type, status, start_date, end_date
                        FROM subscriptions 
                        WHERE user_id = %s 
                        ORDER BY created_at DESC
                    """, (user_data[0],))
                    subscriptions = cur.fetchall()
                    
                    print(f"\n📋 SUBSCRIPTIONS ({len(subscriptions)}):")
                    for sub in subscriptions:
                        print(f"  - {sub[0]}: {sub[1]} ({sub[2]} to {sub[3]})")
                    
                    # Check purchases
                    cur.execute("""
                        SELECT StripeProductID, TotalAmount, DateCreated
                        FROM purchases 
                        WHERE UserID = %s OR FirebaseUID = %s
                        ORDER BY DateCreated DESC LIMIT 5
                    """, (user_data[0], user_data[2]))
                    purchases = cur.fetchall()
                    
                    print(f"\n💰 RECENT PURCHASES ({len(purchases)}):")
                    for purchase in purchases:
                        print(f"  - {purchase[0]}: ${purchase[1]/100:.2f} on {purchase[2]}")
                    
                    # Check OXIO activations
                    cur.execute("""
                        SELECT product_id, iccid, line_id, phone_number, activation_status, created_at
                        FROM oxio_activations 
                        WHERE user_id = %s 
                        ORDER BY created_at DESC
                    """, (user_data[0],))
                    activations = cur.fetchall()
                    
                    print(f"\n📱 OXIO ACTIVATIONS ({len(activations)}):")
                    for activation in activations:
                        print(f"  - {activation[0]}: {activation[4]} - {activation[3]} on {activation[5]}")
                    
                else:
                    print(f"❌ USER NOT FOUND!")
                    
                    # Check if user exists with similar email
                    cur.execute("""
                        SELECT email FROM users 
                        WHERE email LIKE %s
                    """, (f"%{email.split('@')[0]}%",))
                    similar = cur.fetchall()
                    
                    if similar:
                        print(f"Similar emails found:")
                        for sim in similar:
                            print(f"  - {sim[0]}")
                
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    check_user_aakstinas()
