#!/usr/bin/env python3
"""
Sample chatting application demonstrating networking concepts
Can be configured to emphasize SDN, Wireless, or 5G aspects
"""

import argparse
import sys
import os
import yaml
import threading
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')

# Add project root and src directory to path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

from src.core.network_layer import NetworkLayer
from src.core.transport_layer import TransportLayer
from src.core.application_layer import ChatServer, ChatClient, ChatMessage, MessageType
from src.modules.sdn.sdn_module import SDNModule
from src.modules.wireless.wireless_module import WirelessModule
from src.modules._5g._5g_module import _5gModule


class NetworkingApp:
    """Main application that integrates networking concepts"""

    def __init__(self, config_file: str = None):
        self.config = self._load_config(config_file)
        self.network_layer = NetworkLayer()
        self.transport_layer = TransportLayer(self.network_layer)
        self.modules = {}
        self.chat_server = None
        self.chat_client = None
        self.running = False

        # Initialize basic network interface
        self.network_layer.add_interface("eth0", "192.168.1.100")
        self.network_layer.add_route("0.0.0.0/0", "192.168.1.1")

        # Load modules based on configuration
        self._load_modules()

    def _load_config(self, config_file: str) -> dict:
        """Load configuration from YAML file"""
        default_config = {
            'sdn': {'enabled': False},
            'wireless': {'enabled': False},
            '_5g': {'enabled': False},
            'chat': {
                'server_port': 8888,
                'server_host': 'localhost'
            }
        }

        if not config_file or not os.path.exists(config_file):
            return default_config

        try:
            with open(config_file, 'r') as f:
                user_config = yaml.safe_load(f)
                # Merge with defaults
                for key in default_config:
                    if key in user_config:
                        default_config[key].update(user_config[key])
                return default_config
        except Exception as e:
            print(f"Error loading config: {e}")
            return default_config

    def _load_modules(self):
        """Load enabled modules based on configuration"""
        if self.config.get('sdn', {}).get('enabled', False):
            self.modules['sdn'] = SDNModule()
            self.modules['sdn'].activate()
            # Create sample topology for demo
            self.modules['sdn'].create_sample_topology()
            print("SDN module loaded and activated")

        if self.config.get('wireless', {}).get('enabled', False):
            self.modules['wireless'] = WirelessModule()
            self.modules['wireless'].activate()
            print("Wireless module loaded and activated")

        if self.config.get('_5g', {}).get('enabled', False):
            self.modules['_5g'] = _5gModule()
            self.modules['_5g'].activate()
            print("5G module loaded and activated")

    def start_server(self):
        """Start the chat server"""
        port = self.config.get('chat', {}).get('server_port', 8888)
        self.chat_server = ChatServer(self.transport_layer, port)
        
        # Connect simulation hook
        self.chat_server.on_message_broadcast = self._simulate_routing
            
        self.chat_server.start()
        print(f"Chat server started on port {self.chat_server.port}")

    def _simulate_routing(self, message: ChatMessage):
        """Callback to trigger visual routing simulation when a message is sent"""
        if message.type == MessageType.USER_LIST:
            # Dynamically map new users to the topology
            if 'sdn' in self.modules and self.modules['sdn'].is_active:
                users = message.content.split(',')
                for user in users:
                    if user.strip():
                        self.modules['sdn'].controller.register_user_to_switch(user.strip())
            return
            
        if 'sdn' in self.modules and self.modules['sdn'].is_active:
            # Determine destination (broadcast or specific)
            dst_user = "broadcast"
            # For this demo, let's just pick another active user if possible, or broadcast
            active_users = [u for u in self.chat_server.users.keys() if u != message.username]
            if active_users:
                dst_user = active_users[0] # Route to the first other user found
                
            self.modules['sdn'].simulate_chat_routing(
                src_user=message.username,
                msg_type=message.type.name,
                dst_user=dst_user
            )
            
        if 'wireless' in self.modules and self.modules['wireless'].is_active:
            self.modules['wireless'].simulate_wireless_transmission(
                src_user=message.username,
                msg_type=message.type.name
            )
            
        if '_5g' in self.modules and self.modules['_5g'].is_active:
            self.modules['_5g'].simulate_5g_transmission(
                src_user=message.username,
                msg_type=message.type.name
            )

    def start_client(self, username: str):
        """Start the chat client"""
        host = self.config.get('chat', {}).get('server_host', 'localhost')
        port = self.config.get('chat', {}).get('server_port', 8888)
        self.chat_client = ChatClient(self.transport_layer, host, port)
        if self.chat_client.connect(username):
            print(f"Connected to chat server as {username}")
            # Set up message callback
            self.chat_client.set_message_callback(self._on_message_received)
            return True
        else:
            print("Failed to connect to chat server")
            return False

    def _on_message_received(self, message: ChatMessage):
        """Callback for received messages"""
        timestamp = time.strftime('%H:%M:%S', time.localtime(message.timestamp))
        print(f"[{timestamp}] {message.username}: {message.content}")

    def send_message(self, content: str):
        """Send a message via the client"""
        if self.chat_client:
            self.chat_client.send_message(content)

    def get_emphasis_info(self) -> dict:
        """Get information about what aspects are emphasized"""
        emphasis = {}
        if self.config.get('sdn', {}).get('enabled', False):
            emphasis['SDN'] = [
                'Centralized control plane',
                'OpenFlow protocol simulation',
                'Flow table management',
                'Network programmability'
            ]
        if self.config.get('wireless', {}).get('enabled', False):
            emphasis['Wireless'] = [
                'Wireless access point simulation',
                'Handoff management',
                'Channel modeling',
                'Mobile network concepts'
            ]
        if self.config.get('_5g', {}).get('enabled', False):
            emphasis['5G'] = [
                '5G base station (gNodeB) concepts',
                'Network slicing',
                'QoS management for URLLC/eMMB/mMTC',
                'Massive connectivity'
            ]
        return emphasis

    def print_status(self):
        """Print current application status"""
        print("\n=== Networking Application Status ===")
        print(f"Running: {self.running}")
        print(f"Loaded modules: {list(self.modules.keys())}")
        emphasis = self.get_emphasis_info()
        if emphasis:
            print("Emphasized aspects:")
            for tech, aspects in emphasis.items():
                print(f"  {tech}: {', '.join(aspects)}")
        else:
            print("No specific emphasis (core networking only)")
        print("=====================================\n")

    def run_interactive(self):
        """Run the application in interactive mode"""
        self.running = True
        self.print_status()

        print("Commands:")
        print("  /help - Show this help")
        print("  /status - Show application status")
        print("  /traffic <src> <dst> <level> - Congest a link (e.g., /traffic s1 s2 20)")
        print("  /sever <src> <dst> - Break a link (e.g., /sever s1 s2)")
        print("  /ban <user> - Block a user via firewall")
        print("  /msg <text> - Send a chat message")
        print("  /quit - Exit the application")
        print()

        while self.running:
            try:
                user_input = input("> ").strip()
                if not user_input:
                    continue

                if user_input == "/help":
                    print("Commands:")
                    print("  /help - Show this help")
                    print("  /status - Show application status")
                    print("  /traffic <src> <dst> <level> - Congest a link")
                    print("  /sever <src> <dst> - Break a link")
                    print("  /ban <user> - Block a user via firewall")
                    print("  /msg <text> - Send a chat message")
                    print("  /quit - Exit the application")
                elif user_input == "/status":
                    self.print_status()
                elif user_input.startswith("/traffic "):
                    parts = user_input.split()
                    if len(parts) == 4 and 'sdn' in self.modules and self.modules['sdn'].is_active:
                        src, dst, weight = parts[1], parts[2], int(parts[3])
                        if self.modules['sdn'].set_link_weight(src, dst, weight):
                            print(f"[NETWORK ADMIN] Link {src}-{dst} traffic level set to {weight}")
                        else:
                            print(f"[NETWORK ADMIN] Failed to update link {src}-{dst}")
                    else:
                        print("Usage: /traffic <src> <dst> <level> (Requires Server Mode / Local SDN)")
                elif user_input.startswith("/sever "):
                    parts = user_input.split()
                    if len(parts) == 3 and 'sdn' in self.modules and self.modules['sdn'].is_active:
                        src, dst = parts[1], parts[2]
                        if self.modules['sdn'].break_link(src, dst):
                            print(f"[NETWORK ADMIN] Severed link {src}-{dst}")
                    else:
                        print("Usage: /sever <src> <dst> (Requires Server Mode / Local SDN)")
                elif user_input.startswith("/ban "):
                    parts = user_input.split()
                    if len(parts) == 2 and 'sdn' in self.modules and self.modules['sdn'].is_active:
                        user = parts[1]
                        if self.modules['sdn'].ban_user(user):
                            print(f"[NETWORK ADMIN] Firewall ban toggled for {user}")
                    else:
                        print("Usage: /ban <user> (Requires Server Mode / Local SDN)")
                elif user_input.startswith("/msg "):
                    message = user_input[5:]
                    if message:
                        self.send_message(message)
                    else:
                        print("Please provide a message to send")
                elif user_input == "/quit":
                    self.running = False
                    break
                else:
                    # Treat as chat message
                    self.send_message(user_input)
            except KeyboardInterrupt:
                self.running = False
                break
            except EOFError:
                self.running = False
                break

        # Cleanup
        if self.chat_client:
            self.chat_client.disconnect()
        print("Application stopped")


