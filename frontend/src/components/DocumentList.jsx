import React, { useState } from 'react';
import { FaFile, FaTrash, FaEye, FaSearch, FaSync } from 'react-icons/fa';
import { formatFileSize, formatDate, getFileIcon, getStatusColor } from '../utils/helpers';
import './DocumentList.css';

const DocumentList = ({ documents, onDocumentSelect, onDocumentDelete, onRefresh }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState('date');

  const filteredDocuments = documents
    .filter(doc => 
      doc.filename.toLowerCase().includes(searchQuery.toLowerCase())
    )
    .sort((a, b) => {
      if (sortBy === 'date') {
        return new Date(b.upload_date) - new Date(a.upload_date);
      } else if (sortBy === 'name') {
        return a.filename.localeCompare(b.filename);
      } else if (sortBy === 'size') {
        return b.file_size - a.file_size;
      }
      return 0;
    });

  const handleDelete = (e, docId) => {
    e.stopPropagation();
    if (window.confirm('Are you sure you want to delete this document?')) {
      onDocumentDelete(docId);
    }
  };

  return (
    <div className="document-list">
      <div className="list-header">
        <div>
          <h2>📁 Your Documents</h2>
          <p className="subtitle">{documents.length} document{documents.length !== 1 ? 's' : ''} uploaded</p>
        </div>
        <button className="btn btn-secondary" onClick={onRefresh}>
          <FaSync /> Refresh
        </button>
      </div>

      <div className="list-controls">
        <div className="search-box">
          <FaSearch />
          <input
            type="text"
            placeholder="Search documents..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        <select
          className="sort-select"
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value)}
        >
          <option value="date">Sort by Date</option>
          <option value="name">Sort by Name</option>
          <option value="size">Sort by Size</option>
        </select>
      </div>

      {filteredDocuments.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">📄</div>
          <h3>No documents found</h3>
          <p>{searchQuery ? 'Try a different search query' : 'Upload your first document to get started'}</p>
        </div>
      ) : (
        <div className="documents-grid">
          {filteredDocuments.map(doc => (
            <div
              key={doc._id}
              className="document-card"
              onClick={() => onDocumentSelect(doc)}
            >
              <div className="doc-header">
                <span className="doc-icon">{getFileIcon(doc.file_type)}</span>
                <div
                  className="doc-status"
                  style={{ background: getStatusColor(doc.analysis_status) }}
                >
                  {doc.analysis_status || 'pending'}
                </div>
              </div>

              <div className="doc-info">
                <h3 className="doc-title" title={doc.filename}>
                  {doc.filename}
                </h3>
                <div className="doc-meta">
                  <span>📏 {formatFileSize(doc.file_size)}</span>
                  <span>🕒 {formatDate(doc.upload_date)}</span>
                </div>
                {doc.requires_ocr && (
                  <div className="doc-badge">
                    📸 OCR Applied
                  </div>
                )}
              </div>

              <div className="doc-actions">
                <button
                  className="action-btn view"
                  onClick={(e) => {
                    e.stopPropagation();
                    onDocumentSelect(doc);
                  }}
                  title="View Analysis"
                >
                  <FaEye /> View
                </button>
                <button
                  className="action-btn delete"
                  onClick={(e) => handleDelete(e, doc._id)}
                  title="Delete Document"
                >
                  <FaTrash /> Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default DocumentList;