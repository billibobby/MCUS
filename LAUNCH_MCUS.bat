@echo off
title MCUS Launcher
color 0A

echo.
echo ========================================
echo    MCUS - Minecraft Unified Server
echo         One-Click Launcher
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed!
    echo.
    echo Please install Python 3.7+ from:
    echo https://python.org/downloads/
    echo.
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

echo Python found! Starting MCUS...
echo.
echo 🚀 Launching MCUS with enhanced progress tracking...
echo This will show real-time progress during installation.
echo.

REM Run the launcher
python launch_mcus.py

echo.
echo MCUS has stopped.
pause 