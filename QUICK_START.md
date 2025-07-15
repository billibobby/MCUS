# 🚀 MCUS Quick Start Guide

## One-Click Launch (EASIEST WAY)

### Windows Users:
1. **Double-click `LAUNCH_MCUS.bat`**
2. **Wait for setup to complete (2-3 minutes)**
3. **Browser will open automatically to http://localhost:3000**

### Mac/Linux Users:
1. **Double-click `LAUNCH_MCUS.sh`**
2. **Wait for setup to complete (2-3 minutes)**
3. **Browser will open automatically to http://localhost:3000**

📖 **For detailed platform-specific guides:**
- **[Windows Guide](QUICK_START_WINDOWS.md)** - Complete Windows setup and troubleshooting
- **[macOS Guide](QUICK_START_MAC.md)** - Complete macOS setup and troubleshooting
- **[Linux Guide](QUICK_START_LINUX.md)** - Complete Linux setup and troubleshooting

## What the Launcher Does:

✅ **Checks Python installation** (requires Python 3.7+)  
✅ **Checks Java installation** (needed for Minecraft)  
✅ **Creates virtual environment** (isolates dependencies)  
✅ **Installs all dependencies** (Flask, requests, etc.)  
✅ **Creates necessary directories** (server, mods, backups)  
✅ **Starts MCUS web interface**  
✅ **Opens browser automatically**  
✅ **Shows your IP address** (for friends to connect)  

## System Requirements:

- **Python 3.7 or higher** - [Download here](https://python.org/downloads/)
- **Java 8 or higher** - [Download here](https://adoptium.net/)
- **Internet connection** (for mod downloads)
- **2GB+ RAM** recommended

## Troubleshooting:

### If the launcher doesn't work:

1. **Python not found**: Install Python from python.org
2. **Java not found**: Install Java from adoptium.net
3. **Permission errors**: Run as administrator (Windows) or use sudo (Mac/Linux)
4. **Browser doesn't open**: Manually go to http://localhost:3000

### Manual Setup (if launcher fails):

```bash
# Create virtual environment
python3 -m venv mcus_env

# Activate environment
source mcus_env/bin/activate  # Mac/Linux
mcus_env\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Start MCUS
python web_app.py
```

## Next Steps:

1. **Install Forge** - Go to "Install Forge" in the web interface
2. **Browse Mods** - Check out popular mods from Modrinth
3. **Start Server** - Launch your Minecraft server
4. **Share with Friends** - Use the "Share with Friends" button

## Network Information:

When MCUS starts, it will show your IP address. Share this with your friends so they can join your hosting network!

---

## 📚 Additional Resources

### Platform-Specific Guides:
- **[Windows Guide](QUICK_START_WINDOWS.md)** - Complete Windows setup, troubleshooting, and advanced features
- **[macOS Guide](QUICK_START_MAC.md)** - Complete macOS setup, troubleshooting, and advanced features
- **[Linux Guide](QUICK_START_LINUX.md)** - Complete Linux setup, troubleshooting, and advanced features

### Main Documentation:
- **[README.md](README.md)** - Complete project overview and detailed documentation

---

**Need help?** Check the platform-specific guides above or the main README.md for detailed instructions. 