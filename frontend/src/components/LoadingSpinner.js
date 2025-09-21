import React from 'react';
import './LoadingSpinner.css';

const LoadingSpinner = () => {
  return (
    <div className="loading">
      <div className="spinner"></div>
      <p>Researching your question...</p>
    </div>
  );
};

export default LoadingSpinner;
