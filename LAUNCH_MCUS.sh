#!/bin/bash

# MCUS Launcher for Mac/Linux
# Double-click this file to launch MCUS

echo ""
echo "========================================"
echo "   MCUS - Minecraft Unified Server"
echo "        One-Click Launcher"
echo "========================================"
echo ""

# Check if Python is installed
echo "🔍 Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "❌ ERROR: Python 3 is not installed!"
    echo ""
    echo "Please install Python 3.7+ from:"
    echo "https://python.org/downloads/"
    echo ""
    echo "Or use your package manager:"
    echo "  Ubuntu/Debian: sudo apt install python3"
    echo "  macOS: brew install python3"
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

echo "✅ Python found!"
python3 --version
echo ""

# Make sure we're in the right directory
echo "📁 Setting up directory..."
cd "$(dirname "$0")"
echo "Working directory: $(pwd)"
echo ""

echo "🚀 Starting MCUS launcher..."
echo "This will take 2-3 minutes for first-time setup."
echo "You'll see real-time progress updates below:"
echo "Enhanced progress tracking shows detailed installation status."
echo ""

# Run the launcher
python3 launch_mcus.py

echo ""
echo "MCUS has stopped."
read -p "Press Enter to exit..." 

