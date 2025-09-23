import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import UserProfile from './UserProfile';
import './Header.css';

const Header = () => {
  const { user, logout, isAuthenticated } = useAuth();
  const [showUserProfile, setShowUserProfile] = useState(false);

  const handleLogout = async () => {
    await logout();
  };

  return (
    <header>
      <div className="header-content">
        <div className="header-main">
          <h1>🔍 Multi-hop Research Agent</h1>
          <p>Ask complex questions and get comprehensive answers using Chroma-powered document retrieval</p>
        </div>
        
        {isAuthenticated && user && (
          <div className="header-user">
            <div className="user-info">
              <span className="user-name">
                Welcome, {user.full_name || user.username}!
              </span>
              {user.is_admin && (
                <span className="admin-badge">Admin</span>
              )}
            </div>
            <div className="user-actions">
              <button
                className="profile-btn"
                onClick={() => setShowUserProfile(true)}
                title="User Profile"
              >
                👤 Profile
              </button>
              <button
                className="logout-btn"
                onClick={handleLogout}
                title="Logout"
              >
                🚪 Logout
              </button>
            </div>
          </div>
        )}
      </div>

      {showUserProfile && (
        <UserProfile onClose={() => setShowUserProfile(false)} />
      )}
    </header>
  );
};

export default Header;
