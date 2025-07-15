#!/bin/bash

echo "========================================"
echo "   MCUS - Minecraft Unified Server"
echo "========================================"
echo ""
echo "Starting MCUS application..."
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed or not in PATH"
    echo "Please install Python 3.7 or higher"
    echo ""
    exit 1
fi

# Check if required files exist
if [ ! -f "src/main.py" ]; then
    echo "ERROR: main.py not found"
    echo "Please make sure you're running this from the MCUS directory"
    echo ""
    exit 1
fi

# Install dependencies if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "Installing/updating dependencies..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "WARNING: Some dependencies may not have installed correctly"
        echo "The application may still work, but some features might be limited"
        echo ""
    fi
fi

# Create necessary directories
mkdir -p server/mods
mkdir -p backups

echo ""
echo "Starting MCUS..."
echo ""

# Start the application
python3 src/main.py

# If the application exits with an error
if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: The application crashed or encountered an error"
    echo "Check the console output above for details"
    echo ""
    echo "Common solutions:"
    echo "- Make sure Java is installed"
    echo "- Check if all dependencies are installed"
    echo "- Verify firewall settings"
    echo ""
    read -p "Press Enter to continue..."
fi

echo ""
echo "MCUS has been closed." 