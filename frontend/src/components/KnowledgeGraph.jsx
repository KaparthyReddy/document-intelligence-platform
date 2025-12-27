import React from 'react';
import './KnowledgeGraph.css';
import { getEntityColor } from '../utils/helpers';

const KnowledgeGraph = ({ analysis }) => {
  const kgData = analysis?.knowledge_graph || {};
  const nodes = kgData.nodes || [];
  const edges = kgData.edges || [];
  const stats = kgData.statistics || {};

  // Simple visualization using CSS positioning
  const getNodePosition = (index, total) => {
    const angle = (index / total) * 2 * Math.PI;
    const radius = 200;
    const x = 250 + radius * Math.cos(angle);
    const y = 250 + radius * Math.sin(angle);
    return { x, y };
  };

  return (
    <div className="knowledge-graph">
      {/* Statistics */}
      <div className="kg-stats">
        <div className="kg-stat-card">
          <div className="stat-icon">🔵</div>
          <div>
            <div className="stat-value">{stats.total_nodes || 0}</div>
            <div className="stat-label">Nodes</div>
          </div>
        </div>
        <div className="kg-stat-card">
          <div className="stat-icon">🔗</div>
          <div>
            <div className="stat-value">{stats.total_edges || 0}</div>
            <div className="stat-label">Connections</div>
          </div>
        </div>
        <div className="kg-stat-card">
          <div className="stat-icon">📊</div>
          <div>
            <div className="stat-value">
              {stats.density ? (stats.density * 100).toFixed(1) + '%' : '0%'}
            </div>
            <div className="stat-label">Density</div>
          </div>
        </div>
        <div className="kg-stat-card">
          <div className="stat-icon">🔌</div>
          <div>
            <div className="stat-value">
              {stats.is_connected ? 'Yes' : 'No'}
            </div>
            <div className="stat-label">Connected</div>
          </div>
        </div>
      </div>

      {/* Graph Visualization */}
      {nodes.length > 0 ? (
        <div className="card">
          <h3>🕸️ Knowledge Graph Visualization</h3>
          <div className="graph-container">
            <svg className="graph-svg" viewBox="0 0 500 500">
              {/* Draw edges */}
              {edges.map((edge, idx) => {
                const sourceNode = nodes.find(n => n.id === edge.source);
                const targetNode = nodes.find(n => n.id === edge.target);
                
                if (!sourceNode || !targetNode) return null;
                
                const sourcePos = getNodePosition(nodes.indexOf(sourceNode), nodes.length);
                const targetPos = getNodePosition(nodes.indexOf(targetNode), nodes.length);
                
                return (
                  <g key={idx}>
                    <line
                      x1={sourcePos.x}
                      y1={sourcePos.y}
                      x2={targetPos.x}
                      y2={targetPos.y}
                      stroke="#475569"
                      strokeWidth="2"
                      opacity="0.5"
                    />
                  </g>
                );
              })}
              
              {/* Draw nodes */}
              {nodes.map((node, idx) => {
                const pos = getNodePosition(idx, nodes.length);
                const color = getEntityColor(node.type);
                
                return (
                  <g key={idx}>
                    <circle
                      cx={pos.x}
                      cy={pos.y}
                      r={Math.max(20, Math.min(40, node.size || 20))}
                      fill={color}
                      opacity="0.8"
                      stroke="#0f172a"
                      strokeWidth="2"
                    />
                    <text
                      x={pos.x}
                      y={pos.y + 50}
                      textAnchor="middle"
                      fill="#f1f5f9"
                      fontSize="12"
                      fontWeight="600"
                    >
                      {node.label.length > 15 ? node.label.substring(0, 15) + '...' : node.label}
                    </text>
                  </g>
                );
              })}
            </svg>
            
            <div className="graph-legend">
              <div className="legend-title">Entity Types:</div>
              {Object.entries(stats.entity_types || {}).map(([type, count]) => (
                <div key={type} className="legend-item">
                  <span 
                    className="legend-dot"
                    style={{ background: getEntityColor(type) }}
                  />
                  <span>{type} ({count})</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : (
        <div className="card">
          <div className="empty-graph">
            <div className="empty-icon">🕸️</div>
            <h3>No Graph Data</h3>
            <p>Not enough entities or relationships to build a knowledge graph</p>
          </div>
        </div>
      )}

      {/* Connections List */}
      {edges.length > 0 && (
        <div className="card">
          <h3>🔗 Entity Relationships</h3>
          <div className="relationships-list">
            {edges.slice(0, 20).map((edge, idx) => (
              <div key={idx} className="relationship-item">
                <div className="rel-source">{edge.source}</div>
                <div className="rel-arrow">
                  <span className="rel-label">{edge.relation || 'related to'}</span>
                  →
                </div>
                <div className="rel-target">{edge.target}</div>
              </div>
            ))}
            {edges.length > 20 && (
              <div className="relationships-footer">
                Showing 20 of {edges.length} relationships
              </div>
            )}
          </div>
        </div>
      )}

      {/* Top Nodes */}
      {nodes.length > 0 && (
        <div className="card">
          <h3>⭐ Most Connected Entities</h3>
          <div className="top-nodes">
            {nodes
              .sort((a, b) => (b.size || 0) - (a.size || 0))
              .slice(0, 10)
              .map((node, idx) => (
                <div key={idx} className="top-node-item">
                  <div className="node-rank">#{idx + 1}</div>
                  <div className="node-info">
                    <div className="node-name">{node.label}</div>
                    <div className="node-meta">
                      <span 
                        className="node-type"
                        style={{ background: getEntityColor(node.type) }}
                      >
                        {node.type}
                      </span>
                      <span className="node-connections">
                        {node.size || 0} connections
                      </span>
                    </div>
                  </div>
                </div>
              ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default KnowledgeGraph;