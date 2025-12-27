import React, { useState, useEffect } from 'react';
import { FaArrowLeft, FaSync, FaDownload, FaSpinner } from 'react-icons/fa';
import api from '../services/api';
import EntityViewer from './EntityViewer';
import KnowledgeGraph from './KnowledgeGraph';
import SentimentChart from './SentimentChart';
import TimelineView from './TimelineView';
import InsightsPanel from './InsightsPanel';
import './AnalysisDashboard.css';

const AnalysisDashboard = ({ document, onBack }) => {
  const [activeSection, setActiveSection] = useState('overview');
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchAnalysis();
  }, [document._id]);

  const fetchAnalysis = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await api.getAnalysis(document._id);
      setAnalysis(response.data.data);
    } catch (err) {
      if (err.response?.status === 404) {
        setError('No analysis found. Click "Analyze Document" to start.');
      } else {
        setError('Failed to load analysis');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyze = async () => {
    setAnalyzing(true);
    setError(null);

    try {
      await api.analyzeDocument(document._id);
      
      // Poll for results
      let attempts = 0;
      const maxAttempts = 60; // 2 minutes
      
      const pollInterval = setInterval(async () => {
        attempts++;
        
        try {
          const response = await api.getAnalysis(document._id);
          if (response.data.data) {
            setAnalysis(response.data.data);
            setAnalyzing(false);
            clearInterval(pollInterval);
          }
        } catch (err) {
          // Keep polling
        }
        
        if (attempts >= maxAttempts) {
          clearInterval(pollInterval);
          setAnalyzing(false);
          setError('Analysis is taking longer than expected. Please refresh.');
        }
      }, 2000);
      
    } catch (err) {
      setAnalyzing(false);
      setError('Failed to start analysis');
    }
  };

  const handleExport = async () => {
    try {
      const response = await api.exportReport(document._id, 'markdown');
      const blob = new Blob([response.data.data], { type: 'text/markdown' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${document.filename}_report.md`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert('Failed to export report');
    }
  };

  return (
    <div className="analysis-dashboard">
      {/* Header */}
      <div className="dashboard-header">
        <div className="header-left">
          <button className="btn btn-secondary" onClick={onBack}>
            <FaArrowLeft /> Back
          </button>
          <div className="doc-info-header">
            <h2>{document.filename}</h2>
            <div className="header-meta">
              <span>{document.file_type}</span>
              <span>•</span>
              <span>Status: {document.analysis_status || 'pending'}</span>
            </div>
          </div>
        </div>
        
        <div className="header-actions">
          {analysis && (
            <button className="btn btn-secondary" onClick={handleExport}>
              <FaDownload /> Export Report
            </button>
          )}
          <button
            className="btn btn-primary"
            onClick={handleAnalyze}
            disabled={analyzing}
          >
            {analyzing ? (
              <>
                <FaSpinner className="spinner" /> Analyzing...
              </>
            ) : (
              <>
                <FaSync /> Analyze Document
              </>
            )}
          </button>
        </div>
      </div>

      {/* Navigation */}
      {analysis && (
        <div className="section-nav">
          <button
            className={`nav-btn ${activeSection === 'overview' ? 'active' : ''}`}
            onClick={() => setActiveSection('overview')}
          >
            📊 Overview
          </button>
          <button
            className={`nav-btn ${activeSection === 'entities' ? 'active' : ''}`}
            onClick={() => setActiveSection('entities')}
          >
            🏷️ Entities
          </button>
          <button
            className={`nav-btn ${activeSection === 'sentiment' ? 'active' : ''}`}
            onClick={() => setActiveSection('sentiment')}
          >
            💭 Sentiment
          </button>
          <button
            className={`nav-btn ${activeSection === 'knowledge' ? 'active' : ''}`}
            onClick={() => setActiveSection('knowledge')}
          >
            🕸️ Knowledge Graph
          </button>
          <button
            className={`nav-btn ${activeSection === 'timeline' ? 'active' : ''}`}
            onClick={() => setActiveSection('timeline')}
          >
            ⏱️ Timeline
          </button>
          <button
            className={`nav-btn ${activeSection === 'insights' ? 'active' : ''}`}
            onClick={() => setActiveSection('insights')}
          >
            💡 Insights
          </button>
        </div>
      )}

      {/* Content */}
      <div className="dashboard-content">
        {loading && (
          <div className="loading-state">
            <FaSpinner className="spinner large" />
            <p>Loading analysis...</p>
          </div>
        )}

        {error && !loading && (
          <div className="error-state">
            <div className="error-icon">⚠️</div>
            <h3>{error}</h3>
            {!analysis && (
              <button className="btn btn-primary" onClick={handleAnalyze}>
                Start Analysis
              </button>
            )}
          </div>
        )}

        {analyzing && (
          <div className="analyzing-state">
            <FaSpinner className="spinner large" />
            <h3>Analyzing Document...</h3>
            <p>This may take 30 seconds to 2 minutes</p>
            <div className="progress-steps">
              <div className="step">✓ Text Extraction</div>
              <div className="step active">⏳ Entity Recognition</div>
              <div className="step">Sentiment Analysis</div>
              <div className="step">Knowledge Graph</div>
            </div>
          </div>
        )}

        {analysis && !loading && !analyzing && (
          <>
            {activeSection === 'overview' && (
              <div className="overview-section">
                <div className="stats-grid">
                  <div className="stat-card">
                    <div className="stat-icon">📄</div>
                    <div className="stat-info">
                      <div className="stat-label">Category</div>
                      <div className="stat-value">
                        {analysis.classification?.category || 'Unknown'}
                      </div>
                      <div className="stat-sub">
                        {(analysis.classification?.confidence * 100).toFixed(0)}% confidence
                      </div>
                    </div>
                  </div>

                  <div className="stat-card">
                    <div className="stat-icon">💭</div>
                    <div className="stat-info">
                      <div className="stat-label">Sentiment</div>
                      <div className="stat-value">
                        {analysis.sentiment?.overall_sentiment || 'Neutral'}
                      </div>
                      <div className="stat-sub">
                        Score: {(analysis.sentiment?.average_score || 0).toFixed(2)}
                      </div>
                    </div>
                  </div>

                  <div className="stat-card">
                    <div className="stat-icon">🏷️</div>
                    <div className="stat-info">
                      <div className="stat-label">Entities</div>
                      <div className="stat-value">
                        {analysis.entities?.total_entities || 0}
                      </div>
                      <div className="stat-sub">
                        {(analysis.entities?.entity_types || []).length} types
                      </div>
                    </div>
                  </div>

                  <div className="stat-card">
                    <div className="stat-icon">📝</div>
                    <div className="stat-info">
                      <div className="stat-label">Words</div>
                      <div className="stat-value">
                        {analysis.statistics?.total_words || 0}
                      </div>
                      <div className="stat-sub">
                        {analysis.statistics?.total_sentences || 0} sentences
                      </div>
                    </div>
                  </div>
                </div>

                {/* Document Structure */}
                <div className="card">
                  <h3>📋 Document Structure</h3>
                  <div className="structure-info">
                    <div className="structure-item">
                      <span className="structure-label">Has Tables:</span>
                      <span className="structure-value">
                        {analysis.structure?.has_tables ? '✅ Yes' : '❌ No'}
                      </span>
                    </div>
                    <div className="structure-item">
                      <span className="structure-label">Has Lists:</span>
                      <span className="structure-value">
                        {analysis.structure?.has_lists ? '✅ Yes' : '❌ No'}
                      </span>
                    </div>
                    <div className="structure-item">
                      <span className="structure-label">Total Lines:</span>
                      <span className="structure-value">
                        {analysis.structure?.total_lines || 0}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Key Phrases */}
                {analysis.key_phrases && analysis.key_phrases.length > 0 && (
                  <div className="card">
                    <h3>🔑 Key Phrases</h3>
                    <div className="phrases-list">
                      {analysis.key_phrases.slice(0, 10).map((phrase, idx) => (
                        <div key={idx} className="phrase-item">
                          {phrase.text}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {activeSection === 'entities' && (
              <EntityViewer analysis={analysis} documentId={document._id} />
            )}

            {activeSection === 'sentiment' && (
              <SentimentChart analysis={analysis} />
            )}

            {activeSection === 'knowledge' && (
              <KnowledgeGraph analysis={analysis} />
            )}

            {activeSection === 'timeline' && (
              <TimelineView analysis={analysis} />
            )}

            {activeSection === 'insights' && (
              <InsightsPanel documentId={document._id} />
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default AnalysisDashboard;