import asyncio
import json
import time
from typing import Dict, Set, Optional
from dataclasses import dataclass

@dataclass
class PeerInfo:
    id: str
    address: str 
    last_seen: float
    capabilities: Set[str]
    health_score: float = 1.0

class DHTPeerDiscovery:
    def __init__(self, node_id: str, bootstrap_peers: list[str]):
        self.node_id = node_id
        self.peers: Dict[str, PeerInfo] = {}
        self.bootstrap_peers = bootstrap_peers
        self.heartbeat_interval = 30  # seconds
        self.peer_timeout = 90  # seconds

    async def start(self):
        """Start peer discovery and health monitoring"""
        await asyncio.gather(
            self.discovery_loop(),
            self.health_check_loop()
        )

    async def discovery_loop(self):
        """Continuously discover and track peers"""
        while True:
            try:
                # Announce self to bootstrap peers
                for peer in self.bootstrap_peers:
                    await self.announce_to_peer(peer)
                
                # Request peer lists from known peers
                for peer_id, peer in self.peers.items():
                    peer_list = await self.request_peer_list(peer)
                    if peer_list:
                        self.merge_peer_list(peer_list)

            except Exception as e:
                print(f"Discovery error: {e}")
            
            await asyncio.sleep(self.heartbeat_interval)

    async def health_check_loop(self):
        """Monitor peer health and remove stale peers"""
        while True:
            current_time = time.time()
            stale_peers = []

            for peer_id, peer in self.peers.items():
                # Remove peers not seen recently
                if current_time - peer.last_seen > self.peer_timeout:
                    stale_peers.append(peer_id)
                    continue

                # Check peer health
                is_healthy = await self.check_peer_health(peer)
                if is_healthy:
                    peer.health_score = min(1.0, peer.health_score + 0.1)
                else:
                    peer.health_score *= 0.5
                    if peer.health_score < 0.2:
                        stale_peers.append(peer_id)

            # Remove stale peers
            for peer_id in stale_peers:
                del self.peers[peer_id]

            await asyncio.sleep(self.heartbeat_interval)

    async def announce_to_peer(self, peer_address: str) -> None:
        """Announce this node's presence to a peer"""
        try:
            # Simulate network call
            announcement = {
                'node_id': self.node_id,
                'capabilities': ['mesh', 'storage'],
                'timestamp': time.time()
            }
            # await self.send_to_peer(peer_address, announcement)
            pass
        except Exception as e:
            print(f"Failed to announce to {peer_address}: {e}")

    async def request_peer_list(self, peer: PeerInfo) -> Optional[Dict]:
        """Request known peers from a given peer"""
        try:
            # Simulate network call
            # return await self.send_to_peer(peer.address, {'type': 'get_peers'})
            return {}
        except Exception:
            return None

    def merge_peer_list(self, peer_list: Dict) -> None:
        """Merge received peer list with known peers"""
        current_time = time.time()
        
        for peer_id, peer_data in peer_list.items():
            if peer_id not in self.peers:
                self.peers[peer_id] = PeerInfo(
                    id=peer_id,
                    address=peer_data['address'],
                    last_seen=current_time,
                    capabilities=set(peer_data['capabilities'])
                )
            else:
                self.peers[peer_id].last_seen = current_time

    async def check_peer_health(self, peer: PeerInfo) -> bool:
        """Check if a peer is healthy and responsive"""
        try:
            # Simulate health check
            # response = await self.send_to_peer(peer.address, {'type': 'health_check'})
            # return response and response.get('status') == 'healthy'
            return True
        except Exception:
            return False

    def get_healthy_peers(self, min_health: float = 0.5) -> Dict[str, PeerInfo]:
        """Get dictionary of peers above specified health threshold"""
        return {k: v for k, v in self.peers.items() if v.health_score >= min_health}

    def get_peers_with_capability(self, capability: str, min_health: float = 0.5) -> Dict[str, PeerInfo]:
        """Get peers that have a specific capability"""
        return {k: v for k, v in self.peers.items() 
                if capability in v.capabilities and v.health_score >= min_health}