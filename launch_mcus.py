#!/usr/bin/env python3
"""
MCUS One-Click Launcher
Automatically sets up and starts MCUS with a single click
"""

import os
import sys
import subprocess
import platform
import webbrowser
import time
import socket
from pathlib import Path
import threading
import shutil

class RealTimeProgressBar:
    """Enhanced progress bar with real-time updates"""
    
    def __init__(self, total_steps, description="Setup Progress"):
        self.total_steps = total_steps
        self.current_step = 0
        self.description = description
        self.current_operation = ""
        self.operation_progress = 0
        self.operation_total = 100
        
    def update_step(self, step_description=""):
        """Update to next step"""
        self.current_step += 1
        self.current_operation = step_description
        self.operation_progress = 0
        self._display_progress()
        
    def update_operation_progress(self, progress, total=100, operation=""):
        """Update progress within current operation"""
        self.operation_progress = progress
        self.operation_total = total
        if operation:
            self.current_operation = operation
        self._display_progress()
        
    def _display_progress(self):
        """Display the current progress"""
        # Overall progress
        overall_percentage = (self.current_step / self.total_steps) * 100
        bar_length = 30
        filled_length = int(bar_length * self.current_step // self.total_steps)
        bar = '█' * filled_length + '░' * (bar_length - filled_length)
        
        # Operation progress
        op_percentage = (self.operation_progress / self.operation_total) * 100 if self.operation_total > 0 else 0
        op_bar_length = 20
        op_filled_length = int(op_bar_length * self.operation_progress // self.operation_total)
        op_bar = '█' * op_filled_length + '░' * (op_bar_length - op_filled_length)
        
        # Clear line and display
        print(f"\r{self.description}: [{bar}] {overall_percentage:.1f}% - {self.current_operation} [{op_bar}] {op_percentage:.1f}%", end='', flush=True)
        
    def complete(self, final_message=""):
        """Complete the progress bar"""
        self.current_step = self.total_steps
        self.operation_progress = self.operation_total
        self.current_operation = final_message
        self._display_progress()
        print()

class InstallationMonitor:
    """Monitor installation progress in real-time"""
    
    def __init__(self, progress_bar):
        self.progress_bar = progress_bar
        self.current_operation = ""
        
    def install_package_with_progress(self, pip_path, package_name, timeout=120):
        """Install a package with real-time progress monitoring"""
        self.progress_bar.update_operation_progress(0, 100, f"Installing {package_name}...")
        
        try:
            # Start the installation process
            process = subprocess.Popen(
                [pip_path, 'install', package_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Monitor output in real-time
            progress = 0
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    # Update progress based on output
                    if "Collecting" in output:
                        progress = 20
                    elif "Downloading" in output:
                        progress = 40
                    elif "Installing" in output:
                        progress = 60
                    elif "Successfully" in output:
                        progress = 100
                    elif "Requirement already satisfied" in output:
                        progress = 100
                    
                    self.progress_bar.update_operation_progress(progress, 100, f"Installing {package_name}...")
                    
                    # Add a small delay to make progress visible
                    time.sleep(0.1)
            
            # Wait for process to complete
            return_code = process.poll()
            
            if return_code == 0:
                self.progress_bar.update_operation_progress(100, 100, f"✅ {package_name} installed")
                return True
            else:
                self.progress_bar.update_operation_progress(100, 100, f"⚠️  {package_name} had issues")
                return False
                
        except subprocess.TimeoutExpired:
            self.progress_bar.update_operation_progress(100, 100, f"⚠️  {package_name} timed out")
            return False
        except Exception as e:
            self.progress_bar.update_operation_progress(100, 100, f"❌ {package_name} failed: {str(e)[:30]}")
            return False

def get_local_ip():
    """Get the local IP address"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except:
        return "127.0.0.1"

def check_python():
    """Check if Python is installed and has the right version"""
    try:
        version = sys.version_info
        if version.major >= 3 and version.minor >= 7:
            return True, f"Python {version.major}.{version.minor}.{version.micro}"
        else:
            return False, f"Python {version.major}.{version.minor}.{version.micro} (Need 3.7+)"
    except:
        return False, "Python not found"

def check_java():
    """Check if Java is installed"""
    try:
        result = subprocess.run(['java', '-version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            return True, "Java found"
        else:
            return False, "Java not working"
    except:
        return False, "Java not found"

def create_directories(progress_bar):
    """Create necessary directories with progress"""
    progress_bar.update_operation_progress(0, 100, "Creating directories...")
    
    dirs = ['server', 'server/mods', 'backups', 'logs']
    for i, dir_name in enumerate(dirs):
        progress = int((i / len(dirs)) * 100)
        progress_bar.update_operation_progress(progress, 100, f"Creating {dir_name}...")
        Path(dir_name).mkdir(exist_ok=True)
        time.sleep(0.1)  # Small delay for visual feedback
    
    progress_bar.update_operation_progress(100, 100, "✅ Directories created")

def setup_virtual_environment(progress_bar):
    """Set up Python virtual environment with progress"""
    venv_path = Path("mcus_env")
    
    if venv_path.exists():
        # Check if it's a valid virtual environment
        if platform.system() == "Windows":
            python_path = venv_path / "Scripts" / "python"
        else:
            python_path = venv_path / "bin" / "python"
        
        if python_path.exists():
            progress_bar.update_operation_progress(100, 100, "✅ Virtual environment already exists")
            return True
        else:
            # Invalid venv, remove and recreate
            progress_bar.update_operation_progress(0, 100, "Recreating invalid virtual environment...")
            shutil.rmtree(venv_path)
    
    progress_bar.update_operation_progress(0, 100, "Creating virtual environment...")
    
    try:
        # Start venv creation
        process = subprocess.Popen(
            [sys.executable, '-m', 'venv', 'mcus_env'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        
        # Monitor progress
        progress = 0
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                progress = min(progress + 20, 90)  # Increment progress
                progress_bar.update_operation_progress(progress, 100, "Creating virtual environment...")
                time.sleep(0.1)
        
        return_code = process.poll()
        
        if return_code == 0:
            progress_bar.update_operation_progress(100, 100, "✅ Virtual environment created")
            return True
        else:
            progress_bar.update_operation_progress(100, 100, "❌ Virtual environment creation failed")
            return False
            
    except subprocess.TimeoutExpired:
        progress_bar.update_operation_progress(100, 100, "⚠️  Virtual environment creation timed out")
        return True  # Continue anyway
    except subprocess.CalledProcessError as e:
        progress_bar.update_operation_progress(100, 100, f"❌ Virtual environment error: {str(e)[:30]}")
        return False

def check_dependencies_installed():
    """Check if basic dependencies are already installed"""
    try:
        # Determine the python path
        if platform.system() == "Windows":
            python_path = "mcus_env/Scripts/python"
        else:
            python_path = "mcus_env/bin/python"
        
        # Check if virtual environment exists
        if not Path("mcus_env").exists():
            return False
        
        # Check if pip is available
        pip_path = python_path.replace("python", "pip")
        if not Path(pip_path).exists():
            return False
        
        # Try to import basic dependencies
        result = subprocess.run([python_path, '-c', 'import flask, requests, psutil'], 
                              capture_output=True, timeout=10)
        
        if result.returncode == 0:
            return True
        
        # If import failed, check if packages are installed via pip
        result = subprocess.run([pip_path, 'list'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            output = result.stdout.lower()
            if 'flask' in output and 'requests' in output and 'psutil' in output:
                return True
        
        return False
    except:
        return False

def install_dependencies(progress_bar):
    """Install Python dependencies with real-time progress"""
    # Check if dependencies are already installed
    if check_dependencies_installed():
        progress_bar.update_operation_progress(100, 100, "✅ Dependencies already installed")
        return True
    
    # Determine the pip path
    if platform.system() == "Windows":
        pip_path = "mcus_env/Scripts/pip"
    else:
        pip_path = "mcus_env/bin/pip"
    
    # Create installation monitor
    monitor = InstallationMonitor(progress_bar)
    
    try:
        # Check which packages are already installed
        progress_bar.update_operation_progress(0, 100, "Checking existing packages...")
        installed_packages = set()
        
        try:
            result = subprocess.run([pip_path, 'list'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 1:
                            installed_packages.add(parts[0].lower())
        except:
            pass
        
        # Install basic dependencies first
        basic_deps = ['flask', 'requests', 'psutil']
        success_count = 0
        
        for i, dep in enumerate(basic_deps):
            if dep.lower() in installed_packages:
                progress_bar.update_operation_progress(100, 100, f"✅ {dep} already installed")
                success_count += 1
                time.sleep(0.1)
                continue
                
            progress_bar.update_operation_progress(0, 100, f"Installing {dep}...")
            
            if monitor.install_package_with_progress(pip_path, dep):
                success_count += 1
            
            # Small delay between packages
            time.sleep(0.2)
        
        # Try to install requirements.txt if it exists
        if Path("requirements.txt").exists():
            progress_bar.update_operation_progress(0, 100, "Installing from requirements.txt...")
            
            try:
                process = subprocess.Popen(
                    [pip_path, 'install', '-r', 'requirements.txt'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True
                )
                
                progress = 0
                while True:
                    output = process.stdout.readline()
                    if output == '' and process.poll() is not None:
                        break
                    if output:
                        progress = min(progress + 10, 90)
                        progress_bar.update_operation_progress(progress, 100, "Installing requirements...")
                        time.sleep(0.1)
                
                return_code = process.poll()
                if return_code == 0:
                    progress_bar.update_operation_progress(100, 100, "✅ Requirements installed")
                    success_count += 1
                else:
                    progress_bar.update_operation_progress(100, 100, "⚠️  Requirements had issues")
                    
            except Exception as e:
                progress_bar.update_operation_progress(100, 100, f"❌ Requirements failed: {str(e)[:30]}")
        
        # Overall success if at least basic deps installed
        if success_count > 0:
            progress_bar.update_operation_progress(100, 100, f"✅ {success_count} packages installed successfully")
            return True
        else:
            progress_bar.update_operation_progress(100, 100, "❌ No packages installed successfully")
            return False
        
    except Exception as e:
        progress_bar.update_operation_progress(100, 100, f"❌ Installation error: {str(e)[:30]}")
        return False

def check_port_available(port=3000):
    """Check if a port is available"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('localhost', port))
            return True
    except:
        return False

def kill_processes_on_port(port=3000):
    """Kill processes using the specified port"""
    try:
        if platform.system() == "Windows":
            # Windows command
            result = subprocess.run(f'netstat -ano | findstr :{port}', 
                                  shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 5:
                            pid = parts[-1]
                            subprocess.run(f'taskkill /PID {pid} /F', shell=True)
        else:
            # Unix command
            result = subprocess.run(f'lsof -ti :{port}', 
                                  shell=True, capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    if pid.strip():
                        subprocess.run(f'kill {pid}', shell=True)
    except:
        pass

def start_mcus(progress_bar):
    """Start the MCUS web application with progress"""
    # Determine the python path
    if platform.system() == "Windows":
        python_path = "mcus_env/Scripts/python"
    else:
        python_path = "mcus_env/bin/python"
    
    progress_bar.update_operation_progress(0, 100, "Checking port availability...")
    
    # Check if port 3000 is available
    if not check_port_available(3000):
        progress_bar.update_operation_progress(25, 100, "Port 3000 in use, attempting to free it...")
        kill_processes_on_port(3000)
        time.sleep(1)
        
        # Check again
        if not check_port_available(3000):
            progress_bar.update_operation_progress(100, 100, "❌ Port 3000 still in use")
            return None
    
    progress_bar.update_operation_progress(50, 100, "Starting MCUS web server...")
    
    try:
        # Start the web app
        process = subprocess.Popen([python_path, 'web_app.py'], 
                                  stdout=subprocess.PIPE, 
                                  stderr=subprocess.PIPE,
                                  text=True)
        
        # Monitor startup progress
        for i in range(10):
            progress = 50 + (i + 1) * 5
            progress_bar.update_operation_progress(progress, 100, "Starting MCUS web server...")
            time.sleep(0.3)
            
            # Check if process is still running
            if process.poll() is not None:
                # Process failed
                stdout, stderr = process.communicate()
                progress_bar.update_operation_progress(100, 100, "❌ MCUS failed to start")
                return None
        
        # Process is running
        progress_bar.update_operation_progress(100, 100, "✅ MCUS web server started")
        return process
        
    except Exception as e:
        progress_bar.update_operation_progress(100, 100, f"❌ MCUS start error: {str(e)[:30]}")
        return None

def open_browser():
    """Open the browser to the MCUS interface"""
    time.sleep(2)  # Give the server a moment to start
    try:
        webbrowser.open('http://localhost:3000')
    except:
        pass

def show_network_info():
    """Show network information for friends to connect"""
    local_ip = get_local_ip()
    print("\n" + "="*50)
    print("🌐 NETWORK INFORMATION")
    print("="*50)
    print(f"Your IP Address: {local_ip}")
    print("Share this IP with your friends!")
    print("They can join your hosting network using this IP.")
    print("="*50)

def main():
    """Main launcher function"""
    print("🎮 MCUS - Minecraft Unified Server")
    print("="*50)
    print("One-Click Launcher")
    print("="*50)
    
    # Initialize enhanced progress bar (8 total steps)
    progress = RealTimeProgressBar(8, "MCUS Setup Progress")
    
    # Check system requirements
    print("\n🔍 Checking system requirements...")
    
    python_ok, python_version = check_python()
    print(f"Python: {python_version}")
    progress.update_step("Python check complete")
    
    java_ok, java_version = check_java()
    print(f"Java: {java_version}")
    progress.update_step("Java check complete")
    
    if not python_ok:
        print("\n❌ Python 3.7+ is required!")
        print("Please install Python from: https://python.org")
        input("Press Enter to exit...")
        return
    
    if not java_ok:
        print("\n⚠️  Java not detected!")
        print("Java is needed for Minecraft servers.")
        print("Please install Java from: https://adoptium.net")
        print("Continuing anyway...")
    
    # Create directories
    print("\n📁 Setting up directories...")
    create_directories(progress)
    progress.update_step("Directories created")
    
    # Setup virtual environment
    print("\n🐍 Setting up Python environment...")
    if not setup_virtual_environment(progress):
        print("❌ Failed to setup virtual environment")
        input("Press Enter to exit...")
        return
    progress.update_step("Virtual environment ready")
    
    # Install dependencies
    print("\n📦 Installing dependencies...")
    if not install_dependencies(progress):
        print("❌ Failed to install dependencies")
        input("Press Enter to exit...")
        return
    progress.update_step("Dependencies installed")
    
    # Start MCUS
    print("\n🚀 Starting MCUS...")
    process = start_mcus(progress)
    progress.update_step("MCUS starting")
    
    if process:
        progress.update_step("MCUS running")
        
        # Show network info
        show_network_info()
        
        # Open browser in a separate thread
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()
        
        progress.complete("Setup complete! Browser opening...")
        
        print("\n✅ MCUS is running!")
        print("🌐 Open your browser to: http://localhost:3000")
        print("🔄 To stop MCUS, close this window or press Ctrl+C")
        print("\n" + "="*50)
        
        try:
            # Keep the process running
            process.wait()
        except KeyboardInterrupt:
            print("\n🛑 Stopping MCUS...")
            process.terminate()
            process.wait()
            print("✅ MCUS stopped")
    else:
        progress.complete("Setup failed")
        print("❌ Failed to start MCUS")
        print("Please check the error messages above")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main() 