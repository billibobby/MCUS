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
import sys

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
    """Show popular mods from Modrinth"""
    # Comprehensive popular mods with detailed information
    popular_mods_data = {
        'tech': {
            'name': 'Technology & Automation',
            'icon': 'fas fa-cogs',
            'color': 'primary',
            'description': 'Automation, machines, and technological advancements',
            'mods': [
                {
                    'id': 'create',
                    'name': 'Create',
                    'description': 'Adds mechanical power and automation to Minecraft',
                    'downloads': '5.2M',
                    'followers': '125K',
                    'versions': ['1.20.1', '1.19.2', '1.18.2'],
                    'categories': ['tech', 'automation'],
                    'icon_url': 'https://cdn.modrinth.com/data/X1zDcYw9/icon.png',
                    'author': 'simibubi',
                    'rating': 4.9
                },
                {
                    'id': 'mekanism',
                    'name': 'Mekanism',
                    'description': 'High-tech machinery, automation, and energy systems',
                    'downloads': '8.1M',
                    'followers': '200K',
                    'versions': ['1.20.1', '1.19.2', '1.18.2', '1.16.5'],
                    'categories': ['tech', 'automation', 'energy'],
                    'icon_url': 'https://cdn.modrinth.com/data/HnFTFcuf/icon.png',
                    'author': 'aidancbrady',
                    'rating': 4.8
                },
                {
                    'id': 'thermal-expansion',
                    'name': 'Thermal Expansion',
                    'description': 'Technology mod with machines, automation, and energy',
                    'downloads': '3.8M',
                    'followers': '95K',
                    'versions': ['1.19.2', '1.18.2', '1.16.5'],
                    'categories': ['tech', 'automation'],
                    'icon_url': 'https://cdn.modrinth.com/data/thermal-expansion/icon.png',
                    'author': 'TeamCoFH',
                    'rating': 4.7
                },
                {
                    'id': 'industrial-foregoing',
                    'name': 'Industrial Foregoing',
                    'description': 'Industrial automation and resource processing',
                    'downloads': '2.9M',
                    'followers': '75K',
                    'versions': ['1.19.2', '1.18.2', '1.16.5'],
                    'categories': ['tech', 'automation'],
                    'icon_url': 'https://cdn.modrinth.com/data/industrial-foregoing/icon.png',
                    'author': 'Buuz135',
                    'rating': 4.6
                }
            ]
        },
        'magic': {
            'name': 'Magic & Fantasy',
            'icon': 'fas fa-magic',
            'color': 'purple',
            'description': 'Magical spells, rituals, and mystical content',
            'mods': [
                {
                    'id': 'botania',
                    'name': 'Botania',
                    'description': 'Nature magic mod with flowers, spells, and automation',
                    'downloads': '4.5M',
                    'followers': '110K',
                    'versions': ['1.20.1', '1.19.2', '1.18.2', '1.16.5'],
                    'categories': ['magic', 'nature'],
                    'icon_url': 'https://cdn.modrinth.com/data/botania/icon.png',
                    'author': 'Vazkii',
                    'rating': 4.9
                },
                {
                    'id': 'thaumcraft',
                    'name': 'Thaumcraft',
                    'description': 'Magic research and arcane technology',
                    'downloads': '6.2M',
                    'followers': '150K',
                    'versions': ['1.12.2'],
                    'categories': ['magic', 'research'],
                    'icon_url': 'https://cdn.modrinth.com/data/thaumcraft/icon.png',
                    'author': 'Azanor',
                    'rating': 4.8
                },
                {
                    'id': 'astral-sorcery',
                    'name': 'Astral Sorcery',
                    'description': 'Starlight magic and celestial rituals',
                    'downloads': '3.1M',
                    'followers': '85K',
                    'versions': ['1.19.2', '1.18.2', '1.16.5'],
                    'categories': ['magic', 'celestial'],
                    'icon_url': 'https://cdn.modrinth.com/data/astral-sorcery/icon.png',
                    'author': 'HellFirePvP',
                    'rating': 4.7
                },
                {
                    'id': 'blood-magic',
                    'name': 'Blood Magic',
                    'description': 'Dark magic using blood and life essence',
                    'downloads': '2.8M',
                    'followers': '70K',
                    'versions': ['1.19.2', '1.18.2', '1.16.5'],
                    'categories': ['magic', 'dark'],
                    'icon_url': 'https://cdn.modrinth.com/data/blood-magic/icon.png',
                    'author': 'WayofTime',
                    'rating': 4.6
                }
            ]
        },
        'adventure': {
            'name': 'Adventure & Exploration',
            'icon': 'fas fa-compass',
            'color': 'success',
            'description': 'Dungeons, structures, and exploration content',
            'mods': [
                {
                    'id': 'dungeons-plus',
                    'name': 'Dungeons Plus',
                    'description': 'Enhanced dungeons and adventure structures',
                    'downloads': '1.8M',
                    'followers': '45K',
                    'versions': ['1.20.1', '1.19.2', '1.18.2'],
                    'categories': ['adventure', 'dungeons'],
                    'icon_url': 'https://cdn.modrinth.com/data/dungeons-plus/icon.png',
                    'author': 'ModdingLegacy',
                    'rating': 4.5
                },
                {
                    'id': 'biomes-o-plenty',
                    'name': 'Biomes O\' Plenty',
                    'description': 'Adds 80+ new biomes and world generation',
                    'downloads': '7.5M',
                    'followers': '180K',
                    'versions': ['1.20.1', '1.19.2', '1.18.2', '1.16.5'],
                    'categories': ['worldgen', 'biomes'],
                    'icon_url': 'https://cdn.modrinth.com/data/biomes-o-plenty/icon.png',
                    'author': 'Forstride',
                    'rating': 4.8
                },
                {
                    'id': 'quark',
                    'name': 'Quark',
                    'description': 'Small improvements and features to vanilla Minecraft',
                    'downloads': '9.2M',
                    'followers': '220K',
                    'versions': ['1.20.1', '1.19.2', '1.18.2', '1.16.5'],
                    'categories': ['vanilla+', 'improvements'],
                    'icon_url': 'https://cdn.modrinth.com/data/quark/icon.png',
                    'author': 'Vazkii',
                    'rating': 4.9
                },
                {
                    'id': 'waystones',
                    'name': 'Waystones',
                    'description': 'Teleportation system with waystone blocks',
                    'downloads': '3.3M',
                    'followers': '90K',
                    'versions': ['1.20.1', '1.19.2', '1.18.2'],
                    'categories': ['utility', 'teleportation'],
                    'icon_url': 'https://cdn.modrinth.com/data/waystones/icon.png',
                    'author': 'BlayTheNinth',
                    'rating': 4.7
                }
            ]
        },
        'storage': {
            'name': 'Storage & Organization',
            'icon': 'fas fa-boxes',
            'color': 'warning',
            'description': 'Storage solutions and inventory management',
            'mods': [
                {
                    'id': 'refined-storage',
                    'name': 'Refined Storage',
                    'description': 'Digital storage system with wireless access',
                    'downloads': '4.8M',
                    'followers': '120K',
                    'versions': ['1.19.2', '1.18.2', '1.16.5'],
                    'categories': ['storage', 'digital'],
                    'icon_url': 'https://cdn.modrinth.com/data/refined-storage/icon.png',
                    'author': 'raoulvdberge',
                    'rating': 4.8
                },
                {
                    'id': 'applied-energistics-2',
                    'name': 'Applied Energistics 2',
                    'description': 'Digital storage and automation network',
                    'downloads': '6.5M',
                    'followers': '160K',
                    'versions': ['1.19.2', '1.18.2', '1.16.5'],
                    'categories': ['storage', 'automation'],
                    'icon_url': 'https://cdn.modrinth.com/data/applied-energistics-2/icon.png',
                    'author': 'AlgorithmX2',
                    'rating': 4.9
                },
                {
                    'id': 'iron-chests',
                    'name': 'Iron Chests',
                    'description': 'Upgradable chests with more storage capacity',
                    'downloads': '2.1M',
                    'followers': '55K',
                    'versions': ['1.20.1', '1.19.2', '1.18.2', '1.16.5'],
                    'categories': ['storage', 'chests'],
                    'icon_url': 'https://cdn.modrinth.com/data/iron-chests/icon.png',
                    'author': 'ProgWML6',
                    'rating': 4.6
                },
                {
                    'id': 'storage-drawers',
                    'name': 'Storage Drawers',
                    'description': 'Compact storage with visual item display',
                    'downloads': '3.7M',
                    'followers': '95K',
                    'versions': ['1.20.1', '1.19.2', '1.18.2', '1.16.5'],
                    'categories': ['storage', 'drawers'],
                    'icon_url': 'https://cdn.modrinth.com/data/storage-drawers/icon.png',
                    'author': 'Texelsaur',
                    'rating': 4.7
                }
            ]
        },
        'food': {
            'name': 'Food & Agriculture',
            'icon': 'fas fa-utensils',
            'color': 'info',
            'description': 'Cooking, farming, and food-related content',
            'mods': [
                {
                    'id': 'pam-harvestcraft',
                    'name': 'Pam\'s HarvestCraft 2',
                    'description': 'Expanded farming and cooking with 1000+ items',
                    'downloads': '5.9M',
                    'followers': '140K',
                    'versions': ['1.19.2', '1.18.2', '1.16.5'],
                    'categories': ['food', 'farming'],
                    'icon_url': 'https://cdn.modrinth.com/data/pams-harvestcraft-2/icon.png',
                    'author': 'PamelaCollins',
                    'rating': 4.8
                },
                {
                    'id': 'cooking-for-blockheads',
                    'name': 'Cooking for Blockheads',
                    'description': 'Kitchen automation and cooking tools',
                    'downloads': '2.4M',
                    'followers': '65K',
                    'versions': ['1.20.1', '1.19.2', '1.18.2', '1.16.5'],
                    'categories': ['food', 'automation'],
                    'icon_url': 'https://cdn.modrinth.com/data/cooking-for-blockheads/icon.png',
                    'author': 'BlayTheNinth',
                    'rating': 4.7
                },
                {
                    'id': 'farmer-delight',
                    'name': 'Farmer\'s Delight',
                    'description': 'Enhanced farming and cooking mechanics',
                    'downloads': '1.9M',
                    'followers': '50K',
                    'versions': ['1.20.1', '1.19.2', '1.18.2'],
                    'categories': ['food', 'farming'],
                    'icon_url': 'https://cdn.modrinth.com/data/farmers-delight/icon.png',
                    'author': 'vectorwing',
                    'rating': 4.6
                },
                {
                    'id': 'simple-farming',
                    'name': 'Simple Farming',
                    'description': 'Simple and balanced farming additions',
                    'downloads': '1.2M',
                    'followers': '35K',
                    'versions': ['1.20.1', '1.19.2', '1.18.2'],
                    'categories': ['food', 'farming'],
                    'icon_url': 'https://cdn.modrinth.com/data/simple-farming/icon.png',
                    'author': 'enemeez1',
                    'rating': 4.5
                }
            ]
        },
        'decorative': {
            'name': 'Decorative & Building',
            'icon': 'fas fa-paint-brush',
            'color': 'secondary',
            'description': 'Building blocks, furniture, and decorative items',
            'mods': [
                {
                    'id': 'chisel',
                    'name': 'Chisel',
                    'description': 'Decorative blocks and building variations',
                    'downloads': '4.2M',
                    'followers': '105K',
                    'versions': ['1.19.2', '1.18.2', '1.16.5'],
                    'categories': ['decorative', 'building'],
                    'icon_url': 'https://cdn.modrinth.com/data/chisel/icon.png',
                    'author': 'tterrag1098',
                    'rating': 4.7
                },
                {
                    'id': 'bibliocraft',
                    'name': 'BiblioCraft',
                    'description': 'Furniture and decorative items for builders',
                    'downloads': '3.6M',
                    'followers': '90K',
                    'versions': ['1.19.2', '1.18.2', '1.16.5'],
                    'categories': ['decorative', 'furniture'],
                    'icon_url': 'https://cdn.modrinth.com/data/bibliocraft/icon.png',
                    'author': 'Nuchaz',
                    'rating': 4.6
                },
                {
                    'id': 'decorative-blocks',
                    'name': 'Decorative Blocks',
                    'description': 'Additional decorative blocks and building materials',
                    'downloads': '2.8M',
                    'followers': '75K',
                    'versions': ['1.20.1', '1.19.2', '1.18.2'],
                    'categories': ['decorative', 'building'],
                    'icon_url': 'https://cdn.modrinth.com/data/decorative-blocks/icon.png',
                    'author': 'stohun',
                    'rating': 4.5
                },
                {
                    'id': 'building-gadgets',
                    'name': 'Building Gadgets',
                    'description': 'Tools for faster and easier building',
                    'downloads': '3.1M',
                    'followers': '85K',
                    'versions': ['1.19.2', '1.18.2', '1.16.5'],
                    'categories': ['utility', 'building'],
                    'icon_url': 'https://cdn.modrinth.com/data/building-gadgets/icon.png',
                    'author': 'Direwolf20',
                    'rating': 4.8
                }
            ]
        }
    }
    
    return render_template('popular_mods.html', categories=popular_mods_data)

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
    global server_manager
    
    if server_manager:
        try:
            # Check if Forge is already installed
            server_jar = server_manager.find_server_jar()
            if server_jar:
                flash('Forge is already installed!', 'info')
                return redirect(url_for('mods'))
            
            # Redirect to version selection page
            return redirect(url_for('select_forge_version'))
            
        except Exception as e:
            flash(f'Error checking Forge installation: {str(e)}', 'error')
    else:
        flash('Server manager not initialized', 'error')
    
    return redirect(url_for('mods'))

