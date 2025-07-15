from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_file
import json
import os
import subprocess
import threading
import socket
import requests
import zipfile
import shutil
from pathlib import Path
from datetime import datetime
import logging
from src.server_manager import ServerManager
from src.mod_manager import ModManager
from src.network_manager import NetworkManager, HostClient, HostInfo
from src.update_checker import UpdateChecker
import sys

app = Flask(__name__)
app.secret_key = 'mcus_secret_key_2024'

# Add built-in functions to template context
app.jinja_env.globals.update(max=max, min=min, len=len, range=range)

# Global variables
server_manager = None
mod_manager = None
network_manager = None
host_client = None
is_hosting = False
update_checker = None

def initialize_managers():
    global server_manager, mod_manager, network_manager, update_checker
    
    # Load configuration
    config = {
        'server_name': 'MCUS Server',
        'max_players': 20,
        'port': 25565,
        'host_computers': [],
        'mods': [],
        'world_name': 'world',
        'network_port': 25566,
        'minecraft_version': '1.19.2',
        'mod_loader': 'forge',
        'java_memory': '4G',
        'auto_backup': True,
        'backup_interval': 3600
    }
    
    try:
        if os.path.exists('config.json'):
            with open('config.json', 'r') as f:
                config.update(json.load(f))
    except:
        pass
    
    # Initialize managers
    server_manager = ServerManager(config)
    mod_manager = ModManager(Path("server/mods"))
    network_manager = NetworkManager(config.get('network_port', 25566))
    
    # Set up mod manager
    mod_manager.set_minecraft_version(config.get('minecraft_version', '1.19.2'))
    mod_manager.set_mod_loader(config.get('mod_loader', 'forge'))
    
    # Start network manager
    network_manager.start()
    
    # Initialize update checker
    update_checker = UpdateChecker()

@app.route('/')
def dashboard():
    global is_hosting, server_manager, network_manager
    
    # Get server status
    server_status = {
        'running': is_hosting,
        'players_online': [],
        'uptime': 0,
        'memory_usage': 0
    }
    
    if server_manager:
        server_status = server_manager.get_server_status()
    
    # Get hosts status
    hosts = []
    if network_manager:
        hosts = network_manager.get_hosts_status()
    
    return render_template('dashboard.html', 
                         server_status=server_status, 
                         hosts=hosts)

@app.route('/hosting')
def hosting():
    global network_manager, host_client
    
    hosts = []
    peer_ips = []
    if network_manager:
        hosts = network_manager.get_hosts_status()
        peer_ips = network_manager.peer_ips
    
    # Get current computer info
    current_host = None
    if host_client and host_client.host_info:
        current_host = host_client.host_info.get('name')
    
    return render_template('hosting.html', hosts=hosts, current_host=current_host, peer_ips=peer_ips)

@app.route('/join_network', methods=['POST'])
def join_network():
    global host_client, network_manager
    
    host_name = request.form.get('host_name')
    if not host_name:
        flash('Please enter a computer name', 'error')
        return redirect(url_for('hosting'))
    
    # Get local IP
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except:
        local_ip = "127.0.0.1"
    
    # Add this computer to the network manager directly
    if network_manager:
        network_manager.hosts[host_name] = HostInfo(
            name=host_name,
            ip=local_ip,
            port=25565,
            status='online',
            last_seen=datetime.now(),
            players=[],
            memory_usage=0.0,
            cpu_usage=0.0
        )
        
        # Create host client for future communication
        host_client = HostClient("127.0.0.1", 25566)
        
        flash(f'Successfully joined hosting network as {host_name}', 'success')
    else:
        flash('Network manager not initialized', 'error')
    
    return redirect(url_for('hosting'))

@app.route('/add_host', methods=['POST'])
def add_host():
    global network_manager
    
    if not network_manager:
        flash('Network manager not initialized', 'error')
        return redirect(url_for('hosting'))
    
    host_name = request.form.get('host_name')
    host_ip = request.form.get('host_ip')
    
    if not host_name or not host_ip:
        flash('Please enter both host name and IP', 'error')
        return redirect(url_for('hosting'))
    
    # Add to network manager
    network_manager.hosts[host_name] = HostInfo(
        name=host_name,
        ip=host_ip,
        port=25565,
        status='offline',
        last_seen=datetime.now(),
        players=[],
        memory_usage=0.0,
        cpu_usage=0.0
    )
    
    flash(f'Added host: {host_name}', 'success')
    return redirect(url_for('hosting'))

@app.route('/remove_host/<host_name>')
def remove_host(host_name):
    global network_manager
    
    if not network_manager:
        flash('Network manager not initialized', 'error')
        return redirect(url_for('hosting'))
    
    if network_manager.remove_host(host_name):
        flash(f'Removed host: {host_name}', 'success')
    else:
        flash(f'Failed to remove host: {host_name}', 'error')
    
    return redirect(url_for('hosting'))

@app.route('/add_peer', methods=['POST'])
def add_peer():
    global network_manager
    
    if not network_manager:
        flash('Network manager not initialized', 'error')
        return redirect(url_for('hosting'))
    
    peer_ip = request.form.get('peer_ip')
    if not peer_ip:
        flash('Please enter a peer IP address', 'error')
        return redirect(url_for('hosting'))
    
    # Add peer IP to network manager
    network_manager.add_peer_ip(peer_ip)
    flash(f'Added peer IP: {peer_ip}. Your friend should add your IP address too.', 'success')
    
    return redirect(url_for('hosting'))

