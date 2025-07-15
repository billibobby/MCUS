# MCUS Installation Guide

## Prerequisites

Before installing MCUS, make sure you have the following installed:

### Required Software

1. **Python 3.7 or higher**
   - Download from: https://python.org
   - Make sure to check "Add Python to PATH" during installation

2. **Java 8 or higher**
   - Download from: https://adoptium.net or https://java.com
   - Required for running Minecraft servers

3. **Git (optional)**
   - Download from: https://git-scm.com
   - Only needed if you want to clone the repository

## Installation Steps

### Windows Installation

1. **Download MCUS**
   - Download the ZIP file from the releases page
   - Extract to a folder (e.g., `C:\MCUS`)

2. **Run the installer**
   - Double-click `start_mcus.bat`
   - The script will automatically:
     - Check Python installation
     - Install dependencies
     - Create necessary folders
     - Start the application

3. **Alternative manual installation**
   ```cmd
   cd C:\MCUS
   pip install -r requirements.txt
   python src\main.py
   ```

### macOS Installation

1. **Download MCUS**
   ```bash
   git clone <repository-url>
   cd MCUS
   ```

2. **Make script executable**
   ```bash
   chmod +x start_mcus.sh
   ```

3. **Run the installer**
   ```bash
   ./start_mcus.sh
   ```

4. **Alternative manual installation**
   ```bash
   pip3 install -r requirements.txt
   python3 src/main.py
   ```

### Linux Installation

1. **Download MCUS**
   ```bash
   git clone <repository-url>
   cd MCUS
   ```

2. **Install system dependencies**
   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install python3 python3-pip openjdk-11-jre

   # CentOS/RHEL
   sudo yum install python3 python3-pip java-11-openjdk

   # Arch Linux
   sudo pacman -S python python-pip jre-openjdk
   ```

3. **Run the installer**
   ```bash
   chmod +x start_mcus.sh
   ./start_mcus.sh
   ```

4. **Alternative manual installation**
   ```bash
   pip3 install -r requirements.txt
   python3 src/main.py
   ```

## First-Time Setup

### 1. Configure Server Settings

1. Launch MCUS
2. Go to the **Settings** tab
3. Configure:
   - **Server Name**: Your server's display name
   - **Max Players**: Maximum number of players (default: 20)
   - **Port**: Minecraft server port (default: 25565)
   - **World Name**: Name for your world folder
4. Click "Save Settings"

### 2. Install Forge

1. Go to the **Mods** tab
2. Click "Install Forge"
3. Wait for the download and installation to complete
4. This may take several minutes depending on your internet connection

### 3. Set Up Hosting Network

1. Go to the **Hosting** tab
2. Enter your computer name
3. Click "Join Hosting Network"
4. Your computer is now part of the hosting network

### 4. Add Friends' Computers

1. Share the MCUS application with your friends
2. They follow the same installation steps
3. They join your hosting network using your IP address
4. Their computers become available for failover

## Troubleshooting

### Common Installation Issues

1. **Python not found**
   - Make sure Python is installed and added to PATH
   - Try running `python --version` in command prompt

2. **Java not found**
   - Install Java from https://adoptium.net
   - Make sure JAVA_HOME is set correctly

3. **Permission denied (Linux/macOS)**
   - Make sure the script is executable: `chmod +x start_mcus.sh`
   - Run with sudo if needed: `sudo ./start_mcus.sh`

4. **Dependencies not installing**
   - Try upgrading pip: `pip install --upgrade pip`
   - Install dependencies manually: `pip install requests psutil`

### Network Issues

1. **Can't connect to hosting network**
   - Check firewall settings
   - Make sure port 25566 is open
   - Verify all computers are on the same network

2. **Server won't start**
   - Check if Java is installed correctly
   - Verify Forge installation
   - Check server logs in the application

### Performance Issues

1. **Server is slow**
   - Increase Java memory allocation in settings
   - Close other applications
   - Check system resources

2. **Mods not loading**
   - Verify mod compatibility with Minecraft version
   - Check if Forge is installed
   - Restart server after mod installation

## Advanced Configuration

### Custom Java Arguments

You can modify Java memory and other settings in the configuration:

1. Edit `config.json`
2. Modify the `java_memory` setting
3. Add custom Java arguments if needed

### Firewall Configuration

For the hosting network to work, make sure these ports are open:

- **25565**: Minecraft server port
- **25566**: MCUS network communication port

### Automatic Backups

Enable automatic world backups:

1. Go to Settings
2. Enable "Auto Backup"
3. Set backup interval (in seconds)

## Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review the application logs
3. Check the server logs in the `server/` folder
4. Create an issue on the repository with:
   - Your operating system
   - Python version
   - Java version
   - Error messages from logs

## Uninstallation

To remove MCUS:

1. Stop the application
2. Delete the MCUS folder
3. Optionally remove Python dependencies:
   ```bash
   pip uninstall requests psutil
   ```

The server files and worlds will be preserved in the `server/` folder. 