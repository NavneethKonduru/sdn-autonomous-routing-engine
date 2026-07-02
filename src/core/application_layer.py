"""
Application layer functionality
Handles application-level protocols like our chat protocol
"""

import json
import time
import uuid
import threading
import struct
from enum import Enum
from typing import Dict, List, Optional, Callable
from .transport_layer import TransportLayer, TCPSocket
import logging

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """Types of chat messages"""
    JOIN = "join"
    LEAVE = "leave"
    MESSAGE = "message"
    USER_LIST = "user_list"
    ERROR = "error"


class ChatMessage:
    """Represents a chat message"""

    def __init__(self, msg_type: MessageType, username: str,
                 content: str = "", timestamp: float = None):
        self.type = msg_type
        self.username = username
        self.content = content
        self.timestamp = timestamp or time.time()
        self.message_id = str(uuid.uuid4())

    def to_json(self) -> str:
        """Serialize message to JSON"""
        return json.dumps({
            'type': self.type.value,
            'username': self.username,
            'content': self.content,
            'timestamp': self.timestamp,
            'message_id': self.message_id
        })

    @classmethod
    def from_json(cls, json_str: str) -> 'ChatMessage':
        """Deserialize message from JSON"""
        data = json.loads(json_str)
        return cls(
            msg_type=MessageType(data['type']),
            username=data['username'],
            content=data['content'],
            timestamp=data['timestamp']
        )


class ChatProtocol:
    """Handles chat protocol encoding/decoding"""

    @staticmethod
    def encode_message(message: ChatMessage) -> bytes:
        """Encode a chat message for transmission"""
        json_data = message.to_json()
        # Add length prefix for framing
        length_prefix = struct.pack('!I', len(json_data))
        return length_prefix + json_data.encode('utf-8')

    @staticmethod
    def decode_message(data: bytes) -> Optional[ChatMessage]:
        """Decode a chat message from bytes"""
        if len(data) < 4:
            return None

        # Extract length prefix
        length = struct.unpack('!I', data[:4])[0]
        if len(data) < 4 + length:
            return None  # Not enough data yet

        json_data = data[4:4+length].decode('utf-8')
        try:
            return ChatMessage.from_json(json_data)
        except Exception as e:
            logger.error(f"Failed to decode message: {e}")
            return None


class ChatServer:
    """Chat server implementation"""

    def __init__(self, transport_layer: TransportLayer, port: int = 8888):
        self.transport = transport_layer
        self.port = port
        self.users: Dict[str, Tuple[str, TCPSocket]] = {}  # username -> (addr, socket)
        self.messages: List[ChatMessage] = []
        self.running = False
        self.on_message_broadcast: Optional[Callable[['ChatMessage'], None]] = None
        logger.info(f"Chat server initialized on port {port}")

    def start(self):
        """Start the chat server"""
        def client_handler(data: bytes, client_ip: str, client_port: int, tcp_sock=None):
            self._handle_client_data(data, client_ip, client_port, tcp_sock)

        self.transport.register_handler(self.port, lambda p: None)  # Placeholder
        actual_port = self.transport.start_listener(self.port, client_handler)
        if actual_port != -1:
            self.port = actual_port
            self.running = True
            logger.info(f"Chat server started on port {self.port}")
        else:
            logger.error("Failed to start chat server: No available ports")

    def _handle_client_data(self, data: bytes, client_ip: str, client_port: int, tcp_sock=None):
        """Handle incoming data from a client"""
        try:
            message = ChatProtocol.decode_message(data)
            if message:
                self._process_message(message, client_ip, client_port, tcp_sock)
            else:
                logger.warning(f"Failed to decode message from {client_ip}:{client_port}")
        except Exception as e:
            logger.error(f"Error handling client data: {e}")

    def _process_message(self, message: ChatMessage, client_ip: str, client_port: int, tcp_sock=None):
        """Process a decoded chat message based on its type"""
        if message.type == MessageType.JOIN:
            self._handle_join(message, client_ip, client_port, tcp_sock)
        elif message.type == MessageType.LEAVE:
            self._handle_leave(message, client_ip, client_port, tcp_sock)
        elif message.type == MessageType.MESSAGE:
            self._handle_message(message, client_ip, client_port, tcp_sock)
        else:
            logger.warning(f"Unknown message type: {message.type}")

    def _handle_join(self, message: ChatMessage, client_ip: str, client_port: int, tcp_sock=None):
        """Handle user joining the chat"""
        username = message.username
        self.users[username] = ((client_ip, client_port), tcp_sock)
        join_msg = ChatMessage(
            MessageType.JOIN,
            "Server",
            f"{username} has joined the chat"
        )
        self.broadcast_message(join_msg, exclude=username)
        self._send_user_list(username)
        logger.info(f"User {username} joined from {client_ip}:{client_port}")

    def _handle_leave(self, message: ChatMessage, client_ip: str, client_port: int, tcp_sock=None):
        """Handle user leaving the chat"""
        username = message.username
        if username in self.users:
            del self.users[username]
            leave_msg = ChatMessage(
                MessageType.LEAVE,
                "Server",
                f"{username} has left the chat"
            )
            self.broadcast_message(leave_msg)
            logger.info(f"User {username} left")

    def _handle_message(self, message: ChatMessage, client_ip: str, client_port: int, tcp_sock=None):
        """Handle a chat message from a user"""
        # Store message
        self.messages.append(message)
        # Broadcast to all users
        self.broadcast_message(message)
        logger.info(f"Message from {message.username}: {message.content}")

    def broadcast_message(self, message: ChatMessage, exclude: str = None):
        """Broadcast a message to all connected users"""
        if self.on_message_broadcast:
            self.on_message_broadcast(message)
            
        encoded = ChatProtocol.encode_message(message)
        for username, (addr, sock) in self.users.items():
            if username != exclude and sock:
                try:
                    sock.send(encoded)
                except Exception as e:
                    logger.error(f"Failed to send to {username}: {e}")

    def _send_user_list(self, username: str):
        """Send current user list to a specific user"""
        user_list = ChatMessage(
            MessageType.USER_LIST,
            "Server",
            ",".join(self.users.keys())
        )
        if self.on_message_broadcast:
            self.on_message_broadcast(user_list)
        # In real implementation, we'd send this to specific user
        logger.info(f"User list for {username}: {user_list.content}")


