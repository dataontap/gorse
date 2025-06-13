
import requests
import os
import json
from typing import Optional, Dict, Any

class FirebaseAppDistribution:
    def __init__(self):
        self.project_id = os.environ.get('FIREBASE_PROJECT_ID', 'gorse-24e76')
        self.access_token = os.environ.get('FIREBASE_ACCESS_TOKEN')
        self.app_id = os.environ.get('FIREBASE_APP_ID')
        self.base_url = f"https://firebase.googleapis.com/v1/projects/{self.project_id}"
    
    def add_tester_to_group(self, email: str, group_name: str = "beta-testers") -> Dict[str, Any]:
        """Add a tester to a Firebase App Distribution group"""
        if not self.access_token or not self.app_id:
            return {
                'success': False,
                'error': 'Firebase credentials not configured'
            }
        
        try:
            # First, create the group if it doesn't exist
            self._create_group_if_not_exists(group_name)
            
            # Add tester to the group
            url = f"{self.base_url}/apps/{self.app_id}/testers:batchAdd"
            
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'emails': [email]
            }
            
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                # Now add to group
                group_url = f"{self.base_url}/groups/{group_name}:batchJoin"
                group_payload = {
                    'emails': [email]
                }
                
                group_response = requests.post(group_url, headers=headers, json=group_payload)
                
                return {
                    'success': True,
                    'message': f'Tester {email} added to group {group_name}',
                    'group_response': group_response.status_code == 200
                }
            else:
                return {
                    'success': False,
                    'error': f'Failed to add tester: {response.text}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def remove_tester_from_group(self, email: str, group_name: str = "beta-testers") -> Dict[str, Any]:
        """Remove a tester from a Firebase App Distribution group"""
        if not self.access_token or not self.app_id:
            return {
                'success': False,
                'error': 'Firebase credentials not configured'
            }
        
        try:
            url = f"{self.base_url}/groups/{group_name}:batchLeave"
            
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'emails': [email]
            }
            
            response = requests.post(url, headers=headers, json=payload)
            
            return {
                'success': response.status_code == 200,
                'message': f'Tester {email} removed from group {group_name}' if response.status_code == 200 else f'Failed to remove tester: {response.text}'
            }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _create_group_if_not_exists(self, group_name: str) -> bool:
        """Create a tester group if it doesn't exist"""
        try:
            url = f"{self.base_url}/groups"
            
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'name': group_name,
                'displayName': f'Beta Testers - {group_name.title()}'
            }
            
            response = requests.post(url, headers=headers, json=payload)
            
            # Group already exists or was created successfully
            return response.status_code in [200, 409]
            
        except Exception as e:
            print(f"Error creating group: {str(e)}")
            return False

# Instance for easy importing
firebase_distribution = FirebaseAppDistribution()
