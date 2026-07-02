import React, { useState, useEffect, useRef } from 'react';
import { Terminal, Send } from 'lucide-react';

const LiveLogs = ({ logsSDN, logsTrad, onSendMessage }) => {
  const [inputText, setInputText] = useState('');
  const sdnEndRef = useRef(null);
  const tradEndRef = useRef(null);

  const scrollToBottom = () => {
    sdnEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    tradEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [logsSDN, logsTrad]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (inputText.trim()) {
      onSendMessage(inputText);
      setInputText('');
    }
  };

  return (
    <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      
      {/* TRADITIONAL LOGS (Top Half) */}
      <h2 style={{ marginBottom: '8px', fontSize: '0.9rem' }}><Terminal size={18} /> Traditional Logs</h2>
      <div className="logs-container" style={{ flex: '1 1 40%', marginBottom: '15px' }}>
        {logsTrad.map((log, index) => (
          <div key={index} className={`log-entry ${log.type}`}>
            <span style={{ color: '#888', marginRight: '8px' }}>
              [{new Date(log.timestamp).toLocaleTimeString()}]
            </span>
            {log.message}
          </div>
        ))}
        <div ref={tradEndRef} />
      </div>

      <div style={{ height: '1px', background: 'var(--panel-border)', margin: '0 -24px 15px -24px' }}></div>

      {/* SDN LOGS (Bottom Half) */}
      <h2 style={{ marginBottom: '8px', fontSize: '0.9rem' }}><Terminal size={18} /> SDN Controller Logs</h2>
      <div className="logs-container" style={{ flex: '1 1 40%', marginBottom: '10px' }}>
        {logsSDN.map((log, index) => (
          <div key={index} className={`log-entry ${log.type}`}>
            <span style={{ color: '#888', marginRight: '8px' }}>
              [{new Date(log.timestamp).toLocaleTimeString()}]
            </span>
            {log.message}
          </div>
        ))}
        <div ref={sdnEndRef} />
      </div>

      <form className="chat-input-container" onSubmit={handleSubmit} style={{ marginTop: 'auto', paddingTop: '10px' }}>
        <div style={{ fontSize: '0.8rem', color: 'var(--accent-cyan)' }}>Simulate User Traffic:</div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <input 
            type="text" 
            className="input-field" 
            style={{ flexGrow: 1 }}
            placeholder="Type a message..." 
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
          />
          <button type="submit" className="btn" style={{ width: 'auto', marginBottom: 0, padding: '10px' }}>
            <Send size={18} />
          </button>
        </div>
      </form>
    </div>
  );
};

export default LiveLogs;
