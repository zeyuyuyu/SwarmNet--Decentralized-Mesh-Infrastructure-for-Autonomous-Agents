import random
import hashlib
import time
import logging

from collections import deque

logger = logging.getLogger(__name__)

class PeerDiscovery:
    def __init__(self, node_id, bootstrap_nodes):
        self.node_id = node_id
        self.bootstrap_nodes = bootstrap_nodes
        self.peer_list = deque(bootstrap_nodes)
        self.known_peers = set(bootstrap_nodes)
        self.last_discovery = time.time()
        self.discovery_interval = 60  # Seconds

    def discover_peers(self):
        if time.time() - self.last_discovery < self.discovery_interval:
            return

        self.last_discovery = time.time()

        if not self.peer_list:
            self.peer_list = deque(self.bootstrap_nodes)
            self.known_peers = set(self.bootstrap_nodes)

        try:
            peer = self.peer_list.popleft()
            logger.debug(f'Discovering peers from {peer}')
            new_peers = self.query_peer(peer)
            self.add_peers(new_peers)
        except IndexError:
            logger.debug('No more peers to query')

    def query_peer(self, peer):
        # Implement peer query logic here
        # Return a list of new peers discovered
        new_peers = []
        for _ in range(3):
            new_peer = f'peer_{hashlib.sha1(str(random.random()).encode()).hexdigest()[:8]}'
            if new_peer not in self.known_peers:
                new_peers.append(new_peer)
                self.known_peers.add(new_peer)
        return new_peers

    def add_peers(self, new_peers):
        for peer in new_peers:
            if peer not in self.known_peers:
                self.peer_list.append(peer)
                self.known_peers.add(peer)
                logger.debug(f'Added new peer: {peer}')