@app.route('/select_forge_version')
def select_forge_version():
    """Show Forge version selection page"""
    # Comprehensive Minecraft versions and their Forge builds with detailed information
    forge_versions = {
        '1.20.4': {
            'name': 'Minecraft 1.20.4',
            'status': 'Latest Stable',
            'recommended': '49.0.3',
            'latest': '49.0.3',
            'builds': [
                {'version': '49.0.3', 'type': 'recommended', 'date': '2024-01-15', 'notes': 'Latest stable build'},
                {'version': '49.0.2', 'type': 'stable', 'date': '2024-01-10', 'notes': 'Previous stable'},
                {'version': '49.0.1', 'type': 'stable', 'date': '2024-01-05', 'notes': 'Bug fixes'},
                {'version': '49.0.0', 'type': 'stable', 'date': '2024-01-01', 'notes': 'Initial release'}
            ],
            'description': 'Latest Minecraft version with newest features and mods',
            'mod_count': '5000+',
            'java_version': '17+',
            'performance': 'Excellent',
            'stability': 'Very Stable'
        },
        '1.20.1': {
            'name': 'Minecraft 1.20.1',
            'status': 'Popular',
            'recommended': '47.1.0',
            'latest': '47.2.0',
            'builds': [
                {'version': '47.1.0', 'type': 'recommended', 'date': '2023-06-15', 'notes': 'Most stable for mods'},
                {'version': '47.2.0', 'type': 'latest', 'date': '2023-06-20', 'notes': 'Latest features'},
                {'version': '47.0.0', 'type': 'stable', 'date': '2023-06-10', 'notes': 'Initial release'},
                {'version': '46.0.0', 'type': 'stable', 'date': '2023-06-05', 'notes': 'Previous major'}
            ],
            'description': 'Popular version with excellent mod support and stability',
            'mod_count': '4000+',
            'java_version': '17+',
            'performance': 'Very Good',
            'stability': 'Very Stable'
        },
        '1.19.2': {
            'name': 'Minecraft 1.19.2',
            'status': 'Recommended',
            'recommended': '43.2.0',
            'latest': '43.3.0',
            'builds': [
                {'version': '43.2.0', 'type': 'recommended', 'date': '2022-08-15', 'notes': 'Most stable for modpacks'},
                {'version': '43.3.0', 'type': 'latest', 'date': '2022-08-20', 'notes': 'Latest features'},
                {'version': '43.1.0', 'type': 'stable', 'date': '2022-08-10', 'notes': 'Bug fixes'},
                {'version': '43.0.0', 'type': 'stable', 'date': '2022-08-05', 'notes': 'Initial release'}
            ],
            'description': 'Most stable version with extensive mod library and community support',
            'mod_count': '6000+',
            'java_version': '17+',
            'performance': 'Excellent',
            'stability': 'Extremely Stable'
        },
        '1.18.2': {
            'name': 'Minecraft 1.18.2',
            'status': 'LTS',
            'recommended': '40.2.0',
            'latest': '40.2.0',
            'builds': [
                {'version': '40.2.0', 'type': 'recommended', 'date': '2022-02-15', 'notes': 'Long-term support'},
                {'version': '40.1.0', 'type': 'stable', 'date': '2022-02-10', 'notes': 'Previous stable'},
                {'version': '40.0.0', 'type': 'stable', 'date': '2022-02-05', 'notes': 'Initial release'},
                {'version': '39.0.0', 'type': 'stable', 'date': '2022-01-30', 'notes': 'Previous major'}
            ],
            'description': 'Long-term support version with mature mod ecosystem',
            'mod_count': '3500+',
            'java_version': '17+',
            'performance': 'Very Good',
            'stability': 'Very Stable'
        },
        '1.16.5': {
            'name': 'Minecraft 1.16.5',
            'status': 'Legacy',
            'recommended': '36.2.0',
            'latest': '36.2.0',
            'builds': [
                {'version': '36.2.0', 'type': 'recommended', 'date': '2021-03-15', 'notes': 'Final stable'},
                {'version': '36.1.0', 'type': 'stable', 'date': '2021-03-10', 'notes': 'Previous stable'},
                {'version': '36.0.0', 'type': 'stable', 'date': '2021-03-05', 'notes': 'Initial release'},
                {'version': '35.0.0', 'type': 'stable', 'date': '2021-02-28', 'notes': 'Previous major'}
            ],
            'description': 'Legacy version with classic mods and established modpacks',
            'mod_count': '2500+',
            'java_version': '8+',
            'performance': 'Good',
            'stability': 'Stable'
        },
        '1.12.2': {
            'name': 'Minecraft 1.12.2',
            'status': 'Classic',
            'recommended': '14.23.5.2855',
            'latest': '14.23.5.2855',
            'builds': [
                {'version': '14.23.5.2855', 'type': 'recommended', 'date': '2018-01-15', 'notes': 'Final stable'},
                {'version': '14.23.5.2854', 'type': 'stable', 'date': '2018-01-10', 'notes': 'Previous stable'},
                {'version': '14.23.5.2853', 'type': 'stable', 'date': '2018-01-05', 'notes': 'Bug fixes'},
                {'version': '14.23.5.2852', 'type': 'stable', 'date': '2018-01-01', 'notes': 'Previous major'}
            ],
            'description': 'Classic version with legendary mods and nostalgic modpacks',
            'mod_count': '1500+',
            'java_version': '8',
            'performance': 'Good',
            'stability': 'Stable'
        }
    }
    
    return render_template('select_forge_version.html', forge_versions=forge_versions)

