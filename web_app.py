from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
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

app = Flask(__name__)
app.secret_key = 'mcus_secret_key_2024'

# Global variables
server_manager = None
mod_manager = None
network_manager = None
host_client = None
is_hosting = False

def initialize_managers():
    global server_manager, mod_manager, network_manager
    
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
    if mod_manager:
        installed_mods = mod_manager.get_installed_mods()
    
    return render_template('mods.html', mods=installed_mods)

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
    global mod_manager
    
    mods = []
    if mod_manager:
        mods = mod_manager.get_popular_modrinth_mods(30)
    
    return render_template('popular_mods.html', mods=mods)

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
            
            flash('Server started successfully', 'success')
        else:
            flash('Failed to start server. Check if Java is installed and Forge is available.', 'error')
    else:
        flash('Server is already running', 'warning')
    
    return redirect(url_for('dashboard'))

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
    global server_manager
    
    if server_manager:
        try:
            # Check if Forge is already installed
            server_jar = server_manager.find_server_jar()
            if server_jar:
                flash('Forge is already installed!', 'info')
                return redirect(url_for('mods'))
            
            flash('Installing Forge... This may take a few minutes. Please wait.', 'info')
            
            if server_manager.install_forge():
                flash('Forge installed successfully! You can now start your server.', 'success')
            else:
                flash('Failed to install Forge automatically. Please try again or download manually from https://files.minecraftforge.net/', 'error')
        except Exception as e:
            flash(f'Error installing Forge: {str(e)}', 'error')
    else:
        flash('Server manager not initialized', 'error')
    
    return redirect(url_for('mods'))

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

if __name__ == '__main__':
    # Initialize managers
    initialize_managers()
    
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    
    print("MCUS Web Server starting...")
    print("Open your browser and go to: http://localhost:3000")
    print("To share with friends, use your IP address instead of localhost")
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=3000, debug=True) 