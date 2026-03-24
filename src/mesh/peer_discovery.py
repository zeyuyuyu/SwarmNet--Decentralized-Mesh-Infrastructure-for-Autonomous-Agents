import random
import hashlib
import time
from typing import List, Tuple

class PeerDiscovery:
    def __init__(self, node_id: str, initial_peers: List[str]):
        self.node_id = node_id
        self.peers = initial_peers
        self.known_peers = set(initial_peers)
        self.peer_scores = {peer: 1.0 for peer in initial_peers}

    def discover_peers(self) -> List[str]:
        new_peers = []
        for peer in self.peers:
            try:
                new_peers.extend(self.query_peer(peer))
            except Exception:
                self.peer_scores[peer] -= 0.1
                if self.peer_scores[peer] <= 0:
                    self.peers.remove(peer)
                    del self.peer_scores[peer]
                    self.known_peers.remove(peer)

        for new_peer in new_peers:
            if new_peer not in self.known_peers:
                self.known_peers.add(new_peer)
                self.peer_scores[new_peer] = 1.0
                self.peers.append(new_peer)

        random.shuffle(self.peers)
        return self.peers[:10]

    def query_peer(self, peer: str) -> List[str]:
        # Simulate a network query to the peer
        time.sleep(random.uniform(0.1, 1.0))
        return [self.generate_peer_id() for _ in range(random.randint(3, 10))]

    def generate_peer_id(self) -> str:
        return hashlib.sha256(f'{time.time()}{random.random()}'.encode()).hexdigest()[:8]
