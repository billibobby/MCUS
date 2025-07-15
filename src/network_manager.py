import socket
import threading
import json
import time
import logging
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
import struct
import requests

@dataclass
class HostInfo:
    name: str
    ip: str
    port: int
    status: str
    last_seen: datetime
    players: List[str]
    memory_usage: float
    cpu_usage: float

class NetworkManager:
    def __init__(self, port: int = 25566, mode: str = "peer"):
        self.port = port
        self.mode = mode  # "peer" or "central"
        self.hosts: Dict[str, HostInfo] = {}
        self.is_running = False
        self.server_socket = None
        self.message_handlers: Dict[str, Callable] = {}
        self.heartbeat_interval = 30  # seconds
        self.host_timeout = 90  # seconds
        self.peer_connections: Dict[str, socket.socket] = {}
        self.peer_ips: List[str] = []
        
        # Register message handlers
        self.register_handlers()
        
    def register_handlers(self):
        """Register message handlers for different message types"""
        self.message_handlers = {
            'register': self.handle_register,
            'heartbeat': self.handle_heartbeat,
            'status_update': self.handle_status_update,
            'player_join': self.handle_player_join,
            'player_leave': self.handle_player_leave,
            'server_command': self.handle_server_command,
            'failover_request': self.handle_failover_request,
            'peer_discovery': self.handle_peer_discovery,
            'peer_sync': self.handle_peer_sync
        }
        
    def start(self):
        """Start the network manager"""
        if self.is_running:
            return False
            
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('', self.port))
            self.server_socket.listen(5)
            
            self.is_running = True
            
            # Start listening thread
            threading.Thread(target=self.listen_for_connections, daemon=True).start()
            
            # Start heartbeat monitoring thread
            threading.Thread(target=self.monitor_heartbeats, daemon=True).start()
            
            # Start peer discovery thread (for peer mode)
            if self.mode == "peer":
                threading.Thread(target=self.discover_peers, daemon=True).start()
                threading.Thread(target=self.broadcast_to_peers, daemon=True).start()
            
            logging.info(f"Network manager started on port {self.port} in {self.mode} mode")
            return True
            
        except Exception as e:
            logging.error(f"Failed to start network manager: {e}")
            return False
            
    def stop(self):
        """Stop the network manager"""
        self.is_running = False
        if self.server_socket:
            self.server_socket.close()
        logging.info("Network manager stopped")
        
    def listen_for_connections(self):
        """Listen for incoming connections from host computers"""
        while self.is_running and self.server_socket:
            try:
                client_socket, address = self.server_socket.accept()
                logging.info(f"Connection from {address}")
                
                # Handle client in separate thread
                threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, address),
                    daemon=True
                ).start()
                
            except Exception as e:
                if self.is_running:
                    logging.error(f"Error accepting connection: {e}")
                    
    def handle_client(self, client_socket: socket.socket, address: tuple):
        """Handle communication with a client"""
        try:
            while self.is_running:
                # Receive message length
                length_data = client_socket.recv(4)
                if not length_data:
                    break
                    
                message_length = struct.unpack('!I', length_data)[0]
                
                # Receive message data
                message_data = b''
                while len(message_data) < message_length:
                    chunk = client_socket.recv(message_length - len(message_data))
                    if not chunk:
                        break
                    message_data += chunk
                    
                if len(message_data) < message_length:
                    break
                    
                # Parse and handle message
                message = json.loads(message_data.decode('utf-8'))
                self.handle_message(message, client_socket)
                
        except Exception as e:
            logging.error(f"Error handling client {address}: {e}")
        finally:
            client_socket.close()
            
    def handle_message(self, message: Dict, client_socket: socket.socket):
        """Handle incoming message"""
        try:
            message_type = message.get('type')
            if message_type in self.message_handlers:
                response = self.message_handlers[message_type](message)
                if response:
                    self.send_message(client_socket, response)
            else:
                logging.warning(f"Unknown message type: {message_type}")
                
        except Exception as e:
            logging.error(f"Error handling message: {e}")
            
    def send_message(self, client_socket: socket.socket, message: Dict):
        """Send message to client"""
        try:
            message_data = json.dumps(message).encode('utf-8')
            message_length = struct.pack('!I', len(message_data))
            client_socket.send(message_length + message_data)
        except Exception as e:
            logging.error(f"Error sending message: {e}")
            
    def handle_register(self, message: Dict) -> Optional[Dict]:
        """Handle host registration"""
        host_info = message.get('host_info', {})
        host_name = host_info.get('name')
        host_ip = host_info.get('ip')
        host_port = host_info.get('port', 25565)
        
        if not host_name or not host_ip:
            return {'type': 'error', 'message': 'Missing host information'}
            
        # Create or update host info
        self.hosts[host_name] = HostInfo(
            name=host_name,
            ip=host_ip,
            port=host_port,
            status='online',
            last_seen=datetime.now(),
            players=[],
            memory_usage=0.0,
            cpu_usage=0.0
        )
        
        logging.info(f"Host registered: {host_name} ({host_ip}:{host_port})")
        
        return {
            'type': 'register_response',
            'success': True,
            'message': 'Host registered successfully'
        }
        
    def handle_heartbeat(self, message: Dict) -> Optional[Dict]:
        """Handle heartbeat from host"""
        host_name = message.get('host_name')
        if host_name in self.hosts:
            self.hosts[host_name].last_seen = datetime.now()
            self.hosts[host_name].status = 'online'
            
        return {'type': 'heartbeat_response', 'success': True}
        
    def handle_status_update(self, message: Dict) -> Optional[Dict]:
        """Handle status update from host"""
        host_name = message.get('host_name')
        if host_name in self.hosts:
            host = self.hosts[host_name]
            host.players = message.get('players', [])
            host.memory_usage = message.get('memory_usage', 0.0)
            host.cpu_usage = message.get('cpu_usage', 0.0)
            host.status = message.get('status', 'online')
            
        return {'type': 'status_update_response', 'success': True}
        
    def handle_player_join(self, message: Dict) -> Optional[Dict]:
        """Handle player join notification"""
        host_name = message.get('host_name')
        player_name = message.get('player_name')
        
        if host_name in self.hosts and player_name:
            if player_name not in self.hosts[host_name].players:
                self.hosts[host_name].players.append(player_name)
                logging.info(f"Player {player_name} joined on {host_name}")
                
        return {'type': 'player_join_response', 'success': True}
        
    def handle_player_leave(self, message: Dict) -> Optional[Dict]:
        """Handle player leave notification"""
        host_name = message.get('host_name')
        player_name = message.get('player_name')
        
        if host_name in self.hosts and player_name:
            if player_name in self.hosts[host_name].players:
                self.hosts[host_name].players.remove(player_name)
                logging.info(f"Player {player_name} left from {host_name}")
                
        return {'type': 'player_leave_response', 'success': True}
        
    def handle_server_command(self, message: Dict) -> Optional[Dict]:
        """Handle server command from another host"""
        command = message.get('command')
        if command:
            logging.info(f"Received server command: {command}")
            # This would be handled by the server manager
            return {'type': 'command_response', 'success': True}
            
        return {'type': 'error', 'message': 'No command specified'}
        
    def handle_failover_request(self, message: Dict) -> Optional[Dict]:
        """Handle failover request"""
        requesting_host = message.get('host_name')
        logging.info(f"Failover requested by {requesting_host}")
        
        # Find next available host
        next_host = self.select_next_host(requesting_host)
        
        if next_host:
            return {
                'type': 'failover_response',
                'success': True,
                'next_host': {
                    'name': next_host.name,
                    'ip': next_host.ip,
                    'port': next_host.port
                }
            }
        else:
            return {
                'type': 'failover_response',
                'success': False,
                'message': 'No available hosts for failover'
            }
            
    def handle_peer_discovery(self, message: Dict) -> Optional[Dict]:
        """Handle peer discovery message"""
        peer_hosts = message.get('hosts', [])
        for host_data in peer_hosts:
            host_name = host_data['name']
            if host_name not in self.hosts:
                # Add new host from peer
                self.hosts[host_name] = HostInfo(
                    name=host_data['name'],
                    ip=host_data['ip'],
                    port=host_data['port'],
                    status=host_data['status'],
                    last_seen=datetime.fromisoformat(host_data['last_seen']),
                    players=host_data['players'],
                    memory_usage=host_data['memory_usage'],
                    cpu_usage=host_data['cpu_usage']
                )
                logging.info(f"Added host from peer: {host_name}")
                
        return {'type': 'peer_discovery_response', 'success': True}
        
    def handle_peer_sync(self, message: Dict) -> Optional[Dict]:
        """Handle peer sync message"""
        host_data = message.get('host_info', {})
        host_name = host_data.get('name')
        if host_name and host_name in self.hosts:
            host = self.hosts[host_name]
            host.status = host_data.get('status', host.status)
            host.players = host_data.get('players', host.players)
            host.memory_usage = host_data.get('memory_usage', host.memory_usage)
            host.cpu_usage = host_data.get('cpu_usage', host.cpu_usage)
            host.last_seen = datetime.fromisoformat(host_data.get('last_seen', host.last_seen.isoformat()))
            
        return {'type': 'peer_sync_response', 'success': True}
        
    def monitor_heartbeats(self):
        """Monitor host heartbeats and mark offline hosts"""
        while self.is_running:
            current_time = datetime.now()
            
            for host_name, host_info in list(self.hosts.items()):
                time_since_last_seen = (current_time - host_info.last_seen).total_seconds()
                
                if time_since_last_seen > self.host_timeout:
                    host_info.status = 'offline'
                    logging.warning(f"Host {host_name} marked as offline (no heartbeat for {time_since_last_seen:.0f}s)")
                    
            time.sleep(10)  # Check every 10 seconds
            
    def select_next_host(self, exclude_host: Optional[str] = None) -> Optional[HostInfo]:
        """Select next available host for failover"""
        available_hosts = [
            host for host in self.hosts.values()
            if host.status == 'online' and (exclude_host is None or host.name != exclude_host)
        ]
        
        if not available_hosts:
            return None
            
        # Simple round-robin selection
        # In a more advanced implementation, this could consider load balancing
        return available_hosts[0]
        
    def get_hosts_status(self) -> List[Dict]:
        """Get status of all hosts"""
        return [
            {
                'name': host.name,
                'ip': host.ip,
                'port': host.port,
                'status': host.status,
                'players': host.players,
                'memory_usage': host.memory_usage,
                'cpu_usage': host.cpu_usage,
                'last_seen': host.last_seen.isoformat()
            }
            for host in self.hosts.values()
        ]
        
    def remove_host(self, host_name: str) -> bool:
        """Remove a host from the network"""
        if host_name in self.hosts:
            del self.hosts[host_name]
            logging.info(f"Host removed: {host_name}")
            return True
        return False
        
    def add_peer_ip(self, ip: str):
        """Add a peer IP address to connect to"""
        if ip not in self.peer_ips:
            self.peer_ips.append(ip)
            logging.info(f"Added peer IP: {ip}")
            
    def remove_peer_ip(self, ip: str):
        """Remove a peer IP address"""
        if ip in self.peer_ips:
            self.peer_ips.remove(ip)
            logging.info(f"Removed peer IP: {ip}")
            
    def discover_peers(self):
        """Discover other peers on the network"""
        while self.is_running:
            for peer_ip in self.peer_ips:
                try:
                    # Try to connect to peer
                    peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    peer_socket.settimeout(5)
                    peer_socket.connect((peer_ip, self.port))
                    
                    # Send discovery message
                    discovery_msg = {
                        'type': 'peer_discovery',
                        'hosts': self.get_hosts_status()
                    }
                    self.send_message_to_socket(peer_socket, discovery_msg)
                    
                    # Store connection
                    self.peer_connections[peer_ip] = peer_socket
                    
                    # Start listening for messages from this peer
                    threading.Thread(
                        target=self.listen_to_peer,
                        args=(peer_socket, peer_ip),
                        daemon=True
                    ).start()
                    
                except Exception as e:
                    # Peer not available, remove from connections
                    if peer_ip in self.peer_connections:
                        del self.peer_connections[peer_ip]
                        
            time.sleep(60)  # Check every minute
            
    def listen_to_peer(self, peer_socket: socket.socket, peer_ip: str):
        """Listen for messages from a specific peer"""
        try:
            while self.is_running:
                # Receive message length
                length_data = peer_socket.recv(4)
                if not length_data:
                    break
                    
                message_length = struct.unpack('!I', length_data)[0]
                
                # Receive message data
                message_data = b''
                while len(message_data) < message_length:
                    chunk = peer_socket.recv(message_length - len(message_data))
                    if not chunk:
                        break
                    message_data += chunk
                    
                if len(message_data) < message_length:
                    break
                    
                # Parse and handle message
                message = json.loads(message_data.decode('utf-8'))
                self.handle_peer_message(message, peer_ip)
                
        except Exception as e:
            logging.error(f"Error listening to peer {peer_ip}: {e}")
        finally:
            if peer_ip in self.peer_connections:
                del self.peer_connections[peer_ip]
            peer_socket.close()
            
    def handle_peer_message(self, message: Dict, peer_ip: str):
        """Handle message from peer"""
        try:
            message_type = message.get('type')
            if message_type == 'peer_discovery':
                # Sync hosts from peer
                peer_hosts = message.get('hosts', [])
                for host_data in peer_hosts:
                    host_name = host_data['name']
                    if host_name not in self.hosts:
                        # Add new host from peer
                        self.hosts[host_name] = HostInfo(
                            name=host_data['name'],
                            ip=host_data['ip'],
                            port=host_data['port'],
                            status=host_data['status'],
                            last_seen=datetime.fromisoformat(host_data['last_seen']),
                            players=host_data['players'],
                            memory_usage=host_data['memory_usage'],
                            cpu_usage=host_data['cpu_usage']
                        )
                        logging.info(f"Added host from peer {peer_ip}: {host_name}")
                        
            elif message_type == 'peer_sync':
                # Handle host updates from peer
                host_data = message.get('host_info', {})
                host_name = host_data.get('name')
                if host_name and host_name in self.hosts:
                    host = self.hosts[host_name]
                    host.status = host_data.get('status', host.status)
                    host.players = host_data.get('players', host.players)
                    host.memory_usage = host_data.get('memory_usage', host.memory_usage)
                    host.cpu_usage = host_data.get('cpu_usage', host.cpu_usage)
                    host.last_seen = datetime.fromisoformat(host_data.get('last_seen', host.last_seen.isoformat()))
                    
        except Exception as e:
            logging.error(f"Error handling peer message: {e}")
            
    def broadcast_to_peers(self):
        """Broadcast host updates to all peers"""
        while self.is_running:
            try:
                # Get current host status
                current_hosts = self.get_hosts_status()
                
                # Broadcast to all connected peers
                for peer_ip, peer_socket in list(self.peer_connections.items()):
                    try:
                        sync_msg = {
                            'type': 'peer_sync',
                            'hosts': current_hosts
                        }
                        self.send_message_to_socket(peer_socket, sync_msg)
                    except Exception as e:
                        logging.error(f"Failed to broadcast to peer {peer_ip}: {e}")
                        # Remove failed connection
                        del self.peer_connections[peer_ip]
                        
            except Exception as e:
                logging.error(f"Error in broadcast: {e}")
                
            time.sleep(30)  # Broadcast every 30 seconds
            
    def send_message_to_socket(self, sock: socket.socket, message: Dict):
        """Send message to a specific socket"""
        try:
            message_data = json.dumps(message).encode('utf-8')
            message_length = struct.pack('!I', len(message_data))
            sock.send(message_length + message_data)
        except Exception as e:
            logging.error(f"Error sending message to socket: {e}")
            raise

