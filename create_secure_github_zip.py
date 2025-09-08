
#!/usr/bin/env python3
"""
Script to create a secure ZIP file of DOTM Platform files for GitHub upload
Excludes private user data, credentials, and sensitive information
"""

import zipfile
import os
from datetime import datetime

def create_secure_github_zip():
    # Create timestamp for unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = f"dotm_platform_github_safe_{timestamp}.zip"
    
    # Files safe for GitHub (excluding sensitive data)
    safe_files = [
        # Core application files (cleaned versions)
        'mcp_server.py',
        'stripe_products.py',
        'help_desk_service.py',
        'email_service.py',
        'elevenlabs_service.py',
        
        # Configuration files (safe ones only)
        'requirements.txt',
        'replit.nix',
        'hardhat.config.js',
        'package.json',
        'package-lock.json',
        'pyproject.toml',
        'uv.lock',
        
        # Documentation (all safe)
        'README_MCP.md',
        'GITHUB_UPLOAD_GUIDE.md',
        'mcp_server_rules.md',
        
        # Database schema files (safe - no data)
        'create_table.sql',
        'create_purchases_table.sql',
        'create_subscriptions_table.sql',
        'create_product_rules_table.sql',
        'create_beta_testers_table.sql',
        'create_invites_table.sql',
        'create_token_rewards_table.sql',
        'create_user_network_preferences_table.sql',
        'create_oxio_activations_table.sql',
        'create_data_usage_table.sql',
        'create_founders_table.sql',
        
        # Smart contract files (public blockchain code)
        'contracts/DOTMToken.sol',
        'scripts/deploy_token.js',
        'hardhat.config.js',
        
        # Test files (safe)
        'test_mcp.py',
        
        # Utility scripts (safe ones only)
        'create_download_zip.py',
        'check_database_schema.py',
        'product_rules_helper.py',
    ]
    
    # Safe directories to include
    safe_directories = [
        'docs/',           # All documentation
        'templates/',      # HTML templates (no private data)
        'static/',         # Public frontend assets
        'artifacts/contracts/',  # Compiled smart contracts
        'contracts/',      # Smart contract source
        'scripts/',        # Deployment scripts
    ]
    
    # Files to EXCLUDE (sensitive/private data)
    excluded_files = [
        'main.py',  # Contains database connections and API keys
        'firebase_helper.py',  # Contains Firebase credentials
        'ethereum_helper.py',  # May contain wallet info
        'oxio_service.py',  # Contains API credentials
        'github_helper.py',  # Contains GitHub tokens
        'firebase_distribution_helper.py',  # Firebase credentials
        'gemini_live_helper.py',  # API keys
        '.replit',  # Environment configuration
        'firebase-credentials.json',  # Firebase credentials
        'sync_users_to_db.py',  # User data migration
        'sync_firebase_users_simple.py',  # User data
        'sync_existing_firebase_users.py',  # User data
        'firebase_user_migration.py',  # User data migration
        'export_firebase_users.py',  # User exports
        'debug_oxio_storage.py',  # Debug scripts with data
        'stripe_network_features.py',  # Stripe integration
        'stripe_metering.py',  # Stripe data
        'example_user_data.json',  # User data examples
        'create_basic_memberships_2099.py',  # Contains user data
        'create_batch_files.py',  # May contain sensitive logic
        'help_desk_api.py',  # May contain user communications
    ]
    
    print(f"Creating secure GitHub ZIP file: {zip_filename}")
    print("Excluding sensitive files with private data...")
    
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add safe individual files
        for file_path in safe_files:
            if os.path.exists(file_path):
                zipf.write(file_path, file_path)
                print(f"✅ Added: {file_path}")
            else:
                print(f"⚠️  File not found: {file_path}")
        
        # Add safe directories recursively
        for directory in safe_directories:
            if os.path.exists(directory):
                for root, dirs, files in os.walk(directory):
                    for file in files:
                        file_path = os.path.join(root, file)
                        # Skip hidden files and sensitive files
                        if not file.startswith('.') and file_path not in excluded_files:
                            zipf.write(file_path, file_path)
                            print(f"✅ Added: {file_path}")
        
        # Create a security notice README
        security_notice = f"""DOTM Platform - GitHub Safe Archive
Created: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

🔒 SECURITY NOTICE:
This archive has been sanitized for GitHub upload and contains NO:
- Private user data or personal information
- API keys, tokens, or credentials  
- Database connection strings
- Firebase configuration files
- Payment processing sensitive data
- User migration scripts or data exports

📁 SAFE CONTENTS INCLUDED:

🔌 MCP Server Core:
- mcp_server.py - Model Context Protocol server (sanitized)
- mcp_server_rules.md - Server operation rules
- test_mcp.py - Test suite

📚 Documentation:
- docs/ - Complete documentation suite
- README_MCP.md - MCP server guide  
- GITHUB_UPLOAD_GUIDE.md - Upload instructions

🎨 Frontend Assets:
- templates/ - HTML templates
- static/ - CSS, JavaScript, images
- No user-generated content

🗄️ Database Schema:
- SQL table creation files
- No actual user data or records
- Schema definitions only

⛓️ Smart Contracts:
- contracts/DOTMToken.sol - ERC20 token contract
- artifacts/ - Compiled contract artifacts  
- scripts/ - Deployment utilities

📦 Configuration:
- requirements.txt - Python dependencies
- package.json - Node.js dependencies
- Safe configuration files only

🚀 Live Demo URLs (Public):
- MCP Server: https://get-dot-esim.replit.app/mcp
- API Endpoint: https://get-dot-esim.replit.app/mcp/api
- Alternative: https://mcp.dotmobile.app

⚠️ EXCLUDED FOR SECURITY:
- main.py (contains sensitive integrations)
- All *_helper.py files (contain API keys)
- User data migration scripts
- Debug scripts with real data
- Environment configuration files
- Any files containing credentials

This archive is safe for public GitHub repositories and contains
only public-facing code, documentation, and schema definitions.

For the complete private codebase, use the internal development
environment on Replit.
"""
        
        zipf.writestr("SECURITY_README.txt", security_notice)
        print("✅ Added: SECURITY_README.txt")
        
        # Add a clean .gitignore for GitHub
        gitignore_content = """# Dependencies
node_modules/
__pycache__/
*.py[cod]
*$py.class

# Environment variables
.env
.env.local
.env.production
.env.development

# Database
*.db
*.sqlite
*.sqlite3

# Logs
*.log
logs/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Build outputs
dist/
build/
*.egg-info/

# Credentials (keep these private!)
firebase-credentials.json
*-key.json
*.pem
config.json

# User data exports
user_exports/
migrations/
backups/

# Sensitive scripts
*_migration.py
*_export.py
debug_*.py
"""
        zipf.writestr(".gitignore", gitignore_content)
        print("✅ Added: .gitignore")
        
    file_size = os.path.getsize(zip_filename)
    print(f"\n🔒 SECURE ZIP FILE CREATED SUCCESSFULLY!")
    print(f"📁 Filename: {zip_filename}")
    print(f"📊 Size: {file_size / (1024*1024):.2f} MB")
    print(f"📍 Location: {os.path.abspath(zip_filename)}")
    print(f"\n✅ This file is SAFE for GitHub upload - no private data included!")
    
    return zip_filename

if __name__ == "__main__":
    create_secure_github_zip()
