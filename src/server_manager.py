import subprocess
import threading
import socket
import json
import os
import time
import requests
import zipfile
import shutil
import re
from pathlib import Path
from datetime import datetime
import logging
import webbrowser

class ServerManager:
    def __init__(self, config):
        self.config = config
        self.server_process = None
        self.is_running = False
        self.hosts = []
        self.current_host = None
        self.server_dir = Path("server")
        self.mods_dir = self.server_dir / "mods"
        self.world_dir = self.server_dir / "world"
        
        # Create directories
        self.server_dir.mkdir(exist_ok=True)
        self.mods_dir.mkdir(exist_ok=True)
        
        # Setup logging
        logging.basicConfig(
            filename='server.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
    def start_server(self):
        """Start the Minecraft server with comprehensive error checking"""
        if self.is_running:
            logging.warning("Server is already running")
            return False
            
        try:
            # Step 1: Validate and create server directory
            if not self._validate_server_directory():
                return False
            
            # Step 2: Check Java installation
            java_info = self._check_java_installation()
            if not java_info['available']:
                logging.error(f"Java not found: {java_info['error']}")
                return False
            
            # Step 3: Check for server JAR
            server_jar = self.find_server_jar()
            if not server_jar:
                logging.info("No server JAR found. Attempting to install Forge...")
                if not self.install_forge():
                    logging.error("Failed to install Forge automatically")
                    return False
                server_jar = self.find_server_jar()
                
            if not server_jar:
                logging.error("No server JAR found after Forge installation attempt")
                return False
            
            # Step 4: Validate server JAR
            if not self._validate_server_jar(server_jar):
                return False
                
            # Step 5: Create server.properties
            if not self._create_server_properties():
                return False
            
            # Step 6: Check available memory
            memory_info = self._check_system_resources()
            if not memory_info['sufficient']:
                logging.warning(f"Insufficient memory: {memory_info['message']}")
                # Continue anyway but with reduced memory allocation
            
            # Step 7: Start server process
            return self._start_server_process(server_jar, java_info, memory_info)
            
        except Exception as e:
            logging.error(f"Failed to start server: {e}")
            return False

    def _validate_server_directory(self):
        """Validate and create server directory with proper permissions"""
        try:
            # Ensure server directory exists
            self.server_dir.mkdir(parents=True, exist_ok=True)
            
            # Check if directory is writable
            test_file = self.server_dir / ".test_write"
            try:
                test_file.write_text("test")
                test_file.unlink()
            except PermissionError:
                logging.error(f"Server directory not writable: {self.server_dir}")
                return False
            except Exception as e:
                logging.error(f"Cannot write to server directory: {e}")
                return False
            
            # Create necessary subdirectories
            subdirs = ['mods', 'config', 'logs', 'world', 'backups']
            for subdir in subdirs:
                subdir_path = self.server_dir / subdir
                subdir_path.mkdir(exist_ok=True)
            
            logging.info(f"Server directory validated: {self.server_dir}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to validate server directory: {e}")
            return False

    def _check_java_installation(self):
        """Check Java installation and return detailed information"""
        try:
            # Try to get Java version
            result = subprocess.run(
                ["java", "-version"], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            
            if result.returncode != 0:
                return {
                    'available': False,
                    'error': 'Java command failed',
                    'version': None,
                    'path': None
                }
            
            # Parse Java version from stderr (Java outputs version to stderr)
            version_output = result.stderr
            if "version" in version_output:
                # Extract version number
                import re
                version_match = re.search(r'"([^"]+)"', version_output)
                version = version_match.group(1) if version_match else "Unknown"
                
                # Check if it's Java 8 or higher
                version_num = re.search(r'(\d+)', version)
                if version_num:
                    major_version = int(version_num.group(1))
                    if major_version >= 8:
                        return {
                            'available': True,
                            'error': None,
                            'version': version,
                            'path': 'java'
                        }
                    else:
                        return {
                            'available': False,
                            'error': f'Java version {version} is too old. Java 8 or higher required.',
                            'version': version,
                            'path': 'java'
                        }
            
            return {
                'available': True,
                'error': None,
                'version': 'Unknown',
                'path': 'java'
            }
            
        except FileNotFoundError:
            return {
                'available': False,
                'error': 'Java not found in PATH. Please install Java 8 or higher.',
                'version': None,
                'path': None
            }
        except subprocess.TimeoutExpired:
            return {
                'available': False,
                'error': 'Java command timed out',
                'version': None,
                'path': None
            }
        except Exception as e:
            return {
                'available': False,
                'error': f'Error checking Java: {e}',
                'version': None,
                'path': None
            }

    def _validate_server_jar(self, server_jar):
        """Validate server JAR file"""
        try:
            if not server_jar.exists():
                logging.error(f"Server JAR does not exist: {server_jar}")
                return False
            
            # Check file size (should be at least 1MB for a server JAR)
            if server_jar.stat().st_size < 1024 * 1024:
                logging.error(f"Server JAR seems too small: {server_jar.stat().st_size} bytes")
                return False
            
            # Try to read JAR file to ensure it's valid
            import zipfile
            try:
                with zipfile.ZipFile(server_jar, 'r') as jar:
                    # Check for essential files
                    file_list = jar.namelist()
                    if not any('META-INF' in f for f in file_list):
                        logging.error("Invalid JAR file: missing META-INF")
                        return False
            except zipfile.BadZipFile:
                logging.error(f"Invalid JAR file: {server_jar}")
                return False
            
            logging.info(f"Server JAR validated: {server_jar}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to validate server JAR: {e}")
            return False

    def _create_server_properties(self):
        """Create server.properties with error handling"""
        try:
            properties = {
                "server-port": self.config.get('port', 25565),
                "max-players": self.config.get('max_players', 20),
                "server-name": self.config.get('server_name', 'MCUS Server'),
                "gamemode": "survival",
                "difficulty": "normal",
                "spawn-protection": 16,
                "view-distance": 10,
                "simulation-distance": 10,
                "motd": "MCUS - Minecraft Unified Server",
                "enable-command-block": "false",
                "allow-flight": "false",
                "white-list": "false",
                "online-mode": "false",
                "enable-rcon": "false",
                "rcon-port": "25575",
                "rcon-password": "",
                "enable-query": "false",
                "query-port": "25565"
            }
            
            properties_file = self.server_dir / "server.properties"
            
            # Check if we can write to the file
            try:
                with open(properties_file, 'w') as f:
                    for key, value in properties.items():
                        f.write(f"{key}={value}\n")
            except PermissionError:
                logging.error(f"Cannot write server.properties: Permission denied")
                return False
            except Exception as e:
                logging.error(f"Failed to create server.properties: {e}")
                return False
            
            logging.info("Server properties created successfully")
            return True
            
        except Exception as e:
            logging.error(f"Failed to create server properties: {e}")
            return False

    def _check_system_resources(self):
        """Check system resources (memory, disk space)"""
        try:
            import psutil
            
            # Check available memory
            memory = psutil.virtual_memory()
            available_gb = memory.available / (1024**3)
            
            # Check disk space
            disk = psutil.disk_usage(str(self.server_dir))
            available_disk_gb = disk.free / (1024**3)
            
            # Minimum requirements
            min_memory_gb = 2.0
            min_disk_gb = 1.0
            
            if available_gb < min_memory_gb:
                return {
                    'sufficient': False,
                    'message': f'Only {available_gb:.1f}GB RAM available, {min_memory_gb}GB recommended',
                    'available_memory_gb': available_gb,
                    'available_disk_gb': available_disk_gb
                }
            
            if available_disk_gb < min_disk_gb:
                return {
                    'sufficient': False,
                    'message': f'Only {available_disk_gb:.1f}GB disk space available, {min_disk_gb}GB recommended',
                    'available_memory_gb': available_gb,
                    'available_disk_gb': available_disk_gb
                }
            
            return {
                'sufficient': True,
                'message': f'System resources OK: {available_gb:.1f}GB RAM, {available_disk_gb:.1f}GB disk',
                'available_memory_gb': available_gb,
                'available_disk_gb': available_disk_gb
            }
            
        except ImportError:
            # psutil not available, assume resources are sufficient
            return {
                'sufficient': True,
                'message': 'System resource check skipped (psutil not available)',
                'available_memory_gb': None,
                'available_disk_gb': None
            }
        except Exception as e:
            logging.warning(f"Failed to check system resources: {e}")
            return {
                'sufficient': True,
                'message': f'System resource check failed: {e}',
                'available_memory_gb': None,
                'available_disk_gb': None
            }

    def _start_server_process(self, server_jar, java_info, memory_info):
        """Start the server process with proper error handling"""
        try:
            # Check if this is a Forge server and get startup files
            forge_files = self._get_forge_startup_files(server_jar)
            
            if forge_files:
                # Use Forge-specific startup method
                return self._start_forge_server(forge_files, java_info, memory_info)
            else:
                # Use standard server startup method
                return self._start_standard_server(server_jar, java_info, memory_info)
                
        except Exception as e:
            logging.error(f"Failed to start server process: {e}")
            return False

    def _start_forge_server(self, forge_files, java_info, memory_info):
        """Start a Forge server using the proper startup method"""
        try:
            # Determine memory allocation based on available resources
            if memory_info['available_memory_gb']:
                available_gb = memory_info['available_memory_gb']
                if available_gb >= 8:
                    max_heap = "4G"
                    min_heap = "2G"
                elif available_gb >= 4:
                    max_heap = "3G"
                    min_heap = "1G"
                else:
                    max_heap = "2G"
                    min_heap = "1G"
            else:
                max_heap = "2G"
                min_heap = "1G"
            
            # Create or update user_jvm_args.txt with memory settings
            user_jvm_args = forge_files['user_jvm_args']
            if user_jvm_args:
                with open(user_jvm_args, 'w') as f:
                    f.write(f"-Xmx{max_heap}\n")
                    f.write(f"-Xms{min_heap}\n")
                    f.write("-XX:+UseG1GC\n")
                    f.write("-XX:+ParallelRefProcEnabled\n")
                    f.write("-XX:MaxGCPauseMillis=200\n")
                    f.write("-XX:+UnlockExperimentalVMOptions\n")
                    f.write("-XX:+DisableExplicitGC\n")
                    f.write("-XX:+AlwaysPreTouch\n")
                    f.write("-XX:G1NewSizePercent=30\n")
                    f.write("-XX:G1MaxNewSizePercent=40\n")
                    f.write("-XX:G1HeapRegionSize=8M\n")
                    f.write("-XX:G1ReservePercent=20\n")
                    f.write("-XX:G1HeapWastePercent=5\n")
                    f.write("-XX:G1MixedGCCountTarget=4\n")
                    f.write("-XX:InitiatingHeapOccupancyPercent=15\n")
                    f.write("-XX:G1MixedGCLiveThresholdPercent=90\n")
                    f.write("-XX:G1RSetUpdatingPauseTimePercent=5\n")
                    f.write("-XX:SurvivorRatio=32\n")
                    f.write("-XX:+PerfDisableSharedMem\n")
                    f.write("-XX:MaxTenuringThreshold=1\n")
            
            # Build Forge startup command using the specific Java path
            cmd = [java_info['path']]
            
            # Add JVM arguments from user_jvm_args.txt if it exists
            if user_jvm_args and user_jvm_args.exists():
                cmd.extend([f"@{user_jvm_args}"])
            
            # Add platform-specific args
            if os.name == 'nt' and forge_files['win_args']:
                cmd.extend([f"@{forge_files['win_args']}"])
            elif forge_files['unix_args']:
                cmd.extend([f"@{forge_files['unix_args']}"])
            
            # Add nogui argument
            cmd.append("nogui")
            
            logging.info(f"Starting Forge server with command: {' '.join(cmd[:3])}... @args nogui")
            
            # Start server process
            self.server_process = subprocess.Popen(
                cmd,
                cwd=str(self.server_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.PIPE,
                universal_newlines=True,
                creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
            )
            
            # Wait a moment to see if process starts successfully
            time.sleep(2)
            
            if self.server_process.poll() is not None:
                # Process terminated immediately
                logging.error("Forge server process terminated immediately")
                return False
            
            self.is_running = True
            
            # Start output monitoring thread
            threading.Thread(target=self.monitor_server_output, daemon=True).start()
            
            logging.info(f"Forge server started successfully with {max_heap} max heap, {min_heap} min heap")
            return True
            
        except PermissionError:
            logging.error("Permission denied when starting Forge server process")
            return False
        except FileNotFoundError:
            logging.error("Forge startup files or Java executable not found")
            return False
        except Exception as e:
            logging.error(f"Failed to start Forge server process: {e}")
            return False

    def _start_standard_server(self, server_jar, java_info, memory_info):
        """Start a standard Minecraft server (vanilla or other modloaders)"""
        try:
            # Determine memory allocation based on available resources
            if memory_info['available_memory_gb']:
                available_gb = memory_info['available_memory_gb']
                if available_gb >= 8:
                    max_heap = "4G"
                    min_heap = "2G"
                elif available_gb >= 4:
                    max_heap = "3G"
                    min_heap = "1G"
                else:
                    max_heap = "2G"
                    min_heap = "1G"
            else:
                max_heap = "2G"
                min_heap = "1G"
            
            # Build command with optimized JVM arguments using the specific Java path
            cmd = [
                java_info['path'],
                f"-Xmx{max_heap}",
                f"-Xms{min_heap}",
                "-XX:+UseG1GC",
                "-XX:+ParallelRefProcEnabled",
                "-XX:MaxGCPauseMillis=200",
                "-XX:+UnlockExperimentalVMOptions",
                "-XX:+DisableExplicitGC",
                "-XX:+AlwaysPreTouch",
                "-XX:G1NewSizePercent=30",
                "-XX:G1MaxNewSizePercent=40",
                "-XX:G1HeapRegionSize=8M",
                "-XX:G1ReservePercent=20",
                "-XX:G1HeapWastePercent=5",
                "-XX:G1MixedGCCountTarget=4",
                "-XX:InitiatingHeapOccupancyPercent=15",
                "-XX:G1MixedGCLiveThresholdPercent=90",
                "-XX:G1RSetUpdatingPauseTimePercent=5",
                "-XX:SurvivorRatio=32",
                "-XX:+PerfDisableSharedMem",
                "-XX:MaxTenuringThreshold=1",
                "-jar", str(server_jar),
                "nogui"
            ]
            
            logging.info(f"Starting standard server with command: {' '.join(cmd[:3])}... -jar {server_jar.name}")
            
            # Start server process
            self.server_process = subprocess.Popen(
                cmd,
                cwd=str(self.server_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.PIPE,
                universal_newlines=True,
                creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
            )
            
            # Wait a moment to see if process starts successfully
            time.sleep(2)
            
            if self.server_process.poll() is not None:
                # Process terminated immediately
                logging.error("Standard server process terminated immediately")
                return False
            
            self.is_running = True
            
            # Start output monitoring thread
            threading.Thread(target=self.monitor_server_output, daemon=True).start()
            
            logging.info(f"Standard server started successfully with {max_heap} max heap, {min_heap} min heap")
            return True
            
        except PermissionError:
            logging.error("Permission denied when starting standard server process")
            return False
        except FileNotFoundError:
            logging.error("Server JAR or Java executable not found")
            return False
        except Exception as e:
            logging.error(f"Failed to start standard server process: {e}")
            return False
            
    def stop_server(self):
        """Stop the Minecraft server"""
        if not self.is_running or not self.server_process:
            return False
            
        try:
            # Send stop command to server
            self.send_server_command("stop")
            
            # Wait for process to terminate
            self.server_process.wait(timeout=30)
            self.is_running = False
            self.server_process = None
            
            logging.info("Server stopped successfully")
            return True
            
        except Exception as e:
            logging.error(f"Failed to stop server: {e}")
            # Force kill if necessary
            if self.server_process:
                self.server_process.kill()
                self.is_running = False
            return False
            
    def send_server_command(self, command):
        """Send a command to the running server"""
        if self.server_process and self.is_running and self.server_process.stdin:
            try:
                self.server_process.stdin.write(command + "\n")
                self.server_process.stdin.flush()
                logging.info(f"Sent command to server: {command}")
                return True
            except Exception as e:
                logging.error(f"Failed to send command: {e}")
                return False
        else:
            logging.warning("Server not running or stdin not available")
            return False
        
    def monitor_server_output(self):
        """Monitor server output for logs and status"""
        if not self.server_process or not self.server_process.stdout:
            return
            
        for line in iter(self.server_process.stdout.readline, ''):
            if line:
                # Log the output
                logging.info(line.strip())
                
                # Check for server ready message
                if "Done" in line and "For help" in line:
                    logging.info("Server is ready for connections")
                    
                # Check for player join/leave
                if "joined the game" in line:
                    self.handle_player_join(line)
                elif "left the game" in line:
                    self.handle_player_leave(line)
                    
    def handle_player_join(self, line):
        """Handle player join events"""
        # Extract player name from log line
        # Format: [Server thread/INFO]: PlayerName joined the game
        try:
            player_name = line.split("]: ")[1].split(" joined")[0]
            logging.info(f"Player {player_name} joined the game")
        except:
            pass
            
    def handle_player_leave(self, line):
        """Handle player leave events"""
        # Extract player name from log line
        try:
            player_name = line.split("]: ")[1].split(" left")[0]
            logging.info(f"Player {player_name} left the game")
        except:
            pass
            
    def find_server_jar(self):
        """Find the server jar file with improved Forge detection"""
        # First, check for Forge server JARs in the libraries directory
        forge_libs_dir = self.server_dir / "libraries" / "net" / "minecraftforge" / "forge"
        if forge_libs_dir.exists():
            for version_dir in forge_libs_dir.iterdir():
                if version_dir.is_dir():
                    server_jar = version_dir / f"forge-{version_dir.name}-server.jar"
                    if server_jar.exists():
                        logging.info(f"Found Forge server JAR: {server_jar.name}")
                        return server_jar
        
        # Fallback to checking for JARs in the main server directory
        jar_files = list(self.server_dir.glob("*.jar"))
        
        if not jar_files:
            return None
            
        # Priority order for server JAR detection
        priority_patterns = [
            # Forge server JARs (most specific)
            lambda f: "forge" in f.name.lower() and "server" in f.name.lower(),
            lambda f: "forge" in f.name.lower() and "universal" in f.name.lower(),
            lambda f: "forge" in f.name.lower() and any(version in f.name.lower() for version in ["1.19", "1.20", "1.18"]),
            
            # Vanilla server JARs
            lambda f: "server" in f.name.lower() and "minecraft" in f.name.lower(),
            lambda f: "server" in f.name.lower() and any(version in f.name.lower() for version in ["1.19", "1.20", "1.18"]),
            
            # Generic server JARs
            lambda f: "server" in f.name.lower(),
            lambda f: "forge" in f.name.lower(),
            
            # Any JAR file as fallback
            lambda f: True
        ]
        
        for pattern in priority_patterns:
            for jar_file in jar_files:
                if pattern(jar_file):
                    # Additional validation: check if it's a valid server JAR
                    if self._is_valid_server_jar(jar_file):
                        logging.info(f"Found server JAR: {jar_file.name}")
                        return jar_file
        
        return None

    def _is_forge_server(self, server_jar):
        """Check if the server JAR is a Forge server"""
        if not server_jar:
            return False
        
        # Check if it's in the Forge libraries directory
        if "libraries/net/minecraftforge/forge" in str(server_jar):
            return True
        
        # Check if it's a Forge server JAR by name
        if "forge" in server_jar.name.lower() and "server" in server_jar.name.lower():
            return True
        
        return False

    def _get_forge_startup_files(self, server_jar):
        """Get the Forge startup files (shim JAR and args files)"""
        if not self._is_forge_server(server_jar):
            return None
        
        # Extract version from server JAR path
        # Path format: libraries/net/minecraftforge/forge/1.21.7-57.0.2/forge-1.21.7-57.0.2-server.jar
        jar_path = Path(server_jar)
        version_dir = jar_path.parent
        version = version_dir.name
        
        # Check for shim JAR and args files
        shim_jar = self.server_dir / f"forge-{version}-shim.jar"
        unix_args = version_dir / "unix_args.txt"
        win_args = version_dir / "win_args.txt"
        user_jvm_args = self.server_dir / "user_jvm_args.txt"
        
        if shim_jar.exists() and (unix_args.exists() or win_args.exists()):
            return {
                'shim_jar': shim_jar,
                'unix_args': unix_args if unix_args.exists() else None,
                'win_args': win_args if win_args.exists() else None,
                'user_jvm_args': user_jvm_args if user_jvm_args.exists() else None,
                'version': version
            }
        
        return None
        
    def _is_valid_server_jar(self, jar_path):
        """Check if a JAR file is a valid Minecraft server JAR with improved Forge detection"""
        try:
            import zipfile
            with zipfile.ZipFile(jar_path, 'r') as jar:
                file_list = jar.namelist()
                
                # Check for Forge server JARs specifically
                if self._is_forge_server_jar(jar_path, file_list):
                    return True
                
                # Check for essential server files
                server_indicators = [
                    'META-INF/MANIFEST.MF',
                    'net/minecraft/server/',
                    'com/mojang/',
                    'META-INF/mods.toml',  # Forge mods
                    'fabric.mod.json',     # Fabric mods
                    'server.properties',
                    'eula.txt'
                ]
                
                # Check for any server indicator
                for indicator in server_indicators:
                    if any(indicator in f for f in file_list):
                        return True
                
                # Check for Minecraft server classes
                if any('minecraft' in f.lower() and 'server' in f.lower() for f in file_list):
                    return True
                    
                return False
                
        except zipfile.BadZipFile:
            logging.warning(f"Invalid JAR file: {jar_path}")
            return False
        except Exception as e:
            logging.warning(f"Error checking JAR {jar_path}: {e}")
            return False

    def _is_forge_server_jar(self, jar_path, file_list):
        """Check if this is specifically a Forge server JAR"""
        jar_name = jar_path.name.lower()
        
        # Check if it's a Forge server JAR by name and contents
        if "forge" in jar_name and "server" in jar_name:
            # Check for Forge-specific files
            forge_indicators = [
                'META-INF/mods.toml',
                'net/minecraftforge/',
                'cpw/mods/',
                'org/spongepowered/',
                'fml/',
                'forge-'
            ]
            
            for indicator in forge_indicators:
                if any(indicator in f for f in file_list):
                    return True
            
            # Check for Forge version in JAR name
            if any(char.isdigit() for char in jar_name):
                return True
        
        return False

    def is_forge_properly_installed(self):
        """Check if Forge is properly installed and ready to run"""
        try:
            # First, check if there's a Forge server JAR in the main server directory
            server_jar = self._find_forge_server_jar()
            if not server_jar:
                logging.info("No Forge server JAR found in server directory")
                return False
            
            # Check for required startup files
            forge_files = self._get_forge_startup_files(server_jar)
            if not forge_files:
                logging.info("Forge startup files not found")
                return False
            
            # Check if all required files exist
            required_files = [
                forge_files['shim_jar'],
                forge_files['user_jvm_args']
            ]
            
            if os.name == 'nt' and forge_files['win_args']:
                required_files.append(forge_files['win_args'])
            elif forge_files['unix_args']:
                required_files.append(forge_files['unix_args'])
            
            for file_path in required_files:
                if not file_path.exists():
                    logging.info(f"Required Forge file missing: {file_path}")
                    return False
            
            # Check Java compatibility
            java_info = self._check_java_installation()
            if not java_info['available']:
                logging.info(f"Java not available: {java_info['error']}")
                return False
            
            # Check if Java version is compatible with Forge
            if java_info['version']:
                import re
                version_match = re.search(r'(\d+)', java_info['version'])
                if version_match:
                    java_major = int(version_match.group(1))
                    # Forge 1.21.x requires Java 21+
                    if java_major < 21:
                        logging.info(f"Java {java_major} is too old for Forge 1.21.x (requires Java 21+)")
                        return False
            
            logging.info(f"Forge {forge_files['version']} is properly installed and ready")
            return True
            
        except Exception as e:
            logging.error(f"Error checking Forge installation: {e}")
            return False

    def _find_forge_server_jar(self):
        """Find the actual Forge server JAR in the server directory"""
        try:
            # Look for Forge server JAR in the main server directory
            for file in self.server_dir.iterdir():
                if file.is_file() and file.suffix == '.jar':
                    if self._is_forge_server_jar(file, []):  # We'll check contents separately
                        # Verify it's actually a Forge server JAR by checking contents
                        if self._verify_forge_server_jar(file):
                            return file
            
            # If not found in main directory, check libraries (but this is less ideal)
            forge_libs_dir = self.server_dir / "libraries" / "net" / "minecraftforge" / "forge"
            if forge_libs_dir.exists():
                for version_dir in forge_libs_dir.iterdir():
                    if version_dir.is_dir():
                        potential_jar = version_dir / f"forge-{version_dir.name}-server.jar"
                        if potential_jar.exists() and self._verify_forge_server_jar(potential_jar):
                            return potential_jar
            
            return None
            
        except Exception as e:
            logging.error(f"Error finding Forge server JAR: {e}")
            return None

    def _verify_forge_server_jar(self, jar_path):
        """Verify that a JAR is actually a Forge server JAR by checking its contents"""
        try:
            import zipfile
            with zipfile.ZipFile(jar_path, 'r') as jar:
                file_list = jar.namelist()
                
                # Check for Forge-specific files that indicate this is a server JAR
                forge_indicators = [
                    'META-INF/mods.toml',
                    'net/minecraftforge/',
                    'cpw/mods/',
                    'org/spongepowered/',
                    'fml/',
                    'META-INF/MANIFEST.MF'
                ]
                
                has_forge_files = any(any(indicator in f for f in file_list) for indicator in forge_indicators)
                
                # Also check that it's not an installer
                is_installer = any('installer' in f.lower() for f in file_list)
                
                return has_forge_files and not is_installer
                
        except Exception as e:
            logging.warning(f"Error verifying JAR {jar_path}: {e}")
            return False

    def get_forge_installation_status(self):
        """Get detailed status of Forge installation"""
        status = {
            'installed': False,
            'version': None,
            'java_compatible': False,
            'startup_files_ready': False,
            'server_jar_location': None,
            'issues': []
        }
        
        try:
            # Find the actual Forge server JAR
            server_jar = self._find_forge_server_jar()
            if not server_jar:
                status['issues'].append("Forge server JAR not found in server directory")
                return status
            
            status['server_jar_location'] = str(server_jar)
            
            # Extract version from JAR name or path
            jar_name = server_jar.name
            if 'forge-' in jar_name and '-server.jar' in jar_name:
                version = jar_name.replace('forge-', '').replace('-server.jar', '')
                status['version'] = version
                status['installed'] = True
            else:
                status['issues'].append("Could not determine Forge version from JAR name")
                return status
            
            # Check Java compatibility
            java_info = self._check_java_installation()
            if not java_info['available']:
                status['issues'].append(f"Java not available: {java_info['error']}")
            else:
                status['java_compatible'] = True
                if java_info['version']:
                    import re
                    version_match = re.search(r'(\d+)', java_info['version'])
                    if version_match:
                        java_major = int(version_match.group(1))
                        if java_major < 21:
                            status['issues'].append(f"Java {java_major} is too old for Forge 1.21.x (requires Java 21+)")
                            status['java_compatible'] = False
            
            # Check startup files
            forge_files = self._get_forge_startup_files(server_jar)
            if forge_files:
                status['startup_files_ready'] = True
            else:
                status['issues'].append("Forge startup files not found")
            
            return status
            
        except Exception as e:
            status['issues'].append(f"Error checking installation: {e}")
            return status
            
    def create_server_properties(self):
        """Create server.properties file"""
        properties = {
            "server-port": self.config.get('port', 25565),
            "max-players": self.config.get('max_players', 20),
            "server-name": self.config.get('server_name', 'MCUS Server'),
            "gamemode": "survival",
            "difficulty": "normal",
            "spawn-protection": 16,
            "view-distance": 10,
            "simulation-distance": 10,
            "motd": "MCUS - Minecraft Unified Server",
            "enable-command-block": "false",
            "allow-flight": "false",
            "white-list": "false",
            "online-mode": "false"
        }
        
        properties_file = self.server_dir / "server.properties"
        with open(properties_file, 'w') as f:
            for key, value in properties.items():
                f.write(f"{key}={value}\n")
                
    def install_forge(self, version="1.19.2"):
        """Install Forge server with improved version selection"""
        try:
            # Try different Forge versions for compatibility (more recent versions first)
            forge_versions = [
                # 1.19.2 versions (most stable)
                f"{version}-43.2.0",
                f"{version}-43.1.7",
                f"{version}-43.1.6",
                f"{version}-43.1.5",
                f"{version}-43.1.4",
                f"{version}-43.1.3",
                f"{version}-43.1.2",
                f"{version}-43.1.1",
                f"{version}-43.1.0",
                f"{version}-43.0.0",
                # Fallback to older versions
                f"{version}-42.0.0",
                f"{version}-41.0.0",
                f"{version}-40.2.0",
                f"{version}-40.1.0", 
                f"{version}-40.0.0",
                f"{version}-39.0.0"
            ]
            
            logging.info(f"Attempting to install Forge for Minecraft {version}")
            
            for forge_version in forge_versions:
                try:
                    # Download Forge installer
                    forge_url = f"https://maven.minecraftforge.net/net/minecraftforge/forge/{forge_version}/forge-{forge_version}-installer.jar"
                    
                    installer_path = self.server_dir / "forge-installer.jar"
                    
                    logging.info(f"Trying Forge version: {forge_version}")
                    logging.info(f"Downloading from: {forge_url}")
                    
                    response = requests.get(forge_url, stream=True, timeout=30)
                    
                    if response.status_code == 404:
                        logging.warning(f"Forge version {forge_version} not found (404)")
                        continue
                    
                    response.raise_for_status()
                    
                    with open(installer_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                            
                    logging.info(f"Downloaded Forge installer: {installer_path.stat().st_size} bytes")
                            
                    # Run installer
                    logging.info(f"Installing Forge {forge_version}...")
                    result = subprocess.run([
                        "java", "-jar", str(installer_path),
                        "--installServer"
                    ], cwd=str(self.server_dir), capture_output=True, text=True, timeout=300)
                    
                    # Clean up installer
                    installer_path.unlink()
                    
                    if result.returncode == 0:
                        logging.info(f"Forge {forge_version} installed successfully")
                        logging.info(f"Installation output: {result.stdout}")
                        return True
                    else:
                        logging.warning(f"Forge {forge_version} installation failed with return code {result.returncode}")
                        logging.warning(f"Error output: {result.stderr}")
                        continue
                        
                except requests.exceptions.RequestException as e:
                    logging.warning(f"Failed to download Forge {forge_version}: {e}")
                    continue
                except subprocess.TimeoutExpired:
                    logging.warning(f"Forge {forge_version} installation timed out")
                    continue
                except Exception as e:
                    logging.warning(f"Error with Forge {forge_version}: {e}")
                    continue
            
            # If all versions failed, log the issue
            logging.error("All automatic Forge installations failed. Please install Forge manually.")
            logging.error("You can download Forge manually from: https://files.minecraftforge.net/")
            return False
            
        except Exception as e:
            logging.error(f"Failed to install Forge: {e}")
            return False

    def install_forge_specific(self, minecraft_version, forge_build):
        """Install a specific Forge version"""
        try:
            forge_version = f"{minecraft_version}-{forge_build}"
            
            # Download Forge installer
            forge_url = f"https://maven.minecraftforge.net/net/minecraftforge/forge/{forge_version}/forge-{forge_version}-installer.jar"
            
            installer_path = self.server_dir / "forge-installer.jar"
            
            logging.info(f"Installing specific Forge version: {forge_version}")
            response = requests.get(forge_url, stream=True, timeout=30)
            response.raise_for_status()
            
            with open(installer_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
            # Run installer
            logging.info(f"Installing Forge {forge_version}...")
            result = subprocess.run([
                "java", "-jar", str(installer_path),
                "--installServer"
            ], cwd=str(self.server_dir), capture_output=True, text=True, timeout=300)
            
            # Clean up installer
            installer_path.unlink()
            
            if result.returncode == 0:
                logging.info(f"Forge {forge_version} installed successfully")
                return True
            else:
                logging.error(f"Forge {forge_version} installation failed: {result.stderr}")
                return False
                
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to download Forge {forge_version}: {e}")
            return False
        except subprocess.TimeoutExpired:
            logging.error(f"Forge {forge_version} installation timed out")
            return False
        except Exception as e:
            logging.error(f"Failed to install Forge {forge_version}: {e}")
            return False
            
    def install_mod(self, mod_path):
        """Install a mod from file"""
        try:
            mod_file = Path(mod_path)
            if not mod_file.exists():
                raise Exception("Mod file not found")
                
            # Copy mod to mods directory
            shutil.copy2(mod_file, self.mods_dir / mod_file.name)
            
            logging.info(f"Mod {mod_file.name} installed successfully")
            return True
            
        except Exception as e:
            logging.error(f"Failed to install mod: {e}")
            return False
            
    def remove_mod(self, mod_name):
        """Remove a mod"""
        try:
            mod_file = self.mods_dir / mod_name
            if mod_file.exists():
                mod_file.unlink()
                logging.info(f"Mod {mod_name} removed successfully")
                return True
            return False
        except Exception as e:
            logging.error(f"Failed to remove mod: {e}")
            return False
            
    def get_installed_mods(self):
        """Get list of installed mods"""
        mods = []
        for mod_file in self.mods_dir.glob("*.jar"):
            mods.append({
                'name': mod_file.name,
                'size': mod_file.stat().st_size,
                'modified': datetime.fromtimestamp(mod_file.stat().st_mtime)
            })
        return mods
        
    def backup_world(self):
        """Create a backup of the world"""
        try:
            if not self.world_dir.exists():
                return False
                
            backup_dir = Path("backups")
            backup_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"world_backup_{timestamp}.zip"
            backup_path = backup_dir / backup_name
            
            # Create zip backup
            shutil.make_archive(
                str(backup_path.with_suffix('')),
                'zip',
                self.world_dir
            )
            
            logging.info(f"World backed up to {backup_path}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to backup world: {e}")
            return False
            
    def get_server_status(self):
        """Get current server status"""
        return {
            'running': self.is_running,
            'players_online': self.get_online_players(),
            'uptime': self.get_uptime(),
            'memory_usage': self.get_memory_usage()
        }
        
    def get_online_players(self):
        """Get list of online players"""
        # This would require parsing server logs or using server API
        # For now, return empty list
        return []
        
    def get_uptime(self):
        """Get server uptime"""
        if not self.is_running:
            return 0
        # This would track start time and calculate uptime
        return 0
        
    def get_memory_usage(self):
        """Get memory usage of server process"""
        if not self.server_process:
            return 0
        try:
            import psutil
            process = psutil.Process(self.server_process.pid)
            return process.memory_info().rss / 1024 / 1024  # MB
        except:
            return 0

    def detect_forge_versions(self):
        """Detect all available Forge versions in the server directory"""
        detected_versions = []
        
        if not self.server_dir.exists():
            return detected_versions
            
        for jar_file in self.server_dir.glob("*.jar"):
            try:
                # Check if it's a Forge JAR
                if self._is_forge_jar(jar_file):
                    version_info = self._extract_forge_version(jar_file)
                    if version_info:
                        detected_versions.append(version_info)
                        
            except Exception as e:
                logging.warning(f"Error analyzing JAR {jar_file.name}: {e}")
                
        # Sort by version (newest first)
        detected_versions.sort(key=lambda x: x['version_number'], reverse=True)
        return detected_versions
        
    def _is_forge_jar(self, jar_path):
        """Check if a JAR file is a Forge server JAR"""
        try:
            import zipfile
            with zipfile.ZipFile(jar_path, 'r') as jar:
                file_list = jar.namelist()
                
                # Check for Forge-specific indicators
                forge_indicators = [
                    'net/minecraftforge/',
                    'META-INF/mods.toml',
                    'forge-',
                    'fml/',
                    'cpw/mods/'
                ]
                
                for indicator in forge_indicators:
                    if any(indicator in f for f in file_list):
                        return True
                        
                # Check filename for Forge patterns
                filename = jar_path.name.lower()
                if 'forge' in filename and ('server' in filename or 'universal' in filename):
                    return True
                    
                return False
                
        except zipfile.BadZipFile:
            return False
        except Exception as e:
            logging.warning(f"Error checking if JAR is Forge: {e}")
            return False
            
    def _extract_forge_version(self, jar_path):
        """Extract version information from a Forge JAR"""
        try:
            import zipfile
            import re
            
            with zipfile.ZipFile(jar_path, 'r') as jar:
                file_list = jar.namelist()
                
                # Try to extract version from filename first
                filename = jar_path.name
                version_match = re.search(r'forge-(\d+\.\d+\.\d+)-(\d+\.\d+\.\d+)', filename)
                if version_match:
                    minecraft_version = version_match.group(1)
                    forge_version = version_match.group(2)
                    return {
                        'file': jar_path.name,
                        'path': str(jar_path),
                        'minecraft_version': minecraft_version,
                        'forge_version': forge_version,
                        'version_number': f"{minecraft_version}-{forge_version}",
                        'size_mb': round(jar_path.stat().st_size / (1024 * 1024), 1),
                        'type': 'server'
                    }
                
                # Try to extract from mods.toml
                for file_name in file_list:
                    if file_name.endswith('mods.toml'):
                        try:
                            with jar.open(file_name) as f:
                                content = f.read().decode('utf-8')
                                
                                # Extract version info from mods.toml
                                minecraft_match = re.search(r'loaderVersion\s*=\s*"(\d+\.\d+\.\d+)"', content)
                                if minecraft_match:
                                    minecraft_version = minecraft_match.group(1)
                                    # Try to get Forge version from filename or other sources
                                    forge_match = re.search(r'forge-(\d+\.\d+\.\d+)', filename)
                                    forge_version = forge_match.group(1) if forge_match else "Unknown"
                                    
                                    return {
                                        'file': jar_path.name,
                                        'path': str(jar_path),
                                        'minecraft_version': minecraft_version,
                                        'forge_version': forge_version,
                                        'version_number': f"{minecraft_version}-{forge_version}",
                                        'size_mb': round(jar_path.stat().st_size / (1024 * 1024), 1),
                                        'type': 'server'
                                    }
                        except Exception as e:
                            logging.warning(f"Error reading mods.toml: {e}")
                            continue
                            
                # Fallback: try to extract from any version info in the JAR
                for file_name in file_list:
                    if 'version' in file_name.lower() or 'build' in file_name.lower():
                        try:
                            with jar.open(file_name) as f:
                                content = f.read().decode('utf-8', errors='ignore')
                                version_match = re.search(r'(\d+\.\d+\.\d+)', content)
                                if version_match:
                                    return {
                                        'file': jar_path.name,
                                        'path': str(jar_path),
                                        'minecraft_version': 'Unknown',
                                        'forge_version': version_match.group(1),
                                        'version_number': f"Unknown-{version_match.group(1)}",
                                        'size_mb': round(jar_path.stat().st_size / (1024 * 1024), 1),
                                        'type': 'server'
                                    }
                        except:
                            continue
                            
                # If we can't extract version info, return basic info
                return {
                    'file': jar_path.name,
                    'path': str(jar_path),
                    'minecraft_version': 'Unknown',
                    'forge_version': 'Unknown',
                    'version_number': 'Unknown',
                    'size_mb': round(jar_path.stat().st_size / (1024 * 1024), 1),
                    'type': 'server'
                }
                
        except Exception as e:
            logging.error(f"Error extracting Forge version from {jar_path}: {e}")
            return None
            
    def get_available_forge_versions(self):
        """Get list of available Forge versions for installation"""
        try:
            # Common Forge versions for different Minecraft versions
            available_versions = {
                '1.20.4': [
                    '1.20.4-49.0.3', '1.20.4-49.0.2', '1.20.4-49.0.1', '1.20.4-49.0.0',
                    '1.20.4-48.0.3', '1.20.4-48.0.2', '1.20.4-48.0.1', '1.20.4-48.0.0'
                ],
                '1.20.1': [
                    '1.20.1-47.1.0', '1.20.1-47.0.0', '1.20.1-46.0.0'
                ],
                '1.19.4': [
                    '1.19.4-45.1.0', '1.19.4-45.0.0', '1.19.4-44.0.0'
                ],
                '1.19.3': [
                    '1.19.3-44.1.0', '1.19.3-44.0.0', '1.19.3-43.0.0'
                ],
                '1.19.2': [
                    '1.19.2-43.2.0', '1.19.2-43.1.7', '1.19.2-43.1.6', '1.19.2-43.1.5',
                    '1.19.2-43.1.4', '1.19.2-43.1.3', '1.19.2-43.1.2', '1.19.2-43.1.1',
                    '1.19.2-43.1.0', '1.19.2-43.0.0', '1.19.2-42.0.0', '1.19.2-41.0.0'
                ],
                '1.18.2': [
                    '1.18.2-40.2.0', '1.18.2-40.1.0', '1.18.2-40.0.0', '1.18.2-39.0.0'
                ]
            }
            
            return available_versions
            
        except Exception as e:
            logging.error(f"Error getting available Forge versions: {e}")
            return {}

class HostNetwork:
    """Manages distributed hosting network"""
    
    def __init__(self):
        self.hosts = []
        self.current_leader = None
        self.network_port = 25566
        
    def add_host(self, host_info):
        """Add a host to the network"""
        host = {
            'name': host_info['name'],
            'ip': host_info['ip'],
            'port': host_info.get('port', 25565),
            'status': 'offline',
            'last_seen': None
        }
        
        self.hosts.append(host)
        return True
        
    def remove_host(self, host_name):
        """Remove a host from the network"""
        self.hosts = [h for h in self.hosts if h['name'] != host_name]
        
    def get_available_hosts(self):
        """Get list of available hosts"""
        return [h for h in self.hosts if h['status'] == 'online']
        
    def select_next_host(self):
        """Select the next available host for failover"""
        available = self.get_available_hosts()
        if available:
            # Simple round-robin selection
            if not self.current_leader:
                self.current_leader = available[0]
            else:
                current_index = available.index(self.current_leader)
                next_index = (current_index + 1) % len(available)
                self.current_leader = available[next_index]
        return self.current_leader
        
    def start_network_listener(self):
        """Start listening for host connections"""
        # This would implement the network communication protocol
        pass 