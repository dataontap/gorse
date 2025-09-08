
#!/usr/bin/env python3
"""
Script to create a ZIP file of the DOTM Platform files for download
"""

import zipfile
import os
from datetime import datetime

def create_platform_zip():
    # Create timestamp for unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = f"dotm_platform_{timestamp}.zip"
    
    # Files and directories to include
    files_to_include = [
        # Main application files
        'main.py',
        'mcp_server.py',
        'oxio_service.py',
        'stripe_products.py',
        'help_desk_service.py',
        'ethereum_helper.py',
        'firebase_helper.py',
        'email_service.py',
        'elevenlabs_service.py',
        
        # Configuration files
        'requirements.txt',
        'replit.nix',
        '.replit',
        'hardhat.config.js',
        'package.json',
        
        # Documentation
        'README_MCP.md',
        'GITHUB_UPLOAD_GUIDE.md',
        'mcp_server_rules.md',
        
        # Database scripts
        'create_table.sql',
        'create_purchases_table.sql',
        'create_subscriptions_table.sql',
        'create_product_rules_table.sql',
        'create_beta_testers_table.sql',
        'create_invites_table.sql',
        'create_token_rewards_table.sql',
        'create_user_network_preferences_table.sql',
        'create_oxio_activations_table.sql',
        
        # Migration and sync scripts
        'sync_users_to_db.py',
        'firebase_user_migration.py',
        'export_firebase_users.py',
        'stripe_network_features.py',
        'stripe_metering.py',
        
        # Smart contract files
        'contracts/DOTMToken.sol',
        'scripts/deploy_token.js',
        
        # Test files
        'test_mcp.py',
    ]
    
    # Directories to include recursively
    directories_to_include = [
        'docs/',
        'templates/',
        'static/',
        'artifacts/contracts/',
    ]
    
    print(f"Creating ZIP file: {zip_filename}")
    
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add individual files
        for file_path in files_to_include:
            if os.path.exists(file_path):
                zipf.write(file_path, file_path)
                print(f"Added: {file_path}")
            else:
                print(f"Warning: File not found: {file_path}")
        
        # Add directories recursively
        for directory in directories_to_include:
            if os.path.exists(directory):
                for root, dirs, files in os.walk(directory):
                    for file in files:
                        file_path = os.path.join(root, file)
                        zipf.write(file_path, file_path)
                        print(f"Added: {file_path}")
            else:
                print(f"Warning: Directory not found: {directory}")
        
        # Add a README for the ZIP contents
        readme_content = f"""DOTM Platform Archive
Created: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

This archive contains the complete DOTM Platform codebase including:

📁 Core Application:
- main.py - Main Flask application
- mcp_server.py - Model Context Protocol server
- oxio_service.py - OXIO API integration
- stripe_products.py - Payment processing

📁 Documentation:
- docs/ - Complete documentation
- README_MCP.md - MCP server documentation
- GITHUB_UPLOAD_GUIDE.md - GitHub publishing guide

📁 Frontend:
- templates/ - HTML templates
- static/ - CSS, JavaScript, and assets

📁 Database:
- SQL files for table creation
- Migration and sync scripts

📁 Smart Contracts:
- contracts/ - Solidity contracts
- artifacts/ - Compiled contract artifacts

📁 Configuration:
- requirements.txt - Python dependencies
- package.json - Node.js dependencies
- hardhat.config.js - Blockchain development config

🚀 Live Platform URLs:
- Main Platform: https://get-dot-esim.replit.app
- MCP Server: https://get-dot-esim.replit.app/mcp
- Alternative MCP: https://mcp.dotmobile.app

For deployment instructions, see GITHUB_UPLOAD_GUIDE.md
"""
        
        zipf.writestr("README_ARCHIVE.txt", readme_content)
        print("Added: README_ARCHIVE.txt")
    
    file_size = os.path.getsize(zip_filename)
    print(f"\n✅ ZIP file created successfully!")
    print(f"📁 Filename: {zip_filename}")
    print(f"📊 Size: {file_size / (1024*1024):.2f} MB")
    print(f"📍 Location: {os.path.abspath(zip_filename)}")
    
    return zip_filename

if __name__ == "__main__":
    create_platform_zip()
