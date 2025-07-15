@echo off
title MCUS - Minecraft Unified Server
echo ========================================
echo    MCUS - Minecraft Unified Server
echo ========================================
echo.
echo Starting MCUS application...
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

REM Check if required files exist
if not exist "src\main.py" (
    echo ERROR: main.py not found
    echo Please make sure you're running this from the MCUS directory
    echo.
    pause
    exit /b 1
)

REM Install dependencies if requirements.txt exists
if exist "requirements.txt" (
    echo Installing/updating dependencies...
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo WARNING: Some dependencies may not have installed correctly
        echo The application may still work, but some features might be limited
        echo.
    )
)

REM Create necessary directories
if not exist "server" mkdir server
if not exist "server\mods" mkdir server\mods
if not exist "backups" mkdir backups

echo.
echo Starting MCUS...
echo.

REM Start the application
python src\main.py

REM If the application exits with an error
if errorlevel 1 (
    echo.
    echo ERROR: The application crashed or encountered an error
    echo Check the console output above for details
    echo.
    echo Common solutions:
    echo - Make sure Java is installed
    echo - Check if all dependencies are installed
    echo - Verify firewall settings
    echo.
    pause
)

echo.
echo MCUS has been closed.
pause 