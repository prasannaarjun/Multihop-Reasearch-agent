import React from 'react';
import './SubqueryDisplay.css';

const SubqueryDisplay = ({ subqueries = [], visibleCount = 0, isProcessing = false }) => {
  if (!subqueries || subqueries.length === 0) {
    return null;
  }

  return (
    <div className="subquery-display">
      <div className="subquery-header">
        <div className="subquery-icon">🔍</div>
        <div className="subquery-title">
          {isProcessing ? 'Researching subqueries...' : 'Research subqueries:'}
        </div>
        {isProcessing && (
          <div className="subquery-progress">
            {visibleCount} / {subqueries.length}
          </div>
        )}
      </div>
      <div className="subquery-list">
        {subqueries.slice(0, visibleCount).map((subquery, index) => (
          <div key={index} className="subquery-item">
            <div className="subquery-number">{index + 1}</div>
            <div className="subquery-text">{subquery}</div>
            <div className="subquery-status">
              {index < visibleCount - 1 ? (
                <div className="completed-check">✓</div>
              ) : isProcessing ? (
                <div className="processing-dot"></div>
              ) : (
                <div className="completed-check">✓</div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default SubqueryDisplay;
