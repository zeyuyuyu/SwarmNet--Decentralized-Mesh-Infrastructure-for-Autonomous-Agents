import asyncio
from typing import Dict, Set
import time
import json
import logging

class PeerDiscovery:
    def __init__(self, node_id: str, port: int):
        self.node_id = node_id
        self.port = port
        self.peers: Dict[str, dict] = {}
        self.active_peers: Set[str] = set()
        self.last_heartbeat: Dict[str, float] = {}
        self.logger = logging.getLogger('PeerDiscovery')

    async def start(self):
        """Start peer discovery service"""
        self.logger.info(f'Starting peer discovery service for node {self.node_id}')
        await asyncio.gather(
            self.heartbeat_loop(),
            self.cleanup_loop()
        )

    async def heartbeat_loop(self):
        """Periodically broadcast heartbeat to all known peers"""
        while True:
            try:
                heartbeat = {
                    'node_id': self.node_id,
                    'timestamp': time.time(),
                    'port': self.port,
                    'peers': list(self.active_peers)
                }
                for peer_id, peer_info in self.peers.items():
                    try:
                        await self.send_heartbeat(peer_info['address'], peer_info['port'], heartbeat)
                    except Exception as e:
                        self.logger.warning(f'Failed to send heartbeat to {peer_id}: {e}')
                await asyncio.sleep(5)  # Heartbeat interval
            except Exception as e:
                self.logger.error(f'Error in heartbeat loop: {e}')
                await asyncio.sleep(1)

    async def cleanup_loop(self):
        """Remove stale peers that haven't sent heartbeat recently"""
        while True:
            try:
                current_time = time.time()
                stale_peers = [
                    peer_id for peer_id, last_beat in self.last_heartbeat.items()
                    if current_time - last_beat > 15  # Peer timeout threshold
                ]
                for peer_id in stale_peers:
                    self.remove_peer(peer_id)
                await asyncio.sleep(5)
            except Exception as e:
                self.logger.error(f'Error in cleanup loop: {e}')
                await asyncio.sleep(1)

    async def send_heartbeat(self, address: str, port: int, data: dict):
        """Send heartbeat to a specific peer"""
        try:
            reader, writer = await asyncio.open_connection(address, port)
            writer.write(json.dumps(data).encode())
            await writer.drain()
            writer.close()
            await writer.wait_closed()
        except Exception as e:
            raise Exception(f'Failed to send heartbeat: {e}')

    def handle_heartbeat(self, peer_heartbeat: dict):
        """Process received heartbeat from peer"""
        peer_id = peer_heartbeat['node_id']
        self.last_heartbeat[peer_id] = peer_heartbeat['timestamp']
        
        if peer_id not in self.peers:
            self.peers[peer_id] = {
                'address': peer_heartbeat.get('address'),
                'port': peer_heartbeat.get('port')
            }
            self.active_peers.add(peer_id)
            self.logger.info(f'New peer discovered: {peer_id}')

        # Merge peer lists
        new_peers = set(peer_heartbeat['peers']) - self.active_peers
        self.active_peers.update(new_peers)

    def remove_peer(self, peer_id: str):
        """Remove a peer from tracking"""
        if peer_id in self.peers:
            del self.peers[peer_id]
            self.active_peers.remove(peer_id)
            del self.last_heartbeat[peer_id]
            self.logger.info(f'Removed stale peer: {peer_id}')

    def get_active_peers(self) -> Set[str]:
        """Get set of currently active peer IDs"""
        return self.active_peers.copy()

    def get_peer_info(self, peer_id: str) -> dict:
        """Get connection info for specific peer"""
        return self.peers.get(peer_id, {})
