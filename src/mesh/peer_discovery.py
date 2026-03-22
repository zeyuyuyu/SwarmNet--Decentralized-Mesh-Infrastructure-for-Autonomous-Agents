import random
import time
import json
import socket
import threading

class PeerDiscovery:
    def __init__(self, mesh_config):
        self.mesh_config = mesh_config
        self.peers = set()
        self.gossip_thread = threading.Thread(target=self.gossip_loop)
        self.gossip_thread.start()

    def gossip_loop(self):
        while True:
            # Randomly select a peer to gossip with
            peer = random.sample(self.peers, 1)[0]
            try:
                # Connect to the peer and exchange peer lists
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((peer, self.mesh_config['port']))
                    s.sendall(json.dumps(list(self.peers)).encode())
                    data = s.recv(1024)
                    new_peers = json.loads(data.decode())
                    self.peers.update(new_peers)
            except:
                # Remove the peer from the list if the connection fails
                self.peers.remove(peer)
            time.sleep(self.mesh_config['gossip_interval'])

    def join_mesh(self, peer):
        # Add a new peer to the mesh
        self.peers.add(peer)

    def leave_mesh(self, peer):
        # Remove a peer from the mesh
        self.peers.remove(peer)
