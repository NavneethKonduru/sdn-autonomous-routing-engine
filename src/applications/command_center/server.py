import os
import sys
import logging
from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

from src.applications.chat_app.chat_app import NetworkingApp
from src.core.application_layer import ChatMessage, MessageType

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger('CommandCenter')

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize SDN App
network_app = NetworkingApp()
network_app.config['sdn'] = {'enabled': True}
network_app._load_modules()
sdn_module = network_app.modules['sdn']

def sdn_event_callback(event_data):
    """Callback when SDN module emits an event, forwards to websocket clients"""
    logger.info(f"Forwarding SDN Event to WS: {event_data['type']}")
    socketio.emit('sdn_event', event_data)

sdn_module.on_event_callback = sdn_event_callback

# Start internal chat server manually so routing triggers work
# Using a background thread so it doesn't block Flask
import threading
server_thread = threading.Thread(target=network_app.start_server, daemon=True)
server_thread.start()

@app.route('/api/status', methods=['GET'])
def get_status():
    if not sdn_module.controller:
        return jsonify({"status": "error", "message": "SDN not initialized"}), 500
        
    topology = {k: dict(v) for k, v in sdn_module.controller.network_topology.items()}
    return jsonify({
        "status": "running",
        "topology": topology,
        "inactive_switches": list(sdn_module.inactive_switches)
    })

@socketio.on('connect')
def handle_connect():
    logger.info("Client connected")
    if sdn_module.controller:
        emit('sdn_event', {
            "type": "topology_update",
            "topology": sdn_module.controller.network_topology.copy(),
            "inactive_switches": list(sdn_module.inactive_switches)
        })

@socketio.on('command')
def handle_command(data):
    """Handle commands from the frontend UI"""
    cmd_type = data.get('type')
    
    if cmd_type == 'toggle_switch':
        switch_id = data.get('switch_id', 's2')
        active = data.get('active', False)
        logger.info(f"Command Center toggling switch {switch_id} to {'active' if active else 'inactive'}")
        success = sdn_module.toggle_switch(switch_id, active)
        if success:
            emit('command_response', {"status": "success", "message": f"Switch {switch_id} {'enabled' if active else 'disabled'}"})
        else:
            emit('command_response', {"status": "error", "message": f"Failed to toggle switch {switch_id}"})
            
    elif cmd_type == 'set_link_weight':
        src = data.get('src')
        dst = data.get('dst')
        weight = data.get('weight', 10)
        logger.info(f"Command Center setting congestion on link {src}-{dst} to {weight}")
        success = sdn_module.set_link_weight(src, dst, weight)
        if success:
            emit('command_response', {"status": "success", "message": f"Congestion set to {weight} for link {src}-{dst}"})
        else:
            emit('command_response', {"status": "error", "message": f"Failed to set link weight for {src}-{dst}"})
            
    elif cmd_type == 'break_link':
        src = data.get('src')
        dst = data.get('dst')
        success = sdn_module.break_link(src, dst)
        if success:
            emit('command_response', {"status": "success", "message": f"Severed link {src}-{dst}"})
            
    elif cmd_type == 'create_link':
        src = data.get('src')
        dst = data.get('dst')
        success = sdn_module.create_link(src, dst)
        if success:
            emit('command_response', {"status": "success", "message": f"Created link {src}-{dst}"})
            
    elif cmd_type == 'add_switch':
        new_id = sdn_module.add_switch()
        if new_id:
            emit('command_response', {"status": "success", "message": f"Added new switch {new_id}"})
            
    elif cmd_type == 'ban_user':
        user = data.get('user', 'userA')
        logger.info(f"Command Center banning/unbanning user {user}")
        success = sdn_module.ban_user(user)
        if success:
            emit('command_response', {"status": "success", "message": f"Firewall rule toggled for {user}."})
        else:
            emit('command_response', {"status": "error", "message": f"Failed to toggle firewall for {user}"})
            
    elif cmd_type == 'set_topology':
        topo_type = data.get('topology', 'linear')
        logger.info(f"Command Center setting topology to {topo_type}")
        if topo_type == 'linear':
            sdn_module.create_linear_topology(6)
        elif topo_type == 'star':
            sdn_module.create_star_topology(6)
        elif topo_type == 'ring':
            sdn_module.create_ring_topology(6)
        elif topo_type == 'mesh':
            sdn_module.create_mesh_topology(6)
        
        # Broadcast new topology
        emit('sdn_event', {
            "type": "topology_update",
            "topology": {k: dict(v) for k, v in sdn_module.controller.network_topology.items()},
            "inactive_switches": list(sdn_module.inactive_switches)
        }, broadcast=True)
        emit('command_response', {"status": "success", "message": f"Topology changed to {topo_type}"})
        
    elif cmd_type == 'send_message':
        src_user = data.get('src_user', 'user1')
        dst_user = data.get('dst_user', 'userB')
        content = data.get('content', 'Hello World!')
        logger.info(f"Command Center injecting message from {src_user} to {dst_user}: {content}")
        
        # Manually create a message and trigger routing directly
        msg = ChatMessage(MessageType.MESSAGE, src_user, content)
        
        # Call the SDN routing simulator directly to pass dst_user
        if sdn_module.is_active:
            sdn_module.simulate_chat_routing(src_user, "MESSAGE", dst_user)
        
        emit('command_response', {"status": "success", "message": "Message sent"})

if __name__ == '__main__':
    logger.info("Starting Autonomous Network Command Center Server...")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, use_reloader=False, allow_unsafe_werkzeug=True)
