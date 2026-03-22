import asyncio
from dataclasses import dataclass
from typing import Dict, List, Set
import json
import logging

@dataclass
class Peer:
    id: str
    address: str
    port: int
    capabilities: List[str]
    last_seen: float

class PeerDiscovery:
    def __init__(self, host: str, port: int, node_id: str):
        self.host = host
        self.port = port
        self.node_id = node_id
        self.peers: Dict[str, Peer] = {}
        self.active_peers: Set[str] = set()
        self.logger = logging.getLogger('PeerDiscovery')

    async def start(self):
        """Start peer discovery service"""
        self.server = await asyncio.start_server(
            self._handle_connection, self.host, self.port
        )
        self.logger.info(f'Peer discovery running on {self.host}:{self.port}')
        await self._periodic_ping()

    async def _handle_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handle incoming peer connections"""
        try:
            data = await reader.read(1024)
            msg = json.loads(data.decode())
            
            if msg['type'] == 'discovery':
                peer = Peer(
                    id=msg['node_id'],
                    address=msg['address'],
                    port=msg['port'], 
                    capabilities=msg['capabilities'],
                    last_seen=asyncio.get_event_loop().time()
                )
                self._add_peer(peer)
                
                # Send peer list back
                response = {
                    'type': 'peers',
                    'peers': [
                        {
                            'id': p.id,
                            'address': p.address,
                            'port': p.port,
                            'capabilities': p.capabilities
                        } for p in self.peers.values()
                    ]
                }
                writer.write(json.dumps(response).encode())
                await writer.drain()
                
        except Exception as e:
            self.logger.error(f'Error handling connection: {e}')
        finally:
            writer.close()
            await writer.wait_closed()

    def _add_peer(self, peer: Peer):
        """Add new peer to registry"""
        if peer.id not in self.peers:
            self.logger.info(f'New peer discovered: {peer.id}')
        self.peers[peer.id] = peer
        self.active_peers.add(peer.id)

    async def _periodic_ping(self, interval: int = 30):
        """Periodically ping peers to maintain mesh network"""
        while True:
            await asyncio.sleep(interval)
            current_time = asyncio.get_event_loop().time()
            
            # Remove stale peers
            stale_peers = [
                pid for pid, p in self.peers.items() 
                if current_time - p.last_seen > interval * 2
            ]
            for pid in stale_peers:
                self.logger.warning(f'Peer {pid} appears to be offline')
                self.peers.pop(pid)
                self.active_peers.discard(pid)
                
            # Ping active peers
            for peer in list(self.peers.values()):
                try:
                    reader, writer = await asyncio.open_connection(
                        peer.address, peer.port
                    )
                    msg = {
                        'type': 'discovery',
                        'node_id': self.node_id,
                        'address': self.host,
                        'port': self.port,
                        'capabilities': ['mesh', 'discovery']
                    }
                    writer.write(json.dumps(msg).encode())
                    await writer.drain()
                    
                    data = await reader.read(1024)
                    response = json.loads(data.decode())
                    
                    if response['type'] == 'peers':
                        for p in response['peers']:
                            self._add_peer(Peer(
                                id=p['id'],
                                address=p['address'], 
                                port=p['port'],
                                capabilities=p['capabilities'],
                                last_seen=current_time
                            ))
                            
                    writer.close()
                    await writer.wait_closed()
                    
                except Exception as e:
                    self.logger.error(f'Error pinging peer {peer.id}: {e}')
                    self.active_peers.discard(peer.id)

    async def stop(self):
        """Stop peer discovery service"""
        self.server.close()
        await self.server.wait_closed()
        self.logger.info('Peer discovery stopped')