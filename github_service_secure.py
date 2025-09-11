"""
Secure GitHub Service for automated repository uploads and management
Eliminates code injection vulnerabilities through safe JSON communication
"""

import os
import json
import tempfile
import subprocess
import re
from typing import Optional, Dict, List, Any
from datetime import datetime
import uuid
from github_config import github_config

class SecureGitHubService:
    def __init__(self):
        self.client = None
        # Load configuration from persistent storage
        config = github_config.get_repository()
        self.repo_owner = config.get('repo_owner')
        self.repo_name = config.get('repo_name')
        self.default_branch = config.get('default_branch', 'main')
        
        # Security: Set of allowed file extensions and patterns
        self.allowed_extensions = {
            '.py', '.js', '.html', '.css', '.md', '.txt', '.json', 
            '.yml', '.yaml', '.sql', '.sh', '.ts', '.jsx', '.tsx'
        }
        
        # Maximum file size (5MB)
        self.max_file_size = 5 * 1024 * 1024
    
    def _validate_input(self, value: str, field_name: str, max_length: int = 255) -> str:
        """Validate and sanitize input strings"""
        if not isinstance(value, str):
            raise ValueError(f"{field_name} must be a string")
        
        value = value.strip()
        if not value:
            raise ValueError(f"{field_name} cannot be empty")
            
        if len(value) > max_length:
            raise ValueError(f"{field_name} exceeds maximum length of {max_length}")
            
        # Remove dangerous characters
        value = re.sub(r'[<>"|*?\\]', '', value)
        
        return value
    
    def _validate_file_path(self, file_path: str) -> str:
        """Validate file path for security"""
        file_path = self._validate_input(file_path, "file_path", 500)
        
        # Prevent path traversal attacks
        if '..' in file_path or file_path.startswith('/'):
            raise ValueError("Invalid file path: path traversal not allowed")
        
        # Check file extension
        _, ext = os.path.splitext(file_path)
        if ext.lower() not in self.allowed_extensions:
            raise ValueError(f"File extension {ext} not allowed")
            
        return file_path
    
    def _validate_content(self, content: str) -> str:
        """Validate file content"""
        if not isinstance(content, str):
            raise ValueError("Content must be a string")
            
        if len(content.encode('utf-8')) > self.max_file_size:
            raise ValueError(f"Content exceeds maximum size of {self.max_file_size} bytes")
            
        return content
    
    def _validate_repository_info(self, owner: str, repo: str) -> tuple:
        """Validate repository owner and name"""
        owner = self._validate_input(owner, "repository owner", 100)
        repo = self._validate_input(repo, "repository name", 100)
        
        # GitHub username/repo validation
        if not re.match(r'^[a-zA-Z0-9._-]+$', owner):
            raise ValueError("Invalid repository owner format")
            
        if not re.match(r'^[a-zA-Z0-9._-]+$', repo):
            raise ValueError("Invalid repository name format")
            
        return owner, repo
    
    def get_authenticated_client(self) -> bool:
        """Test GitHub authentication using secure client"""
        try:
            # Create a temporary config file for testing
            test_config = {
                "operation": "test_auth"
            }
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(test_config, f)
                config_path = f.name
            
            try:
                result = subprocess.run([
                    'node', '-e', '''
                    const { getUncachableGitHubClient } = require('./github_client.js');
                    getUncachableGitHubClient().then(client => {
                        console.log("AUTH_SUCCESS");
                    }).catch(err => {
                        console.log("AUTH_ERROR", err.message);
                        process.exit(1);
                    });
                    '''
                ], capture_output=True, text=True, timeout=10)
                
                success = "AUTH_SUCCESS" in result.stdout
                if not success:
                    print(f"GitHub authentication failed: {result.stderr}")
                
                return success
                
            finally:
                # Clean up temp file
                try:
                    os.unlink(config_path)
                except:
                    pass
                    
        except Exception as e:
            print(f"Error testing GitHub authentication: {str(e)}")
            return False
    
    def set_repository(self, owner: str, repo_name: str, branch: str = "main"):
        """Set the target repository for uploads with validation"""
        owner, repo_name = self._validate_repository_info(owner, repo_name)
        branch = self._validate_input(branch, "branch", 100)
        
        self.repo_owner = owner
        self.repo_name = repo_name
        self.default_branch = branch
        
        # Persist configuration
        github_config.set_repository(owner, repo_name, branch)
        print(f"GitHub service configured for {owner}/{repo_name} (branch: {branch})")
    
    def upload_file(self, file_path: str, content: str, commit_message: str, 
                   repo_owner: Optional[str] = None, repo_name: Optional[str] = None) -> Dict[str, Any]:
        """Upload a single file to GitHub repository securely"""
        try:
            # Validate all inputs
            file_path = self._validate_file_path(file_path)
            content = self._validate_content(content)
            commit_message = self._validate_input(commit_message, "commit message", 500)
            
            owner = repo_owner or self.repo_owner
            repo = repo_name or self.repo_name
            
            if not owner or not repo:
                raise ValueError("Repository owner and name must be specified")
            
            owner, repo = self._validate_repository_info(owner, repo)
            
            # Create secure configuration for Node.js client
            config = {
                "owner": owner,
                "repo": repo,
                "path": file_path,
                "message": commit_message,
                "content": content,
                "branch": self.default_branch
            }
            
            # Write config to temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
                config_path = f.name
            
            try:
                # Execute secure Node.js client
                result = subprocess.run([
                    'node', 'github_secure_client.js', config_path
                ], capture_output=True, text=True, timeout=60)
                
                # Parse JSON response
                try:
                    response = json.loads(result.stdout.strip())
                except json.JSONDecodeError:
                    response = {
                        "status": "error",
                        "error": f"Invalid response: {result.stdout[:200]}"
                    }
                
                if response.get("status") == "success":
                    print(f"Successfully uploaded {file_path} to {owner}/{repo}")
                    return {
                        "status": "success",
                        "file_path": file_path,
                        "result": response
                    }
                else:
                    error_msg = response.get("error", "Unknown error")
                    print(f"Failed to upload {file_path}: {error_msg}")
                    return {
                        "status": "error",
                        "file_path": file_path,
                        "error": error_msg
                    }
                    
            finally:
                # Clean up temp file
                try:
                    os.unlink(config_path)
                except:
                    pass
                    
        except Exception as e:
            error_msg = f"Exception uploading {file_path}: {str(e)}"
            print(error_msg)
            return {
                "status": "error",
                "file_path": file_path,
                "error": error_msg
            }
    
    def upload_multiple_files(self, files: List[Dict[str, str]], 
                            repo_owner: Optional[str] = None, repo_name: Optional[str] = None) -> Dict[str, Any]:
        """Upload multiple files to GitHub repository securely"""
        if not isinstance(files, list):
            return {
                "status": "error",
                "error": "Files must be a list",
                "results": []
            }
        
        if len(files) > 50:  # Limit batch size
            return {
                "status": "error",
                "error": "Too many files in batch (max 50)",
                "results": []
            }
        
        owner = repo_owner or self.repo_owner
        repo = repo_name or self.repo_name
        
        if not owner or not repo:
            return {
                "status": "error",
                "error": "Repository owner and name must be specified",
                "results": []
            }
        
        try:
            owner, repo = self._validate_repository_info(owner, repo)
        except ValueError as e:
            return {
                "status": "error",
                "error": str(e),
                "results": []
            }
        
        print(f"Starting secure batch upload of {len(files)} files to {owner}/{repo}")
        
        results = []
        for i, file_info in enumerate(files):
            if not isinstance(file_info, dict):
                results.append({
                    "status": "error",
                    "error": "Invalid file info format",
                    "file_info": file_info
                })
                continue
            
            file_path = file_info.get('path')
            content = file_info.get('content', '')
            commit_message = file_info.get('message', f'Update {file_path}')
            
            if not file_path:
                results.append({
                    "status": "error",
                    "error": "Missing file path",
                    "file_info": file_info
                })
                continue
            
            result = self.upload_file(file_path, content, commit_message, owner, repo)
            results.append(result)
            
            # Small delay between uploads to avoid rate limiting
            if i < len(files) - 1:  # Don't delay after last file
                import time
                time.sleep(1)
        
        successful_uploads = [r for r in results if r.get('status') == 'success']
        failed_uploads = [r for r in results if r.get('status') == 'error']
        
        print(f"Secure batch upload completed: {len(successful_uploads)} successful, {len(failed_uploads)} failed")
        
        return {
            "status": "completed",
            "total_files": len(files),
            "successful": len(successful_uploads),
            "failed": len(failed_uploads),
            "results": results
        }
    
    def get_project_files_for_upload(self) -> List[Dict[str, str]]:
        """Get list of key project files to upload to GitHub with security validation"""
        files_to_upload = []
        
        # Core application files - only include safe files
        core_files = [
            'main.py',
            'github_service_secure.py',
            'oxio_service.py', 
            'stripe_products.py',
            'ethereum_helper.py',
            'elevenlabs_service.py',
            'mcp_server.py',
            'README.md',
            'replit.md',
            'package.json'
        ]
        
        for file_path in core_files:
            try:
                # Validate file path
                self._validate_file_path(file_path)
                
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Validate content
                    self._validate_content(content)
                    
                    files_to_upload.append({
                        'path': file_path,
                        'content': content,
                        'message': f'Update {file_path} - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
                    })
                    print(f"Prepared {file_path} for secure upload ({len(content)} chars)")
                    
            except Exception as e:
                print(f"Skipping {file_path}: {str(e)}")
        
        # Template files - only include safe templates
        template_files = [
            'templates/index.html',
            'templates/dashboard.html',
            'templates/profile.html'
        ]
        
        for file_path in template_files:
            try:
                # Validate file path
                self._validate_file_path(file_path)
                
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Validate content
                    self._validate_content(content)
                    
                    files_to_upload.append({
                        'path': file_path,
                        'content': content,
                        'message': f'Update {file_path} - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
                    })
                    print(f"Prepared {file_path} for secure upload")
                    
            except Exception as e:
                print(f"Skipping {file_path}: {str(e)}")
        
        print(f"Total files prepared for secure upload: {len(files_to_upload)}")
        return files_to_upload

# Global secure instance
github_service_secure = SecureGitHubService()