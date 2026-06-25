"""
Core network layer functionality
Handles network protocols, addressing, and routing concepts
"""

import socket
import struct
import json
from typing import Dict, List, Tuple, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ProtocolType(Enum):
    """Network protocol types"""
    TCP = 6
    UDP = 17
    ICMP = 1


class NetworkLayer:
    """Base network layer handling IP addressing and routing concepts"""

    def __init__(self):
        self.connections: Dict[str, socket.socket] = {}
        self.routing_table: Dict[str, str] = {}  # destination -> next_hop
        self.interfaces: Dict[str, str] = {}     # interface_name -> ip_address

    def add_interface(self, name: str, ip_address: str):
        """Add a network interface"""
        self.interfaces[name] = ip_address
        logger.info(f"Added interface {name} with IP {ip_address}")

    def add_route(self, destination: str, next_hop: str):
        """Add a route to the routing table"""
        self.routing_table[destination] = next_hop
        logger.info(f"Added route: {destination} via {next_hop}")

    def create_socket(self, protocol: ProtocolType = ProtocolType.TCP) -> socket.socket:
        """Create a network socket"""
        if protocol == ProtocolType.TCP:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        elif protocol == ProtocolType.UDP:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        else:
            raise ValueError(f"Unsupported protocol: {protocol}")

        return sock

    def get_local_ip(self, interface: str = None) -> Optional[str]:
        """Get local IP address for an interface"""
        if interface and interface in self.interfaces:
            return self.interfaces[interface]
        # Return first interface IP if none specified
        if self.interfaces:
            return list(self.interfaces.values())[0]
        return None


class Packet:
    """Represents a network packet"""

    def __init__(self, src_ip: str, dst_ip: str, protocol: ProtocolType,
                 payload: bytes, ttl: int = 64):
        self.src_ip = src_ip
        self.dst_ip = dst_ip
        self.protocol = protocol
        self.payload = payload
        self.ttl = ttl
        self.timestamp = None

    def to_dict(self) -> Dict:
        """Convert packet to dictionary for serialization"""
        return {
            'src_ip': self.src_ip,
            'dst_ip': self.dst_ip,
            'protocol': self.protocol.name,
            'payload_length': len(self.payload),
            'ttl': self.ttl
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Packet':
        """Create packet from dictionary"""
        return cls(
            src_ip=data['src_ip'],
            dst_ip=data['dst_ip'],
            protocol=ProtocolType[data['protocol']],
            payload=b'x' * data['payload_length'],  # Simplified
            ttl=data['ttl']
        )


def calculate_checksum(data: bytes) -> int:
    """Calculate Internet checksum"""
    if len(data) % 2 == 1:
        data += b'\x00'
    res = sum(struct.unpack("!%dH" % (len(data)//2), data))
    res = (res >> 16) + (res & 0xffff)
    res += res >> 16
    return ~res & 0xffff


if __name__ == "__main__":
    # Simple test
    nl = NetworkLayer()
    nl.add_interface("eth0", "192.168.1.100")
    nl.add_route("0.0.0.0/0", "192.168.1.1")

    sock = nl.create_socket(ProtocolType.TCP)
    print(f"Created {sock.type} socket")
    print(f"Local IP: {nl.get_local_ip()}")