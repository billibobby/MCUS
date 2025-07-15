# 🚀 MCUS Quick Start Guide - Windows

## ⚡ One-Click Launch (RECOMMENDED)

### Step 1: Download and Extract
1. **Download** the MCUS zip file
2. **Extract** it to a folder (e.g., `C:\MCUS`)
3. **Open** the extracted folder

### Step 2: Launch MCUS
1. **Double-click** `LAUNCH_MCUS.bat`
2. **Wait** for setup to complete (2-3 minutes)
3. **Browser opens** automatically to http://localhost:3000

**That's it!** MCUS is now running and ready to use.

---

## 🔧 System Requirements

### Required Software:
- **Windows 10 or 11** (Windows 7/8 may work but not recommended)
- **Python 3.7 or higher** - [Download here](https://python.org/downloads/)
- **Java 8 or higher** - [Download here](https://adoptium.net/)
- **4GB+ RAM** recommended
- **Internet connection** (for mod downloads)

### Installation Tips:
- **Python**: Check "Add Python to PATH" during installation
- **Java**: Download the latest LTS version from Adoptium
- **Antivirus**: May need to allow MCUS through Windows Defender

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
2. **Check "Add Python to PATH"** during installation
3. Restart your computer
4. Try launching again

#### ❌ "Java not found"
**Solution:**
1. Download Java from https://adoptium.net/
2. Install the latest LTS version
3. Restart your computer
4. Try launching again

#### ❌ "Permission denied"
**Solution:**
1. Right-click `LAUNCH_MCUS.bat`
2. Select **"Run as administrator"**
3. Allow through Windows Defender if prompted

#### ❌ "Browser doesn't open"
**Solution:**
1. Manually open your browser
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
1. Check **Windows Firewall** settings
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

### Access from Phone/Tablet:
1. Find your **computer's IP address** (shown in launcher)
2. On your mobile device, go to **http://[YOUR_IP]:3000**
3. **Control MCUS** from anywhere on your network

### Example:
- Your IP: `192.168.1.100`
- Mobile URL: `http://192.168.1.100:3000`

---

## 🎉 You're Ready!

Your MCUS server is now set up and running! Here's what you can do:

✅ **Start your Minecraft server**  
✅ **Install mods from Modrinth**  
✅ **Add friends' computers for failover**  
✅ **Manage players and chat**  
✅ **Backup your world**  
✅ **Access from mobile devices**  

**Happy hosting!** 🎮

---

**Need more help?** Check the main README.md for detailed documentation. 