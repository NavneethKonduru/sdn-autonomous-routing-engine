import React, { useState, useEffect } from 'react';
import { io } from 'socket.io-client';
import NetworkGraph from './NetworkGraph';
import ControlPanel from './ControlPanel';
import LiveLogs from './LiveLogs';
import ScenariosModal from './ScenariosModal';
import './index.css';

const socket = io('http://127.0.0.1:5000');

function App() {
  const [topology, setTopology] = useState({});
  const [inactiveSwitches, setInactiveSwitches] = useState([]);
  
  // Dual State
  const [activePathSDN, setActivePathSDN] = useState([]);
  const [packetInfoSDN, setPacketInfoSDN] = useState(null);
  const [activePathTrad, setActivePathTrad] = useState([]);
  const [packetInfoTrad, setPacketInfoTrad] = useState(null);
  
  const [logsSDN, setLogsSDN] = useState([{ type: 'info', message: 'SDN Controller initialized...', timestamp: Date.now() }]);
  const [logsTrad, setLogsTrad] = useState([{ type: 'info', message: 'Traditional Routing initialized...', timestamp: Date.now() }]);
  
  const [isAutoDemo, setIsAutoDemo] = useState(false);
  const [bannedUsers, setBannedUsers] = useState([]);
  const [showScenarios, setShowScenarios] = useState(false);

  // Auto-Demo Logic
  useEffect(() => {
    let demoInterval;
    if (isAutoDemo) {
      demoInterval = setInterval(() => {
        // 70% send message, 15% toggle random switch, 15% congest random link
        const rand = Math.random();
        if (rand > 0.3) {
          const messages = ["Hello from User!", "Checking network latency...", "Is the connection stable?", "SDN rules applied.", "Transferring data packet.", "Streaming 4K Video Data...", "IoT Sensor heartbeat."];
          const randomMsg = messages[Math.floor(Math.random() * messages.length)];
          const users = ['userA', 'userB', 'userC', 'userD', 'userE', 'userF'];
          const randomUserSrc = users[Math.floor(Math.random() * users.length)];
          const randomUserDst = users[Math.floor(Math.random() * users.length)];
          handleSendMessage(randomMsg, randomUserSrc, randomUserDst !== randomUserSrc ? randomUserDst : 'userB');
        } else if (rand > 0.15) {
          const randomSwitch = `s${Math.floor(Math.random() * 5) + 2}`;
          setInactiveSwitches(currentInactive => {
            const isDown = currentInactive.includes(randomSwitch);
            socket.emit('command', { type: 'toggle_switch', switch_id: randomSwitch, active: isDown });
            return currentInactive;
          });
        } else {
          const edgeLinks = [['s1', 's2'], ['s2', 's3'], ['s1', 's4'], ['s4', 's5'], ['s5', 's6'], ['s6', 's3']];
          const rl = edgeLinks[Math.floor(Math.random() * edgeLinks.length)];
          socket.emit('command', { type: 'set_link_weight', src: rl[0], dst: rl[1], weight: 20 });
          
          setTimeout(() => {
            socket.emit('command', { type: 'set_link_weight', src: rl[0], dst: rl[1], weight: 1 });
          }, 6000);
        }
      }, 3500); // Trigger an action every 3.5 seconds
    }
    return () => clearInterval(demoInterval);
  }, [isAutoDemo]);

  useEffect(() => {
    socket.on('connect', () => {
      addLogSDN('System connected to SDN Controller.', 'info');
      addLogTrad('System connected to Traditional Network.', 'info');
    });

    socket.on('disconnect', () => {
      addLogSDN('Connection lost.', 'error');
      addLogTrad('Connection lost.', 'error');
    });

    socket.on('sdn_event', (event) => {
      if (event.type === 'topology_update') {
        setTopology(event.topology);
        setInactiveSwitches(event.inactive_switches);
        addLogSDN(`Topology updated. Active nodes: ${Object.keys(event.topology).length}`, 'info');
      } 
      
      // SDN ROUTING
      else if (event.type === 'packet_routed_sdn') {
        const pathStr = event.path.join(' -> ');
        addLogSDN(`[SDN] Found path: ${pathStr}`, 'routing');
        setActivePathSDN(event.path);
        setPacketInfoSDN({ src: event.src_user, dst: event.dst_user, type: event.msg_type });
        setTimeout(() => { setActivePathSDN([]); setPacketInfoSDN(null); }, 8000);
      } 
      else if (event.type === 'packet_dropped_sdn') {
        const prefix = event.reason.includes('Firewall') ? '[FIREWALL]' : '[ROUTING]';
        addLogSDN(`${prefix} Packet from ${event.src_user} DROPPED. Reason: ${event.reason}`, 'error');
      }
      
      // TRADITIONAL ROUTING
      else if (event.type === 'packet_routed_trad') {
        const pathStr = event.path.join(' -> ');
        addLogTrad(`[TRADITIONAL] Found path: ${pathStr}`, 'routing');
        setActivePathTrad(event.path);
        setPacketInfoTrad({ src: event.src_user, dst: event.dst_user, type: event.msg_type });
        setTimeout(() => { setActivePathTrad([]); setPacketInfoTrad(null); }, 8000);
      } 
      else if (event.type === 'packet_dropped_trad') {
        addLogTrad(`[TRADITIONAL] Packet from ${event.src_user} DROPPED. Reason: ${event.reason}`, 'error');
      }
      
      // FIREWALL RULES
      else if (event.type === 'user_banned') {
        setBannedUsers(prev => [...prev, event.user]);
        addLogSDN(`[SECURITY] Firewall rules updated: Dropping all traffic from ${event.user}`, 'error');
      }
      else if (event.type === 'user_unbanned') {
        setBannedUsers(prev => prev.filter(u => u !== event.user));
        addLogSDN(`[SECURITY] Firewall rules updated: Allowing traffic from ${event.user}`, 'success');
      }
    });

    socket.on('command_response', (res) => {
      addLogSDN(`Command response: ${res.message}`, res.status === 'error' ? 'error' : 'info');
    });

    return () => {
      socket.off('connect');
      socket.off('disconnect');
      socket.off('sdn_event');
      socket.off('command_response');
    };
  }, []);

  const addLogSDN = (message, type) => {
    setLogsSDN(prev => [...prev, { message, type, timestamp: Date.now() }].slice(-50));
  };
  const addLogTrad = (message, type) => {
    setLogsTrad(prev => [...prev, { message, type, timestamp: Date.now() }].slice(-50));
  };

  const handleCommand = (commandData) => {
    if (commandData.type === 'toggle_auto_demo') {
      const newState = !isAutoDemo;
      setIsAutoDemo(newState);
      addLogSDN(newState ? '[AUTO-DEMO] Started.' : '[AUTO-DEMO] Stopped.', 'info');
      addLogTrad(newState ? '[AUTO-DEMO] Started.' : '[AUTO-DEMO] Stopped.', 'info');
      return;
    }
    socket.emit('command', commandData);
  };

  const handleSendMessage = (content, src = 'userA', dst = 'userB') => {
    socket.emit('command', {
      type: 'send_message',
      src_user: src,
      dst_user: dst,
      content: content
    });
    addLogSDN(`Sent message from ${src} to ${dst}`, 'info');
    addLogTrad(`Sent message from ${src} to ${dst}`, 'info');
  };

  return (
    <div className="app-container">
      {showScenarios && <ScenariosModal onClose={() => setShowScenarios(false)} />}
      
      <ControlPanel 
        onCommand={handleCommand} 
        inactiveSwitches={inactiveSwitches}
        isAutoDemo={isAutoDemo}
        bannedUsers={bannedUsers}
        onShowScenarios={() => setShowScenarios(true)}
      />
      
      <NetworkGraph 
        graphId="traditional"
        title="Traditional Networking"
        topology={topology} 
        inactiveSwitches={inactiveSwitches} 
        activePath={activePathTrad}
        packetInfo={packetInfoTrad}
        onCommand={handleCommand}
      />

      <NetworkGraph 
        graphId="sdn"
        title="SDN Controlled Network"
        topology={topology} 
        inactiveSwitches={inactiveSwitches} 
        activePath={activePathSDN}
        packetInfo={packetInfoSDN}
        onCommand={handleCommand}
      />
      
      <LiveLogs 
        logsSDN={logsSDN} 
        logsTrad={logsTrad}
        onSendMessage={handleSendMessage} 
      />
    </div>
  );
}

export default App;
