#!/usr/bin/env python3
"""
Modern Forge Installer for MCUS
Handles the latest Forge installation process
"""

import requests
import json
import subprocess
import shutil
import zipfile
import re
import os
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging
from packaging import version as packaging_version

class ModernForgeInstaller:
    def __init__(self, server_dir: Path):
        self.server_dir = server_dir
        self.server_dir.mkdir(exist_ok=True)
        
    def get_available_minecraft_versions(self) -> List[str]:
        """Get available Minecraft versions from Forge"""
        try:
            # Use Forge's version manifest
            manifest_url = "https://launchermeta.mojang.com/mc/game/version_manifest.json"
            response = requests.get(manifest_url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            versions = []
            
            # Get recent versions (last 10 major versions)
            for version in data['versions'][:50]:  # Check first 50 versions
                version_id = version['id']
                # Filter for release versions (not snapshots, pre-releases, etc.)
                if re.match(r'^\d+\.\d+(\.\d+)?$', version_id):
                    versions.append(version_id)
                    if len(versions) >= 10:  # Limit to 10 recent versions
                        break
            
            return versions
            
        except Exception as e:
            logging.error(f"Failed to get Minecraft versions: {e}")
            # Fallback to common versions
            return ["1.20.4", "1.20.2", "1.20.1", "1.19.4", "1.19.3", "1.19.2", "1.18.2", "1.17.1", "1.16.5"]
    
    def get_forge_versions(self, minecraft_version: str) -> List[Dict]:
        """Get available Forge versions for a specific Minecraft version"""
        try:
            # Use Forge's version list
            versions_url = f"https://files.minecraftforge.net/net/minecraftforge/forge/promotions_slim.json"
            response = requests.get(versions_url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            forge_versions = []
            
            # Look for versions matching our Minecraft version
            if 'promos' in data:
                for version_key, build_number in data['promos'].items():
                    # Check if this version matches our Minecraft version
                    if (version_key.startswith(f"{minecraft_version}-") or 
                        (minecraft_version.startswith(version_key.split('-')[0]) and 
                         version_key.split('-')[0] in minecraft_version)):
                        forge_versions.append({
                            'version': version_key,
                            'build': str(build_number),
                            'type': 'recommended' if 'recommended' in version_key else 'latest'
                        })
            # Note: homepage is just a URL string, not a dictionary of versions
            # All available versions are in the 'promos' field
            # Sort by build number (newest first) using version-aware sort
            forge_versions.sort(key=lambda x: packaging_version.parse(x['build']), reverse=True)
            return forge_versions[:10]  # Return top 10 versions
        except Exception as e:
            logging.error(f"Failed to get Forge versions for {minecraft_version}: {e}")
            return []
    
    def download_forge_installer(self, minecraft_version: str, forge_build: str) -> Optional[Path]:
        """Download Forge installer for specific version"""
        try:
            forge_version = f"{minecraft_version}-{forge_build}"
            installer_url = f"https://maven.minecraftforge.net/net/minecraftforge/forge/{forge_version}/forge-{forge_version}-installer.jar"
            
            installer_path = self.server_dir / f"forge-installer-{forge_version}.jar"
            
            logging.info(f"Downloading Forge installer: {installer_url}")
            logging.info(f"Target path: {installer_path}")
            
            response = requests.get(installer_url, stream=True, timeout=60)
            response.raise_for_status()
            
            logging.info(f"Download started, content length: {response.headers.get('content-length', 'unknown')}")
            
            with open(installer_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            if installer_path.exists():
                logging.info(f"Downloaded installer: {installer_path.stat().st_size} bytes")
                return installer_path
            else:
                logging.error("Download completed but file does not exist")
                return None
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Request failed: {e}")
            return None
        except Exception as e:
            logging.error(f"Failed to download Forge installer: {e}")
            return None
    
    def install_forge_server(self, minecraft_version: str, forge_build: str) -> Tuple[bool, str]:
        """Install Forge server using the installer"""
        try:
            # Download installer
            installer_path = self.download_forge_installer(minecraft_version, forge_build)
            if not installer_path:
                return False, "Failed to download Forge installer"
            
            logging.info(f"Installing Forge {minecraft_version}-{forge_build}...")
            logging.info(f"Installer path: {installer_path}")
            logging.info(f"Installer exists: {installer_path.exists()}")
            logging.info(f"Installer size: {installer_path.stat().st_size if installer_path.exists() else 'N/A'}")
            
            # Run the installer
            result = subprocess.run([
                "java", "-jar", str(installer_path),
                "--installServer"
            ], cwd=str(self.server_dir), capture_output=True, text=True, timeout=300)
            
            logging.info(f"Java installer return code: {result.returncode}")
            logging.info(f"Java installer stdout: {result.stdout}")
            logging.info(f"Java installer stderr: {result.stderr}")
            
            # Clean up installer
            try:
                installer_path.unlink()
            except:
                pass
            
            if result.returncode == 0:
                logging.info("Forge installation completed successfully")
                return True, "Forge installed successfully"
            else:
                error_msg = result.stderr if result.stderr else "Unknown error"
                logging.error(f"Forge installation failed: {error_msg}")
                return False, f"Installation failed: {error_msg}"
                
        except subprocess.TimeoutExpired:
            return False, "Installation timed out"
        except Exception as e:
            return False, f"Installation error: {str(e)}"
    
    def find_installed_forge_jar(self) -> Optional[Path]:
        """Find the installed Forge server JAR"""
        try:
            # Look for Forge server JARs
            for jar_file in self.server_dir.glob("*.jar"):
                if self._is_forge_jar(jar_file):
                    return jar_file
            
            return None
            
        except Exception as e:
            logging.error(f"Error finding Forge JAR: {e}")
            return None
    
    def _is_forge_jar(self, jar_path: Path) -> bool:
        """Check if a JAR file is a Forge server JAR"""
        try:
            # Check filename patterns
            filename = jar_path.name.lower()
            if any(pattern in filename for pattern in ['forge', 'server']):
                return True
            
            # Check JAR contents for Forge indicators
            with zipfile.ZipFile(jar_path, 'r') as jar:
                # Look for Forge-specific files
                forge_indicators = [
                    'net/minecraftforge/',
                    'META-INF/mods.toml',
                    'META-INF/mcmod.info',
                    'forge-'
                ]
                
                for file_info in jar.filelist:
                    file_name = file_info.filename.lower()
                    if any(indicator in file_name for indicator in forge_indicators):
                        return True
            
            return False
            
        except Exception as e:
            logging.error(f"Error checking if JAR is Forge: {e}")
            return False
    
    def create_server_script(self, jar_path: Path) -> bool:
        """Create server startup script"""
        try:
            script_content = f"""#!/bin/bash
# MCUS Forge Server Startup Script
# Generated by MCUS Forge Installer

cd "$(dirname "$0")"

# Server settings
MAX_MEMORY="4G"
MIN_MEMORY="2G"
JAR_FILE="{jar_path.name}"

# Start the server
java -Xmx$MAX_MEMORY -Xms$MIN_MEMORY -jar "$JAR_FILE" nogui

# Keep window open on error
if [ $? -ne 0 ]; then
    echo "Server crashed or stopped unexpectedly."
    echo "Press Enter to close this window..."
    read
fi
"""
            
            # Create startup script
            script_path = self.server_dir / "start_server.sh"
            with open(script_path, 'w') as f:
                f.write(script_content)
            
            # Make executable on Unix systems
            if os.name != 'nt':
                os.chmod(script_path, 0o755)
            
            # Create Windows batch file
            batch_content = f"""@echo off
REM MCUS Forge Server Startup Script
REM Generated by MCUS Forge Installer

cd /d "%~dp0"

REM Server settings
set MAX_MEMORY=4G
set MIN_MEMORY=2G
set JAR_FILE={jar_path.name}

REM Start the server
java -Xmx%MAX_MEMORY% -Xms%MIN_MEMORY% -jar "%JAR_FILE%" nogui

REM Keep window open on error
if errorlevel 1 (
    echo Server crashed or stopped unexpectedly.
    echo Press any key to close this window...
    pause
)
"""
            
            batch_path = self.server_dir / "start_server.bat"
            with open(batch_path, 'w') as f:
                f.write(batch_content)
            
            logging.info("Created server startup scripts")
            return True
            
        except Exception as e:
            logging.error(f"Failed to create server script: {e}")
            return False
    
    def install_forge_auto(self, minecraft_version: str = "1.20.4") -> Tuple[bool, str]:
        """Automatically install the latest recommended Forge version"""
        try:
            # Get available Forge versions
            forge_versions = self.get_forge_versions(minecraft_version)
            
            if not forge_versions:
                return False, f"No Forge versions found for Minecraft {minecraft_version}"
            
            # Try recommended version first, then latest
            for version_info in forge_versions:
                if 'recommended' in version_info['type']:
                    success, message = self.install_forge_server(minecraft_version, version_info['build'])
                    if success:
                        return True, message
            
            # If no recommended version, try the first available
            if forge_versions:
                version_info = forge_versions[0]
                return self.install_forge_server(minecraft_version, version_info['build'])
            
            return False, "No suitable Forge version found"
            
        except Exception as e:
            return False, f"Auto-installation failed: {str(e)}"

def main():
    """Test the Forge installer"""
    installer = ModernForgeInstaller(Path("server"))
    
    print("🎮 MCUS Modern Forge Installer")
    print("="*40)
    
    # Get available Minecraft versions
    print("Available Minecraft versions:")
    versions = installer.get_available_minecraft_versions()
    for i, version in enumerate(versions, 1):
        print(f"  {i}. {version}")
    
    # Try to install Forge for the latest version
    if versions:
        latest_version = versions[0]
        print(f"\nInstalling Forge for Minecraft {latest_version}...")
        
        success, message = installer.install_forge_auto(latest_version)
        
        if success:
            print(f"✅ {message}")
            
            # Find installed JAR and create startup script
            jar_path = installer.find_installed_forge_jar()
            if jar_path:
                print(f"Found Forge JAR: {jar_path.name}")
                if installer.create_server_script(jar_path):
                    print("✅ Created server startup scripts")
                else:
                    print("⚠️  Failed to create startup scripts")
            else:
                print("⚠️  Could not find installed Forge JAR")
        else:
            print(f"❌ {message}")
    else:
        print("❌ No Minecraft versions available")

if __name__ == "__main__":
    main() 