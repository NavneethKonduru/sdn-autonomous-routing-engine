"""
SDN (Software Defined Networking) module
Implements SDN-specific concepts like centralized control, OpenFlow simulation
"""

import threading
import time
from typing import Dict, List, Tuple, Optional, Set
import logging
from core.network_layer import NetworkLayer, Packet
from core.transport_layer import TransportLayer

logger = logging.getLogger(__name__)


class FlowEntry:
    """Represents an OpenFlow flow entry"""

    def __init__(self, match_fields: Dict, actions: List[Dict],
                 priority: int = 0, idle_timeout: int = 0,
                 hard_timeout: int = 0):
        self.match_fields = match_fields  # e.g., {'eth_type': 0x0800, 'ipv4_src': '192.168.1.0/24'}
        self.actions = actions            # e.g., [{'type': 'OUTPUT', 'port': 1}]
        self.priority = priority
        self.idle_timeout = idle_timeout
        self.hard_timeout = hard_timeout
        self.packet_count = 0
        self.byte_count = 0
        self.created_time = time.time()


class OpenFlowSwitch:
    """Simulated OpenFlow switch"""

    def __init__(self, switch_id: str):
        self.switch_id = switch_id
        self.flow_table: List[FlowEntry] = []
        self.port_map: Dict[str, int] = {}  # port_name -> port_number
        self.connected_to_controller: bool = False
        logger.info(f"OpenFlow switch {switch_id} initialized")

    def add_flow(self, flow: FlowEntry):
        """Add a flow entry to the flow table"""
        self.flow_table.append(flow)
        # Sort by priority (higher priority first)
        self.flow_table.sort(key=lambda f: f.priority, reverse=True)
        logger.info(f"Added flow to switch {self.switch_id}: {flow.match_fields}")

    def remove_flow(self, match_fields: Dict):
        """Remove flow entries matching criteria"""
        initial_count = len(self.flow_table)
        self.flow_table = [
            f for f in self.flow_table
            if not all(f.match_fields.get(k) == v for k, v in match_fields.items())
        ]
        removed = initial_count - len(self.flow_table)
        logger.info(f"Removed {removed} flows from switch {self.switch_id}")

    def process_packet(self, packet: Packet) -> List[Dict]:
        """Process a packet through the flow table"""
        actions = []
        for flow in self.flow_table:
            if self._matches_flow(packet, flow):
                actions.extend(flow.actions)
                flow.packet_count += 1
                flow.byte_count += len(packet.payload) if packet.payload else 0
                break  # First matching flow wins (in real OF, it's more complex)
        return actions

    def _matches_flow(self, packet: Packet, flow: FlowEntry) -> bool:
        """Check if packet matches flow entry"""
        for field, value in flow.match_fields.items():
            # Simplified matching - real implementation would be more complex
            if field == 'eth_type' and hasattr(packet, 'eth_type'):
                if packet.eth_type != value:
                    return False
            elif field == 'ipv4_src' and hasattr(packet, 'src_ip'):
                # Simplified IP matching
                if not packet.src_ip.startswith(value.split('/')[0].rsplit('.', 1)[0]):
                    return False
            # Add more field types as needed
        return True


class SDNController:
    """Centralized SDN controller"""

    def __init__(self, controller_id: str = "controller-1"):
        self.controller_id = controller_id
        self.switches: Dict[str, OpenFlowSwitch] = {}
        self.network_topology: Dict[str, Set[str]] = {}  # switch -> {neighbor_switches}
        self.flow_rules: Dict[str, List[FlowEntry]] = {}  # switch_id -> [flows]
        logger.info(f"SDN controller {self.controller_id} initialized")

    def register_switch(self, switch_id: str):
        """Register a new switch with the controller"""
        switch = OpenFlowSwitch(switch_id)
        self.switches[switch_id] = switch
        self.flow_rules[switch_id] = []
        self.network_topology[switch_id] = set()
        switch.connected_to_controller = True
        logger.info(f"Switch {switch_id} registered with controller")
        return switch

    def uninstall_switch(self, switch_id: str):
        """Remove a switch from controller management"""
        if switch_id in self.switches:
            del self.switches[switch_id]
            del self.flow_rules[switch_id]
            del self.network_topology[switch_id]
            # Remove from topology maps of other switches
            for switch in self.network_topology.values():
                switch.discard(switch_id)
            logger.info(f"Switch {switch_id} unregistered from controller")

    def add_flow_rule(self, switch_id: str, flow: FlowEntry):
        """Add a flow rule to a specific switch via controller"""
        if switch_id in self.switches:
            self.switches[switch_id].add_flow(flow)
            self.flow_rules[switch_id].append(flow)
            logger.info(f"Controller added flow rule to switch {switch_id}")
        else:
            logger.warning(f"Switch {switch_id} not found")

    def get_network_topology(self) -> Dict[str, Set[str]]:
        """Get current network topology view"""
        return self.network_topology.copy()

    def calculate_shortest_path(self, src: str, dst: str) -> List[str]:
        """Calculate shortest path between switches"""
        # Basic BFS to find shortest path
        queue = [[src]]
        visited = set([src])
        
        while queue:
            path = queue.pop(0)
            node = path[-1]
            
            if node == dst:
                return path
                
            for adjacent in self.network_topology.get(node, set()):
                if adjacent not in visited:
                    visited.add(adjacent)
                    new_path = list(path)
                    new_path.append(adjacent)
                    queue.append(new_path)
                    
        return [src]  # Fallback


