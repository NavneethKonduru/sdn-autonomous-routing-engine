import React, { useState } from 'react';
import { BookOpen, X, CheckCircle, AlertTriangle, ShieldAlert, Network, Radio, Smartphone, Activity } from 'lucide-react';

const ScenariosModal = ({ onClose }) => {
  const [activeTab, setActiveTab] = useState('sdn');

  return (
    <div style={{
      position: 'fixed',
      top: 0, left: 0, right: 0, bottom: 0,
      backgroundColor: 'rgba(0, 0, 0, 0.8)',
      backdropFilter: 'blur(8px)',
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      zIndex: 1000
    }}>
      <div className="glass-panel" style={{
        width: '800px',
        maxHeight: '85vh',
        overflowY: 'auto',
        position: 'relative',
        padding: '30px',
        display: 'flex',
        flexDirection: 'column'
      }}>
        <button 
          onClick={onClose}
          style={{
            position: 'absolute',
            top: '20px',
            right: '20px',
            background: 'transparent',
            border: 'none',
            color: 'var(--text-muted)',
            cursor: 'pointer'
          }}
        >
          <X size={24} />
        </button>
        
        <h2 style={{ marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <BookOpen size={24} color="var(--primary)" /> 
          OmniNet Presentation Script & Topics
        </h2>

        <div style={{ display: 'flex', gap: '10px', marginBottom: '20px', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '10px' }}>
          <button className={`btn ${activeTab === 'sdn' ? 'success' : ''}`} onClick={() => setActiveTab('sdn')}><Network size={16}/> SDN & Workflow</button>
          <button className={`btn ${activeTab === 'wireless' ? 'success' : ''}`} onClick={() => setActiveTab('wireless')}><Radio size={16}/> Wireless & Mobile</button>
          <button className={`btn ${activeTab === '5g' ? 'success' : ''}`} onClick={() => setActiveTab('5g')}><Smartphone size={16}/> 5G Technology</button>
          <button className={`btn ${activeTab === 'scenarios' ? 'success' : ''}`} onClick={() => setActiveTab('scenarios')}><Activity size={16}/> Demo Scenarios</button>
        </div>

        <div style={{ flex: 1, overflowY: 'auto', paddingRight: '10px' }}>
          
          {activeTab === 'sdn' && (
            <div className="fade-in">
              <h3 style={{ color: 'var(--primary)', marginBottom: '15px' }}>Software Defined Networking (SDN)</h3>
              <p style={{ color: 'var(--text-muted)', lineHeight: '1.6', marginBottom: '15px' }}>
                SDN revolutionizes networking by decoupling the network control and forwarding functions. This allows the network control to become directly programmable and the underlying infrastructure to be abstracted for applications and network services.
              </p>
              
              <h4 style={{ color: 'var(--text-main)', marginTop: '20px', marginBottom: '10px' }}>The Packet Workflow in SDN</h4>
              <ol style={{ color: 'var(--text-muted)', lineHeight: '1.7', paddingLeft: '20px' }}>
                <li><b>Packet Arrival (Data Plane):</b> A user sends a packet into the network. It arrives at the first OpenFlow edge switch.</li>
                <li><b>Table Miss (Flow Table Match):</b> The switch checks its Flow Table. If it doesn't know how to route this packet (a "table miss"), it encapsulates the packet header.</li>
                <li><b>Packet-In (Southbound API):</b> The switch sends a `PACKET_IN` message securely via OpenFlow up to the centralized SDN Controller.</li>
                <li><b>Intelligence (Control Plane):</b> The Controller uses Dijkstra's or BFS algorithms on its global network graph (the Topology you see on screen) to compute the optimal path.</li>
                <li><b>Flow-Mod (Programming):</b> The Controller sends `FLOW_MOD` messages down to all switches along the calculated path, installing new rules.</li>
                <li><b>Packet-Out:</b> The packet is forwarded out the correct port, and all subsequent packets in that flow are routed instantly at line-rate hardware speed.</li>
              </ol>
            </div>
          )}

          {activeTab === 'wireless' && (
            <div className="fade-in">
              <h3 style={{ color: 'var(--primary)', marginBottom: '15px' }}>Wireless and Mobile Communication</h3>
              <p style={{ color: 'var(--text-muted)', lineHeight: '1.6', marginBottom: '15px' }}>
                Modern networks must accommodate high-mobility users without dropping connections. 
              </p>
              <ul style={{ color: 'var(--text-muted)', lineHeight: '1.7', paddingLeft: '20px' }}>
                <li><b>Handoff (Handover):</b> As a mobile user moves away from one Access Point (AP) and towards another, the signal strength degrades. The network seamlessly transfers the session to the new AP.</li>
                <li><b>Channel Modeling:</b> Wireless signals suffer from Path Loss, Shadowing, and Fading. Network controllers must dynamically adjust transmission power and modulation schemes.</li>
                <li><b>CSMA/CA:</b> To avoid collisions in the airwaves, devices listen before they transmit and back off exponentially if the channel is busy.</li>
              </ul>
            </div>
          )}

          {activeTab === '5g' && (
            <div className="fade-in">
              <h3 style={{ color: 'var(--primary)', marginBottom: '15px' }}>5G Technology</h3>
              <p style={{ color: 'var(--text-muted)', lineHeight: '1.6', marginBottom: '15px' }}>
                5G is not just faster wireless; it is a complete architectural overhaul designed for distinct use cases.
              </p>
              <ul style={{ color: 'var(--text-muted)', lineHeight: '1.7', paddingLeft: '20px' }}>
                <li><b>Network Slicing:</b> The ability to partition a single physical network into multiple virtual networks. One slice is optimized for ultra-low latency (autonomous driving), while another is optimized for massive bandwidth (4K video streaming).</li>
                <li><b>eMBB (Enhanced Mobile Broadband):</b> Gigabit speeds for AR/VR and high-definition media.</li>
                <li><b>URLLC (Ultra-Reliable Low-Latency Communication):</b> Sub-millisecond latency for remote surgery and industrial automation.</li>
                <li><b>mMTC (Massive Machine Type Communications):</b> Supporting millions of low-power IoT devices per square kilometer.</li>
              </ul>
            </div>
          )}

          {activeTab === 'scenarios' && (
            <div className="fade-in">
              <h3 style={{ color: 'var(--primary)', marginBottom: '15px' }}>Demo Scenarios to Show</h3>
              
              <div style={{ marginBottom: '20px' }}>
                <h4 style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--success)' }}>
                  <CheckCircle size={18} /> 1. Dynamic Topologies
                </h4>
                <p style={{ color: 'var(--text-muted)', lineHeight: '1.6', fontSize: '0.95rem' }}>
                  "Notice the Control Panel on the left. We can instantly reconfigure the physical infrastructure layout from a Star topology to a Mesh topology. The SDN controller immediately maps the new graph and re-calculates all shortest paths dynamically."
                </p>
              </div>

              <div style={{ marginBottom: '20px' }}>
                <h4 style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--danger)' }}>
                  <AlertTriangle size={18} /> 2. Link Failure / Self-Healing
                </h4>
                <p style={{ color: 'var(--text-muted)', lineHeight: '1.6', fontSize: '0.95rem' }}>
                  "If we right click a switch and kill it, the network detects the link down event. The SDN controller autonomously calculates a new path around the failure in milliseconds and pushes new Flow Rules, ensuring zero downtime."
                </p>
              </div>

              <div>
                <h4 style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#ffb86c' }}>
                  <ShieldAlert size={18} /> 3. Programmable Security
                </h4>
                <p style={{ color: 'var(--text-muted)', lineHeight: '1.6', fontSize: '0.95rem' }}>
                  "If a user is flagged for malicious activity, an admin doesn't need to manually log into edge routers. By clicking 'Ban User', the controller pushes a DROP rule directly to the edge switch, blocking the threat at the source."
                </p>
              </div>
            </div>
          )}
          
        </div>
      </div>
    </div>
  );
};

export default ScenariosModal;