@app.route('/install_forge_version', methods=['POST'])
def install_forge_version():
    """Install specific Forge version"""
    global server_manager
    
    if not server_manager:
        flash('Server manager not initialized', 'error')
        return redirect(url_for('mods'))
    
    minecraft_version = request.form.get('minecraft_version')
    forge_build = request.form.get('forge_build')
    
    if not minecraft_version or not forge_build:
        flash('Please select both Minecraft version and Forge build', 'error')
        return redirect(url_for('select_forge_version'))
    
    try:
        # Check if Forge is already installed
        server_jar = server_manager.find_server_jar()
        if server_jar:
            flash('Forge is already installed!', 'info')
            return redirect(url_for('mods'))
        
        flash(f'Installing Forge {minecraft_version}-{forge_build}... This may take a few minutes. Please wait.', 'info')
        
        if server_manager.install_forge_specific(minecraft_version, forge_build):
            flash(f'Forge {minecraft_version}-{forge_build} installed successfully! You can now start your server.', 'success')
        else:
            flash(f'Failed to install Forge {minecraft_version}-{forge_build}. Please try a different version or download manually from https://files.minecraftforge.net/', 'error')
    except Exception as e:
        flash(f'Error installing Forge: {str(e)}', 'error')
    
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

@app.route('/diagnostics')
def diagnostics():
    """Show detailed system diagnostics"""
    diagnostics_info = get_startup_diagnostics()
    
    # Get additional system information
    system_info = {
        'platform': os.name,
        'python_version': sys.version,
        'current_directory': os.getcwd(),
        'server_directory': str(Path("server").absolute()),
        'server_directory_exists': Path("server").exists(),
        'server_directory_writable': False,
        'java_path': None,
        'java_version': None,
        'memory_total': None,
        'memory_available': None,
        'disk_total': None,
        'disk_free': None
    }
    
    # Check server directory permissions
    try:
        server_dir = Path("server")
        test_file = server_dir / ".test_write"
        test_file.write_text("test")
        test_file.unlink()
        system_info['server_directory_writable'] = True
    except:
        pass
    
    # Get Java information
    try:
        result = subprocess.run(['java', '-version'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            system_info['java_path'] = 'java'
            import re
            version_match = re.search(r'"([^"]+)"', result.stderr)
            if version_match:
                system_info['java_version'] = version_match.group(1)
    except:
        pass
    
    # Get system resources
    try:
        import psutil
        memory = psutil.virtual_memory()
        system_info['memory_total'] = f"{memory.total // (1024**3)}GB"
        system_info['memory_available'] = f"{memory.available // (1024**3)}GB"
        
        disk = psutil.disk_usage(str(Path("server")))
        system_info['disk_total'] = f"{disk.total // (1024**3)}GB"
        system_info['disk_free'] = f"{disk.free // (1024**3)}GB"
    except ImportError:
        pass
    
    return render_template('diagnostics.html', diagnostics=diagnostics_info, system_info=system_info)

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
    
    project = mod_manager.get_modrinth_project_details(project_id) if mod_manager else None
    if not project:
        flash('Project not found', 'error')
        return redirect(url_for('browse_modrinth'))
    
    return render_template('modrinth_project.html', project=project)

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