import asyncio
import random
from kademlia.network import Server
from kademlia.node import Node
from kademlia.protocol import KademliaProtocol
from kademlia.routing import RoutingTable

class KademliaDiscovery:
    def __init__(self, node_id, bootstrap_nodes):
        self.node_id = node_id
        self.bootstrap_nodes = bootstrap_nodes
        self.server = Server()

    async def start(self):
        await self.server.listen(random.randint(10000, 20000))
        await self.server.bootstrap(self.bootstrap_nodes)

    async def find_peers(self, target_id):
        node = await self.server.get(target_id)
        if node:
            return [node]
        else:
            return []

class PeerDiscovery:
    def __init__(self, node_id, bootstrap_nodes):
        self.kademlia = KademliaDiscovery(node_id, bootstrap_nodes)

    async def discover_peers(self, target_id):
        return await self.kademlia.find_peers(target_id)

    async def start(self):
        await self.kademlia.start()
