
import requests
import os
from typing import Optional, Dict, Any

class GitHubIntegration:
    def __init__(self):
        self.access_token = os.environ.get('GITHUB_ACCESS_TOKEN')
        self.repo_owner = os.environ.get('GITHUB_REPO_OWNER', 'your-org')
        self.repo_name = os.environ.get('GITHUB_REPO_NAME', 'your-repo')
        self.base_url = "https://api.github.com"
    
    def add_user_to_beta_team(self, github_username: str) -> Dict[str, Any]:
        """Add a GitHub user to the beta testers team"""
        if not self.access_token:
            return {
                'success': False,
                'error': 'GitHub access token not configured'
            }
        
        try:
            # First, create the beta team if it doesn't exist
            team_id = self._get_or_create_beta_team()
            
            if not team_id:
                return {
                    'success': False,
                    'error': 'Could not create or find beta team'
                }
            
            # Add user to team
            url = f"{self.base_url}/orgs/{self.repo_owner}/teams/{team_id}/memberships/{github_username}"
            
            headers = {
                'Authorization': f'token {self.access_token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            payload = {
                'role': 'member'
            }
            
            response = requests.put(url, headers=headers, json=payload)
            
            if response.status_code in [200, 201]:
                return {
                    'success': True,
                    'message': f'User {github_username} added to beta team',
                    'team_id': team_id
                }
            else:
                return {
                    'success': False,
                    'error': f'Failed to add user to team: {response.text}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def remove_user_from_beta_team(self, github_username: str) -> Dict[str, Any]:
        """Remove a GitHub user from the beta testers team"""
        if not self.access_token:
            return {
                'success': False,
                'error': 'GitHub access token not configured'
            }
        
        try:
            team_id = self._get_beta_team_id()
            
            if not team_id:
                return {
                    'success': False,
                    'error': 'Beta team not found'
                }
            
            url = f"{self.base_url}/orgs/{self.repo_owner}/teams/{team_id}/memberships/{github_username}"
            
            headers = {
                'Authorization': f'token {self.access_token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            response = requests.delete(url, headers=headers)
            
            return {
                'success': response.status_code == 204,
                'message': f'User {github_username} removed from beta team' if response.status_code == 204 else f'Failed to remove user: {response.text}'
            }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_beta_release(self, tag_name: str, release_notes: str = "") -> Dict[str, Any]:
        """Create a beta release on GitHub"""
        if not self.access_token:
            return {
                'success': False,
                'error': 'GitHub access token not configured'
            }
        
        try:
            url = f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/releases"
            
            headers = {
                'Authorization': f'token {self.access_token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            payload = {
                'tag_name': tag_name,
                'name': f'Beta Release {tag_name}',
                'body': release_notes or f'Beta release {tag_name} for testing',
                'draft': False,
                'prerelease': True  # Mark as beta/prerelease
            }
            
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code == 201:
                release_data = response.json()
                return {
                    'success': True,
                    'release_id': release_data['id'],
                    'release_url': release_data['html_url'],
                    'download_url': release_data['assets_url'] if release_data.get('assets') else None
                }
            else:
                return {
                    'success': False,
                    'error': f'Failed to create release: {response.text}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_or_create_beta_team(self) -> Optional[int]:
        """Get or create the beta testers team"""
        team_id = self._get_beta_team_id()
        
        if team_id:
            return team_id
        
        # Create the team
        try:
            url = f"{self.base_url}/orgs/{self.repo_owner}/teams"
            
            headers = {
                'Authorization': f'token {self.access_token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            payload = {
                'name': 'beta-testers',
                'description': 'Beta testers for early access features',
                'privacy': 'closed',
                'permission': 'pull'
            }
            
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code == 201:
                return response.json()['id']
                
        except Exception as e:
            print(f"Error creating beta team: {str(e)}")
        
        return None
    
    def _get_beta_team_id(self) -> Optional[int]:
        """Get the ID of the beta testers team"""
        try:
            url = f"{self.base_url}/orgs/{self.repo_owner}/teams"
            
            headers = {
                'Authorization': f'token {self.access_token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                teams = response.json()
                for team in teams:
                    if team['name'] == 'beta-testers':
                        return team['id']
                        
        except Exception as e:
            print(f"Error getting beta team: {str(e)}")
        
        return None

# Instance for easy importing
github_integration = GitHubIntegration()
