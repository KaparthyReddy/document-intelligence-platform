import React, { useState, useEffect } from 'react';
import './App.css';
import { FaFileAlt, FaCheckCircle, FaTimesCircle } from 'react-icons/fa';

import DocumentUpload from './components/DocumentUpload';
import DocumentList from './components/DocumentList';
import AnalysisDashboard from './components/AnalysisDashboard';

import api from './services/api';

function App() {
  const [backendStatus, setBackendStatus] = useState('checking');
  const [activeTab, setActiveTab] = useState('upload');
  const [documents, setDocuments] = useState([]);
  const [selectedDocument, setSelectedDocument] = useState(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  // Check backend health
  useEffect(() => {
    checkBackend();
  }, []);

  // Fetch documents when switching to documents tab
  useEffect(() => {
    if (activeTab === 'documents') {
      fetchDocuments();
    }
  }, [activeTab, refreshTrigger]);

  const checkBackend = async () => {
    try {
      const response = await api.checkHealth();
      setBackendStatus('online');
      console.log('✅ Backend is online:', response.data);
    } catch (err) {
      setBackendStatus('offline');
      console.error('❌ Backend is offline:', err);
    }
  };

  const fetchDocuments = async () => {
    try {
      const response = await api.getDocuments();
      setDocuments(response.data.data.documents);
    } catch (err) {
      console.error('Error fetching documents:', err);
    }
  };

  const handleUploadSuccess = () => {
    setRefreshTrigger(prev => prev + 1);
    setActiveTab('documents');
  };

  const handleDocumentSelect = (doc) => {
    setSelectedDocument(doc);
    setActiveTab('analysis');
  };

  const handleDocumentDelete = async (docId) => {
    try {
      await api.deleteDocument(docId);
      setRefreshTrigger(prev => prev + 1);
      if (selectedDocument && selectedDocument._id === docId) {
        setSelectedDocument(null);
      }
    } catch (err) {
      console.error('Error deleting document:', err);
    }
  };

  return (
    <div className="App">
      {/* Header */}
      <header className="app-header">
        <div className="header-content">
          <div className="app-logo">
            <FaFileAlt className="logo-icon" />
            <div>
              <h1 className="app-title">Document Intelligence</h1>
              <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>
                AI-Powered Document Analysis
              </p>
            </div>
          </div>
          
          <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
            <div className={`status-badge ${backendStatus}`}>
              <span className="status-dot"></span>
              {backendStatus === 'online' ? (
                <>
                  <FaCheckCircle /> Backend Online
                </>
              ) : backendStatus === 'offline' ? (
                <>
                  <FaTimesCircle /> Backend Offline
                </>
              ) : (
                'Checking...'
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="main-content">
        {/* Tabs */}
        <div className="tabs">
          <button
            className={`tab ${activeTab === 'upload' ? 'active' : ''}`}
            onClick={() => setActiveTab('upload')}
          >
            📤 Upload
          </button>
          <button
            className={`tab ${activeTab === 'documents' ? 'active' : ''}`}
            onClick={() => setActiveTab('documents')}
          >
            📁 Documents ({documents.length})
          </button>
          <button
            className={`tab ${activeTab === 'analysis' ? 'active' : ''}`}
            onClick={() => setActiveTab('analysis')}
            disabled={!selectedDocument}
          >
            📊 Analysis
          </button>
        </div>

        {/* Tab Content */}
        <div className="tab-content">
          {activeTab === 'upload' && (
            <DocumentUpload onUploadSuccess={handleUploadSuccess} />
          )}

          {activeTab === 'documents' && (
            <DocumentList
              documents={documents}
              onDocumentSelect={handleDocumentSelect}
              onDocumentDelete={handleDocumentDelete}
              onRefresh={() => setRefreshTrigger(prev => prev + 1)}
            />
          )}

          {activeTab === 'analysis' && selectedDocument && (
            <AnalysisDashboard
              document={selectedDocument}
              onBack={() => setActiveTab('documents')}
            />
          )}

          {activeTab === 'analysis' && !selectedDocument && (
            <div className="empty-state">
              <div className="empty-icon">📊</div>
              <h2>No Document Selected</h2>
              <p>Select a document from the Documents tab to view analysis</p>
            </div>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="footer">
        <p>
          Built with ❤️ using React, FastAPI, MongoDB & AI | Document Intelligence Platform v1.0.0
        </p>
      </footer>
    </div>
  );
}

export default App;