def main():
    parser = argparse.ArgumentParser(description='SDN-Wireless-5G Networking Application')
    parser.add_argument('--config', '-c', type=str, help='Configuration file path')
    parser.add_argument('--server', '-s', action='store_true', help='Run as server')
    parser.add_argument('--client', '-cl', type=str, help='Run as client with username')
    parser.add_argument('--interactive', '-i', action='store_true', help='Run in interactive mode')
    parser.add_argument('--port', '-p', type=int, default=8888, help='Port to run server on or connect to')

    args = parser.parse_args()

    app = NetworkingApp(args.config)
    
    # Override port if provided
    if 'chat' not in app.config:
        app.config['chat'] = {}
    app.config['chat']['server_port'] = args.port

    if args.server:
        app.start_server()
        print("Server running. Press Ctrl+C to stop.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping server...")
    elif args.client:
        if app.start_client(args.client):
            print("Client connected. Type messages to send (Ctrl+C to quit).")
            try:
                app.run_interactive()
            except KeyboardInterrupt:
                print("\nDisconnecting...")
                app.chat_client.disconnect()
        else:
            sys.exit(1)
    elif args.interactive:
        app.run_interactive()
    else:
        # Default: show info and run interactive
        print("SDN-Wireless-5G Networking Application")
        print("=====================================")
        emphasis = app.get_emphasis_info()
        if emphasis:
            print("Current emphasis:")
            for tech, aspects in emphasis.items():
                print(f"  {tech}: {', '.join(aspects)}")
        else:
            print("No specific emphasis - core networking only")
        print()
        app.run_interactive()


if __name__ == "__main__":
    main()