import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 300000, // 5 minutes for long operations
});

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    console.log('🚀 API Request:', config.method.toUpperCase(), config.url);
    return config;
  },
  (error) => {
    console.error('❌ Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor
apiClient.interceptors.response.use(
  (response) => {
    console.log('✅ API Response:', response.config.url, response.status);
    return response;
  },
  (error) => {
    console.error('❌ Response Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

const api = {
  // Health check
  checkHealth: () => apiClient.get('/health'),

  // Document upload
  uploadDocument: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return apiClient.post('/api/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  // Get all documents
  getDocuments: (skip = 0, limit = 50) => {
    return apiClient.get('/api/documents', { params: { skip, limit } });
  },

  // Get single document
  getDocument: (documentId) => {
    return apiClient.get(`/api/document/${documentId}`);
  },

  // Delete document
  deleteDocument: (documentId) => {
    return apiClient.delete(`/api/document/${documentId}`);
  },

  // Analyze document
  analyzeDocument: (documentId, force = false) => {
    return apiClient.post('/api/analyze', { document_id: documentId, force });
  },

  // Get analysis results
  getAnalysis: (documentId) => {
    return apiClient.get(`/api/analysis/${documentId}`);
  },

  // Get entities
  getEntities: (documentId, entityType = null) => {
    const params = entityType ? { entity_type: entityType } : {};
    return apiClient.get(`/api/entities/${documentId}`, { params });
  },

  // Get sentiment
  getSentiment: (documentId) => {
    return apiClient.get(`/api/sentiment/${documentId}`);
  },

  // Get knowledge graph
  getKnowledgeGraph: (documentId) => {
    return apiClient.get(`/api/knowledge-graph/${documentId}`);
  },

  // Get timeline
  getTimeline: (documentId) => {
    return apiClient.get(`/api/timeline/${documentId}`);
  },

  // Search documents
  searchDocuments: (query, limit = 20) => {
    return apiClient.get('/api/search', { params: { query, limit } });
  },

  // Get insights
  getInsights: (documentId) => {
    return apiClient.get(`/api/insights/${documentId}`);
  },

  // Compare documents
  compareDocuments: (docId1, docId2) => {
    return apiClient.post('/api/compare', {
      document_id_1: docId1,
      document_id_2: docId2,
    });
  },

  // Get statistics
  getStatistics: () => {
    return apiClient.get('/api/statistics');
  },

  // Get trends
  getTrends: (limit = 100) => {
    return apiClient.get('/api/trends', { params: { limit } });
  },

  // Export report
  exportReport: (documentId, format = 'json') => {
    return apiClient.get(`/api/export-report/${documentId}`, {
      params: { format },
    });
  },
};

export default api;