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
        # network_topology is now a weighted graph: switch -> {neighbor: weight}
        self.network_topology: Dict[str, Dict[str, int]] = {}  
        self.flow_rules: Dict[str, List[FlowEntry]] = {}  # switch_id -> [flows]
        logger.info(f"SDN controller {self.controller_id} initialized")

    def register_switch(self, switch_id: str):
        """Register a new switch with the controller"""
        switch = OpenFlowSwitch(switch_id)
        self.switches[switch_id] = switch
        self.flow_rules[switch_id] = []
        self.network_topology[switch_id] = {}
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
            for neighbors in self.network_topology.values():
                if switch_id in neighbors:
                    del neighbors[switch_id]
            logger.info(f"Switch {switch_id} unregistered from controller")

    def register_user_to_switch(self, username: str, switch_id: str = None):
        """Dynamically add a user to the graph and attach them to a switch"""
        if switch_id is None:
            # Assign to the first available switch if none provided
            switches = sorted(list(self.switches.keys()))
            if switches:
                # Use hash of username to consistently assign same user to same switch
                switch_id = switches[hash(username) % len(switches)]
                
        if switch_id and switch_id in self.switches:
            if username not in self.network_topology:
                self.network_topology[username] = {}
            self.network_topology[username][switch_id] = 1
            self.network_topology[switch_id][username] = 1
            logger.info(f"Dynamically mapped user '{username}' to edge switch '{switch_id}'")
            return switch_id
        return None

    def add_flow_rule(self, switch_id: str, flow: FlowEntry):
        """Add a flow rule to a specific switch via controller"""
        if switch_id in self.switches:
            self.switches[switch_id].add_flow(flow)
            self.flow_rules[switch_id].append(flow)
            logger.info(f"Controller added flow rule to switch {switch_id}")
        else:
            logger.warning(f"Switch {switch_id} not found")

    def get_network_topology(self) -> Dict[str, Dict[str, int]]:
        """Get current network topology view"""
        return self.network_topology.copy()

    def calculate_shortest_path(self, src: str, dst: str) -> List[str]:
        """Calculate shortest path using Dijkstra's algorithm"""
        import heapq
        
        # Priority queue stores (cost, current_node, path)
        queue = [(0, src, [src])]
        visited = set()
        
        while queue:
            cost, node, path = heapq.heappop(queue)
            
            if node == dst:
                return path
                
            if node in visited:
                continue
                
            visited.add(node)
            
            for neighbor, weight in self.network_topology.get(node, {}).items():
                if neighbor not in visited:
                    heapq.heappush(queue, (cost + weight, neighbor, path + [neighbor]))
                    
        return [src]  # Fallback

    def calculate_traditional_path(self, src: str, dst: str) -> List[str]:
        """Calculate shortest path using BFS (ignores traffic congestion weights)"""
        import collections
        queue = collections.deque([[src]])
        visited = set([src])
        
        while queue:
            path = queue.popleft()
            node = path[-1]
            
            if node == dst:
                return path
                
            for neighbor in self.network_topology.get(node, {}).keys():
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(path + [neighbor])
                    
        return [src]  # Fallback


