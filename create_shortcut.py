#!/usr/bin/env python3
"""
Create desktop shortcuts for MCUS launcher
"""

import os
import platform
import subprocess
from pathlib import Path

def create_windows_shortcut():
    """Create Windows desktop shortcut"""
    try:
        import winshell
        from win32com.client import Dispatch
        
        desktop = winshell.desktop()
        shortcut_path = os.path.join(desktop, "MCUS.lnk")
        
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.Targetpath = os.path.abspath("LAUNCH_MCUS.bat")
        shortcut.WorkingDirectory = os.path.abspath(".")
        shortcut.IconLocation = os.path.abspath("LAUNCH_MCUS.bat")
        shortcut.save()
        
        print(f"✅ Windows shortcut created: {shortcut_path}")
        return True
    except ImportError:
        print("⚠️  Could not create Windows shortcut (missing pywin32)")
        return False
    except Exception as e:
        print(f"❌ Error creating Windows shortcut: {e}")
        return False

def create_mac_shortcut():
    """Create macOS desktop shortcut"""
    try:
        desktop = Path.home() / "Desktop"
        app_path = Path.cwd() / "LAUNCH_MCUS.sh"
        
        # Create .command file (executable on macOS)
        command_file = desktop / "MCUS.command"
        
        with open(command_file, 'w') as f:
            f.write(f'''#!/bin/bash
cd "{Path.cwd()}"
./LAUNCH_MCUS.sh
''')
        
        # Make it executable
        os.chmod(command_file, 0o755)
        
        print(f"✅ macOS shortcut created: {command_file}")
        return True
    except Exception as e:
        print(f"❌ Error creating macOS shortcut: {e}")
        return False

def create_linux_shortcut():
    """Create Linux desktop shortcut"""
    try:
        desktop = Path.home() / "Desktop"
        desktop_file = desktop / "MCUS.desktop"
        
        with open(desktop_file, 'w') as f:
            f.write(f'''[Desktop Entry]
Version=1.0
Type=Application
Name=MCUS
Comment=Minecraft Unified Server
Exec={Path.cwd()}/LAUNCH_MCUS.sh
Icon=terminal
Terminal=true
Categories=Game;
''')
        
        # Make it executable
        os.chmod(desktop_file, 0o755)
        
        print(f"✅ Linux shortcut created: {desktop_file}")
        return True
    except Exception as e:
        print(f"❌ Error creating Linux shortcut: {e}")
        return False

def main():
    """Create shortcut based on platform"""
    print("🎮 Creating MCUS Desktop Shortcut...")
    print("=" * 40)
    
    system = platform.system()
    
    if system == "Windows":
        success = create_windows_shortcut()
    elif system == "Darwin":  # macOS
        success = create_mac_shortcut()
    elif system == "Linux":
        success = create_linux_shortcut()
    else:
        print(f"❌ Unsupported platform: {system}")
        return
    
    if success:
        print("\n✅ Shortcut created successfully!")
        print("🎯 You can now double-click the shortcut on your desktop to launch MCUS")
    else:
        print("\n⚠️  Could not create shortcut automatically")
        print("You can still run the launcher manually:")
        if system == "Windows":
            print("   Double-click: LAUNCH_MCUS.bat")
        else:
            print("   Double-click: LAUNCH_MCUS.sh")

if __name__ == "__main__":
    main() 