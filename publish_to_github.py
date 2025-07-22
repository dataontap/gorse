
#!/usr/bin/env python3
"""
Script to publish current code to GitHub repository
"""

import os
import subprocess
import json
from datetime import datetime

def run_command(command, cwd=None):
    """Run a shell command and return the result"""
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            cwd=cwd
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def init_git_repo():
    """Initialize git repository if not already initialized"""
    if not os.path.exists('.git'):
        print("Initializing Git repository...")
        success, stdout, stderr = run_command("git init")
        if not success:
            print(f"Failed to initialize git: {stderr}")
            return False
        
        # Set up git config if not set
        run_command("git config user.name 'DOT Mobile API'")
        run_command("git config user.email 'api@dotmobile.app'")
    
    return True

def create_gitignore():
    """Create .gitignore file for the project"""
    gitignore_content = """
# Environment variables
.env
.env.local
.env.production

# Database
*.db
*.sqlite

# Logs
*.log
logs/

# Cache
__pycache__/
*.pyc
*.pyo
cache/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Node modules (if any)
node_modules/

# Python virtual environment
venv/
env/

# Sensitive files
*.key
*.pem
service-account.json

# Build artifacts
build/
dist/
artifacts/

# Replit specific
.replit
replit.nix

# User uploads and attachments
attached_assets/
uploads/

# Migration files with sensitive data
users_batch_*.json
missing_*.json
retry_*.json
migration_*.json
duplicate_analysis_*.json
"""
    
    with open('.gitignore', 'w') as f:
        f.write(gitignore_content.strip())
    
    print("Created .gitignore file")

def create_readme():
    """Create comprehensive README.md"""
    readme_content = """
# dot. - DOT GLOBAL CONNECTIVITY

A comprehensive Flask-based API platform providing global eSIM connectivity, token management, and network services.

## Features

- **Firebase Authentication**: Secure user authentication and management
- **OXIO eSIM Integration**: Global eSIM activation and connectivity services  
- **Stripe Payments**: Subscription and marketplace payment processing
- **DOTM Token System**: Blockchain token rewards and management
- **Network Features**: Configurable network optimization and security
- **Beta Program**: eSIM testing and activation for beta users
- **Real-time Notifications**: FCM push notifications and WebSocket support

## API Documentation

- **Swagger UI**: [https://get-dot-esim.replit.app/api/](https://get-dot-esim.replit.app/api/)
- **Static Docs**: [https://get-dot-esim.replit.app/api/export-docs](https://get-dot-esim.replit.app/api/export-docs)
- **GORSE Docs**: [https://gorse.dotmobile.app/api/](https://gorse.dotmobile.app/api/)

## Quick Start

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up environment variables (see .env.example)
4. Run the application: `python main.py`

## Environment Variables

```
DATABASE_URL=postgresql://...
STRIPE_SECRET_KEY=sk_...
FIREBASE_ADMIN_SDK={"type": "service_account"...}
OXIO_API_KEY=...
OXIO_AUTH_TOKEN=...
```

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register Firebase user
- `GET /api/auth/current-user` - Get current user data
- `POST /api/auth/update-imei` - Update user IMEI

### OXIO eSIM Services  
- `GET /api/oxio/test-connection` - Test OXIO API connection
- `POST /api/oxio/activate-line` - Activate eSIM line
- `GET /api/oxio-user-data` - Get user OXIO data

### Payments & Subscriptions
- `POST /api/record-global-purchase` - Record marketplace purchase
- `GET /api/subscription-status` - Get user subscription status
- `GET /api/user/data-balance` - Get user data balance

### DOTM Tokens
- `GET /api/token/price` - Get current token price
- `GET /api/token/balance/<address>` - Get token balance
- `POST /api/token/founding-token` - Assign founding member token

### Network Features
- `GET /api/network-features/<firebase_uid>` - Get user network features
- `PUT /api/network-features/<firebase_uid>/<product_id>` - Toggle network feature

## Technology Stack

- **Backend**: Flask, Flask-RESTX, Flask-SocketIO
- **Database**: PostgreSQL with psycopg2
- **Authentication**: Firebase Admin SDK
- **Payments**: Stripe API
- **Blockchain**: Web3.py for Ethereum integration
- **eSIM**: OXIO API integration
- **Real-time**: WebSocket with SocketIO

## License

Proprietary - DOT Mobile Inc.

## Support

For API support, contact: api@dotmobile.app
"""
    
    with open('README.md', 'w') as f:
        f.write(readme_content.strip())
    
    print("Created README.md file")

def publish_to_github():
    """Main function to publish code to GitHub"""
    print("=== Publishing DOT Mobile API to GitHub ===")
    
    # Initialize git repository
    if not init_git_repo():
        return False
    
    # Create essential files
    create_gitignore()
    create_readme()
    
    # Add all files to git
    print("Adding files to git...")
    success, stdout, stderr = run_command("git add .")
    if not success:
        print(f"Failed to add files: {stderr}")
        return False
    
    # Create commit
    commit_message = f"DOT Mobile API v3.0 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    print(f"Creating commit: {commit_message}")
    success, stdout, stderr = run_command(f'git commit -m "{commit_message}"')
    if not success and "nothing to commit" not in stderr:
        print(f"Failed to create commit: {stderr}")
        return False
    
    print("✅ Git repository prepared successfully!")
    print("\nNext steps to publish to GitHub:")
    print("1. Create a new repository on GitHub")
    print("2. Run: git remote add origin https://github.com/yourusername/dot-mobile-api.git")
    print("3. Run: git branch -M main")
    print("4. Run: git push -u origin main")
    
    # Generate deployment summary
    summary = {
        "project": "dot. - DOT GLOBAL CONNECTIVITY", 
        "version": "3.0",
        "api_endpoints": 60,
        "main_features": [
            "Firebase Authentication",
            "OXIO eSIM Integration", 
            "Stripe Payments",
            "DOTM Token System",
            "Network Configuration",
            "Beta Program Management"
        ],
        "documentation_urls": [
            "https://get-dot-esim.replit.app/api/",
            "https://gorse.dotmobile.app/api/",
            "https://get-dot-esim.replit.app/api/export-docs"
        ],
        "timestamp": datetime.now().isoformat()
    }
    
    with open('deployment_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n📄 Deployment summary saved to deployment_summary.json")
    
    return True

if __name__ == "__main__":
    publish_to_github()
