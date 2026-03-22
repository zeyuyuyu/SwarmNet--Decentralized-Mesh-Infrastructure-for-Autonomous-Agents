import socket
import struct
import time
import threading

MULTICAST_GROUP = '224.0.0.250'
MULTICAST_PORT = 5000

def peer_discover():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', MULTICAST_PORT))
    mreq = struct.pack('4sl', socket.inet_aton(MULTICAST_GROUP), socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    while True:
        print('Listening for peer announcements...')
        data, addr = sock.recvfrom(1024)
        print(f'Received announcement from {addr[0]}')
        # Process peer announcement and add to local mesh network

    sock.close()

def announce_peer():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)

    while True:
        message = f'SwarmNet peer announcement from {socket.gethostbyname(socket.gethostname())}'
        sock.sendto(message.encode(), (MULTICAST_GROUP, MULTICAST_PORT))
        print('Sent peer announcement')
        time.sleep(60)  # Announce every minute

    sock.close()

def start_peer_discovery():
    discovery_thread = threading.Thread(target=peer_discover)
    announcement_thread = threading.Thread(target=announce_peer)
    discovery_thread.start()
    announcement_thread.start()
