"""
GitHub configuration persistence for server restart resilience
"""

import os
import json
from typing import Optional, Dict

class GitHubConfig:
    def __init__(self, config_file: str = 'github_config.json'):
        self.config_file = config_file
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        """Load configuration from file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading GitHub config: {str(e)}")
        
        return {
            'repo_owner': None,
            'repo_name': None,
            'default_branch': 'main'
        }
    
    def _save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Error saving GitHub config: {str(e)}")
    
    def set_repository(self, owner: str, repo_name: str, branch: str = 'main'):
        """Set repository configuration"""
        self.config['repo_owner'] = owner
        self.config['repo_name'] = repo_name
        self.config['default_branch'] = branch
        self._save_config()
    
    def get_repository(self) -> Dict:
        """Get current repository configuration"""
        return self.config.copy()
    
    def is_configured(self) -> bool:
        """Check if repository is configured"""
        return bool(self.config.get('repo_owner') and self.config.get('repo_name'))

# Global config instance
github_config = GitHubConfig()