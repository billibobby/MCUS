import requests
import json
import os
import shutil
import zipfile
from pathlib import Path
from typing import List, Dict, Optional
import logging

class ModManager:
    def __init__(self, mods_dir: Path):
        self.mods_dir = mods_dir
        self.mods_dir.mkdir(exist_ok=True)
        self.mc_version = "1.19.2"
        self.loader = "forge"  # or "fabric"
        
    def set_minecraft_version(self, version: str):
        """Set Minecraft version for mod compatibility"""
        self.mc_version = version
        
    def set_mod_loader(self, loader: str):
        """Set mod loader (forge or fabric)"""
        self.loader = loader
        
    def install_mod_from_file(self, mod_path: str) -> bool:
        """Install a mod from a local file"""
        try:
            mod_file = Path(mod_path)
            if not mod_file.exists():
                logging.error(f"Mod file not found: {mod_path}")
                return False
                
            # Validate it's a jar file
            if not mod_file.suffix.lower() == '.jar':
                logging.error(f"File is not a JAR: {mod_path}")
                return False
                
            # Copy to mods directory
            target_path = self.mods_dir / mod_file.name
            shutil.copy2(mod_file, target_path)
            
            logging.info(f"Mod installed: {mod_file.name}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to install mod: {e}")
            return False
            
    def remove_mod(self, mod_name: str) -> bool:
        """Remove a mod by name"""
        try:
            mod_file = self.mods_dir / mod_name
            if mod_file.exists():
                mod_file.unlink()
                logging.info(f"Mod removed: {mod_name}")
                return True
            else:
                logging.warning(f"Mod not found: {mod_name}")
                return False
                
        except Exception as e:
            logging.error(f"Failed to remove mod: {e}")
            return False
            
    def get_installed_mods(self) -> List[Dict]:
        """Get list of installed mods with metadata"""
        mods = []
        for mod_file in self.mods_dir.glob("*.jar"):
            try:
                mod_info = {
                    'name': mod_file.name,
                    'size': mod_file.stat().st_size,
                    'modified': mod_file.stat().st_mtime,
                    'enabled': True  # All mods are enabled by default
                }
                mods.append(mod_info)
            except Exception as e:
                logging.error(f"Error reading mod info for {mod_file.name}: {e}")
                
        return mods
        
    def enable_mod(self, mod_name: str) -> bool:
        """Enable a mod (currently all mods are enabled by default)"""
        # In a more advanced implementation, this could move files to/from a disabled folder
        logging.info(f"Mod enabled: {mod_name}")
        return True
        
    def disable_mod(self, mod_name: str) -> bool:
        """Disable a mod by moving it to a disabled folder"""
        try:
            mod_file = self.mods_dir / mod_name
            disabled_dir = self.mods_dir / "disabled"
            disabled_dir.mkdir(exist_ok=True)
            
            if mod_file.exists():
                shutil.move(str(mod_file), str(disabled_dir / mod_name))
                logging.info(f"Mod disabled: {mod_name}")
                return True
            else:
                logging.warning(f"Mod not found: {mod_name}")
                return False
                
        except Exception as e:
            logging.error(f"Failed to disable mod: {e}")
            return False
            
    def search_modrinth_mods(self, query: str, limit: int = 50) -> List[Dict]:
        """Search for mods on Modrinth with improved error handling and more results"""
        try:
            # Modrinth API endpoint
            search_url = "https://api.modrinth.com/v2/search"
            params = {
                'query': query,
                'facets': json.dumps([
                    [f"versions:{self.mc_version}"],
                    [f"loader:{self.loader}"]
                ]),
                'limit': limit,
                'sort_by': 'relevance'
            }
            
            response = requests.get(search_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            mods = []
            
            for hit in data.get('hits', []):
                mod_info = {
                    'id': hit['project_id'],
                    'name': hit['title'],
                    'description': hit.get('description', ''),
                    'downloads': hit.get('downloads', 0),
                    'followers': hit.get('followers', 0),
                    'author': hit.get('author', 'Unknown'),
                    'categories': hit.get('categories', []),
                    'icon_url': hit.get('icon_url'),
                    'project_type': hit.get('project_type', 'mod'),
                    'client_side': hit.get('client_side', 'unknown'),
                    'server_side': hit.get('server_side', 'unknown'),
                    'date_created': hit.get('date_created'),
                    'date_modified': hit.get('date_modified')
                }
                mods.append(mod_info)
                
            return mods
            
        except requests.exceptions.Timeout:
            logging.error("Modrinth search timed out")
            return []
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to search Modrinth: {e}")
            return []
        except Exception as e:
            logging.error(f"Unexpected error searching Modrinth: {e}")
            return []
            
    def get_latest_modrinth_version(self, project_id: str) -> Optional[Dict]:
        """Get the latest version for a mod that's compatible with current Minecraft version"""
        try:
            versions_url = f"https://api.modrinth.com/v2/project/{project_id}/version"
            params = {
                'loaders': json.dumps([self.loader]),
                'game_versions': json.dumps([self.mc_version])
            }
            
            response = requests.get(versions_url, params=params)
            response.raise_for_status()
            
            versions = response.json()
            if versions:
                # Get the latest version
                latest = versions[0]
                return {
                    'id': latest['id'],
                    'name': latest['name'],
                    'version_number': latest['version_number'],
                    'files': latest.get('files', []),
                    'date_published': latest.get('date_published', '')
                }
                
        except Exception as e:
            logging.error(f"Failed to get latest version for mod {project_id}: {e}")
            
        return None
        
    def download_mod_from_modrinth(self, project_id: str, version_id: str) -> bool:
        """Download a mod from Modrinth"""
        try:
            # Get version details
            version_url = f"https://api.modrinth.com/v2/version/{version_id}"
            response = requests.get(version_url)
            response.raise_for_status()
            
            version_data = response.json()
            files = version_data.get('files', [])
            
            if not files:
                logging.error("No files found for this version")
                return False
                
            # Get the primary file (usually the first one)
            primary_file = files[0]
            download_url = primary_file['url']
            filename = primary_file['filename']
            
            # Download the file
            logging.info(f"Downloading mod file: {filename}")
            file_response = requests.get(download_url, stream=True)
            file_response.raise_for_status()
            
            file_path = self.mods_dir / filename
            
            with open(file_path, 'wb') as f:
                for chunk in file_response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
            logging.info(f"Mod downloaded: {filename}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to download mod: {e}")
            return False
            
    def get_popular_modrinth_mods(self, limit: int = 100) -> List[Dict]:
        """Get popular mods from Modrinth with more results and better error handling"""
        try:
            # Search for popular mods
            search_url = "https://api.modrinth.com/v2/search"
            params = {
                'query': '',
                'facets': json.dumps([
                    [f"versions:{self.mc_version}"],
                    [f"loader:{self.loader}"]
                ]),
                'limit': limit,
                'sort_by': 'downloads'
            }
            
            response = requests.get(search_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            mods = []
            
            for hit in data.get('hits', []):
                mod_info = {
                    'id': hit['project_id'],
                    'name': hit['title'],
                    'description': hit.get('description', ''),
                    'downloads': hit.get('downloads', 0),
                    'followers': hit.get('followers', 0),
                    'author': hit.get('author', 'Unknown'),
                    'categories': hit.get('categories', []),
                    'icon_url': hit.get('icon_url'),
                    'date_created': hit.get('date_created'),
                    'date_modified': hit.get('date_modified'),
                    'project_type': hit.get('project_type', 'mod'),
                    'client_side': hit.get('client_side', 'unknown'),
                    'server_side': hit.get('server_side', 'unknown')
                }
                mods.append(mod_info)
                
            return mods
            
        except requests.exceptions.Timeout:
            logging.error("Modrinth popular mods request timed out")
            return []
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to get popular Modrinth mods: {e}")
            return []
        except Exception as e:
            logging.error(f"Unexpected error getting popular Modrinth mods: {e}")
            return []
            
    def install_modpack(self, modpack_path: str) -> bool:
        """Install a modpack from a zip file"""
        try:
            modpack_file = Path(modpack_path)
            if not modpack_file.exists():
                logging.error(f"Modpack file not found: {modpack_path}")
                return False
                
            # Create temporary directory for extraction
            temp_dir = Path("temp_modpack")
            temp_dir.mkdir(exist_ok=True)
            
            # Extract modpack
            with zipfile.ZipFile(modpack_file, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
                
            # Find mods folder in extracted content
            mods_source = None
            for item in temp_dir.rglob("mods"):
                if item.is_dir():
                    mods_source = item
                    break
                    
            if not mods_source:
                logging.error("No mods folder found in modpack")
                shutil.rmtree(temp_dir)
                return False
                
            # Copy mods to server mods directory
            for mod_file in mods_source.glob("*.jar"):
                shutil.copy2(mod_file, self.mods_dir / mod_file.name)
                logging.info(f"Installed mod from modpack: {mod_file.name}")
                
            # Clean up
            shutil.rmtree(temp_dir)
            
            logging.info("Modpack installed successfully")
            return True
            
        except Exception as e:
            logging.error(f"Failed to install modpack: {e}")
            return False
            
    def create_modpack(self, modpack_name: str, output_path: str) -> bool:
        """Create a modpack from currently installed mods"""
        try:
            modpack_path = Path(output_path)
            
            with zipfile.ZipFile(modpack_path, 'w', zipfile.ZIP_DEFLATED) as zip_ref:
                # Add all mods
                for mod_file in self.mods_dir.glob("*.jar"):
                    zip_ref.write(mod_file, f"mods/{mod_file.name}")
                    
            logging.info(f"Modpack created: {modpack_path}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to create modpack: {e}")
            return False
            
    def validate_mods(self) -> List[str]:
        """Validate installed mods for compatibility"""
        issues = []
        
        for mod_file in self.mods_dir.glob("*.jar"):
            try:
                # Basic validation - check if it's a valid JAR
                with zipfile.ZipFile(mod_file, 'r') as jar:
                    # Check for mod metadata files
                    has_mod_metadata = any(
                        name.endswith('mods.toml') or name.endswith('mcmod.info') or name.endswith('fabric.mod.json')
                        for name in jar.namelist()
                    )
                    
                    if not has_mod_metadata:
                        issues.append(f"{mod_file.name} - No mod metadata found")
                        
            except zipfile.BadZipFile:
                issues.append(f"{mod_file.name} - Invalid JAR file")
            except Exception as e:
                issues.append(f"{mod_file.name} - Error: {e}")
                
        return issues
        
    def get_mod_dependencies(self, mod_name: str) -> List[str]:
        """Get dependencies for a specific mod"""
        # This would require parsing mod metadata files
        # For now, return empty list
        return []
        
    def check_for_updates(self) -> List[Dict]:
        """Check for updates for installed mods"""
        # This would compare installed versions with latest versions on Modrinth
        # For now, return empty list
        return [] 

    def get_all_modrinth_mods(self, page: int = 1, limit: int = 50, sort_by: str = 'downloads', 
                             categories: Optional[List[str]] = None, loader: Optional[str] = None, 
                             game_version: Optional[str] = None) -> Dict:
        """Get all mods from Modrinth with pagination and filtering"""
        try:
            search_url = "https://api.modrinth.com/v2/search"
            
            # Build facets for filtering
            facets = []
            if game_version:
                facets.append([f"versions:{game_version}"])
            if loader:
                facets.append([f"loader:{loader}"])
            if categories:
                for category in categories:
                    facets.append([f"categories:{category}"])
            
            params = {
                'query': '',
                'limit': limit,
                'offset': (page - 1) * limit,
                'sort_by': sort_by
            }
            
            if facets:
                params['facets'] = json.dumps(facets)
            
            response = requests.get(search_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            mods = []
            
            for hit in data.get('hits', []):
                mod_info = {
                    'id': hit['project_id'],
                    'name': hit['title'],
                    'description': hit.get('description', ''),
                    'downloads': hit.get('downloads', 0),
                    'followers': hit.get('followers', 0),
                    'author': hit.get('author', 'Unknown'),
                    'categories': hit.get('categories', []),
                    'icon_url': hit.get('icon_url'),
                    'date_created': hit.get('date_created'),
                    'date_modified': hit.get('date_modified'),
                    'project_type': hit.get('project_type', 'mod'),
                    'client_side': hit.get('client_side', 'unknown'),
                    'server_side': hit.get('server_side', 'unknown'),
                    'gallery': hit.get('gallery', []),
                    'license': hit.get('license', {}),
                    'team': hit.get('team', ''),
                    'body': hit.get('body', ''),
                    'issues_url': hit.get('issues_url'),
                    'source_url': hit.get('source_url'),
                    'wiki_url': hit.get('wiki_url'),
                    'discord_url': hit.get('discord_url'),
                    'donation_urls': hit.get('donation_urls', [])
                }
                mods.append(mod_info)
                
            return {
                'mods': mods,
                'total_hits': data.get('total_hits', 0),
                'page': page,
                'limit': limit,
                'total_pages': (data.get('total_hits', 0) + limit - 1) // limit
            }
            
        except Exception as e:
            logging.error(f"Failed to get all Modrinth mods: {e}")
            return {'mods': [], 'total_hits': 0, 'page': page, 'limit': limit, 'total_pages': 0}
    
    def get_modrinth_categories(self) -> List[Dict]:
        """Get all available categories from Modrinth"""
        try:
            categories_url = "https://api.modrinth.com/v2/tag/category"
            response = requests.get(categories_url)
            response.raise_for_status()
            
            categories = response.json()
            return [
                {
                    'name': cat['name'],
                    'display_name': cat.get('display_name', cat['name']),
                    'description': cat.get('description', ''),
                    'icon': cat.get('icon', ''),
                    'color': cat.get('color', '#000000')
                }
                for cat in categories
            ]
            
        except Exception as e:
            logging.error(f"Failed to get Modrinth categories: {e}")
            return []
    
    def get_modrinth_loaders(self) -> List[str]:
        """Get all available loaders from Modrinth"""
        try:
            loaders_url = "https://api.modrinth.com/v2/tag/loader"
            response = requests.get(loaders_url)
            response.raise_for_status()
            
            loaders = response.json()
            return [loader['name'] for loader in loaders]
            
        except Exception as e:
            logging.error(f"Failed to get Modrinth loaders: {e}")
            return ['forge', 'fabric', 'quilt']
    
    def get_modrinth_game_versions(self) -> List[str]:
        """Get all available game versions from Modrinth"""
        try:
            versions_url = "https://api.modrinth.com/v2/tag/game_version"
            response = requests.get(versions_url)
            response.raise_for_status()
            
            versions = response.json()
            # Sort versions in descending order (newest first)
            sorted_versions = sorted(versions, key=lambda x: x['name'], reverse=True)
            return [version['name'] for version in sorted_versions]
            
        except Exception as e:
            logging.error(f"Failed to get Modrinth game versions: {e}")
            return ['1.20.2', '1.20.1', '1.19.4', '1.19.3', '1.19.2', '1.18.2']
    
    def get_modrinth_project_details(self, project_id: str) -> Optional[Dict]:
        """Get detailed information about a specific Modrinth project with improved error handling"""
        try:
            project_url = f"https://api.modrinth.com/v2/project/{project_id}"
            response = requests.get(project_url, timeout=30)
            response.raise_for_status()
            
            project_data = response.json()
            
            # Get versions for this project
            versions_url = f"https://api.modrinth.com/v2/project/{project_id}/version"
            versions_response = requests.get(versions_url, timeout=30)
            versions_response.raise_for_status()
            versions_data = versions_response.json()
            
            # Process versions to ensure they have all required fields
            processed_versions = []
            for version in versions_data:
                processed_version = {
                    'id': version.get('id', ''),
                    'name': version.get('name', ''),
                    'version_number': version.get('version_number', ''),
                    'game_versions': version.get('game_versions', []),
                    'loaders': version.get('loaders', []),
                    'date_published': version.get('date_published', ''),
                    'files': version.get('files', []),
                    'dependencies': version.get('dependencies', [])
                }
                processed_versions.append(processed_version)
            
            # Sort versions by date (newest first)
            processed_versions.sort(key=lambda x: x.get('date_published', ''), reverse=True)
            
            return {
                'id': project_data.get('id', project_id),
                'name': project_data.get('title', 'Unknown Project'),
                'description': project_data.get('description', ''),
                'body': project_data.get('body', ''),
                'downloads': project_data.get('downloads', 0),
                'followers': project_data.get('followers', 0),
                'author': project_data.get('author', 'Unknown'),
                'categories': project_data.get('categories', []),
                'icon_url': project_data.get('icon_url'),
                'date_created': project_data.get('date_created', ''),
                'date_modified': project_data.get('date_modified', ''),
                'project_type': project_data.get('project_type', 'mod'),
                'client_side': project_data.get('client_side', 'unknown'),
                'server_side': project_data.get('server_side', 'unknown'),
                'gallery': project_data.get('gallery', []),
                'license': project_data.get('license', {}),
                'team': project_data.get('team', ''),
                'issues_url': project_data.get('issues_url'),
                'source_url': project_data.get('source_url'),
                'wiki_url': project_data.get('wiki_url'),
                'discord_url': project_data.get('discord_url'),
                'donation_urls': project_data.get('donation_urls', []),
                'versions': processed_versions
            }
            
        except requests.exceptions.Timeout:
            logging.error(f"Timeout getting Modrinth project details for {project_id}")
            return None
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to get Modrinth project details for {project_id}: {e}")
            return None
        except Exception as e:
            logging.error(f"Unexpected error getting Modrinth project details for {project_id}: {e}")
            return None 