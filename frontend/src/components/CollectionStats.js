import React, { useState, useEffect } from 'react';
import './CollectionStats.css';

const CollectionStats = ({ refreshTrigger }) => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchStats();
  }, [refreshTrigger]);

  const fetchStats = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch('/collection-stats');
      if (!response.ok) {
        throw new Error('Failed to fetch collection stats');
      }
      
      const data = await response.json();
      setStats(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const formatFileType = (type) => {
    return type.replace('.', '').toUpperCase();
  };

  if (loading) {
    return (
      <div className="collection-stats">
        <h3>Document Collection</h3>
        <div className="loading-stats">
          <div className="spinner"></div>
          <p>Loading statistics...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="collection-stats">
        <h3>Document Collection</h3>
        <div className="error-stats">
          <p>Error loading statistics: {error}</p>
          <button onClick={fetchStats} className="retry-btn">
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!stats) {
    return null;
  }

  return (
    <div className="collection-stats">
      <h3>Document Collection</h3>
      
      <div className="stats-grid">
        <div className="stat-item">
          <div className="stat-number">{stats.total_documents}</div>
          <div className="stat-label">Total Documents</div>
        </div>
        
        <div className="stat-item">
          <div className="stat-number">{stats.unique_files}</div>
          <div className="stat-label">Unique Files</div>
        </div>
      </div>

      {stats.file_types && Object.keys(stats.file_types).length > 0 && (
        <div className="file-types-section">
          <h4>File Types</h4>
          <div className="file-types-list">
            {Object.entries(stats.file_types).map(([type, count]) => (
              <div key={type} className="file-type-item">
                <span className="file-type-name">{formatFileType(type)}</span>
                <span className="file-type-count">{count}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="refresh-section">
        <button onClick={fetchStats} className="refresh-btn">
          🔄 Refresh Stats
        </button>
      </div>
    </div>
  );
};

export default CollectionStats;
