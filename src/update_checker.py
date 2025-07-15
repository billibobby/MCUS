#!/usr/bin/env python3
"""
MCUS Update Checker
Automatically checks for updates on GitHub and notifies users.
"""

import requests
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
import subprocess
import sys

class UpdateChecker:
    def __init__(self, repo_owner="yourusername", repo_name="MCUS"):
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.github_api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest"
        self.update_cache_file = Path("logs/update_cache.json")
        self.current_version = "1.1.0"  # Update this when you release new versions
        
        # Ensure logs directory exists
        self.update_cache_file.parent.mkdir(exist_ok=True)
        
    def check_for_updates(self, force_check=False):
        """Check for updates on GitHub"""
        try:
            # Check if we should skip this check (don't check too frequently)
            if not force_check and not self._should_check_for_updates():
                return None
            
            logging.info("Checking for updates...")
            
            # Get latest release from GitHub
            response = requests.get(self.github_api_url, timeout=10)
            if response.status_code != 200:
                logging.warning(f"Failed to check for updates: {response.status_code}")
                return None
            
            latest_release = response.json()
            latest_version = latest_release['tag_name'].lstrip('v')
            
            # Compare versions
            if self._is_newer_version(latest_version, self.current_version):
                update_info = {
                    'version': latest_version,
                    'release_notes': latest_release.get('body', ''),
                    'download_url': latest_release.get('html_url', ''),
                    'published_at': latest_release.get('published_at', ''),
                    'checked_at': datetime.now().isoformat()
                }
                
                # Cache the update info
                self._cache_update_info(update_info)
                
                logging.info(f"New version available: {latest_version}")
                return update_info
            else:
                logging.info("No updates available")
                self._cache_update_info({'checked_at': datetime.now().isoformat()})
                return None
                
        except Exception as e:
            logging.error(f"Error checking for updates: {e}")
            return None
    
    def _should_check_for_updates(self):
        """Check if we should perform an update check (not too frequently)"""
        if not self.update_cache_file.exists():
            return True
        
        try:
            with open(self.update_cache_file, 'r') as f:
                cache_data = json.load(f)
            
            last_check = cache_data.get('checked_at')
            if not last_check:
                return True
            
            last_check_time = datetime.fromisoformat(last_check)
            # Check for updates once per day
            return datetime.now() - last_check_time > timedelta(hours=24)
            
        except Exception as e:
            logging.warning(f"Error reading update cache: {e}")
            return True
    
    def _cache_update_info(self, update_info):
        """Cache update information"""
        try:
            with open(self.update_cache_file, 'w') as f:
                json.dump(update_info, f, indent=2)
        except Exception as e:
            logging.error(f"Error caching update info: {e}")
    
    def _is_newer_version(self, version1, version2):
        """Compare two version strings"""
        try:
            v1_parts = [int(x) for x in version1.split('.')]
            v2_parts = [int(x) for x in version2.split('.')]
            
            # Pad with zeros if needed
            max_len = max(len(v1_parts), len(v2_parts))
            v1_parts.extend([0] * (max_len - len(v1_parts)))
            v2_parts.extend([0] * (max_len - len(v2_parts)))
            
            return v1_parts > v2_parts
            
        except Exception as e:
            logging.error(f"Error comparing versions: {e}")
            return False
    
    def get_cached_update(self):
        """Get cached update information if available"""
        try:
            if self.update_cache_file.exists():
                with open(self.update_cache_file, 'r') as f:
                    cache_data = json.load(f)
                
                # Check if we have update info and it's recent (within 7 days)
                if 'version' in cache_data and 'checked_at' in cache_data:
                    checked_time = datetime.fromisoformat(cache_data['checked_at'])
                    if datetime.now() - checked_time < timedelta(days=7):
                        return cache_data
                        
        except Exception as e:
            logging.error(f"Error reading cached update: {e}")
        
        return None
    
    def mark_update_as_seen(self):
        """Mark the current update as seen by the user"""
        try:
            if self.update_cache_file.exists():
                with open(self.update_cache_file, 'r') as f:
                    cache_data = json.load(f)
                
                cache_data['seen_by_user'] = True
                cache_data['seen_at'] = datetime.now().isoformat()
                
                with open(self.update_cache_file, 'w') as f:
                    json.dump(cache_data, f, indent=2)
                    
        except Exception as e:
            logging.error(f"Error marking update as seen: {e}")
    
    def get_update_notification_html(self, update_info):
        """Generate HTML for update notification"""
        if not update_info or not update_info.get('version'):
            return None
        
        html = f"""
        <div class="alert alert-info alert-dismissible fade show" role="alert">
            <div class="d-flex align-items-center">
                <i class="fas fa-download me-3 fs-4"></i>
                <div class="flex-grow-1">
                    <h6 class="alert-heading mb-1">🎉 New MCUS Update Available!</h6>
                    <p class="mb-2">
                        Version <strong>{update_info['version']}</strong> is now available.
                        <br>
                        <small class="text-muted">Released: {update_info.get('published_at', 'Unknown')}</small>
                    </p>
                    <div class="btn-group btn-group-sm" role="group">
                        <a href="{update_info.get('download_url', '#')}" target="_blank" class="btn btn-primary">
                            <i class="fas fa-download me-1"></i>Download
                        </a>
                        <button type="button" class="btn btn-outline-secondary" onclick="showReleaseNotes()">
                            <i class="fas fa-file-text me-1"></i>Release Notes
                        </button>
                        <button type="button" class="btn btn-outline-secondary" onclick="dismissUpdate()">
                            <i class="fas fa-times me-1"></i>Dismiss
                        </button>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
        function showReleaseNotes() {{
            const notes = `{update_info.get('release_notes', 'No release notes available.').replace('`', '\\`')}`;
            alert('Release Notes:\\n\\n' + notes);
        }}
        
        function dismissUpdate() {{
            fetch('/api/updates/dismiss', {{method: 'POST'}})
                .then(() => {{
                    document.querySelector('.alert').remove();
                }});
        }}
        </script>
        """
        
        return html 