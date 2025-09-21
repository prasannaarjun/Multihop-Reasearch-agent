import React from 'react';
import './ErrorMessage.css';

const ErrorMessage = ({ message, onDismiss }) => {
  return (
    <div className="error">
      <h3>Error</h3>
      <p>{message}</p>
      {onDismiss && (
        <button className="dismiss-btn" onClick={onDismiss}>
          ×
        </button>
      )}
    </div>
  );
};

export default ErrorMessage;
