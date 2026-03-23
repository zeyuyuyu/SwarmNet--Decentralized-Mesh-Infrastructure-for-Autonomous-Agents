import asyncio
from zeroconf import ServiceInfo, Zeroconf, ServiceBrowser
from typing import Dict, Set, Optional
import time
import logging

class PeerDiscovery:
    SERVICE_TYPE = '_swarmnet._tcp.local.'
    
    def __init__(self, node_id: str, port: int):
        self.node_id = node_id
        self.port = port
        self.peers: Dict[str, tuple] = {}
        self.zeroconf = Zeroconf()
        self.browser = None
        self.info = None
        self.logger = logging.getLogger('PeerDiscovery')

    async def start(self):
        """Start peer discovery service"""
        # Register our own service
        self.info = ServiceInfo(
            self.SERVICE_TYPE,
            f'{self.node_id}.{self.SERVICE_TYPE}',
            addresses=[self._get_ip_address()],
            port=self.port,
            properties={'node_id': self.node_id}
        )
        
        try:
            self.zeroconf.register_service(self.info)
            self.browser = ServiceBrowser(self.zeroconf, self.SERVICE_TYPE, handlers=[self._on_peer_discovered])
            self.logger.info(f'Started peer discovery on port {self.port}')
        except Exception as e:
            self.logger.error(f'Failed to start peer discovery: {e}')
            raise

    def stop(self):
        """Stop peer discovery service"""
        if self.browser:
            self.browser.cancel()
        if self.info:
            self.zeroconf.unregister_service(self.info)
        self.zeroconf.close()
        self.logger.info('Stopped peer discovery')

    def _on_peer_discovered(self, zeroconf: Zeroconf, service_type: str, name: str, state_change: str):
        """Callback for when peers are discovered/removed"""
        if state_change == 'Added':
            info = zeroconf.get_service_info(service_type, name)
            if info:
                peer_id = info.properties.get(b'node_id', b'').decode('utf-8')
                if peer_id and peer_id != self.node_id:
                    address = self._get_address_from_info(info)
                    self.peers[peer_id] = (address, info.port)
                    self.logger.info(f'Discovered peer {peer_id} at {address}:{info.port}')

        elif state_change == 'Removed':
            # Remove peer when they go offline
            peer_id = name.replace(f'.{self.SERVICE_TYPE}', '')
            if peer_id in self.peers:
                del self.peers[peer_id]
                self.logger.info(f'Peer {peer_id} went offline')

    def get_active_peers(self) -> Dict[str, tuple]:
        """Get dictionary of active peers with their connection info"""
        return self.peers.copy()

    def _get_ip_address(self) -> bytes:
        """Get local IP address in bytes format"""
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
        except Exception:
            ip = '127.0.0.1'
        finally:
            s.close()
        return socket.inet_aton(ip)

    def _get_address_from_info(self, info: ServiceInfo) -> str:
        """Extract IP address from ServiceInfo"""
        import socket
        return socket.inet_ntoa(info.addresses[0]) if info.addresses else ''

    async def wait_for_peers(self, min_peers: int = 1, timeout: int = 30) -> bool:
        """Wait until minimum number of peers are discovered"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if len(self.peers) >= min_peers:
                return True
            await asyncio.sleep(1)
        return False