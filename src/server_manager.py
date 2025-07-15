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
            
            # Build command with optimized JVM arguments
            cmd = [
                "java",
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
            
            logging.info(f"Starting server with command: {' '.join(cmd[:3])}... -jar {server_jar.name}")
            
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
                logging.error("Server process terminated immediately")
                return False
            
            self.is_running = True
            
            # Start output monitoring thread
            threading.Thread(target=self.monitor_server_output, daemon=True).start()
            
            logging.info(f"Server started successfully with {max_heap} max heap, {min_heap} min heap")
            return True
            
        except PermissionError:
            logging.error("Permission denied when starting server process")
            return False
        except FileNotFoundError:
            logging.error("Server JAR or Java executable not found")
            return False
        except Exception as e:
            logging.error(f"Failed to start server process: {e}")
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
        """Find the server jar file"""
        for file in self.server_dir.glob("*.jar"):
            if "forge" in file.name.lower() or "server" in file.name.lower():
                return file
        return None
        
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
        """Install Forge server"""
        try:
            # Try different Forge versions for compatibility
            forge_versions = [
                f"{version}-40.2.0",
                f"{version}-40.1.0", 
                f"{version}-40.0.0",
                f"{version}-39.0.0"
            ]
            
            for forge_version in forge_versions:
                try:
                    # Download Forge installer
                    forge_url = f"https://maven.minecraftforge.net/net/minecraftforge/forge/{forge_version}/forge-{forge_version}-installer.jar"
                    
                    installer_path = self.server_dir / "forge-installer.jar"
                    
                    logging.info(f"Trying Forge version: {forge_version}")
                    response = requests.get(forge_url, stream=True, timeout=30)
                    response.raise_for_status()
                    
                    with open(installer_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                            
                    # Run installer
                    logging.info("Installing Forge...")
                    result = subprocess.run([
                        "java", "-jar", str(installer_path),
                        "--installServer"
                    ], cwd=str(self.server_dir), capture_output=True, text=True, timeout=300)
                    
                    if result.returncode == 0:
                        # Clean up installer
                        installer_path.unlink()
                        logging.info(f"Forge {forge_version} installed successfully")
                        return True
                    else:
                        logging.warning(f"Forge {forge_version} installation failed: {result.stderr}")
                        installer_path.unlink()
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