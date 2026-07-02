import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';

const ContextMenu = ({ x, y, type, id, source, target, weight, onClose, onCommand, inactiveSwitches = [] }) => {
  const isDown = type === 'switch' && inactiveSwitches.includes(id);
  
  return (
    <div style={{
      position: 'absolute', top: y, left: x,
      background: 'rgba(20, 25, 40, 0.95)',
      border: '1px solid var(--primary)', borderRadius: '8px',
      padding: '10px', zIndex: 100, boxShadow: '0 4px 12px rgba(0,0,0,0.5)',
      minWidth: '150px', backdropFilter: 'blur(5px)'
    }}>
      <div style={{ color: 'var(--text-main)', fontSize: '0.9rem', marginBottom: '10px', borderBottom: '1px solid #333', paddingBottom: '5px' }}>
        {type === 'switch' ? `Switch: ${id}` : type === 'user' ? `User: ${id}` : `Link: ${source}-${target}`}
      </div>
      
      {type === 'switch' && (
        <>
          <button 
            className={`btn ${isDown ? 'success' : 'danger'}`} 
            style={{ width: '100%', padding: '5px', fontSize: '0.8rem', marginBottom: '5px' }}
            onClick={() => {
              onCommand({ type: 'toggle_switch', switch_id: id, active: isDown });
              onClose();
            }}
          >
            {isDown ? 'Restore Switch' : 'Kill Switch'}
          </button>
          
          <button 
            className="btn warning" 
            style={{ width: '100%', padding: '5px', fontSize: '0.8rem' }}
            onClick={() => {
              onCommand({ type: 'init_link', source_id: id });
              onClose();
            }}
          >
            Connect To...
          </button>
        </>
      )}

      {type === 'user' && (
        <>
          <button 
            className="btn danger" 
            style={{ width: '100%', padding: '5px', fontSize: '0.8rem', marginBottom: '5px' }}
            onClick={() => {
              onCommand({ type: 'ban_user', user: id });
              onClose();
            }}
          >
            Toggle Ban Status
          </button>
          
          <button 
            className="btn warning" 
            style={{ width: '100%', padding: '5px', fontSize: '0.8rem' }}
            onClick={() => {
              onCommand({ type: 'init_link', source_id: id });
              onClose();
            }}
          >
            Connect To...
          </button>
        </>
      )}

      {type === 'link' && (
        <>
          <button 
            className="btn warning" 
            style={{ width: '100%', padding: '5px', fontSize: '0.8rem', marginBottom: '5px', background: '#ffb86c', color: '#000' }}
            onClick={() => {
              onCommand({ type: 'set_link_weight', src: source, dst: target, weight: 10 });
              onClose();
            }}
          >
            Set Traffic: Level 2 (Moderate)
          </button>
          <button 
            className="btn danger" 
            style={{ width: '100%', padding: '5px', fontSize: '0.8rem', marginBottom: '5px', background: '#ff5555', color: '#000' }}
            onClick={() => {
              onCommand({ type: 'set_link_weight', src: source, dst: target, weight: 20 });
              onClose();
            }}
          >
            Set Traffic: Level 3 (Severe)
          </button>
          <button 
            className="btn success" 
            style={{ width: '100%', padding: '5px', fontSize: '0.8rem', marginBottom: '5px' }}
            onClick={() => {
              onCommand({ type: 'set_link_weight', src: source, dst: target, weight: 1 });
              onClose();
            }}
          >
            Set Traffic: Level 1 (Normal)
          </button>
          <button 
            className="btn danger" 
            style={{ width: '100%', padding: '5px', fontSize: '0.8rem' }}
            onClick={() => {
              onCommand({ type: 'break_link', src: source, dst: target });
              onClose();
            }}
          >
            Sever Link completely
          </button>
        </>
      )}
      
      <button className="btn" style={{ width: '100%', padding: '5px', fontSize: '0.8rem', marginTop: '10px', background: 'transparent' }} onClick={onClose}>
        Close
      </button>
    </div>
  );
};

