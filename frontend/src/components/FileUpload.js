import React, { useState, useRef } from 'react';
import './FileUpload.css';
import { apiService } from '../services/apiService';

const FileUpload = ({ onUploadSuccess, onUploadError, disabled }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [supportedTypes, setSupportedTypes] = useState([]);
  const fileInputRef = useRef(null);

  React.useEffect(() => {
    // Fetch supported file types
    fetchSupportedTypes();
  }, []);

  const fetchSupportedTypes = async () => {
    try {
      const data = await apiService.getSupportedFileTypes();
      setSupportedTypes(data.supported_extensions || []);
    } catch (error) {
      console.error('Failed to fetch supported file types:', error);
    }
  };

  const handleDragEnter = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (!disabled) {
      setIsDragging(true);
    }
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    if (disabled) return;

    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      handleFileUpload(files[0]);
    }
  };

  const handleFileSelect = (e) => {
    const files = Array.from(e.target.files);
    if (files.length > 0) {
      handleFileUpload(files[0]);
    }
  };

  const handleFileUpload = async (file) => {
    if (disabled) return;

    // Validate file type
    const fileExt = '.' + file.name.split('.').pop().toLowerCase();
    if (!supportedTypes.includes(fileExt)) {
      onUploadError(`Unsupported file type. Supported types: ${supportedTypes.join(', ')}`);
      return;
    }

    // Validate file size (50MB limit)
    const maxSize = 50 * 1024 * 1024; // 50MB
    if (file.size > maxSize) {
      onUploadError('File too large. Maximum size is 50MB.');
      return;
    }

    setIsUploading(true);
    setUploadProgress(0);

    try {
      const result = await apiService.uploadFile(file);
      setUploadProgress(100);
      
      // Simulate progress for better UX
      setTimeout(() => {
        setIsUploading(false);
        setUploadProgress(0);
        onUploadSuccess(result);
      }, 500);

    } catch (error) {
      setIsUploading(false);
      setUploadProgress(0);
      onUploadError(error.message || 'Upload failed');
    }
  };

  const openFileDialog = () => {
    if (!disabled && fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  return (
    <div className="file-upload-container">
      <h3>Upload Documents</h3>
      
      <div className="upload-content">
        <div
          className={`file-drop-zone ${isDragging ? 'dragging' : ''} ${disabled ? 'disabled' : ''}`}
          onDragEnter={handleDragEnter}
          onDragLeave={handleDragLeave}
          onDragOver={handleDragOver}
          onDrop={handleDrop}
          onClick={openFileDialog}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept={supportedTypes.join(',')}
            onChange={handleFileSelect}
            style={{ display: 'none' }}
            disabled={disabled}
          />
          
          {isUploading ? (
            <div className="upload-progress">
              <div className="progress-bar">
                <div 
                  className="progress-fill" 
                  style={{ width: `${uploadProgress}%` }}
                ></div>
              </div>
              <p>Processing file...</p>
            </div>
          ) : (
            <div className="drop-content">
              <div className="upload-icon">📁</div>
              <p className="drop-text">
                {isDragging ? 'Drop file here' : 'Click or drag file here'}
              </p>
              <p className="file-types">
                Supported: {supportedTypes.join(', ')}
              </p>
              <p className="file-size">Max size: 50MB</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default FileUpload;
