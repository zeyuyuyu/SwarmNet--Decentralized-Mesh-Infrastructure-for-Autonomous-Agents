import asyncio
import json
import logging
from typing import Dict, Set, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

@dataclass
class PeerInfo:
    id: str
    address: str
    last_seen: datetime
    capabilities: Set[str]

class PeerDiscovery:
    def __init__(self, node_id: str, port: int = 8765):
        self.node_id = node_id
        self.port = port
        self.peers: Dict[str, PeerInfo] = {}
        self.heartbeat_interval = 30  # seconds
        self.peer_timeout = 90  # seconds
        self.logger = logging.getLogger('PeerDiscovery')

    async def start(self):
        self.logger.info(f'Starting peer discovery service on port {self.port}')
        server = await asyncio.start_server(
            self.handle_connection, '0.0.0.0', self.port
        )
        asyncio.create_task(self.heartbeat_loop())
        asyncio.create_task(self.cleanup_loop())
        await server.serve_forever()

    async def handle_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        try:
            data = await reader.read(1024)
            message = json.loads(data.decode())
            
            if message['type'] == 'heartbeat':
                peer_id = message['node_id']
                peer_addr = writer.get_extra_info('peername')[0]
                
                self.peers[peer_id] = PeerInfo(
                    id=peer_id,
                    address=peer_addr,
                    last_seen=datetime.now(),
                    capabilities=set(message.get('capabilities', []))
                )
                
                # Send response with our peer list
                response = {
                    'type': 'peers',
                    'peers': [
                        {'id': p.id, 'address': p.address, 'capabilities': list(p.capabilities)}
                        for p in self.peers.values()
                    ]
                }
                writer.write(json.dumps(response).encode())
                await writer.drain()
                
        except Exception as e:
            self.logger.error(f'Error handling connection: {e}')
        finally:
            writer.close()
            await writer.wait_closed()

    async def heartbeat_loop(self):
        while True:
            try:
                for peer_id, peer in list(self.peers.items()):
                    try:
                        reader, writer = await asyncio.open_connection(peer.address, self.port)
                        message = {
                            'type': 'heartbeat',
                            'node_id': self.node_id,
                            'capabilities': ['mesh', 'crawler']
                        }
                        writer.write(json.dumps(message).encode())
                        await writer.drain()
                        
                        # Update peer list from response
                        data = await reader.read(1024)
                        response = json.loads(data.decode())
                        if response['type'] == 'peers':
                            for p in response['peers']:
                                if p['id'] not in self.peers and p['id'] != self.node_id:
                                    self.peers[p['id']] = PeerInfo(
                                        id=p['id'],
                                        address=p['address'], 
                                        last_seen=datetime.now(),
                                        capabilities=set(p['capabilities'])
                                    )
                                    
                        writer.close()
                        await writer.wait_closed()
                        
                    except Exception as e:
                        self.logger.warning(f'Failed to heartbeat peer {peer_id}: {e}')
                        
            except Exception as e:
                self.logger.error(f'Error in heartbeat loop: {e}')
                
            await asyncio.sleep(self.heartbeat_interval)

    async def cleanup_loop(self):
        while True:
            try:
                now = datetime.now()
                expired = [
                    peer_id for peer_id, peer in self.peers.items()
                    if now - peer.last_seen > timedelta(seconds=self.peer_timeout)
                ]
                for peer_id in expired:
                    self.logger.info(f'Removing expired peer {peer_id}')
                    del self.peers[peer_id]
            except Exception as e:
                self.logger.error(f'Error in cleanup loop: {e}')
            await asyncio.sleep(self.heartbeat_interval)

    def get_peers_by_capability(self, capability: str) -> Set[PeerInfo]:
        return {p for p in self.peers.values() if capability in p.capabilities}

    def get_all_peers(self) -> Set[PeerInfo]:
        return set(self.peers.values())
