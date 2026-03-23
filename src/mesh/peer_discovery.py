import hashlib
import random
import json
from typing import List, Dict

class PeerDiscovery:
    def __init__(self, seed_peers: List[str], trust_model: str = 'web-of-trust'):
        self.seed_peers = seed_peers
        self.trust_model = trust_model
        self.peer_trust: Dict[str, float] = {}
        self.peer_connections: Dict[str, List[str]] = {}
        self.initialize_trust()

    def initialize_trust(self):
        for peer in self.seed_peers:
            self.peer_trust[peer] = 1.0
            self.peer_connections[peer] = []

    def discover_peers(self) -> List[str]:
        discovered_peers = self.seed_peers[:]
        for peer in self.seed_peers:
            discovered_peers.extend(self.get_trusted_peers(peer))
        return list(set(discovered_peers))

    def get_trusted_peers(self, peer: str) -> List[str]:
        if peer not in self.peer_connections:
            return []
        trusted_peers = []
        for connected_peer in self.peer_connections[peer]:
            if self.peer_trust[connected_peer] >= 0.5:
                trusted_peers.append(connected_peer)
        return trusted_peers

    def add_peer(self, new_peer: str, trusted_by: str) -> bool:
        if new_peer in self.peer_trust:
            return False
        self.peer_trust[new_peer] = self.peer_trust[trusted_by] * 0.8
        self.peer_connections[trusted_by].append(new_peer)
        self.peer_connections[new_peer] = []
        return True

    def remove_peer(self, peer: str):
        if peer not in self.peer_trust:
            return
        for connected_peer in self.peer_connections[peer]:
            self.peer_connections[connected_peer].remove(peer)
        del self.peer_trust[peer]
        del self.peer_connections[peer]

    def update_trust(self, peer: str, trust_score: float):
        if peer not in self.peer_trust:
            return
        self.peer_trust[peer] = trust_score

    def serialize(self) -> str:
        return json.dumps({
            'seed_peers': self.seed_peers,
            'trust_model': self.trust_model,
            'peer_trust': self.peer_trust,
            'peer_connections': self.peer_connections
        })

    def deserialize(self, data: str):
        state = json.loads(data)
        self.seed_peers = state['seed_peers']
        self.trust_model = state['trust_model']
        self.peer_trust = state['peer_trust']
        self.peer_connections = state['peer_connections']
