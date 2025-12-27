import React, { useState, useEffect } from 'react';
import { getEntityColor } from '../utils/helpers';
import api from '../services/api';
import './EntityViewer.css';

const EntityViewer = ({ analysis, documentId }) => {
  const [selectedType, setSelectedType] = useState('all');
  const [entities, setEntities] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchEntities();
  }, [documentId, selectedType]);

  const fetchEntities = async () => {
    setLoading(true);
    try {
      const response = await api.getEntities(
        documentId,
        selectedType === 'all' ? null : selectedType
      );
      setEntities(response.data.data.entities);
    } catch (err) {
      console.error('Error fetching entities:', err);
    } finally {
      setLoading(false);
    }
  };

  const entityTypes = analysis?.entities?.entity_types || [];
  const entityCounts = analysis?.entities?.entity_counts || {};
  const uniqueEntities = analysis?.entities?.unique_entities || {};

  return (
    <div className="entity-viewer">
      {/* Summary */}
      <div className="entity-summary">
        <div className="summary-card">
          <div className="summary-icon">🏷️</div>
          <div>
            <div className="summary-value">{analysis?.entities?.total_entities || 0}</div>
            <div className="summary-label">Total Entities</div>
          </div>
        </div>
        <div className="summary-card">
          <div className="summary-icon">📊</div>
          <div>
            <div className="summary-value">{entityTypes.length}</div>
            <div className="summary-label">Entity Types</div>
          </div>
        </div>
        <div className="summary-card">
          <div className="summary-icon">⭐</div>
          <div>
            <div className="summary-value">
              {Object.values(uniqueEntities).reduce((sum, arr) => sum + arr.length, 0)}
            </div>
            <div className="summary-label">Unique Entities</div>
          </div>
        </div>
      </div>

      {/* Type Filter */}
      <div className="entity-filters">
        <button
          className={`filter-btn ${selectedType === 'all' ? 'active' : ''}`}
          onClick={() => setSelectedType('all')}
        >
          All ({analysis?.entities?.total_entities || 0})
        </button>
        {entityTypes.map(type => (
          <button
            key={type}
            className={`filter-btn ${selectedType === type ? 'active' : ''}`}
            onClick={() => setSelectedType(type)}
            style={{
              borderColor: selectedType === type ? getEntityColor(type) : 'var(--border)',
              color: selectedType === type ? getEntityColor(type) : 'var(--text-muted)'
            }}
          >
            {type} ({entityCounts[type] || 0})
          </button>
        ))}
      </div>

      {/* Entity Distribution */}
      <div className="card">
        <h3>📊 Entity Distribution</h3>
        <div className="distribution-chart">
          {Object.entries(entityCounts).map(([type, count]) => {
            const percentage = (count / (analysis?.entities?.total_entities || 1)) * 100;
            return (
              <div key={type} className="distribution-row">
                <div className="distribution-label">
                  <span
                    className="type-indicator"
                    style={{ background: getEntityColor(type) }}
                  />
                  {type}
                </div>
                <div className="distribution-bar-container">
                  <div
                    className="distribution-bar"
                    style={{
                      width: `${percentage}%`,
                      background: getEntityColor(type)
                    }}
                  />
                </div>
                <div className="distribution-value">{count}</div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Unique Entities */}
      {selectedType !== 'all' && uniqueEntities[selectedType] && (
        <div className="card">
          <h3>⭐ Unique {selectedType} Entities</h3>
          <div className="unique-entities">
            {uniqueEntities[selectedType].map((entity, idx) => (
              <div
                key={idx}
                className="entity-badge"
                style={{ borderColor: getEntityColor(selectedType) }}
              >
                {entity}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Entity List */}
      <div className="card">
        <h3>📋 {selectedType === 'all' ? 'All' : selectedType} Entities</h3>
        {loading ? (
          <div className="loading-entities">Loading...</div>
        ) : entities.length === 0 ? (
          <div className="no-entities">No entities found</div>
        ) : (
          <div className="entities-table">
            <div className="table-header">
              <div className="col-entity">Entity</div>
              <div className="col-type">Type</div>
              <div className="col-context">Context</div>
            </div>
            {entities.slice(0, 50).map((entity, idx) => (
              <div key={idx} className="table-row">
                <div className="col-entity">
                  <span
                    className="entity-dot"
                    style={{ background: getEntityColor(entity.entity_type) }}
                  />
                  {entity.entity_text}
                </div>
                <div className="col-type">
                  <span
                    className="type-badge"
                    style={{ background: getEntityColor(entity.entity_type) }}
                  >
                    {entity.entity_type}
                  </span>
                </div>
                <div className="col-context">
                  Position: {entity.start_pos}
                </div>
              </div>
            ))}
            {entities.length > 50 && (
              <div className="table-footer">
                Showing 50 of {entities.length} entities
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default EntityViewer;