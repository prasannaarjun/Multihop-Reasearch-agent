import React from 'react';
import { useAuth } from '../contexts/AuthContext';
import LoadingSpinner from './LoadingSpinner';

const ProtectedRoute = ({ children, requireAdmin = false }) => {
  const { isAuthenticated, user, isLoading } = useAuth();

  // Show loading spinner while checking authentication
  if (isLoading) {
    return (
      <div className="app">
        <div className="container">
          <div style={{ 
            display: 'flex', 
            justifyContent: 'center', 
            alignItems: 'center', 
            minHeight: '50vh' 
          }}>
            <LoadingSpinner />
          </div>
        </div>
      </div>
    );
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    return (
      <div className="app">
        <div className="container">
          <div style={{ 
            textAlign: 'center', 
            padding: '40px 20px',
            maxWidth: '500px',
            margin: '0 auto'
          }}>
            <h2 style={{ color: '#2c3e50', marginBottom: '20px' }}>
              🔐 Authentication Required
            </h2>
            <p style={{ color: '#7f8c8d', marginBottom: '30px', lineHeight: '1.6' }}>
              You need to be logged in to access this page. Please sign in to continue.
            </p>
            <button
              onClick={() => window.location.href = '/login'}
              style={{
                background: '#667eea',
                color: 'white',
                border: 'none',
                padding: '12px 24px',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '1em',
                fontWeight: '600',
                transition: 'all 0.3s ease'
              }}
              onMouseOver={(e) => {
                e.target.style.background = '#5a6fd8';
                e.target.style.transform = 'translateY(-1px)';
              }}
              onMouseOut={(e) => {
                e.target.style.background = '#667eea';
                e.target.style.transform = 'translateY(0)';
              }}
            >
              Go to Login
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Check admin requirement
  if (requireAdmin && (!user || !user.is_admin)) {
    return (
      <div className="app">
        <div className="container">
          <div style={{ 
            textAlign: 'center', 
            padding: '40px 20px',
            maxWidth: '500px',
            margin: '0 auto'
          }}>
            <h2 style={{ color: '#dc3545', marginBottom: '20px' }}>
              🚫 Access Denied
            </h2>
            <p style={{ color: '#7f8c8d', marginBottom: '30px', lineHeight: '1.6' }}>
              You don't have permission to access this page. Administrator privileges are required.
            </p>
            <button
              onClick={() => window.history.back()}
              style={{
                background: '#6c757d',
                color: 'white',
                border: 'none',
                padding: '12px 24px',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '1em',
                fontWeight: '600',
                transition: 'all 0.3s ease',
                marginRight: '10px'
              }}
              onMouseOver={(e) => {
                e.target.style.background = '#5a6268';
                e.target.style.transform = 'translateY(-1px)';
              }}
              onMouseOut={(e) => {
                e.target.style.background = '#6c757d';
                e.target.style.transform = 'translateY(0)';
              }}
            >
              Go Back
            </button>
            <button
              onClick={() => window.location.href = '/'}
              style={{
                background: '#667eea',
                color: 'white',
                border: 'none',
                padding: '12px 24px',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '1em',
                fontWeight: '600',
                transition: 'all 0.3s ease'
              }}
              onMouseOver={(e) => {
                e.target.style.background = '#5a6fd8';
                e.target.style.transform = 'translateY(-1px)';
              }}
              onMouseOut={(e) => {
                e.target.style.background = '#667eea';
                e.target.style.transform = 'translateY(0)';
              }}
            >
              Go Home
            </button>
          </div>
        </div>
      </div>
    );
  }

  // User is authenticated and has required permissions
  return children;
};

export default ProtectedRoute;
