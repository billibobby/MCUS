# 🚀 MCUS Quick Start Guide - macOS

## ⚡ One-Click Launch (RECOMMENDED)

### Step 1: Download and Extract
1. **Download** the MCUS zip file
2. **Extract** it to a folder (e.g., `~/Documents/MCUS`)
3. **Open** the extracted folder in Finder

### Step 2: Launch MCUS
1. **Double-click** `LAUNCH_MCUS.sh`
2. **Wait** for setup to complete (2-3 minutes)
3. **Browser opens** automatically to http://localhost:3000

**That's it!** MCUS is now running and ready to use.

---

## 🔧 System Requirements

### Required Software:
- **macOS 10.14 (Mojave) or higher** (recommended: macOS 11+)
- **Python 3.7 or higher** - [Download here](https://python.org/downloads/)
- **Java 8 or higher** - [Download here](https://adoptium.net/)
- **4GB+ RAM** recommended
- **Internet connection** (for mod downloads)

### Installation Tips:
- **Python**: Download the latest version from python.org
- **Java**: Download the latest LTS version from Adoptium
- **Terminal**: May need to allow Terminal in Security & Privacy settings

---

## 🎮 First Time Setup

### 1. Install Forge (Required for Mods)
1. Go to the **Dashboard** tab
2. Click **"Install Forge"** button
3. Select **Minecraft version** (recommended: 1.19.2)
4. Wait for installation to complete

### 2. Configure Server Settings
1. Go to **Settings** tab
2. Set your **Server Name**
3. Adjust **Max Players** (default: 20)
4. Click **"Save Settings"**

### 3. Add Host Computers
1. Go to **Hosting** tab
2. Enter your **Computer Name**
3. Click **"Join Hosting Network"**
4. Repeat for each computer that will host

---

## 🌐 Setting Up Distributed Hosting

### Adding Your Computer:
1. In the **Hosting** tab, your computer name should auto-fill
2. Click **"Join Hosting Network"**
3. Your computer is now part of the hosting network

### Adding Friends' Computers:
1. **Share MCUS** with your friends (use "Share with Friends" button)
2. **Friends install** MCUS on their computers
3. **Friends join** your network using your IP address
4. **Multiple computers** can now host the same server

### How Failover Works:
- **Primary host** runs the server normally
- **Backup hosts** monitor for failures
- **Automatic switch** when primary host goes offline
- **Players continue** playing without interruption

---

## 📦 Installing Mods

### Method 1: Browse Modrinth (Recommended)
1. Go to **Mods** tab
2. Click **"Browse Modrinth"**
3. **Search** for mods you want
4. Click **"Download"** on desired mods
5. **Restart server** after installing mods

### Method 2: Popular Mods
1. Go to **Mods** tab
2. Click **"Popular Mods"**
3. Browse **trending mods**
4. Click **"Install Pack"** for curated collections

### Method 3: Local Mod Files
1. Go to **Mods** tab
2. Click **"Browse Mod Files"**
3. Select **.jar files** from your computer
4. Click **"Install"**

---

## 🎯 Starting Your Server

### Quick Start:
1. Go to **Dashboard** tab
2. Click **"Start Server"** button
3. Wait for server to start (30-60 seconds)
4. **Players can now connect!**

### Server Information:
- **IP Address**: Your computer's IP (shown in launcher)
- **Port**: 25565 (default Minecraft port)
- **Status**: Shows online/offline status
- **Players**: Real-time player count

---

## 👥 Player Management

### Viewing Players:
1. Go to **Players** tab
2. See **online players** and their ping
3. View **chat logs** in real-time

### Admin Commands:
1. In **Players** tab, use the chat input
2. Type **server commands** like:
   - `/op [player]` - Give operator status
   - `/kick [player]` - Kick a player
   - `/ban [player]` - Ban a player
   - `/whitelist add [player]` - Add to whitelist

---

## 🔧 Troubleshooting

### Common Issues:

#### ❌ "Python not found"
**Solution:**
1. Download Python from https://python.org/downloads/
2. **Install Python** following the installer instructions
3. **Restart Terminal** or restart your Mac
4. Try launching again

#### ❌ "Java not found"
**Solution:**
1. Download Java from https://adoptium.net/
2. Install the latest LTS version
3. **Restart Terminal** or restart your Mac
4. Try launching again

#### ❌ "Permission denied" or "Operation not permitted"
**Solution:**
1. **Open Terminal** (Applications > Utilities > Terminal)
2. **Navigate** to your MCUS folder:
   ```bash
   cd ~/Documents/MCUS  # or wherever you extracted MCUS
   ```
3. **Make the script executable**:
   ```bash
   chmod +x LAUNCH_MCUS.sh
   ```
4. **Run the script**:
   ```bash
   ./LAUNCH_MCUS.sh
   ```

#### ❌ "Security settings blocked the operation"
**Solution:**
1. Go to **System Preferences > Security & Privacy**
2. Click **"Allow Anyway"** for Terminal or Python
3. **Try launching again**

#### ❌ "Browser doesn't open"
**Solution:**
1. Manually open **Safari** or **Chrome**
2. Go to **http://localhost:3000**
3. MCUS should be running

#### ❌ "Server won't start"
**Solution:**
1. Check **Diagnostics** tab for errors
2. Ensure **Forge is installed**
3. Check **Java installation**
4. Verify **port 25565 is available**

#### ❌ "Can't connect to network"
**Solution:**
1. Check **macOS Firewall** settings
2. Allow MCUS through firewall
3. Ensure **port 25566 is open**
4. Check **network connectivity**

### Getting Help:
1. Check the **Diagnostics** tab for detailed error information
2. Review **server.log** file for technical details
3. Check the main **README.md** for advanced troubleshooting

---

## 🔄 Advanced Features

### World Backup:
1. Go to **Dashboard** tab
2. Click **"Backup World"** button
3. Backups saved in `server/backups/` folder

### Server Settings:
- **Memory allocation**: Adjust in Settings tab
- **Auto-backup**: Enable automatic backups
- **Network port**: Change if needed (default: 25566)

### Sharing with Friends:
1. Click **"Share with Friends"** button
2. **Copy the share link**
3. **Send to friends** via email/message
4. **Friends download** and install MCUS
5. **Friends join** your hosting network

---

## 📱 Mobile Access

### Access from iPhone/iPad:
1. Find your **Mac's IP address** (shown in launcher)
2. On your iOS device, open **Safari**
3. Go to **http://[YOUR_IP]:3000**
4. **Control MCUS** from anywhere on your network

### Example:
- Your Mac's IP: `192.168.1.100`
- Mobile URL: `http://192.168.1.100:3000`

---

## 🍎 macOS-Specific Tips

### Using Terminal (Alternative Method):
If the one-click launcher doesn't work, you can use Terminal:

1. **Open Terminal** (Applications > Utilities > Terminal)
2. **Navigate** to your MCUS folder:
   ```bash
   cd ~/Documents/MCUS
   ```
3. **Make scripts executable**:
   ```bash
   chmod +x LAUNCH_MCUS.sh
   chmod +x QUICK_LAUNCH.sh
   ```
4. **Run the launcher**:
   ```bash
   ./LAUNCH_MCUS.sh
   ```

### Homebrew Installation (Optional):
If you have Homebrew installed, you can install Python and Java:

```bash
# Install Python
brew install python

# Install Java
brew install --cask temurin
```

### Finder Integration:
- **Right-click** on MCUS folder
- Select **"New Terminal at Folder"**
- Run `./LAUNCH_MCUS.sh` in the terminal

---

## 🎉 You're Ready!

Your MCUS server is now set up and running! Here's what you can do:

✅ **Start your Minecraft server**  
✅ **Install mods from Modrinth**  
✅ **Add friends' computers for failover**  
✅ **Manage players and chat**  
✅ **Backup your world**  
✅ **Access from iPhone/iPad**  

**Happy hosting!** 🎮

---

**Need more help?** Check the main README.md for detailed documentation. 