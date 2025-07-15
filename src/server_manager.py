import subprocess
import threading
import socket
import json
import os
import time
import requests
import zipfile
import shutil
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
        """Start the Minecraft server"""
        if self.is_running:
            return False
            
        try:
            # Check if server jar exists
            server_jar = self.find_server_jar()
            if not server_jar:
                # Try to install Forge automatically
                if self.install_forge():
                    server_jar = self.find_server_jar()
                
            if not server_jar:
                raise Exception("No server jar found. Please install Forge first.")
                
            # Create server.properties
            self.create_server_properties()
            
            # Start server process with proper stdin
            cmd = [
                "java", "-Xmx4G", "-Xms2G",
                "-jar", str(server_jar),
                "nogui"
            ]
            
            self.server_process = subprocess.Popen(
                cmd,
                cwd=str(self.server_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.PIPE,
                universal_newlines=True
            )
            
            self.is_running = True
            
            # Start output monitoring thread
            threading.Thread(target=self.monitor_server_output, daemon=True).start()
            
            logging.info("Server started successfully")
            return True
            
        except Exception as e:
            logging.error(f"Failed to start server: {e}")
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
            
            # If all versions failed, try manual download
            logging.info("All automatic Forge installations failed. Please download manually.")
            webbrowser.open("https://files.minecraftforge.net/")
            return False
            
        except Exception as e:
            logging.error(f"Failed to install Forge: {e}")
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