const NetworkGraph = ({ graphId, title, topology, inactiveSwitches, activePath, packetInfo, onCommand }) => {
  const d3Container = useRef(null);
  const [nodes, setNodes] = useState([]);
  const nodesRef = useRef([]); // Track latest nodes to preserve positions
  const [links, setLinks] = useState([]);
  const [contextMenu, setContextMenu] = useState(null);
  const [linkingSourceState, setLinkingSourceState] = useState(null);
  const linkingSourceRef = useRef(null);
  
  // Track dragging state to prevent infinite loops
  const isDraggingRef = useRef(false);

  const setLinkingSource = (val) => {
    linkingSourceRef.current = val;
    setLinkingSourceState(val);
  };

  // Intercept onCommand to handle init_link locally
  const handleGraphCommand = (cmd) => {
    if (cmd.type === 'init_link') {
      setLinkingSource(cmd.source_id);
    } else {
      onCommand(cmd);
    }
  };

  // Transform topology dict into D3 nodes and links
  useEffect(() => {
    if (!topology || Object.keys(topology).length === 0) return;
    
    const newNodes = [];
    const newLinks = [];
    const nodeMap = new Map();

    // Add switches and existing users from topology
    Object.keys(topology).forEach(nodeId => {
      if (!nodeMap.has(nodeId)) {
        const type = nodeId.startsWith('user') ? 'user' : 'switch';
        
        // Preserve exact coordinates and physics momentum so graph doesn't explode/reset on update
        const existingNode = nodesRef.current.find(n => n.id === nodeId);
        const node = { 
          id: nodeId, 
          type, 
          status: inactiveSwitches.includes(nodeId) ? 'inactive' : 'active',
          x: existingNode ? existingNode.x : undefined,
          y: existingNode ? existingNode.y : undefined,
          fx: existingNode ? existingNode.fx : undefined,
          fy: existingNode ? existingNode.fy : undefined,
          vx: existingNode ? existingNode.vx : undefined,
          vy: existingNode ? existingNode.vy : undefined
        };
        
        newNodes.push(node);
        nodeMap.set(nodeId, node);
      }
      
      // Add links
      Object.entries(topology[nodeId]).forEach(([targetId, weight]) => {
        // Ensure bidirectional links are only added once
        if (nodeId < targetId) {
          const isInactive = inactiveSwitches.includes(nodeId) || inactiveSwitches.includes(targetId);
          newLinks.push({ 
            source: nodeId, 
            target: targetId,
            weight: weight,
            status: isInactive ? 'inactive' : 'active'
          });
        }
      });
    });

    // The backend now provides the complete network topology including users!
    // No frontend guessing or hardcoded links are required.

    setNodes(newNodes);
    nodesRef.current = newNodes; // Update ref!
    setLinks(newLinks);
    setContextMenu(null); // Close menu on topology change
  }, [topology, inactiveSwitches]);

  // Render D3 Graph
  useEffect(() => {
    if (!nodes.length || !d3Container.current) return;

    const width = d3Container.current.clientWidth;
    const height = d3Container.current.clientHeight;
    
    if (width === 0 || height === 0) return; // Wait for layout

    // Clear previous
    d3.select(d3Container.current).selectAll('*').remove();

    const svg = d3.select(d3Container.current)
      .append('svg')
      .attr('width', width)
      .attr('height', height)
      .on('click', () => {
        setContextMenu(null);
        setLinkingSource(null); // Cancel linking mode
      });

    // Create simulation
    const simulation = d3.forceSimulation(nodes)
      .force('link', d3.forceLink(links).id(d => d.id).distance(120))
      .force('charge', d3.forceManyBody().strength(-400)) // Reduced repulsion so they don't explode
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(45))
      .force('x', d3.forceX(width / 2).strength(0.05)) // Gentle pull to center
      .force('y', d3.forceY(height / 2).strength(0.05));

    // Draw links
    const linkGroup = svg.append('g').attr('class', 'links');
    const link = linkGroup
      .selectAll('line')
      .data(links)
      .enter()
      .append('line')
      .attr('class', d => `link ${d.status}`)
      .attr('stroke-width', d => Math.min(d.weight * 2, 10)) // Thicker for congestion
      .style('stroke', d => {
        if (d.weight >= 20) return '#ff5555'; // Red (Severe)
        if (d.weight >= 10) return '#ffb86c'; // Orange (Moderate)
        return '#00d2ff'; // Default Cyan
      })
      .on('click', (event, d) => {
        event.stopPropagation();
        setContextMenu({
          x: event.pageX - d3Container.current.getBoundingClientRect().left,
          y: event.pageY - d3Container.current.getBoundingClientRect().top,
          type: 'link', source: d.source.id, target: d.target.id, weight: d.weight
        });
      });

    // Draw nodes
    const nodeGroup = svg.append('g').attr('class', 'nodes');
    const node = nodeGroup
      .selectAll('g')
      .data(nodes)
      .enter()
      .append('g')
      .call(d3.drag()
        .on('start', dragstarted)
        .on('drag', dragged)
        .on('end', dragended))
      .on('click', (event, d) => {
        event.stopPropagation();
        
        const currentLinkingSource = linkingSourceRef.current;
        if (currentLinkingSource) {
          if (currentLinkingSource !== d.id) {
            onCommand({ type: 'create_link', src: currentLinkingSource, dst: d.id });
          }
          setLinkingSource(null);
        } else {
          setContextMenu({
            x: event.pageX - d3Container.current.getBoundingClientRect().left,
            y: event.pageY - d3Container.current.getBoundingClientRect().top,
            type: d.type, id: d.id
          });
        }
      });

    // Node circles
    node.append('circle')
      .attr('r', d => d.type === 'switch' ? 24 : 16)
      .attr('class', 'node')
      .attr('fill', d => {
        if (d.status === 'inactive') return 'var(--danger)';
        return d.type === 'switch' ? 'var(--node-switch)' : 'var(--node-user)';
      });

    // Node labels
    node.append('text')
      .attr('class', 'node-label')
      .attr('dy', 5)
      .attr('text-anchor', 'middle')
      .text(d => d.id);

    // Simulation tick
    simulation.on('tick', () => {
      // Add bounding box constraint so nodes don't fly off screen
      nodes.forEach(d => {
        d.x = Math.max(30, Math.min(width - 30, d.x));
        d.y = Math.max(30, Math.min(height - 30, d.y));
      });

      link
        .attr('x1', d => d.source.x)
        .attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x)
        .attr('y2', d => d.target.y);

      node
        .attr('transform', d => `translate(${d.x},${d.y})`);
        
      // Only broadcast if THIS graph is the one actively running physics/dragging
      if (simulation.alpha() > 0.05) {
        window.dispatchEvent(new CustomEvent('sync-nodes', {
          detail: {
            source: graphId,
            nodes: nodes.map(n => ({ id: n.id, x: n.x, y: n.y, fx: n.fx, fy: n.fy, vx: n.vx, vy: n.vy }))
          }
        }));
      }
    });
    
    // Listen for sync events from the OTHER graph
    const handleSync = (e) => {
      if (e.detail.source !== graphId) {
        // Update our nodes silently
        e.detail.nodes.forEach(syncedNode => {
          const localNode = nodes.find(n => n.id === syncedNode.id);
          if (localNode) {
            localNode.x = syncedNode.x;
            localNode.y = syncedNode.y;
            localNode.fx = syncedNode.fx;
            localNode.fy = syncedNode.fy;
            localNode.vx = syncedNode.vx;
            localNode.vy = syncedNode.vy;
          }
        });
        
        // Manually update DOM since we aren't triggering React render
        node.attr('transform', d => `translate(${d.x},${d.y})`);
        link
          .attr('x1', d => d.source.x)
          .attr('y1', d => d.source.y)
          .attr('x2', d => d.target.x)
          .attr('y2', d => d.target.y);
      }
    };
    window.addEventListener('sync-nodes', handleSync);

    // Handle Active Path Highlighting - SEQUENTIAL
    if (activePath && activePath.length > 0 && packetInfo) {
      // The backend provides the full physical path including the users!
      const fullPath = activePath;
      
      const spawnDot = (delayMs) => {
        const packet = svg.append('circle')
          .attr('class', 'packet')
          .attr('r', 6) // smaller dot
          .attr('fill', '#ffb86c') // yellowish orange
          .attr('opacity', 0)
          .style('filter', 'drop-shadow(0 0 6px #ffb86c)');
  
        let currentStep = 0;
  
        const movePacket = () => {
          if (currentStep >= fullPath.length - 1) {
            packet.transition().duration(200).attr('opacity', 0).remove();
            // Optional: only remove highlight path on the last dot
            if (delayMs === 500) {
              setTimeout(() => link.classed('active-path', false), 400);
            }
            return;
          }
  
          const sourceId = fullPath[currentStep];
          const targetId = fullPath[currentStep + 1];
          
          // Highlight the current segment (only the first dot triggers the highlight)
          if (delayMs === 100) {
            link.classed('active-path', d => {
              for (let i = 0; i <= currentStep; i++) {
                if ((d.source.id === fullPath[i] && d.target.id === fullPath[i+1]) ||
                    (d.target.id === fullPath[i] && d.source.id === fullPath[i+1])) {
                  return true;
                }
              }
              return false;
            });
          }
  
          const sourceNode = nodes.find(n => n.id === sourceId);
          const targetNode = nodes.find(n => n.id === targetId);
  
          if (sourceNode && targetNode) {
            packet
              .attr('cx', sourceNode.x)
              .attr('cy', sourceNode.y)
              .attr('opacity', 1)
              .transition()
              .duration(500) // faster movement
              .ease(d3.easeLinear)
              .tween("position", function() {
                return function(t) {
                  // Dynamically recalculate coordinates based on live node positions
                  const currentCx = sourceNode.x + (targetNode.x - sourceNode.x) * t;
                  const currentCy = sourceNode.y + (targetNode.y - sourceNode.y) * t;
                  d3.select(this).attr('cx', currentCx).attr('cy', currentCy);
                };
              })
              .on('end', () => {
                currentStep++;
                movePacket();
              });
          }
        };
  
        setTimeout(movePacket, delayMs);
      };

      // Spawn 3 consecutive dots
      spawnDot(100);
      spawnDot(300);
      spawnDot(500);
    }

    // Drag functions
    function dragstarted(event, d) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    }

    function dragged(event, d) {
      d.fx = event.x;
      d.fy = event.y;
    }

    function dragended(event, d) {
      if (!event.active) simulation.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    }

    return () => {
      simulation.stop();
      window.removeEventListener('sync-nodes', handleSync);
    };
  }, [nodes, links, activePath, packetInfo]); // Removed onCommand to prevent rerendering

  return (
    <div className="glass-panel" style={{ padding: '8px', position: 'relative' }}>
      {title && (
        <div style={{ position: 'absolute', top: 10, left: 20, zIndex: 10, background: 'rgba(0,0,0,0.6)', padding: '4px 10px', borderRadius: '8px', border: '1px solid var(--panel-border)', fontWeight: 'bold' }}>
          {title}
        </div>
      )}
      
      {linkingSourceState && (
        <div style={{
          position: 'absolute', top: '10px', left: '50%', transform: 'translateX(-50%)',
          background: 'var(--warning)', color: '#000', padding: '8px 16px',
          borderRadius: '20px', fontWeight: 'bold', zIndex: 10, fontSize: '0.9rem',
          pointerEvents: 'none'
        }}>
          Select target node to connect to {linkingSourceState}... (Click background to cancel)
        </div>
      )}
      
      <div className="graph-container" ref={d3Container} style={{ cursor: linkingSourceState ? 'crosshair' : 'pointer' }}></div>
      
      {contextMenu && (
        <ContextMenu 
          {...contextMenu} 
          onClose={() => setContextMenu(null)} 
          onCommand={handleGraphCommand}
          inactiveSwitches={inactiveSwitches}
        />
      )}
    </div>
  );
};

export default NetworkGraph;
