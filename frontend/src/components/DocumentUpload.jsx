import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { FaUpload, FaCheckCircle, FaSpinner } from 'react-icons/fa';
import api from '../services/api';
import './DocumentUpload.css';

const DocumentUpload = ({ onUploadSuccess }) => {
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState(null);

  const onDrop = useCallback(async (acceptedFiles) => {
    if (acceptedFiles.length === 0) return;

    const file = acceptedFiles[0];
    setUploading(true);
    setUploadStatus(null);

    try {
      const response = await api.uploadDocument(file);
      
      if (response.data.success) {
        setUploadStatus({
          type: 'success',
          message: `Successfully uploaded: ${file.name}`,
          data: response.data.data
        });
        
        setTimeout(() => {
          onUploadSuccess();
        }, 1500);
      }
    } catch (err) {
      setUploadStatus({
        type: 'error',
        message: `Upload failed: ${err.response?.data?.detail || err.message}`
      });
    } finally {
      setUploading(false);
    }
  }, [onUploadSuccess]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'image/png': ['.png'],
      'image/jpeg': ['.jpg', '.jpeg'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls'],
      'text/csv': ['.csv']
    },
    multiple: false,
    disabled: uploading
  });

  return (
    <div className="document-upload">
      <div className="upload-container">
        <h2>📤 Upload Document</h2>
        <p className="subtitle">Upload a document for AI-powered analysis</p>

        <div
          {...getRootProps()}
          className={`dropzone ${isDragActive ? 'drag-active' : ''} ${uploading ? 'disabled' : ''}`}
        >
          <input {...getInputProps()} />
          
          {uploading ? (
            <div className="upload-status">
              <FaSpinner className="spinner-icon" />
              <p>Uploading and processing...</p>
            </div>
          ) : (
            <>
              <FaUpload className="upload-icon" />
              <p className="upload-text">
                {isDragActive
                  ? 'Drop the file here...'
                  : 'Drag & drop a document, or click to select'}
              </p>
              <p className="upload-hint">
                Supported: PDF, PNG, JPG, XLSX, XLS, CSV (Max 50MB)
              </p>
            </>
          )}
        </div>

        {uploadStatus && (
          <div className={`status-message ${uploadStatus.type}`}>
            {uploadStatus.type === 'success' ? (
              <>
                <FaCheckCircle />
                <div>
                  <strong>{uploadStatus.message}</strong>
                  {uploadStatus.data?.requires_ocr && (
                    <p style={{ fontSize: '0.9rem', marginTop: '0.5rem' }}>
                      📸 Document appears to be scanned. OCR will be applied automatically.
                    </p>
                  )}
                </div>
              </>
            ) : (
              <>
                ❌ {uploadStatus.message}
              </>
            )}
          </div>
        )}

        <div className="upload-features">
          <h3>What happens next?</h3>
          <div className="features-grid">
            <div className="feature-item">
              <span className="feature-icon">🔍</span>
              <h4>Text Extraction</h4>
              <p>Extract text from PDFs, images (OCR), and spreadsheets</p>
            </div>
            <div className="feature-item">
              <span className="feature-icon">🏷️</span>
              <h4>Entity Recognition</h4>
              <p>Identify people, organizations, locations, and dates</p>
            </div>
            <div className="feature-item">
              <span className="feature-icon">💭</span>
              <h4>Sentiment Analysis</h4>
              <p>Analyze the emotional tone of your documents</p>
            </div>
            <div className="feature-item">
              <span className="feature-icon">🕸️</span>
              <h4>Knowledge Graph</h4>
              <p>Visualize relationships between entities</p>
            </div>
            <div className="feature-item">
              <span className="feature-icon">📊</span>
              <h4>Classification</h4>
              <p>Auto-categorize documents (invoice, contract, etc.)</p>
            </div>
            <div className="feature-item">
              <span className="feature-icon">⏱️</span>
              <h4>Timeline</h4>
              <p>Extract and organize dates and events</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DocumentUpload;