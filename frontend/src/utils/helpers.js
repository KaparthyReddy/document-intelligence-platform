export const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
};

export const formatDate = (dateString) => {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now - date;
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
  if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
  if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;

  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
};

export const getFileIcon = (fileType) => {
  const icons = {
    '.pdf': '📄',
    '.png': '🖼️',
    '.jpg': '🖼️',
    '.jpeg': '🖼️',
    '.xlsx': '📊',
    '.xls': '📊',
    '.csv': '📊',
    '.docx': '📝',
    '.doc': '📝',
  };
  return icons[fileType] || '📄';
};

export const getStatusColor = (status) => {
  const colors = {
    uploaded: '#f59e0b',
    processing: '#3b82f6',
    completed: '#10b981',
    failed: '#ef4444',
    pending: '#94a3b8',
  };
  return colors[status] || '#94a3b8';
};

export const truncateText = (text, maxLength = 100) => {
  if (!text || text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
};

export const getEntityColor = (entityType) => {
  const colors = {
    PERSON: '#60a5fa',
    ORG: '#34d399',
    GPE: '#fbbf24',
    DATE: '#f472b6',
    MONEY: '#a78bfa',
    PRODUCT: '#fb923c',
    EVENT: '#e879f9',
    LOC: '#4ade80',
  };
  return colors[entityType] || '#94a3b8';
};

export const getSentimentEmoji = (sentiment) => {
  const emojis = {
    positive: '😊',
    negative: '😞',
    neutral: '😐',
  };
  return emojis[sentiment] || '😐';
};

export const calculateConfidenceLevel = (score) => {
  if (score >= 0.9) return 'Very High';
  if (score >= 0.7) return 'High';
  if (score >= 0.5) return 'Medium';
  if (score >= 0.3) return 'Low';
  return 'Very Low';
};