class SDNModule:
    """Main SDN module interface"""

    def __init__(self):
        self.controller: Optional[SDNController] = None
        self.is_active = False
        logger.info("SDN module initialized")

    def activate(self):
        """Activate the SDN module"""
        if not self.is_active:
            self.controller = SDNController()
            self.is_active = True
            logger.info("SDN module activated")

    def deactivate(self):
        """Deactivate the SDN module"""
        self.is_active = False
        self.controller = None
        logger.info("SDN module deactivated")

    def create_sample_topology(self):
        """Create a sample network topology for demonstration"""
        if not self.controller:
            self.activate()

        # Create switches
        s1 = self.controller.register_switch("s1")
        s2 = self.controller.register_switch("s2")
        s3 = self.controller.register_switch("s3")

        # Create topology (linear: s1-s2-s3)
        self.controller.network_topology["s1"].add("s2")
        self.controller.network_topology["s2"].add("s1")
        self.controller.network_topology["s2"].add("s3")
        self.controller.network_topology["s3"].add("s2")

        # Add sample flow rules
        # Allow HTTP traffic from s1 to s3 via s2
        http_flow = FlowEntry(
            match_fields={'eth_type': 0x0800, 'ipv4_proto': 6, 'tcp_dst_port': 80},
            actions=[{'type': 'OUTPUT', 'port': 2}],
            priority=100
        )
        self.controller.add_flow_rule("s2", http_flow)

        logger.info("Sample SDN topology created")
        return self.controller

    def simulate_chat_routing(self, src_user: str, msg_type: str):
        """Simulate routing a chat message through the SDN topology"""
        if not self.controller or not self.is_active:
            return

        print(f"\n=======================================================")
        print(f"[SDN CONTROLLER] Intercepted {msg_type} from '{src_user}'")
        print(f"[SDN CONTROLLER] -> PACKET_IN received from edge switch.")
        
        # Determine path
        path = self.controller.calculate_shortest_path("s1", "s3") # Simplified fixed path for demo
        path_str = " -> ".join(path)
        print(f"[SDN CONTROLLER] -> Calculating optimal path... Found: {path_str}")
        
        # Simulate flow modification
        print(f"[SDN CONTROLLER] -> Pushing FLOW_MOD rules to switches {', '.join(path)}...")
        time.sleep(0.5)
        
        for i, switch_id in enumerate(path):
            action = f"OUTPUT=Port_{i+1}" if i < len(path)-1 else "DELIVER_LOCAL"
            print(f"  [OPENFLOW] Switch {switch_id}: Installing flow entry: Match [APP_SRC={src_user}] -> Action [{action}]")
            time.sleep(0.2)
            
        print(f"[SDN DATA PLANE] Packet routed successfully via {path_str}")
        print(f"=======================================================\n")


def get_sdn_module_info() -> Dict:
    """Get information about SDN capabilities for reporting"""
    return {
        'concepts': [
            'Centralized Control Plane',
            'Data Plane Separation',
            'OpenFlow Protocol',
            'Flow Table Management',
            'Network Programmability'
        ],
        'protocols': ['OpenFlow', 'NETCONF', 'RESTCONF'],
        'architectures': ['Imperative SDN', 'Declarative SDN', 'Hybrid SDN'],
        'applications': [
            'Traffic Engineering',
            'Network Virtualization',
            'Security Policies',
            'QoS Management'
        ]
    }


if __name__ == "__main__":
    # Simple test
    sdn = SDNModule()
    topology = sdn.create_sample_topology()
    print(f"SDN module ready with {len(topology.switches)} switches")