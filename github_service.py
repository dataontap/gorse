"""
GitHub Service for automated repository uploads and management
Uses Replit's native GitHub integration for secure authentication
"""

import os
import json
import base64
import asyncio
from typing import Optional, Dict, List, Any
from datetime import datetime

class GitHubService:
    def __init__(self):
        self.client = None
        self.repo_owner = None
        self.repo_name = None
        self.default_branch = "main"
    
    def get_authenticated_client(self):
        """Get authenticated GitHub client using Replit's connection"""
        try:
            # Use Node.js script to get GitHub client (since the auth is in JS)
            import subprocess
            result = subprocess.run([
                'node', '-e', '''
                const { getUncachableGitHubClient } = require('./github_client.js');
                getUncachableGitHubClient().then(client => {
                    console.log("CLIENT_READY");
                }).catch(err => {
                    console.error("AUTH_ERROR:", err.message);
                    process.exit(1);
                });
                '''
            ], capture_output=True, text=True, timeout=10)
            
            if "CLIENT_READY" in result.stdout:
                print("GitHub client authenticated successfully")
                return True
            else:
                print(f"GitHub authentication failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"Error getting GitHub client: {str(e)}")
            return False
    
    def set_repository(self, owner: str, repo_name: str, branch: str = "main"):
        """Set the target repository for uploads"""
        self.repo_owner = owner
        self.repo_name = repo_name
        self.default_branch = branch
        print(f"GitHub service configured for {owner}/{repo_name} (branch: {branch})")
    
    def upload_file(self, file_path: str, content: str, commit_message: str, repo_owner: Optional[str] = None, repo_name: Optional[str] = None) -> Dict[str, Any]:
        """Upload a single file to GitHub repository"""
        try:
            owner = repo_owner or self.repo_owner
            repo = repo_name or self.repo_name
            
            if not owner or not repo:
                raise Exception("Repository owner and name must be specified")
            
            # Create Node.js script for file upload
            upload_script = f'''
const {{ getUncachableGitHubClient }} = require('./github_client.js');

async function uploadFile() {{
    try {{
        const octokit = await getUncachableGitHubClient();
        
        // Check if file exists to get SHA for updates
        let sha = null;
        try {{
            const {{ data }} = await octokit.rest.repos.getContent({{
                owner: "{owner}",
                repo: "{repo}",
                path: "{file_path}"
            }});
            sha = data.sha;
        }} catch (err) {{
            // File doesn't exist, will create new
        }}
        
        const content = Buffer.from(`{content}`, 'utf8').toString('base64');
        
        const result = await octokit.rest.repos.createOrUpdateFileContents({{
            owner: "{owner}",
            repo: "{repo}",
            path: "{file_path}",
            message: "{commit_message}",
            content: content,
            branch: "{self.default_branch}",
            ...(sha && {{ sha }})
        }});
        
        console.log("UPLOAD_SUCCESS", JSON.stringify({{
            path: "{file_path}",
            sha: result.data.content.sha,
            html_url: result.data.content.html_url
        }}));
    }} catch (error) {{
        console.error("UPLOAD_ERROR:", error.message);
        process.exit(1);
    }}
}}

uploadFile();
'''
            
            # Save and execute the script
            with open('/tmp/github_upload.js', 'w') as f:
                f.write(upload_script)
            
            import subprocess
            result = subprocess.run([
                'node', '/tmp/github_upload.js'
            ], capture_output=True, text=True, timeout=30)
            
            if "UPLOAD_SUCCESS" in result.stdout:
                # Parse the success result
                success_data = result.stdout.split("UPLOAD_SUCCESS ")[1].strip()
                upload_result = json.loads(success_data)
                print(f"Successfully uploaded {file_path} to {owner}/{repo}")
                return {
                    "status": "success",
                    "file_path": file_path,
                    "result": upload_result
                }
            else:
                error_msg = result.stderr or result.stdout
                print(f"Failed to upload {file_path}: {error_msg}")
                return {
                    "status": "error",
                    "file_path": file_path,
                    "error": error_msg
                }
                
        except Exception as e:
            error_msg = f"Exception uploading {file_path}: {str(e)}"
            print(error_msg)
            return {
                "status": "error",
                "file_path": file_path,
                "error": error_msg
            }
        finally:
            # Clean up temp file
            try:
                os.remove('/tmp/github_upload.js')
            except:
                pass
    
    def upload_multiple_files(self, files: List[Dict[str, str]], repo_owner: Optional[str] = None, repo_name: Optional[str] = None) -> Dict[str, Any]:
        """Upload multiple files to GitHub repository"""
        results = []
        owner = repo_owner or self.repo_owner
        repo = repo_name or self.repo_name
        
        if not owner or not repo:
            return {
                "status": "error",
                "error": "Repository owner and name must be specified",
                "results": []
            }
        
        print(f"Starting batch upload of {len(files)} files to {owner}/{repo}")
        
        for file_info in files:
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
                
            result = self.upload_file(file_path, content, commit_message, str(owner), str(repo))
            results.append(result)
            
            # Small delay between uploads to avoid rate limiting
            import time
            time.sleep(0.5)
        
        successful_uploads = [r for r in results if r['status'] == 'success']
        failed_uploads = [r for r in results if r['status'] == 'error']
        
        print(f"Batch upload completed: {len(successful_uploads)} successful, {len(failed_uploads)} failed")
        
        return {
            "status": "completed",
            "total_files": len(files),
            "successful": len(successful_uploads),
            "failed": len(failed_uploads),
            "results": results
        }
    
    def get_project_files_for_upload(self) -> List[Dict[str, str]]:
        """Get list of key project files to upload to GitHub"""
        files_to_upload = []
        
        # Core application files
        core_files = [
            'main.py',
            'github_service.py',
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
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Escape content for JSON
                    escaped_content = content.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
                    
                    files_to_upload.append({
                        'path': file_path,
                        'content': escaped_content,
                        'message': f'Update {file_path} - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
                    })
                    print(f"Prepared {file_path} for upload ({len(content)} chars)")
                except Exception as e:
                    print(f"Error reading {file_path}: {str(e)}")
        
        # Template files
        template_files = [
            'templates/index.html',
            'templates/dashboard.html',
            'templates/profile.html'
        ]
        
        for file_path in template_files:
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    escaped_content = content.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
                    
                    files_to_upload.append({
                        'path': file_path,
                        'content': escaped_content,
                        'message': f'Update {file_path} - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
                    })
                    print(f"Prepared {file_path} for upload")
                except Exception as e:
                    print(f"Error reading {file_path}: {str(e)}")
        
        print(f"Total files prepared for upload: {len(files_to_upload)}")
        return files_to_upload

# Global instance
github_service = GitHubService()