class HostClient:
    """Client for connecting to the network manager"""
    
    def __init__(self, server_ip: str, server_port: int = 25566):
        self.server_ip = server_ip
        self.server_port = server_port
        self.socket = None
        self.is_connected = False
        self.host_info = None
        self.heartbeat_thread = None
        
    def connect(self, host_info: Dict) -> bool:
        """Connect to the network manager"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.server_ip, self.server_port))
            
            self.host_info = host_info
            self.is_connected = True
            
            # Register with the network
            self.send_message({
                'type': 'register',
                'host_info': host_info
            })
            
            # Start heartbeat thread
            self.heartbeat_thread = threading.Thread(target=self.send_heartbeats, daemon=True)
            self.heartbeat_thread.start()
            
            logging.info(f"Connected to network manager at {self.server_ip}:{self.server_port}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to connect to network manager: {e}")
            return False
            
    def disconnect(self):
        """Disconnect from the network manager"""
        self.is_connected = False
        if self.socket:
            self.socket.close()
        logging.info("Disconnected from network manager")
        
    def send_message(self, message: Dict) -> Optional[Dict]:
        """Send message to network manager"""
        if not self.is_connected or not self.socket:
            return None
            
        try:
            message_data = json.dumps(message).encode('utf-8')
            message_length = struct.pack('!I', len(message_data))
            self.socket.send(message_length + message_data)
            
            # Wait for response
            length_data = self.socket.recv(4)
            if length_data:
                response_length = struct.unpack('!I', length_data)[0]
                response_data = self.socket.recv(response_length)
                return json.loads(response_data.decode('utf-8'))
                
        except Exception as e:
            logging.error(f"Error sending message: {e}")
            self.is_connected = False
            
        return None
        
    def send_heartbeats(self):
        """Send periodic heartbeats"""
        while self.is_connected and self.host_info:
            try:
                self.send_message({
                    'type': 'heartbeat',
                    'host_name': self.host_info['name']
                })
                time.sleep(30)  # Send heartbeat every 30 seconds
            except Exception as e:
                logging.error(f"Error sending heartbeat: {e}")
                break
                
    def update_status(self, status_info: Dict):
        """Update host status"""
        if self.is_connected and self.host_info:
            message = {
                'type': 'status_update',
                'host_name': self.host_info['name'],
                **status_info
            }
            self.send_message(message)
            
    def notify_player_join(self, player_name: str):
        """Notify network manager of player join"""
        if self.is_connected and self.host_info:
            self.send_message({
                'type': 'player_join',
                'host_name': self.host_info['name'],
                'player_name': player_name
            })
            
    def notify_player_leave(self, player_name: str):
        """Notify network manager of player leave"""
        if self.is_connected and self.host_info:
            self.send_message({
                'type': 'player_leave',
                'host_name': self.host_info['name'],
                'player_name': player_name
            })
            
    def request_failover(self) -> Optional[Dict]:
        """Request failover to another host"""
        if self.is_connected and self.host_info:
            return self.send_message({
                'type': 'failover_request',
                'host_name': self.host_info['name']
            })
        return None 