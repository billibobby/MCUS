#!/usr/bin/env python3
"""
MCUS (Minecraft Unified Server) Setup Script
This script helps new users set up MCUS properly.
"""

import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required!")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python {sys.version.split()[0]} is compatible")
    return True

def check_java_installation():
    """Check if Java is installed and compatible"""
    try:
        result = subprocess.run(['java', '-version'], capture_output=True, text=True)
        if result.returncode == 0:
            version_output = result.stderr  # Java version goes to stderr
            if 'version' in version_output:
                print("✅ Java is installed")
                print(f"   Version info: {version_output.splitlines()[0]}")
                return True
    except FileNotFoundError:
        pass
    
    print("❌ Java is not installed or not in PATH")
    print("   Please install Java 21 or higher:")
    if platform.system() == "Darwin":  # macOS
        print("   brew install openjdk@21")
    elif platform.system() == "Windows":
        print("   Download from: https://adoptium.net/")
    else:  # Linux
        print("   sudo apt install openjdk-21-jdk")
    return False

def install_dependencies():
    """Install Python dependencies"""
    try:
        print("📦 Installing Python dependencies...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], check=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def create_directories():
    """Create necessary directories"""
    directories = ['server', 'server/mods', 'server/backups', 'server/logs', 'logs']
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    print("✅ Directories created")

def create_config():
    """Create default configuration"""
    config = {
        'server_name': 'MCUS Server',
        'max_players': 20,
        'port': 25565,
        'host_computers': [],
        'mods': [],
        'world_name': 'world',
        'network_port': 25566,
        'minecraft_version': '1.21.7',
        'mod_loader': 'forge',
        'java_memory': '4G',
        'auto_backup': True,
        'backup_interval': 3600
    }
    
    import json
    with open('config.json', 'w') as f:
        json.dump(config, f, indent=2)
    print("✅ Default configuration created")

def setup_complete():
    """Show setup completion message"""
    print("\n🎉 MCUS Setup Complete!")
    print("\nNext steps:")
    print("1. Start MCUS:")
    if platform.system() == "Windows":
        print("   LAUNCH_MCUS.bat")
    else:
        print("   ./LAUNCH_MCUS.sh")
    print("\n2. Open your browser to: http://localhost:3000")
    print("\n3. Install Forge from the web interface")
    print("\n4. Start your Minecraft server!")
    print("\nFor help, see QUICK_START.md")

def main():
    """Main setup function"""
    print("🚀 MCUS (Minecraft Unified Server) Setup")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Check Java installation
    if not check_java_installation():
        print("\n⚠️  Java is required but not installed.")
        print("   You can continue setup, but you'll need Java to run the server.")
        response = input("   Continue anyway? (y/N): ")
        if response.lower() != 'y':
            sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        sys.exit(1)
    
    # Create directories
    create_directories()
    
    # Create config
    create_config()
    
    # Setup complete
    setup_complete()

if __name__ == "__main__":
    main() 