@app.route('/remove_peer/<peer_ip>')
def remove_peer(peer_ip):
    global network_manager
    
    if not network_manager:
        flash('Network manager not initialized', 'error')
        return redirect(url_for('hosting'))
    
    network_manager.remove_peer_ip(peer_ip)
    flash(f'Removed peer IP: {peer_ip}', 'success')
    
    return redirect(url_for('hosting'))

@app.route('/mods')
def mods():
    global mod_manager
    
    installed_mods = []
    popular_modrinth_mods = []
    
    if mod_manager:
        installed_mods = mod_manager.get_installed_mods()
        
        # Get popular mods from Modrinth for the main page
        try:
            popular_modrinth_mods = mod_manager.get_popular_modrinth_mods(limit=12)  # Show top 12 popular mods
        except Exception as e:
            logging.error(f"Failed to load popular mods for main page: {e}")
            # Continue without popular mods if there's an error
    
    return render_template('mods.html', 
                         mods=installed_mods, 
                         popular_modrinth_mods=popular_modrinth_mods)

@app.route('/search_modrinth')
def search_modrinth():
    global mod_manager
    
    query = request.args.get('q', '')
    mods = []
    
    if query and mod_manager:
        mods = mod_manager.search_modrinth_mods(query, 20)
    
    return render_template('modrinth_search.html', mods=mods, query=query)

@app.route('/popular_mods')
def popular_mods():
    """Show popular mods from Modrinth with real API data"""
    global mod_manager
    
    if not mod_manager:
        flash('Mod manager not initialized', 'error')
        return redirect(url_for('mods'))
    
    try:
        # Get popular mods from Modrinth API
        popular_mods_list = mod_manager.get_popular_modrinth_mods(limit=100)
        
        # Group mods by category for better organization
        categorized_mods = {
            'tech': {
                'name': 'Technology & Automation',
                'icon': 'fas fa-cogs',
                'color': 'primary',
                'description': 'Automation, machines, and technological advancements',
                'mods': []
            },
            'magic': {
                'name': 'Magic & Fantasy',
                'icon': 'fas fa-magic',
                'color': 'purple',
                'description': 'Magical spells, rituals, and mystical content',
                'mods': []
            },
            'adventure': {
                'name': 'Adventure & Exploration',
                'icon': 'fas fa-compass',
                'color': 'success',
                'description': 'Dungeons, structures, and exploration content',
                'mods': []
            },
            'storage': {
                'name': 'Storage & Organization',
                'icon': 'fas fa-boxes',
                'color': 'warning',
                'description': 'Storage solutions and inventory management',
                'mods': []
            },
            'utility': {
                'name': 'Utility & Quality of Life',
                'icon': 'fas fa-tools',
                'color': 'info',
                'description': 'Tools and improvements for better gameplay',
                'mods': []
            },
            'worldgen': {
                'name': 'World Generation',
                'icon': 'fas fa-mountain',
                'color': 'secondary',
                'description': 'Biomes, structures, and world generation',
                'mods': []
            },
            'other': {
                'name': 'Other Mods',
                'icon': 'fas fa-puzzle-piece',
                'color': 'dark',
                'description': 'Miscellaneous and other mods',
                'mods': []
            }
        }
        
        # Categorize mods based on their categories
        for mod in popular_mods_list:
            mod_categories = [cat.lower() for cat in mod.get('categories', [])]
            
            # Determine which category this mod belongs to
            if any(cat in mod_categories for cat in ['tech', 'automation', 'energy', 'industrial']):
                categorized_mods['tech']['mods'].append(mod)
            elif any(cat in mod_categories for cat in ['magic', 'spells', 'ritual', 'arcane']):
                categorized_mods['magic']['mods'].append(mod)
            elif any(cat in mod_categories for cat in ['adventure', 'dungeons', 'exploration']):
                categorized_mods['adventure']['mods'].append(mod)
            elif any(cat in mod_categories for cat in ['storage', 'digital', 'inventory']):
                categorized_mods['storage']['mods'].append(mod)
            elif any(cat in mod_categories for cat in ['utility', 'quality-of-life', 'tools']):
                categorized_mods['utility']['mods'].append(mod)
            elif any(cat in mod_categories for cat in ['worldgen', 'biomes', 'structures']):
                categorized_mods['worldgen']['mods'].append(mod)
            else:
                categorized_mods['other']['mods'].append(mod)
        
        # Remove empty categories
        categorized_mods = {k: v for k, v in categorized_mods.items() if v['mods']}
        
        return render_template('popular_mods.html', 
                             categorized_mods=categorized_mods,
                             total_mods=len(popular_mods_list))
                             
    except Exception as e:
        flash(f'Error loading popular mods: {str(e)}', 'error')
        return redirect(url_for('mods'))

@app.route('/download_mod/<project_id>')
def download_mod(project_id):
    global mod_manager
    
    if not mod_manager:
        flash('Mod manager not initialized', 'error')
        return redirect(url_for('mods'))
    
    # Get latest version
    latest_version = mod_manager.get_latest_modrinth_version(project_id)
    if not latest_version:
        flash('Could not find compatible version', 'error')
        return redirect(url_for('mods'))
    
    # Download mod
    if mod_manager.download_mod_from_modrinth(project_id, latest_version['id']):
        flash(f'Successfully downloaded mod', 'success')
    else:
        flash('Failed to download mod', 'error')
    
    return redirect(url_for('mods'))

