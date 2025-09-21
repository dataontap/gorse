
#!/usr/bin/env python3
"""
Script to analyze stored OXIO API responses from the database.
This helps debug issues and understand API response patterns.

Usage:
  python analyze_oxio_responses.py [--failed-only] [--recent-hours=24]
"""

import os
import psycopg2
import argparse
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any

def analyze_oxio_responses(failed_only: bool = False, recent_hours: int = None) -> bool:
    """
    Analyze OXIO API responses stored in the database
    
    Args:
        failed_only: If True, only show failed responses
        recent_hours: If specified, only show responses from last N hours
        
    Returns:
        True if successful, False if errors occurred
    """
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("ERROR: DATABASE_URL not set")
        return False
    
    try:
        conn = psycopg2.connect(database_url)
        
        with conn.cursor() as cur:
            # Check if the table exists
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'oxio_api_responses'
                )
            """)
            
            if not cur.fetchone()[0]:
                print("❌ oxio_api_responses table does not exist")
                print("Run the add_oxio_user_ids.py script first to create responses")
                return False
            
            # Build the query with filters
            where_conditions = []
            params = []
            
            if failed_only:
                where_conditions.append("success = false")
            
            if recent_hours:
                where_conditions.append("created_at >= %s")
                cutoff_time = datetime.now() - timedelta(hours=recent_hours)
                params.append(cutoff_time)
            
            where_clause = ""
            if where_conditions:
                where_clause = "WHERE " + " AND ".join(where_conditions)
            
            # Get overall statistics
            print("=== OXIO API RESPONSE ANALYSIS ===")
            
            cur.execute(f"""
                SELECT 
                    COUNT(*) as total_responses,
                    COUNT(CASE WHEN success = true THEN 1 END) as successful,
                    COUNT(CASE WHEN success = false THEN 1 END) as failed,
                    COUNT(CASE WHEN method = 'created' THEN 1 END) as created,
                    COUNT(CASE WHEN method = 'found' THEN 1 END) as found,
                    MIN(created_at) as oldest_response,
                    MAX(created_at) as newest_response
                FROM oxio_api_responses
                {where_clause}
            """, params)
            
            stats = cur.fetchone()
            total, successful, failed, created, found, oldest, newest = stats
            
            if total == 0:
                print("No responses found matching the criteria")
                return True
            
            print(f"📊 OVERALL STATISTICS:")
            print(f"   Total responses: {total:,}")
            print(f"   Successful: {successful:,} ({successful/total*100:.1f}%)")
            print(f"   Failed: {failed:,} ({failed/total*100:.1f}%)")
            print(f"   New users created: {created:,}")
            print(f"   Existing users found: {found:,}")
            print(f"   Date range: {oldest} to {newest}")
            
            # Error analysis
            if failed > 0:
                print(f"\n❌ ERROR ANALYSIS:")
                cur.execute(f"""
                    SELECT 
                        error_code,
                        error_message,
                        COUNT(*) as error_count
                    FROM oxio_api_responses
                    {where_clause} AND success = false
                    GROUP BY error_code, error_message
                    ORDER BY error_count DESC
                """, params)
                
                errors = cur.fetchall()
                for error_code, error_msg, count in errors:
                    print(f"   {error_code or 'Unknown'}: {count:,} occurrences")
                    if error_msg:
                        print(f"      Message: {error_msg[:100]}...")
            
            # Recent activity
            if not recent_hours:
                print(f"\n📈 RECENT ACTIVITY (last 24 hours):")
                cur.execute("""
                    SELECT 
                        DATE_TRUNC('hour', created_at) as hour,
                        COUNT(*) as responses_per_hour,
                        COUNT(CASE WHEN success = true THEN 1 END) as successful_per_hour
                    FROM oxio_api_responses
                    WHERE created_at >= NOW() - INTERVAL '24 hours'
                    GROUP BY DATE_TRUNC('hour', created_at)
                    ORDER BY hour DESC
                    LIMIT 10
                """)
                
                activity = cur.fetchall()
                for hour, total_hour, success_hour in activity:
                    success_rate = (success_hour / total_hour * 100) if total_hour > 0 else 0
                    print(f"   {hour}: {total_hour:,} responses ({success_rate:.1f}% success)")
            
            # Sample failed responses for debugging
            if failed > 0:
                print(f"\n🔍 SAMPLE FAILED RESPONSES:")
                cur.execute(f"""
                    SELECT 
                        user_id,
                        email,
                        error_code,
                        error_message,
                        api_response_json,
                        created_at
                    FROM oxio_api_responses
                    {where_clause} AND success = false
                    ORDER BY created_at DESC
                    LIMIT 5
                """, params)
                
                samples = cur.fetchall()
                for i, (user_id, email, error_code, error_msg, response_json, created_at) in enumerate(samples, 1):
                    print(f"\n   Sample {i}:")
                    print(f"     User ID: {user_id}")
                    print(f"     Email: {email}")
                    print(f"     Error: {error_code} - {error_msg}")
                    print(f"     Time: {created_at}")
                    
                    # Try to parse and show relevant parts of the API response
                    try:
                        response_data = json.loads(response_json)
                        if 'api_response' in response_data:
                            api_resp = response_data['api_response']
                            if 'status_code' in api_resp:
                                print(f"     API Status Code: {api_resp['status_code']}")
                            if 'data' in api_resp and isinstance(api_resp['data'], dict):
                                if 'code' in api_resp['data']:
                                    print(f"     OXIO Error Code: {api_resp['data']['code']}")
                                if 'message' in api_resp['data']:
                                    print(f"     OXIO Message: {api_resp['data']['message']}")
                    except (json.JSONDecodeError, KeyError) as e:
                        print(f"     (Could not parse response JSON: {str(e)})")
            
            return True
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False
        
    finally:
        if 'conn' in locals():
            conn.close()

def main():
    """Main function with command-line argument parsing"""
    parser = argparse.ArgumentParser(
        description="Analyze stored OXIO API responses"
    )
    parser.add_argument(
        '--failed-only', 
        action='store_true', 
        help='Only show failed responses'
    )
    parser.add_argument(
        '--recent-hours', 
        type=int, 
        help='Only show responses from last N hours'
    )
    
    args = parser.parse_args()
    
    print("OXIO API Response Analysis Tool")
    print("=" * 40)
    
    filters = []
    if args.failed_only:
        filters.append("failed responses only")
    if args.recent_hours:
        filters.append(f"last {args.recent_hours} hours")
    
    if filters:
        print(f"Filters: {', '.join(filters)}")
    print()
    
    success = analyze_oxio_responses(
        failed_only=args.failed_only,
        recent_hours=args.recent_hours
    )
    
    if not success:
        print("\n❌ Analysis failed. Please check error messages above.")
        exit(1)
    
    print(f"\n✅ Analysis completed successfully.")

if __name__ == "__main__":
    main()
