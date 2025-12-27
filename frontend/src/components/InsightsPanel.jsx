import React, { useState, useEffect } from 'react';
import { FaSpinner, FaLightbulb } from 'react-icons/fa';
import api from '../services/api';
import './InsightsPanel.css';

const InsightsPanel = ({ documentId }) => {
  const [insights, setInsights] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchInsights();
  }, [documentId]);

  const fetchInsights = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await api.getInsights(documentId);
      setInsights(response.data.data);
    } catch (err) {
      setError('Failed to load insights');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="insights-loading">
        <FaSpinner className="spinner" />
        <p>Generating insights...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="insights-error">
        <div className="error-icon">⚠️</div>
        <p>{error}</p>
      </div>
    );
  }

  return (
    <div className="insights-panel">
      {/* Summary */}
      <div className="card insight-summary">
        <div className="summary-header">
          <FaLightbulb className="summary-icon" />
          <h3>Document Summary</h3>
        </div>
        <p className="summary-text">{insights?.summary}</p>
        {insights?.confidence_score !== undefined && (
          <div className="confidence-bar">
            <div className="confidence-label">
              Confidence Score: {(insights.confidence_score * 100).toFixed(0)}%
            </div>
            <div className="confidence-track">
              <div
                className="confidence-fill"
                style={{ width: `${insights.confidence_score * 100}%` }}
              />
            </div>
          </div>
        )}
      </div>

      {/* Key Findings */}
      {insights?.key_findings && insights.key_findings.length > 0 && (
        <div className="card">
          <h3>🔍 Key Findings</h3>
          <div className="findings-list">
            {insights.key_findings.map((finding, idx) => (
              <div key={idx} className="finding-item">
                <div className="finding-number">{idx + 1}</div>
                <div className="finding-text">{finding}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recommendations */}
      {insights?.recommendations && insights.recommendations.length > 0 && (
        <div className="card">
          <h3>💡 Recommendations</h3>
          <div className="recommendations-list">
            {insights.recommendations.map((rec, idx) => (
              <div key={idx} className="recommendation-item">
                <div className="rec-icon">✓</div>
                <div className="rec-text">{rec}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default InsightsPanel;