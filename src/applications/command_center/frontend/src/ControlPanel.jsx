import React from 'react';
import { Power, PowerOff, ShieldAlert, ShieldCheck, Zap, Play, Square, BookOpen } from 'lucide-react';

const ControlPanel = ({ onCommand, inactiveSwitches, isAutoDemo, bannedUsers = [], onShowScenarios }) => {
  const isS2Down = inactiveSwitches.includes('s2');
  const isUserABanned = bannedUsers.includes('userA');

  const toggleS2 = () => {
    onCommand({ type: 'toggle_switch', switch_id: 's2', active: isS2Down });
  };

  return (
    <div className="glass-panel" style={{ height: 'fit-content' }}>
      <h2><Zap size={20} /> Control Center</h2>
      
      <div style={{ marginBottom: '20px' }}>
        <p style={{ fontSize: '0.85rem', color: '#888', marginBottom: '10px' }}>
          Autonomous SDN Operations
        </p>

        <div style={{ display: 'flex', gap: '4px', marginBottom: '10px' }}>
          <button className="btn success" style={{ padding: '6px', flex: 1 }} onClick={() => onCommand({ type: 'toggle_switch', switch_id: document.getElementById('switchSelect').value, active: true })}><Power size={14} /> Restore</button>
          <button className="btn danger" style={{ padding: '6px', flex: 1 }} onClick={() => onCommand({ type: 'toggle_switch', switch_id: document.getElementById('switchSelect').value, active: false })}><PowerOff size={14} /> Kill</button>
          <select id="switchSelect" className="input-field" style={{ flex: 1, padding: '4px', fontSize: '0.8rem', background: '#2a2f3a', color: '#fff', border: '1px solid #444', borderRadius: '4px' }} defaultValue="s2">
             {['s1','s2','s3','s4','s5','s6'].map(s => <option key={s} value={s}>Switch {s}</option>)}
          </select>
        </div>

        <div style={{ display: 'flex', gap: '4px', marginBottom: '10px' }}>
          <button className="btn warning" style={{ padding: '6px', flex: 2 }} onClick={() => onCommand({ type: 'ban_user', user: document.getElementById('userSelect').value })}><ShieldAlert size={14} /> Toggle Ban</button>
          <select id="userSelect" className="input-field" style={{ flex: 1, padding: '4px', fontSize: '0.8rem', background: '#2a2f3a', color: '#fff', border: '1px solid #444', borderRadius: '4px' }} defaultValue="userA">
             {['userA','userB','userC','userD','userE','userF'].map(u => <option key={u} value={u}>User {u}</option>)}
          </select>
        </div>
        
        <button 
          className={`btn ${isAutoDemo ? 'danger' : 'success'}`} 
          style={{ marginTop: '12px', width: '100%' }}
          onClick={() => onCommand({ type: 'toggle_auto_demo' })}
        >
          {isAutoDemo ? <><Square size={18} /> Stop Auto Demo</> : <><Play size={18} /> Start Auto Demo</>}
        </button>

        <div style={{ marginTop: '20px', padding: '10px', background: 'rgba(255,255,255,0.05)', borderRadius: '8px' }}>
          <h4 style={{ margin: '0 0 10px 0', fontSize: '0.85rem' }}>Select Topology</h4>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
            <button className="btn" style={{ padding: '6px', fontSize: '0.8rem' }} onClick={() => onCommand({ type: 'set_topology', topology: 'linear' })}>Linear</button>
            <button className="btn" style={{ padding: '6px', fontSize: '0.8rem' }} onClick={() => onCommand({ type: 'set_topology', topology: 'star' })}>Star</button>
            <button className="btn" style={{ padding: '6px', fontSize: '0.8rem' }} onClick={() => onCommand({ type: 'set_topology', topology: 'ring' })}>Ring</button>
            <button className="btn" style={{ padding: '6px', fontSize: '0.8rem' }} onClick={() => onCommand({ type: 'set_topology', topology: 'mesh' })}>Mesh</button>
          </div>
        </div>

        <button 
          className="btn" 
          style={{ marginTop: '20px', width: '100%', background: 'var(--primary)', borderColor: 'var(--primary)' }}
          onClick={onShowScenarios}
        >
          <BookOpen size={18} /> Presentation Script
        </button>
      </div>

      <div style={{ padding: '12px', background: 'rgba(0,0,0,0.3)', borderRadius: '8px', fontSize: '0.85rem' }}>
        <h3 style={{ margin: '0 0 8px 0', color: 'var(--text-main)', fontSize: '0.9rem' }}>Network Status</h3>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
          <span>SDN Controller:</span> <span style={{ color: 'var(--success)' }}>Active</span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
          <span>Offline Switches:</span> 
          <span style={{ color: inactiveSwitches.length > 0 ? 'var(--danger)' : 'var(--success)' }}>
            {inactiveSwitches.length} Offline
          </span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
          <span>Banned Users (Firewall):</span> 
          <span style={{ color: bannedUsers.length > 0 ? 'var(--danger)' : 'var(--success)' }}>
            {bannedUsers.length} Blocked
          </span>
        </div>
      </div>

      <div style={{ marginTop: '20px', padding: '12px', background: 'rgba(255,255,255,0.05)', borderRadius: '8px' }}>
        <h4 style={{ margin: '0 0 10px 0', fontSize: '0.85rem' }}>Send Manual Message</h4>
        <form onSubmit={(e) => {
          e.preventDefault();
          const src = e.target.src.value;
          const dst = e.target.dst.value;
          const msg = e.target.msg.value;
          onCommand({ type: 'send_message', src_user: src, dst_user: dst, content: msg });
          e.target.msg.value = '';
        }}>
          <div style={{ display: 'flex', gap: '8px', marginBottom: '8px' }}>
            <select id="srcSelect" name="src" className="input-field" style={{ flex: 1, padding: '4px', fontSize: '0.8rem', background: '#2a2f3a', color: '#fff', border: '1px solid #444', borderRadius: '4px' }} defaultValue="userA">
              {['userA', 'userB', 'userC', 'userD', 'userE', 'userF'].map(u => <option key={`src-${u}`} value={u}>From {u}</option>)}
            </select>
            <select id="dstSelect" name="dst" className="input-field" style={{ flex: 1, padding: '4px', fontSize: '0.8rem', background: '#2a2f3a', color: '#fff', border: '1px solid #444', borderRadius: '4px' }} defaultValue="userB">
              {['userA', 'userB', 'userC', 'userD', 'userE', 'userF'].map(u => <option key={`dst-${u}`} value={u}>To {u}</option>)}
            </select>
          </div>
          <input id="msgInput" name="msg" className="input-field" placeholder="Type custom message & hit Enter..." required style={{ width: '100%', padding: '6px', fontSize: '0.8rem', marginBottom: '8px', background: '#2a2f3a', color: '#fff', border: '1px solid #444', borderRadius: '4px' }} />
          <div style={{ display: 'flex', gap: '4px', marginBottom: '4px', flexWrap: 'wrap' }}>
            <button type="button" className="btn" style={{ fontSize: '0.7rem', padding: '2px 6px' }} onClick={() => { document.getElementById('msgInput').value = 'Hi!'; onCommand({ type: 'send_message', src_user: document.getElementById('srcSelect').value, dst_user: document.getElementById('dstSelect').value, content: 'Hi!' }); }}>Hi</button>
            <button type="button" className="btn" style={{ fontSize: '0.7rem', padding: '2px 6px' }} onClick={() => { document.getElementById('msgInput').value = 'Hello there!'; onCommand({ type: 'send_message', src_user: document.getElementById('srcSelect').value, dst_user: document.getElementById('dstSelect').value, content: 'Hello there!' }); }}>Hello</button>
            <button type="button" className="btn" style={{ fontSize: '0.7rem', padding: '2px 6px' }} onClick={() => { document.getElementById('msgInput').value = 'Ping Test: Checking latency...'; onCommand({ type: 'send_message', src_user: document.getElementById('srcSelect').value, dst_user: document.getElementById('dstSelect').value, content: 'Ping Test: Checking latency...' }); }}>Ping Test</button>
            <button type="button" className="btn" style={{ fontSize: '0.7rem', padding: '2px 6px' }} onClick={() => { document.getElementById('msgInput').value = 'IoT Data: { temp: 24, hum: 45 }'; onCommand({ type: 'send_message', src_user: document.getElementById('srcSelect').value, dst_user: document.getElementById('dstSelect').value, content: 'IoT Data: { temp: 24, hum: 45 }' }); }}>IoT Data</button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ControlPanel;
