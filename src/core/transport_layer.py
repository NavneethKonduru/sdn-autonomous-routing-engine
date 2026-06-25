"""
Transport layer functionality
Handles TCP/UDP concepts, port management, and reliability
"""

import socket
import threading
import time
from typing import Callable, Optional, Tuple
from .network_layer import ProtocolType, Packet
import logging

logger = logging.getLogger(__name__)


class TransportLayer:
    """Transport layer handling end-to-end communication"""

    def __init__(self, network_layer):
        self.network = network_layer
        self.port_map: Dict[int, Callable] = {}  # port -> handler function
        self.active_connections: Dict[Tuple, dict] = {}
        self.next_port = 1024  # Start from well-known port range

    def allocate_port(self) -> int:
        """Allocate a new port number"""
        port = self.next_port
        self.next_port += 1
        return port

    def register_handler(self, port: int, handler: Callable[[Packet], None]):
        """Register a handler function for a specific port"""
        self.port_map[port] = handler
        logger.info(f"Registered handler for port {port}")

    def send_segment(self, dst_ip: str, dst_port: int, data: bytes,
                     src_port: Optional[int] = None,
                     protocol: ProtocolType = ProtocolType.TCP) -> bool:
        """Send a transport segment"""
        if src_port is None:
            src_port = self.allocate_port()

        try:
            # Create packet
            packet = Packet(
                src_ip=self.network.get_local_ip(),
                dst_ip=dst_ip,
                protocol=protocol,
                payload=data
            )

            # In real implementation, this would add TCP/UDP header
            # For simulation, we'll just log
            logger.info(f"Sending {protocol.name} segment from {packet.src_ip}:{src_port} "
                       f"to {dst_ip}:{dst_port}, {len(data)} bytes")

            # Actually send via socket (simplified)
            if protocol == ProtocolType.TCP:
                # TCP connection would be established here
                pass
            elif protocol == ProtocolType.UDP:
                sock = self.network.create_socket(ProtocolType.UDP)
                sock.sendto(data, (dst_ip, dst_port))
                sock.close()

            return True
        except Exception as e:
            logger.error(f"Failed to send segment: {e}")
            return False

    def start_listener(self, port: int, handler: Callable[[bytes, str, int], None]):
        """Start listening for incoming connections on a port"""
        def listener():
            sock = self.network.create_socket(ProtocolType.TCP)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            local_ip = self.network.get_local_ip()
            # Use 127.0.0.1 for actual OS socket binding to avoid OSError
            sock.bind(('127.0.0.1', port))
            sock.listen(5)
            logger.info(f"Listening on {local_ip}:{port}")

            while True:
                try:
                    conn, addr = sock.accept()
                    logger.info(f"Accepted connection from {addr}")
                    # Handle connection in separate thread
                    threading.Thread(
                        target=self._handle_tcp_connection,
                        args=(conn, addr, handler),
                        daemon=True
                    ).start()
                except Exception as e:
                    logger.error(f"Listener error: {e}")

        threading.Thread(target=listener, daemon=True).start()

    def _handle_tcp_connection(self, conn: socket.socket, addr: Tuple,
                              handler: Callable):
        """Handle a TCP connection"""
        tcp_sock = TCPSocket(self)
        tcp_sock.socket = conn
        tcp_sock.connected = True
        tcp_sock.remote_addr = addr
        try:
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                handler(data, addr[0], addr[1], tcp_sock)
        except Exception as e:
            logger.error(f"Connection handler error: {e}")
        finally:
            conn.close()


class TCPSocket:
    """Simplified TCP socket abstraction"""

    def __init__(self, transport_layer: TransportLayer):
        self.transport = transport_layer
        self.socket: Optional[socket.socket] = None
        self.connected = False
        self.local_addr: Optional[Tuple[str, int]] = None
        self.remote_addr: Optional[Tuple[str, int]] = None

    def connect(self, host: str, port: int) -> bool:
        """Connect to a remote host"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            local_ip = self.transport.network.get_local_ip()
            # Use 127.0.0.1 for actual OS socket binding to avoid OSError
            self.socket.bind(('127.0.0.1', 0))  # Let OS choose port
            self.socket.connect((host, port))
            self.local_addr = self.socket.getsockname()
            self.remote_addr = (host, port)
            self.connected = True
            logger.info(f"Connected to {host}:{port} from {self.local_addr}")
            return True
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False

    def send(self, data: bytes) -> int:
        """Send data"""
        if not self.connected or not self.socket:
            raise ConnectionError("Not connected")
        return self.socket.send(data)

    def recv(self, bufsize: int = 1024) -> bytes:
        """Receive data"""
        if not self.connected or not self.socket:
            raise ConnectionError("Not connected")
        return self.socket.recv(bufsize)

    def close(self):
        """Close the connection"""
        if self.socket:
            self.socket.close()
            self.connected = False


class UDPSocket:
    """Simplified UDP socket abstraction"""

    def __init__(self, transport_layer: TransportLayer):
        self.transport = transport_layer
        self.socket: Optional[socket.socket] = None
        self.local_addr: Optional[Tuple[str, int]] = None

    def bind(self, port: int) -> bool:
        """Bind to a local port"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            local_ip = self.transport.network.get_local_ip()
            # Use 127.0.0.1 for actual OS socket binding to avoid OSError
            self.socket.bind(('127.0.0.1', port))
            self.local_addr = (local_ip, port)
            logger.info(f"UDP socket bound to {self.local_addr}")
            return True
        except Exception as e:
            logger.error(f"Bind failed: {e}")
            return False

    def sendto(self, data: bytes, addr: Tuple[str, int]) -> int:
        """Send data to a specific address"""
        if not self.socket:
            raise ConnectionError("Socket not bound")
        return self.socket.sendto(data, addr)

    def recvfrom(self, bufsize: int = 1024) -> Tuple[bytes, Tuple[str, int]]:
        """Receive data from sender"""
        if not self.socket:
            raise ConnectionError("Socket not bound")
        return self.socket.recvfrom(bufsize)

    def close(self):
        """Close the socket"""
        if self.socket:
            self.socket.close()


if __name__ == "__main__":
    # Simple test
    from .network_layer import NetworkLayer

    nl = NetworkLayer()
    nl.add_interface("eth0", "192.168.1.100")

    tl = TransportLayer(nl)

    def echo_handler(data: bytes, src_ip: str, src_port: int):
        print(f"Received {len(data)} bytes from {src_ip}:{src_port}")
        # Echo back (simplified)

    tl.start_listener(8080, echo_handler)
    print("Transport layer initialized")