#!/usr/bin/env python3
"""
MCUS Sharing Script - Makes it easy to share MCUS with friends
"""

import os
import shutil
import zipfile
import json
import subprocess
import socket
from pathlib import Path
from datetime import datetime

def get_local_ip():
    """Get the local IP address"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except:
        return "127.0.0.1"

def create_share_package():
    """Create a shareable MCUS package"""
    print("🎮 Creating MCUS Share Package...")
    print("=" * 50)
    
    # Create share directory
    share_dir = Path("MCUS_Share")
    if share_dir.exists():
        shutil.rmtree(share_dir)
    share_dir.mkdir()
    
    # Copy essential files
    essential_files = [
        "web_app.py",
        "requirements.txt",
        "README.md",
        "launch_mcus.py",
        "LAUNCH_MCUS.bat",
        "LAUNCH_MCUS.sh",
        "check_forge.py"
    ]
    
    essential_dirs = [
        "src",
        "templates"
    ]
    
    print("📁 Copying essential files...")
    for file in essential_files:
        if Path(file).exists():
            shutil.copy2(file, share_dir)
            print(f"  ✅ {file}")
        else:
            print(f"  ⚠️  {file} (not found)")
    
    print("📁 Copying essential directories...")
    for dir_name in essential_dirs:
        if Path(dir_name).exists():
            shutil.copytree(dir_name, share_dir / dir_name)
            print(f"  ✅ {dir_name}/")
        else:
            print(f"  ⚠️  {dir_name}/ (not found)")
    
    # Create easy setup script
    create_setup_script(share_dir)
    
    # Create README for friends
    create_friend_readme(share_dir)
    
    # Create zip file
    zip_name = f"MCUS_Share_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    print(f"📦 Creating zip file: {zip_name}")
    
    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(share_dir):
            for file in files:
                file_path = Path(root) / file
                arcname = file_path.relative_to(share_dir)
                zipf.write(file_path, arcname)
    
    # Clean up
    shutil.rmtree(share_dir)
    
    print("=" * 50)
    print(f"🎉 Share package created: {zip_name}")
    print(f"📧 Send this file to your friends!")
    print(f"🌐 Your IP: {get_local_ip()}")
    print("=" * 50)
    
    return zip_name

def create_setup_script(share_dir):
    """Create an easy setup script for friends"""
    setup_script = '''#!/bin/bash
echo "🎮 MCUS - Minecraft Unified Server"
echo "=================================="
echo ""
echo "Setting up MCUS for you..."
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    echo "Please install Python 3.7+ from https://python.org"
    exit 1
fi

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv mcus_env

# Activate environment
echo "🔧 Activating environment..."
source mcus_env/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Create directories
echo "📁 Creating directories..."
mkdir -p server/mods backups

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start MCUS:"
echo "1. Run: source mcus_env/bin/activate"
echo "2. Run: python web_app.py"
echo "3. Open: http://localhost:3000"
echo ""
echo "To join your friend's server:"
echo "1. Ask them for their IP address"
echo "2. Go to the Hosting tab"
echo "3. Enter their IP and join the network"
echo ""
'''
    
    with open(share_dir / "setup.sh", 'w') as f:
        f.write(setup_script)
    
    # Make it executable
    os.chmod(share_dir / "setup.sh", 0o755)

def create_friend_readme(share_dir):
    """Create a README for friends"""
    readme_content = f'''# 🎮 MCUS - Minecraft Unified Server

## Welcome to MCUS!

This is a Minecraft server management tool that lets you:
- 🚀 Host Minecraft servers with mods
- 🌐 Join your friends' distributed hosting networks
- 📦 Install mods directly from Modrinth
- 🔧 Manage server settings easily

## 🚀 Quick Start (EASIEST WAY)

### Windows Users:
1. **Double-click `LAUNCH_MCUS.bat`**
2. **Wait for setup to complete**
3. **Browser will open automatically**

### Mac/Linux Users:
1. **Double-click `LAUNCH_MCUS.sh`**
2. **Wait for setup to complete**
3. **Browser will open automatically**

That's it! The launcher will:
- ✅ Check if Python is installed
- ✅ Create virtual environment
- ✅ Install all dependencies
- ✅ Start MCUS automatically
- ✅ Open your browser to the interface

## 🔧 Manual Setup (Alternative)

If the launcher doesn't work, you can set up manually:

### 1. Setup (One-time)
```bash
# Run the setup script
./setup.sh

# Or manually:
python3 -m venv mcus_env
source mcus_env/bin/activate
pip install -r requirements.txt
```

### 2. Start MCUS
```bash
source mcus_env/bin/activate
python web_app.py
```

### 3. Open in Browser
Go to: http://localhost:3000

## Join Your Friend's Server

1. **Ask your friend for their IP address**
2. **Open MCUS in your browser**
3. **Go to the "Hosting" tab**
4. **Enter your friend's IP address**
5. **Click "Join Network"**

## Features

- 🌟 **Popular Mods**: Browse and install popular mods
- 🔍 **Mod Search**: Search for specific mods
- 🎮 **Server Management**: Start, stop, and configure servers
- 👥 **Multi-Player**: Join distributed hosting networks
- 📊 **Monitoring**: Real-time server statistics

## System Requirements

- Python 3.7 or higher
- Java 8 or higher (for Minecraft)
- Internet connection
- 2GB+ RAM recommended

## Troubleshooting

### If the launcher doesn't work:
1. Make sure Python 3.7+ is installed
2. Try running the manual setup
3. Check that you have internet connection
4. Make sure Java is installed for Minecraft servers

### Common Issues:
- **"Python not found"**: Install Python from python.org
- **"Java not found"**: Install Java from adoptium.net
- **"Permission denied"**: Run as administrator (Windows) or use sudo (Mac/Linux)

## Need Help?

- Check the README.md for detailed instructions
- Ask your friend who sent you this package
- Visit the project page for more information

---
*Shared with you by a friend using MCUS*
*Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
'''
    
    with open(share_dir / "FRIEND_README.md", 'w') as f:
        f.write(readme_content)

def create_windows_batch(share_dir):
    """Create Windows batch file for easy setup"""
    batch_content = '''@echo off
title MCUS Setup
echo ========================================
echo    MCUS - Minecraft Unified Server
echo         Setup for Windows
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed
    echo Please install Python 3.7+ from https://python.org
    echo.
    pause
    exit /b 1
)

REM Create virtual environment
echo Creating virtual environment...
python -m venv mcus_env

REM Activate environment
echo Activating environment...
call mcus_env\\Scripts\\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Create directories
echo Creating directories...
if not exist "server" mkdir server
if not exist "server\\mods" mkdir server\\mods
if not exist "backups" mkdir backups

echo.
echo Setup complete!
echo.
echo To start MCUS:
echo 1. Run: mcus_env\\Scripts\\activate.bat
echo 2. Run: python web_app.py
echo 3. Open: http://localhost:3000
echo.
pause
'''
    
    with open(share_dir / "setup.bat", 'w') as f:
        f.write(batch_content)

def main():
    """Main function"""
    print("🎮 MCUS Sharing Tool")
    print("=" * 50)
    print("This tool creates a shareable package for your friends.")
    print("")
    
    # Get user's IP
    local_ip = get_local_ip()
    print(f"🌐 Your IP Address: {local_ip}")
    print("(Share this with your friends so they can join your server)")
    print("")
    
    # Create package
    zip_name = create_share_package()
    
    print("")
    print("📋 Instructions for sharing:")
    print("1. Send the zip file to your friends")
    print("2. Tell them to extract it and run setup.sh (or setup.bat on Windows)")
    print("3. Give them your IP address: " + local_ip)
    print("4. They can then join your hosting network!")
    print("")
    print("🎉 Happy gaming!")

if __name__ == "__main__":
    main() 