class ChatClient:
    """Chat client implementation"""

    def __init__(self, transport_layer: TransportLayer,
                 server_host: str, server_port: int = 8888):
        self.transport = transport_layer
        self.server_host = server_host
        self.server_port = server_port
        self.socket: Optional[TCPSocket] = None
        self.username: Optional[str] = None
        self.running = False
        self.message_callback: Optional[Callable[[ChatMessage], None]] = None
        logger.info(f"Chat client initialized for {server_host}:{server_port}")

    def connect(self, username: str) -> bool:
        """Connect to the chat server"""
        self.username = username
        self.socket = TCPSocket(self.transport)

        if not self.socket.connect(self.server_host, self.server_port):
            return False

        # Send join message
        join_msg = ChatMessage(MessageType.JOIN, username)
        self._send_message(join_msg)

        # Start listener thread
        self.running = True
        threading.Thread(target=self._listen_for_messages, daemon=True).start()
        return True

    def _listen_for_messages(self):
        """Listen for incoming messages from server"""
        buffer = b""
        while self.running and self.socket:
            try:
                data = self.socket.recv(4096)
                if not data:
                    break
                buffer += data

                # Process complete messages
                while len(buffer) >= 4:
                    msg_len = struct.unpack('!I', buffer[:4])[0]
                    if len(buffer) < 4 + msg_len:
                        break
                    msg_data = buffer[:4+msg_len]
                    buffer = buffer[4+msg_len:]

                    message = ChatProtocol.decode_message(msg_data)
                    if message and self.message_callback:
                        self.message_callback(message)
            except Exception as e:
                if self.running:
                    logger.error(f"Error in message listener: {e}")
                break

    def send_message(self, content: str):
        """Send a chat message"""
        if not self.username or not self.socket:
            logger.error("Not connected")
            return

        msg = ChatMessage(MessageType.MESSAGE, self.username, content)
        self._send_message(msg)

    def _send_message(self, message: ChatMessage):
        """Send a message to the server"""
        if not self.socket:
            return
        encoded = ChatProtocol.encode_message(message)
        try:
            self.socket.send(encoded)
        except Exception as e:
            logger.error(f"Failed to send message: {e}")

    def set_message_callback(self, callback: Callable[[ChatMessage], None]):
        """Set callback for incoming messages"""
        self.message_callback = callback

    def disconnect(self):
        """Disconnect from the server"""
        if self.username and self.socket:
            leave_msg = ChatMessage(MessageType.LEAVE, self.username)
            self._send_message(leave_msg)
        self.running = False
        if self.socket:
            self.socket.close()
            self.socket = None


if __name__ == "__main__":
    # Simple test
    from ..core.network_layer import NetworkLayer
    from ..core.transport_layer import TransportLayer

    nl = NetworkLayer()
    nl.add_interface("eth0", "192.168.1.100")

    tl = TransportLayer(nl)
    print("Application layer components created")