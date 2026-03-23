import socket
import threading
import time
import json
from typing import Dict, Set
import logging

class PeerDiscovery:
    def __init__(self, port: int = 5000, broadcast_interval: float = 5.0):
        self.port = port
        self.broadcast_interval = broadcast_interval
        self.peers: Dict[str, float] = {}  # IP -> last_seen timestamp
        self.node_id = self._generate_node_id()
        self.running = False
        self.peer_timeout = 15.0  # Seconds before peer is considered offline
        
        # Setup UDP socket for broadcast
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('', self.port))
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger('PeerDiscovery')

    def _generate_node_id(self) -> str:
        """Generate unique node identifier"""
        return f'{socket.gethostname()}-{id(self)}'

    def start(self):
        """Start peer discovery service"""
        self.running = True
        self.broadcast_thread = threading.Thread(target=self._broadcast_loop)
        self.listener_thread = threading.Thread(target=self._listen_loop)
        self.cleanup_thread = threading.Thread(target=self._cleanup_loop)
        
        self.broadcast_thread.start()
        self.listener_thread.start() 
        self.cleanup_thread.start()
        
        self.logger.info(f'Peer discovery started on port {self.port}')

    def stop(self):
        """Stop peer discovery service"""
        self.running = False
        self.broadcast_thread.join()
        self.listener_thread.join()
        self.cleanup_thread.join()
        self.sock.close()
        self.logger.info('Peer discovery stopped')

    def _broadcast_loop(self):
        """Periodically broadcast presence to network"""
        while self.running:
            try:
                message = {
                    'type': 'heartbeat',
                    'node_id': self.node_id,
                    'timestamp': time.time()
                }
                self.sock.sendto(
                    json.dumps(message).encode(),
                    ('<broadcast>', self.port)
                )
                time.sleep(self.broadcast_interval)
            except Exception as e:
                self.logger.error(f'Broadcast error: {str(e)}')

    def _listen_loop(self):
        """Listen for peer broadcasts"""
        while self.running:
            try:
                data, addr = self.sock.recvfrom(1024)
                message = json.loads(data.decode())
                
                if message['type'] == 'heartbeat':
                    peer_ip = addr[0]
                    self.peers[peer_ip] = message['timestamp']
                    self.logger.debug(f'Heartbeat from peer {peer_ip}')
            except Exception as e:
                self.logger.error(f'Listener error: {str(e)}')

    def _cleanup_loop(self):
        """Remove stale peers"""
        while self.running:
            try:
                current_time = time.time()
                stale_peers = [
                    ip for ip, last_seen in self.peers.items()
                    if current_time - last_seen > self.peer_timeout
                ]
                
                for ip in stale_peers:
                    del self.peers[ip]
                    self.logger.info(f'Peer {ip} timed out')
                    
                time.sleep(self.peer_timeout / 2)
            except Exception as e:
                self.logger.error(f'Cleanup error: {str(e)}')

    def get_active_peers(self) -> Set[str]:
        """Return set of currently active peer IPs"""
        return set(self.peers.keys())

    def get_mesh_status(self) -> Dict:
        """Return current mesh network status"""
        return {
            'node_id': self.node_id,
            'active_peers': len(self.peers),
            'peer_ips': list(self.peers.keys()),
            'uptime': time.time() - list(self.peers.values())[0] if self.peers else 0
        }