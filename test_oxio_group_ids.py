#!/usr/bin/env python3
"""
Test script to verify OXIO Group ID assignment works on a small batch
"""

import os
import psycopg2
import time
import random

def generate_unique_group_id():
    """Generate a unique OXIO Group ID following the DOTM pattern"""
    timestamp = int(time.time())
    random_suffix = random.randint(1000, 9999)
    return f"DOTM-{timestamp}-{random_suffix}"

def test_oxio_group_id_assignment():
    """Test OXIO Group ID assignment on first 5 users only"""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("ERROR: DATABASE_URL not set")
        return False
    
    try:
        conn = psycopg2.connect(database_url)
        with conn.cursor() as cur:
            print("=== TESTING OXIO GROUP ID ASSIGNMENT ===")
            
            # Get first 5 users without OXIO Group ID
            cur.execute("""
                SELECT id, email, display_name 
                FROM users 
                WHERE oxio_group_id IS NULL 
                ORDER BY id 
                LIMIT 5
            """)
            
            test_users = cur.fetchall()
            
            if not test_users:
                print("No users found without OXIO Group IDs")
                return True
            
            print(f"Found {len(test_users)} users to test:")
            for user_id, email, display_name in test_users:
                print(f"  User {user_id}: {email or 'no email'}")
            
            # Generate and assign group IDs
            print("\nAssigning OXIO Group IDs...")
            updates = []
            
            for user_id, email, display_name in test_users:
                group_id = generate_unique_group_id()
                updates.append((group_id, user_id))
                print(f"  User {user_id}: {group_id}")
                
                # Small delay for uniqueness
                time.sleep(0.001)
            
            # Execute updates
            cur.executemany("""
                UPDATE users 
                SET oxio_group_id = %s 
                WHERE id = %s
            """, updates)
            conn.commit()
            
            print(f"\n✅ Successfully updated {len(updates)} users")
            
            # Verify updates
            print("\nVerifying updates...")
            for group_id, user_id in updates:
                cur.execute("SELECT oxio_group_id FROM users WHERE id = %s", (user_id,))
                result = cur.fetchone()
                if result and result[0] == group_id:
                    print(f"  ✅ User {user_id}: {result[0]}")
                else:
                    print(f"  ❌ User {user_id}: Expected {group_id}, got {result[0] if result else None}")
                    return False
            
            print("\n🎉 Test completed successfully!")
            return True
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    test_oxio_group_id_assignment()