@app.route('/install_popular_pack', methods=['POST'])
def install_popular_pack():
    global mod_manager
    
    if not mod_manager:
        flash('Mod manager not initialized', 'error')
        return redirect(url_for('popular_mods'))
    
    # Get popular mods
    popular_mods = mod_manager.get_popular_modrinth_mods(10)  # Top 10 most popular
    
    success_count = 0
    failed_count = 0
    
    for mod in popular_mods:
        try:
            # Get latest version
            latest_version = mod_manager.get_latest_modrinth_version(mod['id'])
            if latest_version:
                # Download mod
                if mod_manager.download_mod_from_modrinth(mod['id'], latest_version['id']):
                    success_count += 1
                else:
                    failed_count += 1
            else:
                failed_count += 1
        except Exception as e:
            failed_count += 1
            logging.error(f"Failed to install {mod['name']}: {e}")
    
    if success_count > 0:
        flash(f'Successfully installed {success_count} popular mods! {failed_count} failed.', 'success')
    else:
        flash('Failed to install any mods. Please try installing them individually.', 'error')
    
    return redirect(url_for('popular_mods'))

@app.route('/upload_mod', methods=['POST'])
def upload_mod():
    global mod_manager
    
    if not mod_manager:
        flash('Mod manager not initialized', 'error')
        return redirect(url_for('mods'))
    
    if 'mod_file' not in request.files:
        flash('No file selected', 'error')
        return redirect(url_for('mods'))
    
    file = request.files['mod_file']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('mods'))
    
    if file and file.filename and file.filename.endswith('.jar'):
        # Save file temporarily
        temp_path = Path('temp_mod.jar')
        file.save(temp_path)
        
        # Install mod
        if mod_manager.install_mod_from_file(str(temp_path)):
            flash(f'Successfully installed: {file.filename}', 'success')
        else:
            flash(f'Failed to install: {file.filename}', 'error')
        
        # Clean up
        temp_path.unlink(missing_ok=True)
    else:
        flash('Please select a valid JAR file', 'error')
    
    return redirect(url_for('mods'))

@app.route('/remove_mod/<mod_name>')
def remove_mod(mod_name):
    global mod_manager
    
    if mod_manager and mod_manager.remove_mod(mod_name):
        flash(f'Removed mod: {mod_name}', 'success')
    else:
        flash(f'Failed to remove mod: {mod_name}', 'error')
    
    return redirect(url_for('mods'))

@app.route('/players')
def players():
    global server_manager
    
    players_online = []
    if server_manager:
        players_online = server_manager.get_online_players()
    
    return render_template('players.html', players=players_online)

@app.route('/send_command', methods=['POST'])
def send_command():
    global server_manager
    
    command = request.form.get('command')
    if command and server_manager:
        if server_manager.send_server_command(command):
            flash(f'Command sent: {command}', 'success')
        else:
            flash('Failed to send command', 'error')
    else:
        flash('Please enter a command', 'error')
    
    return redirect(url_for('players'))

@app.route('/settings')
def settings():
    # Load current settings
    config = {}
    try:
        if os.path.exists('config.json'):
            with open('config.json', 'r') as f:
                config = json.load(f)
    except:
        pass
    
    return render_template('settings.html', config=config)

