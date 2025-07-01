
#!/usr/bin/env python3
"""
Script to check the actual database schema and column names
"""

import os
import psycopg2

def check_database_schema():
    """Check the actual database schema"""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("DATABASE_URL not set")
        return
    
    try:
        conn = psycopg2.connect(database_url)
        with conn.cursor() as cur:
            # Check what columns exist in users table
            cur.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'users'
                ORDER BY ordinal_position
            """)
            
            columns = cur.fetchall()
            
            print("=== USERS TABLE SCHEMA ===")
            for column_name, data_type, is_nullable in columns:
                print(f"{column_name:20} {data_type:15} {'NULL' if is_nullable == 'YES' else 'NOT NULL'}")
            
            # Check if there are any users in the table
            cur.execute("SELECT COUNT(*) FROM users")
            user_count = cur.fetchone()[0]
            print(f"\nTotal users in database: {user_count}")
            
            # Check for Firebase-related columns specifically
            firebase_columns = [col for col in columns if 'firebase' in col[0].lower()]
            if firebase_columns:
                print(f"\nFirebase-related columns found:")
                for col in firebase_columns:
                    print(f"  - {col[0]}")
            else:
                print(f"\nNo Firebase-related columns found!")
                
        conn.close()
        
    except Exception as e:
        print(f"Error checking database schema: {str(e)}")

if __name__ == "__main__":
    check_database_schema()
