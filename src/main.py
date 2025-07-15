import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import json
import os
import sys
import subprocess
import requests
import zipfile
import shutil
from pathlib import Path
import socket
import time
from datetime import datetime
import webbrowser
import logging

# Import our custom modules
from server_manager import ServerManager
from mod_manager import ModManager
from network_manager import NetworkManager, HostClient, HostInfo

class MinecraftServerHost:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("MCUS - Minecraft Unified Server")
        self.root.geometry("1200x800")
        self.root.configure(bg='#2b2b2b')
        
        # Server configuration
        self.server_config = {
            'server_name': 'MCUS Server',
            'max_players': 20,
            'port': 25565,
            'host_computers': [],
            'mods': [],
            'world_name': 'world',
            'network_port': 25566,
            'curseforge_api_key': ''
        }
        
        # Load configuration
        self.load_config()
        
        # Initialize managers
        self.server_manager = ServerManager(self.server_config)
        self.mod_manager = ModManager(Path("server/mods"))
        self.network_manager = NetworkManager(self.server_config.get('network_port', 25566))
        self.host_client = None
        
        # Set up mod manager
        self.mod_manager.set_minecraft_version("1.19.2")
        self.mod_manager.set_mod_loader("forge")
        
        # Create GUI
        self.create_gui()
        
        # Server process
        self.server_process = None
        self.is_hosting = False
        
        # Start network manager
        self.network_manager.start()
        
    def create_gui(self):
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create tabs
        self.create_dashboard_tab()
        self.create_hosting_tab()
        self.create_mods_tab()
        self.create_players_tab()
        self.create_settings_tab()
        
    def create_dashboard_tab(self):
        dashboard_frame = ttk.Frame(self.notebook)
        self.notebook.add(dashboard_frame, text="Dashboard")
        
        # Server status
        status_frame = ttk.LabelFrame(dashboard_frame, text="Server Status", padding=10)
        status_frame.pack(fill='x', padx=10, pady=5)
        
        self.status_label = ttk.Label(status_frame, text="Server Status: Offline", font=('Arial', 12))
        self.status_label.pack(side='left')
        
        self.start_stop_btn = ttk.Button(status_frame, text="Start Server", command=self.toggle_server)
        self.start_stop_btn.pack(side='right')
        
        # Active hosts
        hosts_frame = ttk.LabelFrame(dashboard_frame, text="Active Hosts", padding=10)
        hosts_frame.pack(fill='x', padx=10, pady=5)
        
        self.hosts_tree = ttk.Treeview(hosts_frame, columns=('name', 'status', 'players'), show='headings', height=5)
        self.hosts_tree.heading('name', text='Computer Name')
        self.hosts_tree.heading('status', text='Status')
        self.hosts_tree.heading('players', text='Players')
        self.hosts_tree.pack(fill='x')
        
        # Quick actions
        actions_frame = ttk.LabelFrame(dashboard_frame, text="Quick Actions", padding=10)
        actions_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(actions_frame, text="Add Host Computer", command=self.add_host_computer).pack(side='left', padx=5)
        ttk.Button(actions_frame, text="Backup World", command=self.backup_world).pack(side='left', padx=5)
        ttk.Button(actions_frame, text="Open Server Folder", command=self.open_server_folder).pack(side='left', padx=5)
        
    def create_hosting_tab(self):
        hosting_frame = ttk.Frame(self.notebook)
        self.notebook.add(hosting_frame, text="Hosting")
        
        # Host computer setup
        setup_frame = ttk.LabelFrame(hosting_frame, text="Host Computer Setup", padding=10)
        setup_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(setup_frame, text="Computer Name:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.host_name_entry = ttk.Entry(setup_frame, width=30)
        self.host_name_entry.grid(row=0, column=1, padx=5, pady=5)
        self.host_name_entry.insert(0, socket.gethostname())
        
        ttk.Button(setup_frame, text="Join Hosting Network", command=self.join_hosting_network).grid(row=0, column=2, padx=5, pady=5)
        
        # Host list
        host_list_frame = ttk.LabelFrame(hosting_frame, text="Connected Hosts", padding=10)
        host_list_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.host_list_tree = ttk.Treeview(host_list_frame, columns=('name', 'ip', 'status'), show='headings')
        self.host_list_tree.heading('name', text='Computer Name')
        self.host_list_tree.heading('ip', text='IP Address')
        self.host_list_tree.heading('status', text='Status')
        self.host_list_tree.pack(fill='both', expand=True)
        
        # Host controls
        host_controls_frame = ttk.Frame(hosting_frame)
        host_controls_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(host_controls_frame, text="Remove Host", command=self.remove_host).pack(side='left', padx=5)
        ttk.Button(host_controls_frame, text="Refresh Hosts", command=self.refresh_hosts).pack(side='left', padx=5)
        
    def create_mods_tab(self):
        mods_frame = ttk.Frame(self.notebook)
        self.notebook.add(mods_frame, text="Mods")
        
        # Mod installation
        install_frame = ttk.LabelFrame(mods_frame, text="Install Mods", padding=10)
        install_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(install_frame, text="Browse Mod Files", command=self.browse_mods).pack(side='left', padx=5)
        ttk.Button(install_frame, text="Search Modrinth", command=self.search_modrinth).pack(side='left', padx=5)
        ttk.Button(install_frame, text="Popular Mods", command=self.popular_mods).pack(side='left', padx=5)
        ttk.Button(install_frame, text="Install Forge", command=self.install_forge).pack(side='left', padx=5)
        
        # Installed mods
        mods_list_frame = ttk.LabelFrame(mods_frame, text="Installed Mods", padding=10)
        mods_list_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.mods_tree = ttk.Treeview(mods_list_frame, columns=('name', 'version', 'status'), show='headings')
        self.mods_tree.heading('name', text='Mod Name')
        self.mods_tree.heading('version', text='Version')
        self.mods_tree.heading('status', text='Status')
        self.mods_tree.pack(fill='both', expand=True)
        
        # Mod controls
        mod_controls_frame = ttk.Frame(mods_frame)
        mod_controls_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(mod_controls_frame, text="Remove Mod", command=self.remove_mod).pack(side='left', padx=5)
        ttk.Button(mod_controls_frame, text="Enable/Disable Mod", command=self.toggle_mod).pack(side='left', padx=5)
        ttk.Button(mod_controls_frame, text="Refresh Mods", command=self.refresh_mods).pack(side='left', padx=5)
        
    def create_players_tab(self):
        players_frame = ttk.Frame(self.notebook)
        self.notebook.add(players_frame, text="Players")
        
        # Online players
        online_frame = ttk.LabelFrame(players_frame, text="Online Players", padding=10)
        online_frame.pack(fill='x', padx=10, pady=5)
        
        self.players_tree = ttk.Treeview(online_frame, columns=('name', 'ping', 'host'), show='headings', height=8)
        self.players_tree.heading('name', text='Player Name')
        self.players_tree.heading('ping', text='Ping')
        self.players_tree.heading('host', text='Host Computer')
        self.players_tree.pack(fill='x')
        
        # Chat log
        chat_frame = ttk.LabelFrame(players_frame, text="Chat Log", padding=10)
        chat_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.chat_text = tk.Text(chat_frame, height=15, bg='#1e1e1e', fg='#ffffff')
        self.chat_text.pack(fill='both', expand=True)
        
        # Chat input
        chat_input_frame = ttk.Frame(players_frame)
        chat_input_frame.pack(fill='x', padx=10, pady=5)
        
        self.chat_entry = ttk.Entry(chat_input_frame)
        self.chat_entry.pack(side='left', fill='x', expand=True, padx=(0, 5))
        ttk.Button(chat_input_frame, text="Send", command=self.send_chat).pack(side='right')
        
    def create_settings_tab(self):
        settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(settings_frame, text="Settings")
        
        # Server settings
        server_settings_frame = ttk.LabelFrame(settings_frame, text="Server Settings", padding=10)
        server_settings_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(server_settings_frame, text="Server Name:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.server_name_entry = ttk.Entry(server_settings_frame, width=30)
        self.server_name_entry.grid(row=0, column=1, padx=5, pady=5)
        self.server_name_entry.insert(0, self.server_config['server_name'])
        
        ttk.Label(server_settings_frame, text="Max Players:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.max_players_entry = ttk.Entry(server_settings_frame, width=10)
        self.max_players_entry.grid(row=1, column=1, sticky='w', padx=5, pady=5)
        self.max_players_entry.insert(0, str(self.server_config['max_players']))
        
        ttk.Label(server_settings_frame, text="Port:").grid(row=2, column=0, sticky='w', padx=5, pady=5)
        self.port_entry = ttk.Entry(server_settings_frame, width=10)
        self.port_entry.grid(row=2, column=1, sticky='w', padx=5, pady=5)
        self.port_entry.insert(0, str(self.server_config['port']))
        
        ttk.Label(server_settings_frame, text="World Name:").grid(row=3, column=0, sticky='w', padx=5, pady=5)
        self.world_name_entry = ttk.Entry(server_settings_frame, width=30)
        self.world_name_entry.grid(row=3, column=1, padx=5, pady=5)
        self.world_name_entry.insert(0, self.server_config['world_name'])
        
        # Save button
        ttk.Button(server_settings_frame, text="Save Settings", command=self.save_settings).grid(row=4, column=1, sticky='w', padx=5, pady=10)
        
    def load_config(self):
        try:
            if os.path.exists('config.json'):
                with open('config.json', 'r') as f:
                    self.server_config.update(json.load(f))
        except:
            pass
            
    def save_config(self):
        with open('config.json', 'w') as f:
            json.dump(self.server_config, f, indent=2)
            
    def toggle_server(self):
        if not self.is_hosting:
            self.start_server()
        else:
            self.stop_server()
            
    def start_server(self):
        if self.server_manager.start_server():
            self.is_hosting = True
            self.status_label.config(text="Server Status: Online")
            self.start_stop_btn.config(text="Stop Server")
            
            # Update host status
            if self.host_client:
                self.host_client.update_status({
                    'status': 'online',
                    'players': [],
                    'memory_usage': 0.0,
                    'cpu_usage': 0.0
                })
        else:
            messagebox.showerror("Error", "Failed to start server. Check logs for details.")
        
    def stop_server(self):
        if self.server_manager.stop_server():
            self.is_hosting = False
            self.status_label.config(text="Server Status: Offline")
            self.start_stop_btn.config(text="Start Server")
            
            # Update host status
            if self.host_client:
                self.host_client.update_status({
                    'status': 'offline',
                    'players': [],
                    'memory_usage': 0.0,
                    'cpu_usage': 0.0
                })
        else:
            messagebox.showerror("Error", "Failed to stop server. Check logs for details.")
        
    def add_host_computer(self):
        # Open dialog to add host computer
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Host Computer")
        dialog.geometry("400x200")
        
        ttk.Label(dialog, text="Host IP:").grid(row=0, column=0, padx=5, pady=5)
        ip_entry = ttk.Entry(dialog, width=30)
        ip_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(dialog, text="Host Name:").grid(row=1, column=0, padx=5, pady=5)
        name_entry = ttk.Entry(dialog, width=30)
        name_entry.grid(row=1, column=1, padx=5, pady=5)
        
        def add_host():
            ip = ip_entry.get()
            name = name_entry.get()
            if ip and name:
                # Add to network manager
                self.network_manager.hosts[name] = HostInfo(
                    name=name,
                    ip=ip,
                    port=25565,
                    status='offline',
                    last_seen=datetime.now(),
                    players=[],
                    memory_usage=0.0,
                    cpu_usage=0.0
                )
                self.refresh_hosts()
                dialog.destroy()
            else:
                messagebox.showerror("Error", "Please enter both IP and name")
        
        ttk.Button(dialog, text="Add Host", command=add_host).grid(row=2, column=1, pady=10)
        
    def backup_world(self):
        if self.server_manager.backup_world():
            messagebox.showinfo("Success", "World backup created successfully!")
        else:
            messagebox.showerror("Error", "Failed to create world backup")
        
    def open_server_folder(self):
        server_path = Path("server")
        if server_path.exists():
            if sys.platform == "win32":
                os.startfile(str(server_path))
            else:
                subprocess.run(["xdg-open", str(server_path)])
        else:
            messagebox.showerror("Error", "Server folder not found")
        
    def join_hosting_network(self):
        host_name = self.host_name_entry.get()
        if not host_name:
            messagebox.showerror("Error", "Please enter a computer name")
            return
            
        # Get local IP
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
        except:
            local_ip = "127.0.0.1"
            
        # Create host client
        self.host_client = HostClient("127.0.0.1", self.server_config.get('network_port', 25566))
        
        if self.host_client.connect({
            'name': host_name,
            'ip': local_ip,
            'port': self.server_config.get('port', 25565)
        }):
            messagebox.showinfo("Success", f"Joined hosting network as {host_name}")
            self.refresh_hosts()
        else:
            messagebox.showerror("Error", "Failed to join hosting network")
        
    def remove_host(self):
        selection = self.host_list_tree.selection()
        if selection:
            host_name = self.host_list_tree.item(selection[0])['values'][0]
            if self.network_manager.remove_host(host_name):
                self.refresh_hosts()
                messagebox.showinfo("Success", f"Removed host: {host_name}")
            else:
                messagebox.showerror("Error", f"Failed to remove host: {host_name}")
        else:
            messagebox.showwarning("Warning", "Please select a host to remove")
        
    def refresh_hosts(self):
        # Clear existing items
        for item in self.host_list_tree.get_children():
            self.host_list_tree.delete(item)
            
        # Get hosts from network manager
        hosts = self.network_manager.get_hosts_status()
        for host in hosts:
            self.host_list_tree.insert('', 'end', values=(
                host['name'],
                host['ip'],
                host['status']
            ))
        
    def browse_mods(self):
        files = filedialog.askopenfilenames(
            title="Select Mod Files",
            filetypes=[("JAR files", "*.jar"), ("All files", "*.*")]
        )
        
        for file in files:
            if self.mod_manager.install_mod_from_file(file):
                messagebox.showinfo("Success", f"Installed mod: {Path(file).name}")
            else:
                messagebox.showerror("Error", f"Failed to install mod: {Path(file).name}")
                
        self.refresh_mods()
        
    def search_modrinth(self):
        # Open Modrinth search dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Search Modrinth")
        dialog.geometry("600x400")
        
        # Search frame
        search_frame = ttk.Frame(dialog)
        search_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(search_frame, text="Search:").pack(side='left')
        search_entry = ttk.Entry(search_frame, width=40)
        search_entry.pack(side='left', padx=5)
        
        # Results frame
        results_frame = ttk.Frame(dialog)
        results_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Results tree
        results_tree = ttk.Treeview(results_frame, columns=('name', 'author', 'downloads'), show='headings')
        results_tree.heading('name', text='Mod Name')
        results_tree.heading('author', text='Author')
        results_tree.heading('downloads', text='Downloads')
        results_tree.pack(fill='both', expand=True)
        
        def perform_search():
            query = search_entry.get()
            if query:
                # Clear existing results
                for item in results_tree.get_children():
                    results_tree.delete(item)
                
                # Search Modrinth
                mods = self.mod_manager.search_modrinth_mods(query, 20)
                for mod in mods:
                    results_tree.insert('', 'end', values=(
                        mod['name'],
                        mod['author'],
                        f"{mod['downloads']:,}"
                    ), tags=(mod['id'],))
        
        def download_selected():
            selection = results_tree.selection()
            if selection:
                mod_id = results_tree.item(selection[0], 'tags')[0]
                # Get the mod info to find latest version
                mods = self.mod_manager.search_modrinth_mods("", 100)  # Get all mods to find the one
                for mod in mods:
                    if mod['id'] == mod_id and mod['latest_version']:
                        if self.mod_manager.download_mod_from_modrinth(mod_id, mod['latest_version']['id']):
                            messagebox.showinfo("Success", f"Downloaded {mod['name']}")
                            self.refresh_mods()
                        else:
                            messagebox.showerror("Error", f"Failed to download {mod['name']}")
                        break
            else:
                messagebox.showwarning("Warning", "Please select a mod to download")
        
        ttk.Button(search_frame, text="Search", command=perform_search).pack(side='left', padx=5)
        ttk.Button(results_frame, text="Download Selected", command=download_selected).pack(pady=5)
        
    def popular_mods(self):
        # Open popular mods dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Popular Mods")
        dialog.geometry("600x400")
        
        # Results frame
        results_frame = ttk.Frame(dialog)
        results_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Results tree
        results_tree = ttk.Treeview(results_frame, columns=('name', 'author', 'downloads'), show='headings')
        results_tree.heading('name', text='Mod Name')
        results_tree.heading('author', text='Author')
        results_tree.heading('downloads', text='Downloads')
        results_tree.pack(fill='both', expand=True)
        
        def load_popular():
            # Clear existing results
            for item in results_tree.get_children():
                results_tree.delete(item)
            
            # Get popular mods
            mods = self.mod_manager.get_popular_modrinth_mods(20)
            for mod in mods:
                results_tree.insert('', 'end', values=(
                    mod['name'],
                    mod['author'],
                    f"{mod['downloads']:,}"
                ), tags=(mod['id'],))
        
        def download_selected():
            selection = results_tree.selection()
            if selection:
                mod_id = results_tree.item(selection[0], 'tags')[0]
                # Get the mod info to find latest version
                mods = self.mod_manager.get_popular_modrinth_mods(100)  # Get all mods to find the one
                for mod in mods:
                    if mod['id'] == mod_id and mod['latest_version']:
                        if self.mod_manager.download_mod_from_modrinth(mod_id, mod['latest_version']['id']):
                            messagebox.showinfo("Success", f"Downloaded {mod['name']}")
                            self.refresh_mods()
                        else:
                            messagebox.showerror("Error", f"Failed to download {mod['name']}")
                        break
            else:
                messagebox.showwarning("Warning", "Please select a mod to download")
        
        ttk.Button(results_frame, text="Load Popular Mods", command=load_popular).pack(pady=5)
        ttk.Button(results_frame, text="Download Selected", command=download_selected).pack(pady=5)
        
        # Load popular mods automatically
        load_popular()
        
    def install_forge(self):
        if self.server_manager.install_forge():
            messagebox.showinfo("Success", "Forge installed successfully!")
        else:
            messagebox.showerror("Error", "Failed to install Forge")
        
    def remove_mod(self):
        selection = self.mods_tree.selection()
        if selection:
            mod_name = self.mods_tree.item(selection[0])['values'][0]
            if self.mod_manager.remove_mod(mod_name):
                self.refresh_mods()
                messagebox.showinfo("Success", f"Removed mod: {mod_name}")
            else:
                messagebox.showerror("Error", f"Failed to remove mod: {mod_name}")
        else:
            messagebox.showwarning("Warning", "Please select a mod to remove")
        
    def toggle_mod(self):
        selection = self.mods_tree.selection()
        if selection:
            mod_name = self.mods_tree.item(selection[0])['values'][0]
            status = self.mods_tree.item(selection[0])['values'][2]
            
            if status == "Enabled":
                if self.mod_manager.disable_mod(mod_name):
                    self.refresh_mods()
                    messagebox.showinfo("Success", f"Disabled mod: {mod_name}")
            else:
                if self.mod_manager.enable_mod(mod_name):
                    self.refresh_mods()
                    messagebox.showinfo("Success", f"Enabled mod: {mod_name}")
        else:
            messagebox.showwarning("Warning", "Please select a mod to toggle")
        
    def refresh_mods(self):
        # Clear existing items
        for item in self.mods_tree.get_children():
            self.mods_tree.delete(item)
            
        # Get mods from mod manager
        mods = self.mod_manager.get_installed_mods()
        for mod in mods:
            self.mods_tree.insert('', 'end', values=(
                mod['name'],
                f"{mod['size'] / 1024 / 1024:.1f} MB",
                "Enabled" if mod['enabled'] else "Disabled"
            ))
        
    def send_chat(self):
        message = self.chat_entry.get()
        if message:
            # Send command to server
            if self.server_manager.send_server_command(f"say {message}"):
                # Add to chat log
                timestamp = datetime.now().strftime("%H:%M:%S")
                self.chat_text.insert('end', f"[{timestamp}] Console: {message}\n")
                self.chat_text.see('end')
                self.chat_entry.delete(0, 'end')
            else:
                messagebox.showerror("Error", "Failed to send message")
        
    def save_settings(self):
        # Save current settings
        self.server_config['server_name'] = self.server_name_entry.get()
        self.server_config['max_players'] = int(self.max_players_entry.get())
        self.server_config['port'] = int(self.port_entry.get())
        self.server_config['world_name'] = self.world_name_entry.get()
        self.save_config()
        messagebox.showinfo("Settings", "Settings saved successfully!")
        
    def run(self):
        try:
            self.root.mainloop()
        finally:
            # Cleanup on exit
            if self.host_client:
                self.host_client.disconnect()
            if self.network_manager:
                self.network_manager.stop()
            if self.is_hosting:
                self.server_manager.stop_server()

if __name__ == "__main__":
    app = MinecraftServerHost()
    app.run() 