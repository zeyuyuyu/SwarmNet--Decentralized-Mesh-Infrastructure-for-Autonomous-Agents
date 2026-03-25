import asyncio
import time
from typing import Dict, Set
import hashlib
import json

class DHTNode:
    def __init__(self, node_id: str, port: int):
        self.node_id = node_id
        self.port = port
        self.peers: Dict[str, float] = {}  # node_id -> last_seen_timestamp
        self.routing_table: Dict[str, str] = {}  # node_id -> ip_address
        self.heartbeat_interval = 30  # seconds
        self.peer_timeout = 90  # seconds

    async def start(self):
        """Start the DHT node services"""
        await asyncio.gather(
            self.heartbeat_loop(),
            self.cleanup_loop()
        )

    async def heartbeat_loop(self):
        """Periodically send heartbeat to all known peers"""
        while True:
            peers_to_ping = self.peers.copy()
            for peer_id, _ in peers_to_ping.items():
                try:
                    await self.send_heartbeat(peer_id)
                except Exception as e:
                    print(f"Failed to send heartbeat to {peer_id}: {e}")
            await asyncio.sleep(self.heartbeat_interval)

    async def cleanup_loop(self):
        """Remove stale peers that haven't sent heartbeats"""
        while True:
            current_time = time.time()
            stale_peers = [
                peer_id for peer_id, last_seen in self.peers.items()
                if current_time - last_seen > self.peer_timeout
            ]
            for peer_id in stale_peers:
                self.remove_peer(peer_id)
            await asyncio.sleep(self.heartbeat_interval)

    async def send_heartbeat(self, peer_id: str):
        """Send heartbeat to a specific peer"""
        if peer_id in self.routing_table:
            # In real implementation, send UDP heartbeat packet
            # This is a placeholder for the network communication
            self.peers[peer_id] = time.time()

    def add_peer(self, peer_id: str, ip_address: str):
        """Add a new peer to the routing table"""
        self.routing_table[peer_id] = ip_address
        self.peers[peer_id] = time.time()

    def remove_peer(self, peer_id: str):
        """Remove a peer from both routing table and peers list"""
        self.routing_table.pop(peer_id, None)
        self.peers.pop(peer_id, None)

    def get_closest_peers(self, target_id: str, k: int = 3) -> Set[str]:
        """Find k closest peers to a target ID using XOR distance"""
        def xor_distance(id1: str, id2: str) -> int:
            return int(hashlib.sha1(id1.encode()).hexdigest(), 16) ^ \\
                   int(hashlib.sha1(id2.encode()).hexdigest(), 16)

        distances = [
            (xor_distance(target_id, peer_id), peer_id)
            for peer_id in self.peers.keys()
        ]
        distances.sort()
        return {peer_id for _, peer_id in distances[:k]}

    def to_json(self) -> str:
        """Serialize node state to JSON"""
        return json.dumps({
            'node_id': self.node_id,
            'port': self.port,
            'peers': self.peers,
            'routing_table': self.routing_table
        })

    @classmethod
    def from_json(cls, json_str: str) -> 'DHTNode':
        """Create node from JSON state"""
        data = json.loads(json_str)
        node = cls(data['node_id'], data['port'])
        node.peers = data['peers']
        node.routing_table = data['routing_table']
        return node