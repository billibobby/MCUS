@echo off
title MCUS Web Server
echo ========================================
echo    MCUS - Minecraft Unified Server
echo         Web Interface
echo ========================================
echo.
echo Starting MCUS Web Server...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.7 or higher from https://python.org
    echo.
    pause
    exit /b 1
)

REM Install Flask if not already installed
echo Installing Flask...
python -m pip install flask

REM Create necessary directories
if not exist "server" mkdir server
if not exist "server\mods" mkdir server\mods
if not exist "backups" mkdir backups
if not exist "templates" mkdir templates

echo.
echo Starting MCUS Web Server...
echo.
echo Open your browser and go to: http://localhost:3000
echo To share with friends, use your IP address instead of localhost
echo.
echo Press Ctrl+C to stop the server
echo.

REM Start the web server
python web_app.py

echo.
echo MCUS Web Server has been stopped.
pause 