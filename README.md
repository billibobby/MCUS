# MCUS - Minecraft Unified Server

A distributed Minecraft server hosting application that allows multiple computers across the USA to host the same server seamlessly. When one computer goes offline, another can take over without interruption.

## Features

- **Distributed Hosting**: Multiple computers can host the same server
- **Automatic Failover**: Seamless switching between host computers
- **Easy Setup**: Simple GUI for connecting computers to the network
- **Mod Management**: Easy installation and removal of mods
- **Forge Support**: Built-in Forge server installation
- **Server Control**: Logs, chat, and player management
- **World Backup**: Automatic world backup functionality
- **Free Hosting**: Uses Minecraft's Java hosting and Forge mod servers

## Requirements

- Python 3.7 or higher
- Java 8 or higher (for Minecraft server)
- Internet connection for mod downloads
- Windows, macOS, or Linux

## Installation

1. **Clone or download this repository**
   ```bash
   git clone <repository-url>
   cd MCUS
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python src/main.py
   ```

## Quick Start Guide

### 1. Initial Setup

1. Launch the application
2. Go to the **Settings** tab
3. Configure your server settings:
   - Server Name
   - Max Players
   - Port (default: 25565)
   - World Name
4. Click "Save Settings"

### 2. Install Forge

1. Go to the **Mods** tab
2. Click "Install Forge"
3. Wait for the installation to complete

### 3. Add Host Computers

1. Go to the **Hosting** tab
2. Enter your computer name
3. Click "Join Hosting Network"
4. Repeat for each computer that will host the server

### 4. Install Mods

1. Go to the **Mods** tab
2. Click "Browse Mod Files" to install local mod files
3. Or click "Download from CurseForge" to visit the mod website

### 5. Start the Server

1. Go to the **Dashboard** tab
2. Click "Start Server"
3. The server will start and be available to players

## How Distributed Hosting Works

### Network Architecture

- **Network Manager**: Coordinates between host computers (port 25566)
- **Host Clients**: Each computer runs a client that connects to the network
- **Server Manager**: Manages the actual Minecraft server process
- **Failover System**: Automatically switches to available hosts

### Host Computer Setup

1. **Primary Host**: The first computer to start hosting
2. **Backup Hosts**: Additional computers that can take over
3. **Automatic Detection**: System detects when a host goes offline
4. **Seamless Transfer**: Players can continue playing without interruption

### Adding Friends' Computers

1. Share the application with your friends
2. They install it on their computers
3. They join your hosting network using your IP address
4. Their computers become available for failover

## Configuration

### Server Settings

- **Server Name**: Display name for the server
- **Max Players**: Maximum number of players allowed
- **Port**: Minecraft server port (default: 25565)
- **World Name**: Name of the world folder
- **Network Port**: Port for host communication (default: 25566)

### Advanced Settings

- **CurseForge API Key**: For downloading mods directly (optional)
- **Memory Allocation**: Adjust server memory usage
- **Backup Schedule**: Configure automatic backups

## Troubleshooting

### Common Issues

1. **Server won't start**
   - Check if Java is installed
   - Verify Forge is installed
   - Check server logs

2. **Can't connect to network**
   - Verify firewall settings
   - Check network port availability
   - Ensure all computers are on the same network

3. **Mods not working**
   - Verify mod compatibility with Minecraft version
   - Check if Forge is installed
   - Restart server after mod installation

### Logs

- Server logs are saved in `server.log`
- Application logs show in the console
- Check logs for detailed error information

## File Structure

```
MCUS/
├── src/
│   ├── main.py              # Main application
│   ├── server_manager.py    # Server management
│   ├── mod_manager.py       # Mod management
│   └── network_manager.py   # Network communication
├── server/                  # Minecraft server files
│   ├── mods/               # Installed mods
│   ├── world/              # World data
│   └── backups/            # World backups
├── requirements.txt         # Python dependencies
├── README.md               # This file
└── start_mcus.bat          # Windows shortcut
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is open source and available under the MIT License.

## Support

For support and questions:
- Check the troubleshooting section
- Review the logs for error details
- Create an issue on the repository

## Credits

- Minecraft Forge team for the modding platform
- CurseForge for mod hosting
- Python community for the libraries used

---

**Note**: This application is designed for personal use and small groups. For large-scale hosting, consider professional hosting services. 