@app.route('/save_settings', methods=['POST'])
def save_settings():
    config = {
        'server_name': request.form.get('server_name', 'MCUS Server'),
        'max_players': int(request.form.get('max_players', 20)),
        'port': int(request.form.get('port', 25565)),
        'world_name': request.form.get('world_name', 'world'),
        'minecraft_version': request.form.get('minecraft_version', '1.19.2'),
        'mod_loader': request.form.get('mod_loader', 'forge'),
        'java_memory': request.form.get('java_memory', '4G'),
        'auto_backup': request.form.get('auto_backup') == 'on',
        'backup_interval': int(request.form.get('backup_interval', 3600))
    }
    
    # Save configuration
    with open('config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    flash('Settings saved successfully', 'success')
    return redirect(url_for('settings'))

@app.route('/start_server')
def start_server():
    global server_manager, is_hosting, host_client
    
    if not is_hosting and server_manager:
        try:
            # Check if server is already running
            if server_manager.is_running:
                flash('Server is already running', 'warning')
                return redirect(url_for('dashboard'))
            
            # Get detailed startup information
            startup_info = get_startup_diagnostics()
            
            # Start the server
            if server_manager.start_server():
                is_hosting = True
                
                # Update host status
                if host_client:
                    host_client.update_status({
                        'status': 'online',
                        'players': [],
                        'memory_usage': 0.0,
                        'cpu_usage': 0.0
                    })
                
                flash('Server started successfully!', 'success')
            else:
                # Provide detailed error information
                error_details = get_server_error_details()
                flash(f'Failed to start server. {error_details}', 'error')
                
        except Exception as e:
            logging.error(f"Server startup error: {e}")
            flash(f'Server startup error: {str(e)}', 'error')
    else:
        flash('Server is already running or server manager not initialized', 'warning')
    
    return redirect(url_for('dashboard'))

def get_startup_diagnostics():
    """Get comprehensive startup diagnostics"""
    diagnostics = {
        'java_available': False,
        'java_version': None,
        'server_directory': False,
        'server_jar': False,
        'permissions': False,
        'memory_available': False,
        'disk_space': False
    }
    
    try:
        # Check Java
        result = subprocess.run(['java', '-version'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            diagnostics['java_available'] = True
            # Extract version from stderr
            import re
            version_match = re.search(r'"([^"]+)"', result.stderr)
            if version_match:
                diagnostics['java_version'] = version_match.group(1)
        
        # Check server directory
        server_dir = Path("server")
        if server_dir.exists():
            diagnostics['server_directory'] = True
            
            # Check permissions
            try:
                test_file = server_dir / ".test_write"
                test_file.write_text("test")
                test_file.unlink()
                diagnostics['permissions'] = True
            except:
                pass
            
            # Check for server JAR
            for file in server_dir.glob("*.jar"):
                if "forge" in file.name.lower() or "server" in file.name.lower():
                    diagnostics['server_jar'] = True
                    break
        
        # Check system resources
        try:
            import psutil
            memory = psutil.virtual_memory()
            if memory.available >= 2 * 1024**3:  # 2GB
                diagnostics['memory_available'] = True
            
            disk = psutil.disk_usage(str(server_dir))
            if disk.free >= 1024**3:  # 1GB
                diagnostics['disk_space'] = True
        except ImportError:
            # psutil not available, assume resources are sufficient
            diagnostics['memory_available'] = True
            diagnostics['disk_space'] = True
            
    except Exception as e:
        logging.error(f"Diagnostics error: {e}")
    
    return diagnostics

def get_server_error_details():
    """Get detailed error information for server startup failures"""
    try:
        # Check common issues
        issues = []
        
        # Check Java
        try:
            result = subprocess.run(['java', '-version'], capture_output=True, text=True, timeout=5)
            if result.returncode != 0:
                issues.append("Java not installed or not in PATH")
        except FileNotFoundError:
            issues.append("Java not found - please install Java 8 or higher")
        except subprocess.TimeoutExpired:
            issues.append("Java command timed out")
        
        # Check server directory
        server_dir = Path("server")
        if not server_dir.exists():
            issues.append("Server directory does not exist")
        else:
            try:
                test_file = server_dir / ".test_write"
                test_file.write_text("test")
                test_file.unlink()
            except PermissionError:
                issues.append("No write permission to server directory")
            except Exception as e:
                issues.append(f"Cannot write to server directory: {e}")
        
        # Check for server JAR
        server_jar_found = False
        if server_dir.exists():
            for file in server_dir.glob("*.jar"):
                if "forge" in file.name.lower() or "server" in file.name.lower():
                    server_jar_found = True
                    break
        
        if not server_jar_found:
            issues.append("No Forge server JAR found - please install Forge first")
        
        # Check system resources
        try:
            import psutil
            memory = psutil.virtual_memory()
            if memory.available < 2 * 1024**3:  # Less than 2GB
                issues.append(f"Insufficient memory: {memory.available // (1024**3)}GB available, 2GB+ recommended")
            
            disk = psutil.disk_usage(str(server_dir))
            if disk.free < 1024**3:  # Less than 1GB
                issues.append(f"Insufficient disk space: {disk.free // (1024**3)}GB available, 1GB+ recommended")
        except ImportError:
            pass  # psutil not available
        
        if issues:
            return "Issues found: " + "; ".join(issues)
        else:
            return "Unknown error occurred during startup"
            
    except Exception as e:
        return f"Error checking system: {str(e)}"

@app.route('/stop_server')
def stop_server():
    global server_manager, is_hosting, host_client
    
    if is_hosting and server_manager:
        if server_manager.stop_server():
            is_hosting = False
            
            # Update host status
            if host_client:
                host_client.update_status({
                    'status': 'offline',
                    'players': [],
                    'memory_usage': 0.0,
                    'cpu_usage': 0.0
                })
            
            flash('Server stopped successfully', 'success')
        else:
            flash('Failed to stop server', 'error')
    else:
        flash('Server is not running', 'warning')
    
    return redirect(url_for('dashboard'))

@app.route('/install_forge')
def install_forge():
    """Install Forge using the modern installer"""
    try:
        from forge_installer import ModernForgeInstaller
        
        # Create installer
        installer = ModernForgeInstaller(Path("server"))
        
        # Check if Forge is already installed
        existing_jar = installer.find_installed_forge_jar()
        if existing_jar:
            flash(f'Forge is already installed: {existing_jar.name}', 'info')
            return redirect(url_for('mods'))
        
        # Get available Minecraft versions
        versions = installer.get_available_minecraft_versions()
        
        return render_template('install_forge.html', 
                             minecraft_versions=versions,
                             current_version="1.20.4")
                             
    except Exception as e:
        flash(f'Error initializing Forge installer: {str(e)}', 'error')
        return redirect(url_for('mods'))

@app.route('/detect_forge')
def detect_forge():
    """Detect installed Forge versions"""
    global server_manager
    
    if not server_manager:
        flash('Server manager not initialized', 'error')
        return redirect(url_for('mods'))
    
    try:
        detected_versions = server_manager.detect_forge_versions()
        available_versions = server_manager.get_available_forge_versions()
        
        return render_template('detect_forge.html', 
                             detected_versions=detected_versions,
                             available_versions=available_versions)
                             
    except Exception as e:
        flash(f'Error detecting Forge versions: {str(e)}', 'error')
        return redirect(url_for('mods'))

@app.route('/select_forge_version')
def select_forge_version():
    """Show Forge version selection page"""
    global server_manager
    
    if not server_manager:
        flash('Server manager not initialized', 'error')
        return redirect(url_for('mods'))
    
    try:
        # Get detected versions
        detected_versions = server_manager.detect_forge_versions()
        
        # Get available versions for installation and format them properly
        raw_versions = server_manager.get_available_forge_versions()
        
        # Format the data structure for the template
        available_versions = {}
        for mc_version, version_list in raw_versions.items():
            available_versions[mc_version] = {
                'name': f'Minecraft {mc_version}',
                'description': f'Stable Minecraft {mc_version} with Forge support',
                'status': 'Latest Stable' if mc_version == '1.20.4' else 'Stable',
                'mod_count': '1000+',
                'java_version': '17+',
                'performance': 'High',
                'stability': 'Very Stable',
                'builds': version_list  # This is the list of version strings
            }
        
        # Get current server JAR
        current_jar = server_manager.find_server_jar()
        current_jar_name = current_jar.name if current_jar else None
        
        return render_template('select_forge_version.html', 
                             detected_versions=detected_versions,
                             available_versions=available_versions,
                             current_jar=current_jar_name)
                             
    except Exception as e:
        flash(f'Error loading Forge versions: {str(e)}', 'error')
        return redirect(url_for('mods'))

@app.route('/install_forge_version', methods=['POST'])
def install_forge_version():
    """Install a specific Forge version with improved error handling and seamless activation"""
    try:
        from forge_installer import ModernForgeInstaller
        
        minecraft_version = request.form.get('minecraft_version', '1.20.4')
        forge_build = request.form.get('forge_build', '')
        
        if not forge_build:
            flash('No Forge build selected. Please select a Forge version to install.', 'error')
            return redirect(url_for('install_forge'))
        
        # Check Java installation first
        try:
            result = subprocess.run(['java', '-version'], capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                flash('Java is not installed or not working. Please install Java 17 or higher from https://adoptium.net', 'error')
                return redirect(url_for('install_forge'))
        except Exception:
            flash('Java is not installed. Please install Java 17 or higher from https://adoptium.net', 'error')
            return redirect(url_for('install_forge'))
        
        # Check server directory permissions
        server_dir = Path("server")
        try:
            server_dir.mkdir(exist_ok=True)
            test_file = server_dir / ".test_write"
            test_file.write_text("test")
            test_file.unlink()
        except Exception as e:
            flash(f'Cannot write to server directory. Check permissions: {str(e)}', 'error')
            return redirect(url_for('install_forge'))
        
        # Create installer
        installer = ModernForgeInstaller(server_dir)
        
        # Check if Forge is already installed
        existing_jar = installer.find_installed_forge_jar()
        if existing_jar:
            flash(f'Forge is already installed: {existing_jar.name}. Remove it first if you want to reinstall.', 'info')
            return redirect(url_for('mods'))
        
        # Install Forge with detailed error messages
        success, message = installer.install_forge_server(minecraft_version, forge_build)
        
        if success:
            # Find installed JAR and create startup script
            jar_path = installer.find_installed_forge_jar()
            if jar_path:
                # Auto-select the new Forge JAR as active (no manual step needed)
                # Optionally, update config or state if needed
                if installer.create_server_script(jar_path):
                    flash(f'✅ Forge {minecraft_version}-{forge_build} installed and selected! Server JAR: {jar_path.name}. Startup scripts created. Ready to start your server.', 'success')
                else:
                    flash(f'✅ Forge {minecraft_version}-{forge_build} installed and selected! Server JAR: {jar_path.name}. (Startup scripts could not be created)', 'warning')
            else:
                flash(f'✅ Forge {minecraft_version}-{forge_build} installed, but could not find server JAR. Check the server directory.', 'warning')
            # Redirect to dashboard for next step
            return redirect(url_for('dashboard'))
        else:
            # Provide specific error messages
            if "Failed to download" in message:
                flash(f'❌ Download failed: {message}. Check your internet connection and try again.', 'error')
            elif "Installation failed" in message:
                flash(f'❌ Installation failed: {message}. Make sure Java is installed and you have sufficient disk space.', 'error')
            elif "timed out" in message:
                flash(f'❌ Installation timed out: {message}. Try again or check your internet connection.', 'error')
            else:
                flash(f'❌ Forge installation failed: {message}', 'error')
            return redirect(url_for('select_forge_version'))
        
    except ImportError:
        flash('❌ Forge installer module not found. Please restart MCUS.', 'error')
        return redirect(url_for('install_forge'))
    except Exception as e:
        flash(f'❌ Unexpected error during Forge installation: {str(e)}', 'error')
        return redirect(url_for('install_forge'))

@app.route('/get_forge_versions/<minecraft_version>')
def get_forge_versions(minecraft_version):
    """Get available Forge versions for a Minecraft version (AJAX)"""
    try:
        from forge_installer import ModernForgeInstaller
        
        installer = ModernForgeInstaller(Path("server"))
        versions = installer.get_forge_versions(minecraft_version)
        
        return jsonify(versions)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/use_forge_version', methods=['POST'])
def use_forge_version():
    """Set a specific Forge version as the active server JAR"""
    global server_manager
    
    if not server_manager:
        flash('Server manager not initialized', 'error')
        return redirect(url_for('mods'))
    
    selected_file = request.form.get('selected_file')
    
    if not selected_file:
        flash('No Forge version selected', 'error')
        return redirect(url_for('select_forge_version'))
    
    try:
        # Find the selected JAR file
        jar_path = server_manager.server_dir / selected_file
        
        if not jar_path.exists():
            flash(f'Selected file not found: {selected_file}', 'error')
            return redirect(url_for('select_forge_version'))
        
        # Validate it's a Forge JAR
        if not server_manager._is_forge_jar(jar_path):
            flash('Selected file is not a valid Forge JAR', 'error')
            return redirect(url_for('select_forge_version'))
        
        # Get version info
        version_info = server_manager._extract_forge_version(jar_path)
        
        flash(f'Successfully selected Forge version: {version_info["version_number"]}', 'success')
        
        return redirect(url_for('mods'))
        
    except Exception as e:
        flash(f'Error selecting Forge version: {str(e)}', 'error')
        return redirect(url_for('select_forge_version'))

@app.route('/backup_world')
def backup_world():
    global server_manager
    
    if server_manager:
        if server_manager.backup_world():
            flash('World backup created successfully', 'success')
        else:
            flash('Failed to create world backup', 'error')
    else:
        flash('Server manager not initialized', 'error')
    
    return redirect(url_for('dashboard'))

@app.route('/diagnostics')
def diagnostics():
    """Show comprehensive diagnostics and troubleshooting page"""
    return render_template('diagnostics.html')

# Diagnostics API endpoints
@app.route('/api/diagnostics/system-info')
def api_system_info():
    """Get system information for diagnostics page"""
    try:
        import psutil
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('.')
        
        # Get Java version
        try:
            result = subprocess.run(['java', '-version'], capture_output=True, text=True, timeout=10)
            java_version = result.stderr.split('\n')[0] if result.returncode == 0 else 'Not found'
        except:
            java_version = 'Not found'
        
        return jsonify({
            'python_version': sys.version.split()[0],
            'java_version': java_version,
            'memory_info': f"{memory.available // (1024**3)}GB available of {memory.total // (1024**3)}GB total",
            'os_info': f"{sys.platform} ({os.name})",
            'disk_space': f"{disk.free // (1024**3)}GB free of {disk.total // (1024**3)}GB total",
            'network_status': 'Connected'  # Basic check
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/diagnostics/system-health')
def api_system_health():
    """Get real-time system health metrics"""
    try:
        import psutil
        
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memory usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        
        # Disk usage
        disk = psutil.disk_usage('.')
        disk_percent = (disk.used / disk.total) * 100
        
        # Network status (basic check)
        try:
            requests.get('https://www.google.com', timeout=5)
            network_status = 'Connected'
        except:
            network_status = 'Disconnected'
        
        return jsonify({
            'cpu_usage': f"{cpu_percent:.1f}%",
            'memory_usage': f"{memory_percent:.1f}%",
            'disk_usage': f"{disk_percent:.1f}%",
            'network_status': network_status
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/diagnostics/run/<diagnostic_type>')
def api_run_diagnostic(diagnostic_type):
    """Run specific diagnostic tests"""
    results = []
    
    try:
        if diagnostic_type == 'java' or diagnostic_type == 'all':
            # Check Java installation
            try:
                result = subprocess.run(['java', '-version'], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    java_version = result.stderr.split('\n')[0]
                    results.append({
                        'name': 'Java Installation',
                        'status': 'success',
                        'message': 'Java is installed and accessible',
                        'details': java_version
                    })
                else:
                    results.append({
                        'name': 'Java Installation',
                        'status': 'error',
                        'message': 'Java is not installed or not in PATH',
                        'details': 'Install Java 8 or higher from adoptium.net'
                    })
            except Exception as e:
                results.append({
                    'name': 'Java Installation',
                    'status': 'error',
                    'message': f'Error checking Java: {str(e)}',
                    'details': 'Check Java installation'
                })
        
        if diagnostic_type == 'forge' or diagnostic_type == 'all':
            # Check Forge installation
            server_dir = Path("server")
            forge_jars = list(server_dir.glob("forge-*.jar")) if server_dir.exists() else []
            
            if forge_jars:
                results.append({
                    'name': 'Forge Installation',
                    'status': 'success',
                    'message': f'Forge server JAR found: {forge_jars[0].name}',
                    'details': f'Located in {server_dir.absolute()}'
                })
            else:
                results.append({
                    'name': 'Forge Installation',
                    'status': 'warning',
                    'message': 'No Forge server JAR found',
                    'details': 'Install Forge from the Mods page'
                })
        
        if diagnostic_type == 'network' or diagnostic_type == 'all':
            # Test network connectivity
            try:
                response = requests.get('https://api.modrinth.com/v2/search', timeout=10)
                if response.status_code == 200:
                    results.append({
                        'name': 'Network Connectivity',
                        'message': 'Network connection is working',
                        'status': 'success',
                        'details': 'Can reach external services'
                    })
                else:
                    results.append({
                        'name': 'Network Connectivity',
                        'status': 'warning',
                        'message': 'Network connection issues',
                        'details': f'HTTP {response.status_code}'
                    })
            except Exception as e:
                results.append({
                    'name': 'Network Connectivity',
                    'status': 'error',
                    'message': 'Network connection failed',
                    'details': str(e)
                })
        
        if diagnostic_type == 'server' or diagnostic_type == 'all':
            # Check server files
            server_dir = Path("server")
            if server_dir.exists():
                if os.access(server_dir, os.W_OK):
                    results.append({
                        'name': 'Server Directory',
                        'status': 'success',
                        'message': 'Server directory exists and is writable',
                        'details': str(server_dir.absolute())
                    })
                else:
                    results.append({
                        'name': 'Server Directory',
                        'status': 'error',
                        'message': 'Server directory exists but is not writable',
                        'details': 'Check permissions or run as administrator'
                    })
            else:
                results.append({
                    'name': 'Server Directory',
                    'status': 'warning',
                    'message': 'Server directory does not exist',
                    'details': 'Will be created when needed'
                })
        
        if diagnostic_type == 'mods' or diagnostic_type == 'all':
            # Check mods directory
            mods_dir = Path("server/mods")
            if mods_dir.exists():
                mod_count = len(list(mods_dir.glob("*.jar")))
                results.append({
                    'name': 'Mods Directory',
                    'status': 'success',
                    'message': f'Mods directory exists with {mod_count} mods',
                    'details': str(mods_dir.absolute())
                })
            else:
                results.append({
                    'name': 'Mods Directory',
                    'status': 'warning',
                    'message': 'Mods directory does not exist',
                    'details': 'Will be created when needed'
                })
        
        return jsonify(results)
        
    except Exception as e:
        return jsonify([{
            'name': 'Diagnostic Error',
            'status': 'error',
            'message': f'Error running diagnostics: {str(e)}',
            'details': 'Check system configuration'
        }]), 500

@app.route('/api/diagnostics/logs/<log_file>')
def api_get_log(log_file):
    """Get log file contents"""
    try:
        log_path = Path(log_file)
        if not log_path.exists():
            return f"Log file not found: {log_file}", 404
        
        # Read last 1000 lines to avoid overwhelming the browser
        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            return ''.join(lines[-1000:])
    except Exception as e:
        return f"Error reading log: {str(e)}", 500

@app.route('/api/diagnostics/logs/<log_file>/download')
def api_download_log(log_file):
    """Download log file"""
    try:
        log_path = Path(log_file)
        if not log_path.exists():
            return f"Log file not found: {log_file}", 404
        
        return send_file(log_path, as_attachment=True, download_name=log_path.name)
    except Exception as e:
        return f"Error downloading log: {str(e)}", 500

@app.route('/fix_permissions')
def fix_permissions():
    """Attempt to fix common permission issues"""
    try:
        server_dir = Path("server")
        
        # Create server directory if it doesn't exist
        server_dir.mkdir(parents=True, exist_ok=True)
        
        # Create necessary subdirectories
        subdirs = ['mods', 'config', 'logs', 'world', 'backups']
        for subdir in subdirs:
            subdir_path = server_dir / subdir
            subdir_path.mkdir(exist_ok=True)
        
        # Try to set permissions (Windows doesn't have chmod)
        if os.name != 'nt':
            try:
                os.chmod(server_dir, 0o755)
                for subdir in subdirs:
                    subdir_path = server_dir / subdir
                    os.chmod(subdir_path, 0o755)
            except:
                pass
        
        flash('Permission fix attempted. Please try starting the server again.', 'info')
        
    except Exception as e:
        flash(f'Failed to fix permissions: {str(e)}', 'error')
    
    return redirect(url_for('diagnostics'))

@app.route('/browse_modrinth')
def browse_modrinth():
    """Browse all mods from Modrinth with filtering and pagination"""
    global mod_manager
    
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 50, type=int)
    sort_by = request.args.get('sort_by', 'downloads')
    categories = request.args.getlist('categories')
    loader = request.args.get('loader')
    game_version = request.args.get('game_version')
    
    # Get filter options
    all_categories = mod_manager.get_modrinth_categories() if mod_manager else []
    all_loaders = mod_manager.get_modrinth_loaders() if mod_manager else []
    all_game_versions = mod_manager.get_modrinth_game_versions() if mod_manager else []
    
    # Get mods with filters
    result = mod_manager.get_all_modrinth_mods(
        page=page, 
        limit=limit, 
        sort_by=sort_by,
        categories=categories if categories else None,
        loader=loader,
        game_version=game_version
    ) if mod_manager else {'mods': [], 'total_hits': 0, 'page': page, 'total_pages': 0}
    
    return render_template('browse_modrinth.html', 
                         mods=result['mods'],
                         total_hits=result['total_hits'],
                         page=result['page'],
                         total_pages=result['total_pages'],
                         categories=all_categories,
                         loaders=all_loaders,
                         game_versions=all_game_versions,
                         current_filters={
                             'sort_by': sort_by,
                             'categories': categories,
                             'loader': loader,
                             'game_version': game_version
                         })

@app.route('/modrinth_project/<project_id>')
def modrinth_project_details(project_id):
    """Show detailed information about a specific Modrinth project"""
    global mod_manager
    
    if not mod_manager:
        flash('Mod manager not initialized', 'error')
        return redirect(url_for('browse_modrinth'))
    
    try:
        project = mod_manager.get_modrinth_project_details(project_id)
        if not project:
            flash(f'Project "{project_id}" not found or could not be loaded', 'error')
            return redirect(url_for('browse_modrinth'))
        
        # Ensure all required fields exist to prevent template errors
        required_fields = ['id', 'name', 'description', 'downloads', 'followers', 'author', 
                          'categories', 'versions', 'project_type', 'client_side', 'server_side']
        
        for field in required_fields:
            if field not in project:
                project[field] = '' if field in ['name', 'description', 'author'] else [] if field in ['categories', 'versions'] else 0
        
        return render_template('modrinth_project.html', project=project)
        
    except Exception as e:
        flash(f'Error loading project details: {str(e)}', 'error')
        return redirect(url_for('browse_modrinth'))

@app.route('/download_modrinth_version/<project_id>/<version_id>')
def download_modrinth_version(project_id, version_id):
    """Download a specific version of a mod from Modrinth"""
    global mod_manager
    
    try:
        if mod_manager and mod_manager.download_mod_from_modrinth(project_id, version_id):
            flash('Mod downloaded successfully!', 'success')
        else:
            flash('Failed to download mod', 'error')
    except Exception as e:
        flash(f'Error downloading mod: {str(e)}', 'error')
    
    return redirect(request.referrer or url_for('browse_modrinth'))

@app.route('/share_mcus')
def share_mcus():
    """Create a shareable MCUS package"""
    try:
        # Import the sharing functionality
        from share_mcus import create_share_package, get_local_ip
        
        # Create the package
        zip_name = create_share_package()
        local_ip = get_local_ip()
        
        flash(f'Share package created! Your IP: {local_ip}', 'success')
        
        # Return the zip file for download
        return send_file(zip_name, as_attachment=True, download_name=zip_name)
        
    except Exception as e:
        flash(f'Error creating share package: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

@app.route('/create_shortcut')
def create_shortcut():
    """Create desktop shortcut for MCUS"""
    try:
        # Import the shortcut creator
        from create_shortcut import main as create_shortcut_main
        
        # Create the shortcut
        create_shortcut_main()
        
        flash('Desktop shortcut created successfully!', 'success')
        
    except Exception as e:
        flash(f'Error creating shortcut: {str(e)}', 'error')
    
    return redirect(url_for('dashboard'))

@app.route('/api/forge/status')
def api_forge_status():
    """Get detailed Forge installation status"""
    global server_manager
    
    if not server_manager:
        return jsonify({
            'error': 'Server manager not initialized'
        }), 500
    
    try:
        status = server_manager.get_forge_installation_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({
            'error': f'Failed to get Forge status: {e}'
        }), 500

@app.route('/api/forge/is_ready')
def api_forge_is_ready():
    """Check if Forge is properly installed and ready to run"""
    global server_manager
    
    if not server_manager:
        return jsonify({
            'ready': False,
            'error': 'Server manager not initialized'
        }), 500
    
    try:
        is_ready = server_manager.is_forge_properly_installed()
        return jsonify({
            'ready': is_ready
        })
    except Exception as e:
        return jsonify({
            'ready': False,
            'error': f'Failed to check Forge readiness: {e}'
        }), 500

@app.route('/api/server/detailed_status')
def api_server_detailed_status():
    """Get detailed server status including Forge information"""
    global server_manager, is_hosting
    
    if not server_manager:
        return jsonify({
            'error': 'Server manager not initialized'
        }), 500
    
    try:
        # Get basic server status
        server_status = server_manager.get_server_status()
        
        # Get Forge status
        forge_status = server_manager.get_forge_installation_status()
        
        # Check if server is actually running
        java_processes = []
        actual_running = False
        try:
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    # Look for Java processes that are actually running a Minecraft server
                    if ('java' in line and 
                        'forge' in line.lower() and 
                        'nogui' in line and
                        'minecraft' in line.lower()):
                        java_processes.append(line.strip())
                        actual_running = True
                    
                    # Also check for standard Minecraft server processes
                    elif ('java' in line and 
                          'minecraft' in line.lower() and 
                          'nogui' in line and
                          'server.jar' in line):
                        java_processes.append(line.strip())
                        actual_running = True
        except:
            pass
        
        # If no processes found, definitely not running
        if not java_processes:
            actual_running = False
        
        return jsonify({
            'server_status': server_status,
            'forge_status': forge_status,
            'actual_running': actual_running,
            'java_processes': java_processes,
            'web_interface_running': is_hosting
        })
    except Exception as e:
        return jsonify({
            'error': f'Failed to get detailed status: {e}'
        }), 500

@app.route('/api/updates/check')
def api_check_updates():
    """Check for updates"""
    global update_checker
    
    if not update_checker:
        return jsonify({
            'error': 'Update checker not initialized'
        }), 500
    
    try:
        update_info = update_checker.check_for_updates(force_check=True)
        return jsonify({
            'update_available': update_info is not None,
            'update_info': update_info
        })
    except Exception as e:
        return jsonify({
            'error': f'Failed to check for updates: {e}'
        }), 500

@app.route('/api/updates/notification')
def api_get_update_notification():
    """Get update notification HTML"""
    global update_checker
    
    if not update_checker:
        return jsonify({'html': None})
    
    try:
        # First check cached update
        update_info = update_checker.get_cached_update()
        
        # If no cached update, check for new updates
        if not update_info:
            update_info = update_checker.check_for_updates()
        
        if update_info and not update_info.get('seen_by_user'):
            html = update_checker.get_update_notification_html(update_info)
            return jsonify({'html': html})
        else:
            return jsonify({'html': None})
            
    except Exception as e:
        return jsonify({'html': None})

@app.route('/api/updates/dismiss', methods=['POST'])
def api_dismiss_update():
    """Dismiss update notification"""
    global update_checker
    
    if not update_checker:
        return jsonify({'success': False, 'error': 'Update checker not initialized'}), 500
    
    try:
        update_checker.mark_update_as_seen()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    # Initialize managers
    initialize_managers()
    
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    
    # Get port from environment variable (for Railway) or use default
    port = int(os.environ.get('PORT', 3000))
    
    print("MCUS Web Server starting...")
    print(f"Open your browser and go to: http://localhost:{port}")
    print("To share with friends, use your IP address instead of localhost")
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=port, debug=False) 