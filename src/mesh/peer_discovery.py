import random
import hashlib
import time

class PeerDiscovery:
    def __init__(self, node_id, initial_peers):
        self.node_id = node_id
        self.peers = initial_peers
        self.peer_database = {}
        self.consensus_threshold = 3
        self.update_peer_database()

    def update_peer_database(self):
        for peer in self.peers:
            self.peer_database[peer] = {
                'last_seen': time.time(),
                'consensus_score': 0
            }

    def discover_peers(self):
        new_peers = []
        for peer in self.peer_database:
            if self.peer_database[peer]['last_seen'] + 60 > time.time():
                new_peers.extend(self.query_peer(peer))
        self.peers = list(set(self.peers + new_peers))
        self.update_peer_database()

    def query_peer(self, peer):
        # Simulate peer query
        time.sleep(random.uniform(0.1, 0.5))
        return [f'peer_{i}' for i in range(random.randint(1, 5))]

    def maintain_consensus(self):
        for peer in list(self.peer_database.keys()):
            if self.peer_database[peer]['last_seen'] + 300 < time.time():
                del self.peer_database[peer]
                self.peers.remove(peer)
            else:
                self.peer_database[peer]['consensus_score'] += 1
                if self.peer_database[peer]['consensus_score'] >= self.consensus_threshold:
                    self.peer_database[peer]['consensus_score'] = 0
                    self.broadcast_peer_update(peer)

    def broadcast_peer_update(self, peer):
        # Simulate peer update broadcast
        time.sleep(random.uniform(0.1, 0.5))
        print(f'Broadcasting peer update for {peer}')

if __name__ == '__main__':
    node_id = hashlib.sha256(str(random.randint(1, 1000000)).encode()).hexdigest()
    initial_peers = [f'peer_{i}' for i in range(1, 6)]
    peer_discovery = PeerDiscovery(node_id, initial_peers)

    while True:
        peer_discovery.discover_peers()
        peer_discovery.maintain_consensus()
        time.sleep(10)