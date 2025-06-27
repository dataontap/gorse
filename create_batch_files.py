
#!/usr/bin/env python3
"""
Script to create batch files from existing user data
Use this if you already have user data exported
"""

import json
import os
from typing import List, Dict, Any

def create_batch_files_from_data(input_file: str, batch_size: int = 1000):
    """Create batch files from a single large user data file"""
    try:
        print(f"Loading user data from {input_file}")
        
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle different JSON structures
        if isinstance(data, list):
            all_users = data
        elif isinstance(data, dict) and 'users' in data:
            all_users = data['users']
        else:
            print("Error: Invalid JSON structure")
            return
        
        print(f"Found {len(all_users)} users")
        
        # Create batch files
        batch_number = 1
        for i in range(0, len(all_users), batch_size):
            batch_users = all_users[i:i + batch_size]
            
            batch_data = {
                "users": batch_users,
                "batch_number": batch_number,
                "total_users": len(batch_users)
            }
            
            filename = f"users_batch_{batch_number}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(batch_data, f, indent=2, ensure_ascii=False)
            
            print(f"Created {filename} with {len(batch_users)} users")
            batch_number += 1
        
        print(f"Created {batch_number - 1} batch files successfully!")
        
    except Exception as e:
        print(f"Error creating batch files: {str(e)}")

def main():
    print("Batch File Creator")
    print("==================")
    
    input_file = input("Enter path to your user data JSON file: ").strip()
    
    if not os.path.exists(input_file):
        print(f"Error: File not found: {input_file}")
        return
    
    batch_size = int(input("Enter batch size (default 1000): ").strip() or "1000")
    
    create_batch_files_from_data(input_file, batch_size)

if __name__ == "__main__":
    main()