class SDNModule:
    """Main SDN module interface"""

    def __init__(self):
        self.controller: Optional[SDNController] = None
        self.is_active = False
        self.on_event_callback = None  # Hook for the Command Center
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

    def reset_topology(self):
        """Reset the SDN topology"""
        if not self.controller:
            self.activate()
        self.controller.switches = {}
        self.controller.network_topology = {}
        self.controller.flow_rules = {}
        self.baseline_links = []
        self.inactive_switches = set()
        logger.info("SDN topology reset")

    def _add_http_flow(self, switch_id: str, output_port: int):
        http_flow = FlowEntry(
            match_fields={'eth_type': 0x0800, 'ipv4_proto': 6, 'tcp_dst_port': 80},
            actions=[{'type': 'OUTPUT', 'port': output_port}],
            priority=100
        )
        self.controller.add_flow_rule(switch_id, http_flow)

    def _setup_baseline(self):
        # Add users to topology first
        users = ['userA', 'userB', 'userC', 'userD', 'userE', 'userF']
        switches = sorted(list(self.controller.switches.keys()))
        if switches:
            for i, u in enumerate(users):
                target_switch = switches[i % len(switches)]
                if u not in self.controller.network_topology:
                    self.controller.network_topology[u] = {}
                self.controller.network_topology[u][target_switch] = 1
                self.controller.network_topology[target_switch][u] = 1

        for src, neighbors in self.controller.network_topology.items():
            for dst in neighbors.keys():
                if (src, dst) not in self.baseline_links and (dst, src) not in self.baseline_links:
                    self.baseline_links.append((src, dst))

    def create_linear_topology(self, n=6):
        """Create a linear network topology"""
        self.reset_topology()
        for i in range(1, n+1):
            self.controller.register_switch(f"s{i}")
        for i in range(1, n):
            self.controller.network_topology[f"s{i}"][f"s{i+1}"] = 1
            self.controller.network_topology[f"s{i+1}"][f"s{i}"] = 1
        self._setup_baseline()
        if "s2" in self.controller.switches:
            self._add_http_flow("s2", 2)
        return self.controller

    def create_star_topology(self, n=6):
        """Create a star network topology (s1 is central)"""
        self.reset_topology()
        for i in range(1, n+1):
            self.controller.register_switch(f"s{i}")
        for i in range(2, n+1):
            self.controller.network_topology["s1"][f"s{i}"] = 1
            self.controller.network_topology[f"s{i}"]["s1"] = 1
        self._setup_baseline()
        if "s2" in self.controller.switches:
            self._add_http_flow("s2", 2)
        return self.controller
        
    def create_ring_topology(self, n=6):
        """Create a ring network topology"""
        self.reset_topology()
        for i in range(1, n+1):
            self.controller.register_switch(f"s{i}")
        for i in range(1, n+1):
            s_next = f"s{1 if i == n else i+1}"
            self.controller.network_topology[f"s{i}"][s_next] = 1
            self.controller.network_topology[s_next][f"s{i}"] = 1
        self._setup_baseline()
        if "s2" in self.controller.switches:
            self._add_http_flow("s2", 2)
        return self.controller

    def create_mesh_topology(self, n=6):
        """Create a partial mesh network topology"""
        self.reset_topology()
        for i in range(1, n+1):
            self.controller.register_switch(f"s{i}")
        import random
        for i in range(1, n+1):
            for j in range(i+1, n+1):
                if random.random() > 0.4:
                    self.controller.network_topology[f"s{i}"][f"s{j}"] = 1
                    self.controller.network_topology[f"s{j}"][f"s{i}"] = 1
        # Ensure connectivity
        for i in range(1, n):
            self.controller.network_topology[f"s{i}"][f"s{i+1}"] = 1
            self.controller.network_topology[f"s{i+1}"][f"s{i}"] = 1
        self._setup_baseline()
        if "s2" in self.controller.switches:
            self._add_http_flow("s2", 2)
        return self.controller
        
    def create_sample_topology(self):
        """Default to ring for demo so alternative paths exist for routing logic"""
        return self.create_ring_topology(6)
        
    def set_link_weight(self, src: str, dst: str, weight: int):
        """Update link weight (congestion/latency) dynamically"""
        if not self.controller: return False
        
        if src in self.controller.network_topology and dst in self.controller.network_topology[src]:
            self.controller.network_topology[src][dst] = weight
        if dst in self.controller.network_topology and src in self.controller.network_topology[dst]:
            self.controller.network_topology[dst][src] = weight
            
        self._emit_topology_update()
        return True
        
    def break_link(self, src: str, dst: str):
        """Sever a link between two nodes"""
        if not self.controller: return False
        
        if src in self.controller.network_topology:
            self.controller.network_topology[src].pop(dst, None)
        if dst in self.controller.network_topology:
            self.controller.network_topology[dst].pop(src, None)
            
        self._emit_topology_update()
        return True
        
    def create_link(self, src: str, dst: str, weight: int = 1):
        """Create a new link between two nodes"""
        if not self.controller: return False
        
        if src not in self.controller.network_topology:
            self.controller.network_topology[src] = {}
        if dst not in self.controller.network_topology:
            self.controller.network_topology[dst] = {}
            
        self.controller.network_topology[src][dst] = weight
        self.controller.network_topology[dst][src] = weight
        
        # Add to baseline so it persists if nodes are toggled off and on
        if (src, dst) not in self.baseline_links and (dst, src) not in self.baseline_links:
            self.baseline_links.append((src, dst))
            
        self._emit_topology_update()
        return True
        
    def add_switch(self):
        """Dynamically add a new switch"""
        if not self.controller: return None
        count = 1
        while f"s{count}" in self.controller.switches:
            count += 1
        new_id = f"s{count}"
        self.controller.register_switch(new_id)
        self._emit_topology_update()
        return new_id
        
    def _emit_topology_update(self):
        if self.on_event_callback:
            # We must serialize the Dict structure cleanly for JSON
            self.on_event_callback({
                "type": "topology_update",
                "topology": self.controller.network_topology.copy(),
                "inactive_switches": list(self.inactive_switches)
            })

    def toggle_switch(self, switch_id: str, active: bool):
        """Toggle a switch up or down for failure simulation"""
        if not self.controller or switch_id not in self.controller.switches:
            return False
            
        if active:
            if switch_id in self.inactive_switches:
                self.inactive_switches.remove(switch_id)
                # Re-add connections from baseline
                for src, dst in self.baseline_links:
                    if src == switch_id and dst not in self.inactive_switches:
                        self.controller.network_topology[src][dst] = 1
                        self.controller.network_topology[dst][src] = 1
                    elif dst == switch_id and src not in self.inactive_switches:
                        self.controller.network_topology[src][dst] = 1
                        self.controller.network_topology[dst][src] = 1
        else:
            if switch_id not in self.inactive_switches:
                self.inactive_switches.add(switch_id)
                # Remove all connections
                for peer in list(self.controller.network_topology.get(switch_id, {}).keys()):
                    if peer in self.controller.network_topology:
                        self.controller.network_topology[peer].pop(switch_id, None)
                self.controller.network_topology[switch_id].clear()
                
        self._emit_topology_update()
            
        return True

    def ban_user(self, user: str):
        """Block a user by pushing a firewall rule to the edge switch"""
        if not self.controller:
            return False
        
        if not hasattr(self, 'banned_users'):
            self.banned_users = set()
            
        if user not in self.banned_users:
            self.banned_users.add(user)
            if self.on_event_callback:
                self.on_event_callback({
                    "type": "user_banned",
                    "user": user
                })
        else:
            self.banned_users.remove(user)
            if self.on_event_callback:
                self.on_event_callback({
                    "type": "user_unbanned",
                    "user": user
                })
        return True

    def simulate_traditional_routing(self, src_user: str, msg_type: str, dst_user: str = "userB"):
        """Simulate traditional decentralized routing (ignores centralized firewall & dynamic traffic)"""
        if not self.controller or not self.is_active: return

        print(f"[TRADITIONAL NETWORKING] Routing packet from '{src_user}' to '{dst_user}' (Ignoring Traffic/Firewall)")
        
        # Build a static view of the network (slow convergence) using baseline_links
        # This means traditional routers don't instantly know when a link is severed!
        static_topology = {}
        for src, dst in self.baseline_links:
            if src not in static_topology: static_topology[src] = {}
            if dst not in static_topology: static_topology[dst] = {}
            static_topology[src][dst] = 1
            static_topology[dst][src] = 1
            
        # Also need to add the users, they are always connected to their edge switch in baseline
        for u in self.controller.network_topology.keys():
            if u.startswith('user'):
                for edge in self.controller.network_topology[u].keys():
                    if u not in static_topology: static_topology[u] = {}
                    if edge not in static_topology: static_topology[edge] = {}
                    static_topology[u][edge] = 1
                    static_topology[edge][u] = 1

        import collections
        queue = collections.deque([[src_user]])
        visited = set([src_user])
        path = [src_user]
        
        while queue:
            p = queue.popleft()
            node = p[-1]
            if node == dst_user:
                path = p
                break
            for neighbor in static_topology.get(node, {}).keys():
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(p + [neighbor])
        
        if len(path) <= 1 and src_user != dst_user:
            if self.on_event_callback:
                self.on_event_callback({"type": "packet_dropped_trad", "src_user": src_user, "reason": "Destination Unreachable (No Route)"})
            return
            
        # NOW, simulate the packet actually traversing the path!
        # If any link on the static path is ACTUALLY severed in the real topology, the packet drops!
        for i in range(len(path) - 1):
            u = path[i]
            v = path[i+1]
            if v not in self.controller.network_topology.get(u, {}) or self.controller.network_topology[u][v] == 0:
                print(f"[TRADITIONAL NETWORKING] Packet hit severed link {u}-{v}! Dropping.")
                if self.on_event_callback:
                    self.on_event_callback({
                        "type": "packet_dropped_trad", 
                        "src_user": src_user, 
                        "reason": f"Hit Severed Link {u}-{v} (Slow Convergence)"
                    })
                return
            
        if self.on_event_callback:
            self.on_event_callback({
                "type": "packet_routed_trad",
                "src_user": src_user,
                "dst_user": dst_user,
                "msg_type": msg_type,
                "path": path
            })

    def simulate_chat_routing(self, src_user: str, msg_type: str, dst_user: str = "userB"):
        """Simulate routing a chat message through both topologies"""
        # Run Traditional Routing Simulation first
        self.simulate_traditional_routing(src_user, msg_type, dst_user)

        if not self.controller or not self.is_active:
            return

        if hasattr(self, 'banned_users') and src_user in self.banned_users:
            print(f"[SDN CONTROLLER] Packet from '{src_user}' DROPPED by firewall rule.")
            if self.on_event_callback:
                self.on_event_callback({
                    "type": "packet_dropped_sdn",
                    "src_user": src_user,
                    "reason": "Firewall Rule (Banned)"
                })
            return

        print(f"\n=======================================================")
        print(f"[SDN CONTROLLER] Intercepted {msg_type} from '{src_user}' to '{dst_user}'")
        print(f"[SDN CONTROLLER] -> PACKET_IN received from edge switch.")
        
        if src_user not in self.controller.network_topology or dst_user not in self.controller.network_topology:
            print(f"[SDN CONTROLLER] -> ERROR: User endpoint not found in topology.")
            if self.on_event_callback:
                self.on_event_callback({
                    "type": "packet_dropped_sdn",
                    "src_user": src_user,
                    "reason": "Destination Unreachable (No Route)"
                })
            return
            
        # Determine path directly from src_user to dst_user
        path = self.controller.calculate_shortest_path(src_user, dst_user)
        
        if len(path) <= 1 and src_user != dst_user:
            print(f"[SDN CONTROLLER] -> ERROR: No path found to destination.")
            if self.on_event_callback:
                self.on_event_callback({
                    "type": "packet_dropped_sdn",
                    "src_user": src_user,
                    "reason": "Destination Unreachable (No Route)"
                })
            return
            
        path_str = " -> ".join(path)
        print(f"[SDN CONTROLLER] -> Calculating optimal path ({src_user} -> {dst_user})... Found: {path_str}")
        
        # Simulate flow modification
        switches_in_path = [n for n in path if n.startswith('s')]
        if switches_in_path:
            print(f"[SDN CONTROLLER] -> Pushing FLOW_MOD rules to switches {', '.join(switches_in_path)}...")
            time.sleep(0.1)
            for i, switch_id in enumerate(switches_in_path):
                action = f"OUTPUT=Port_{i+1}" if i < len(switches_in_path)-1 else "DELIVER_LOCAL"
                print(f"  [OPENFLOW] Switch {switch_id}: Installing flow entry: Match [APP_SRC={src_user}] -> Action [{action}]")
            
        print(f"[SDN DATA PLANE] Packet routed successfully via {path_str}")
        print(f"=======================================================\n")
        
        if self.on_event_callback:
            self.on_event_callback({
                "type": "packet_routed_sdn",
                "src_user": src_user,
                "dst_user": dst_user,
                "msg_type": msg_type,
                "path": path
            })


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