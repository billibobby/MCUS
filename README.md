# MCUS - Minecraft Unified Server

🎮 **The Ultimate Minecraft Server Management System**

MCUS is a comprehensive Minecraft server management platform that makes it easy to set up, manage, and run Minecraft servers with mod support, Forge integration, and advanced features.

## ✨ Features

- 🚀 **One-Click Server Setup** - Get your Minecraft server running in minutes
- 🔧 **Forge Integration** - Automatic Forge installation and management
- 📦 **Mod Management** - Browse, search, and install mods from Modrinth
- 🌐 **Web Interface** - Beautiful, modern web dashboard for server management
- 🔄 **Real-time Monitoring** - Live server status, player tracking, and performance metrics
- 💾 **Auto Backup** - Automatic world backups with configurable schedules
- 🌍 **Multi-Host Support** - Distribute server load across multiple computers
- 🛠️ **System Diagnostics** - Built-in troubleshooting and health checks
- 📱 **Cross-Platform** - Works on Windows, macOS, and Linux

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+** - [Download Python](https://python.org)
- **Java 21+** - Required for Forge servers
  - **Windows**: Download from [Eclipse Temurin](https://adoptium.net/)
  - **macOS**: `brew install openjdk@21`
  - **Linux**: `sudo apt install openjdk-21-jdk`

### Installation

#### Local Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/MCUS.git
   cd MCUS
   ```

2. **Run the setup script**
   ```bash
   python setup.py
   ```

3. **Start MCUS**
   - **Windows**: Double-click `LAUNCH_MCUS.bat`
   - **macOS/Linux**: `./LAUNCH_MCUS.sh`

4. **Open your browser**
   Navigate to: http://localhost:3000

5. **Install Forge**
   - Click "Install Forge" in the web interface
   - Select your desired Minecraft version
   - Wait for installation to complete

6. **Start your server**
   - Click "Start Server" in the dashboard
   - Your Minecraft server is now running!

#### Cloud Deployment (Railway)

Want to host MCUS in the cloud? Deploy to Railway with one click:

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/new?template=https://github.com/yourusername/MCUS)

**Railway Deployment Steps:**
1. Click the "Deploy on Railway" button above
2. Sign in with your GitHub account
3. Railway will automatically deploy MCUS
4. Access your instance at the provided URL

**Note**: Railway deployment is for the web interface only. The actual Minecraft server should run locally.

For detailed Railway deployment instructions, see [RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md).

## 📖 Detailed Guides

- **[Quick Start Guide](QUICK_START.md)** - Complete setup instructions
- **[Windows Setup](QUICK_START_WINDOWS.md)** - Windows-specific instructions
- **[macOS Setup](QUICK_START_MAC.md)** - macOS-specific instructions
- **[Linux Setup](QUICK_START_LINUX.md)** - Linux-specific instructions

## 🎯 What's New

### Enhanced Forge Detection
- **Smart Installation Detection** - Only shows Forge as "installed" when properly configured
- **Real-time Status Monitoring** - Live updates of server and Forge status
- **Issue Detection** - Automatically identifies and reports setup problems
- **Java Compatibility Checking** - Ensures your Java version works with Forge

### Improved User Experience
- **Progress Tracking** - Real-time installation progress with visual indicators
- **Error Handling** - Better error messages and troubleshooting guidance
- **Status Validation** - Distinguishes between web interface status and actual server process
- **Auto-refresh** - Dashboard updates automatically every 30 seconds

## 🛠️ System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **Python** | 3.8+ | 3.11+ |
| **Java** | 21+ | 21+ |
| **RAM** | 4GB | 8GB+ |
| **Storage** | 2GB | 10GB+ |
| **OS** | Windows 10, macOS 10.15, Ubuntu 20.04 | Latest versions |

## 🔧 Configuration

MCUS uses a simple JSON configuration file (`config.json`) that's created automatically. Key settings:

```json
{
  "server_name": "MCUS Server",
  "max_players": 20,
  "port": 25565,
  "minecraft_version": "1.21.7",
  "mod_loader": "forge",
  "java_memory": "4G",
  "auto_backup": true,
  "backup_interval": 3600
}
```

## 📁 Project Structure

```
MCUS/
├── src/                    # Core application code
│   ├── server_manager.py   # Server management logic
│   ├── mod_manager.py      # Mod installation and management
│   └── network_manager.py  # Multi-host networking
├── templates/              # Web interface templates
├── server/                 # Minecraft server files
├── logs/                   # Application logs
├── web_app.py             # Web interface server
├── setup.py               # Setup script
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## 🎮 Supported Minecraft Versions

- **Minecraft 1.21.x** - Full support with Forge
- **Minecraft 1.20.x** - Full support with Forge
- **Minecraft 1.19.x** - Full support with Forge
- **Minecraft 1.18.x** - Full support with Forge

## 🔗 Modrinth Integration

MCUS includes full integration with Modrinth, allowing you to:
- Browse thousands of mods
- Search by name, category, or tags
- Install mods with one click
- Manage mod dependencies automatically
- View mod popularity and ratings

## 🚨 Troubleshooting

### Common Issues

1. **"Java not found"**
   - Install Java 21+ and ensure it's in your PATH
   - See platform-specific guides for installation instructions

2. **"Forge installation failed"**
   - Check your internet connection
   - Ensure you have sufficient disk space
   - Try running the diagnostics tool in the web interface

3. **"Server won't start"**
   - Check the server logs in the web interface
   - Ensure no other service is using port 25565
   - Verify Java compatibility with your Forge version

4. **"Web interface not loading"**
   - Ensure port 3000 is not in use
   - Check if the web app is running
   - Try accessing http://127.0.0.1:3000 instead

### Getting Help

- 📖 Check the [Quick Start Guide](QUICK_START.md)
- 🔍 Use the built-in [System Diagnostics](http://localhost:3000/diagnostics)
- 🐛 Check the logs in the `logs/` directory
- 💬 Open an issue on GitHub

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines and feel free to submit pull requests.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Minecraft Forge** - For the amazing modding platform
- **Modrinth** - For the comprehensive mod database
- **Flask** - For the web framework
- **The Minecraft Community** - For inspiration and feedback

---

**Made with ❤️ for the Minecraft community**

*MCUS - Making Minecraft server management simple and powerful* 