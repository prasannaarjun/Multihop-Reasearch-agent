import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import './UserProfile.css';

const UserProfile = ({ onClose }) => {
  const { user, updateUser, changePassword, logout, logoutAllSessions } = useAuth();
  const [activeTab, setActiveTab] = useState('profile');
  const [isEditing, setIsEditing] = useState(false);
  const [isChangingPassword, setIsChangingPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Profile form data
  const [profileData, setProfileData] = useState({
    username: '',
    email: '',
    full_name: ''
  });

  // Password form data
  const [passwordData, setPasswordData] = useState({
    current_password: '',
    new_password: '',
    confirm_password: ''
  });

  // Form errors
  const [errors, setErrors] = useState({});

  useEffect(() => {
    if (user) {
      setProfileData({
        username: user.username || '',
        email: user.email || '',
        full_name: user.full_name || ''
      });
    }
  }, [user]);

  const handleProfileChange = (e) => {
    const { name, value } = e.target;
    setProfileData(prev => ({
      ...prev,
      [name]: value
    }));
    
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
    setError('');
  };

  const handlePasswordChange = (e) => {
    const { name, value } = e.target;
    setPasswordData(prev => ({
      ...prev,
      [name]: value
    }));
    
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
    setError('');
  };

  const validateProfileForm = () => {
    const newErrors = {};

    if (!profileData.username.trim()) {
      newErrors.username = 'Username is required';
    } else if (profileData.username.length < 3) {
      newErrors.username = 'Username must be at least 3 characters';
    }

    if (!profileData.email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(profileData.email)) {
      newErrors.email = 'Email is invalid';
    }

    if (!profileData.full_name.trim()) {
      newErrors.full_name = 'Full name is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const validatePasswordForm = () => {
    const newErrors = {};

    if (!passwordData.current_password) {
      newErrors.current_password = 'Current password is required';
    }

    if (!passwordData.new_password) {
      newErrors.new_password = 'New password is required';
    } else if (passwordData.new_password.length < 6) {
      newErrors.new_password = 'Password must be at least 6 characters';
    }

    if (!passwordData.confirm_password) {
      newErrors.confirm_password = 'Please confirm your password';
    } else if (passwordData.new_password !== passwordData.confirm_password) {
      newErrors.confirm_password = 'Passwords do not match';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleProfileSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateProfileForm()) {
      return;
    }

    setIsLoading(true);
    setError('');
    setSuccess('');

    const result = await updateUser(profileData);
    
    if (result.success) {
      setSuccess('Profile updated successfully!');
      setIsEditing(false);
    } else {
      setError(result.error);
    }
    
    setIsLoading(false);
  };

  const handlePasswordSubmit = async (e) => {
    e.preventDefault();
    
    if (!validatePasswordForm()) {
      return;
    }

    setIsLoading(true);
    setError('');
    setSuccess('');

    const result = await changePassword({
      current_password: passwordData.current_password,
      new_password: passwordData.new_password
    });
    
    if (result.success) {
      setSuccess('Password changed successfully!');
      setPasswordData({
        current_password: '',
        new_password: '',
        confirm_password: ''
      });
      setIsChangingPassword(false);
    } else {
      setError(result.error);
    }
    
    setIsLoading(false);
  };

  const handleLogout = async () => {
    await logout();
    onClose();
  };

  const handleLogoutAll = async () => {
    const result = await logoutAllSessions();
    if (result.success) {
      onClose();
    } else {
      setError(result.error);
    }
  };

  if (!user) return null;

  return (
    <div className="user-profile-modal">
      <div className="user-profile-overlay" onClick={onClose}></div>
      <div className="user-profile-content">
        <div className="user-profile-header">
          <h3>👤 User Profile</h3>
          <button className="close-btn" onClick={onClose} title="Close">
            ✕
          </button>
        </div>

        <div className="user-profile-tabs">
          <button
            className={`tab-btn ${activeTab === 'profile' ? 'active' : ''}`}
            onClick={() => setActiveTab('profile')}
          >
            Profile
          </button>
          <button
            className={`tab-btn ${activeTab === 'security' ? 'active' : ''}`}
            onClick={() => setActiveTab('security')}
          >
            Security
          </button>
          <button
            className={`tab-btn ${activeTab === 'sessions' ? 'active' : ''}`}
            onClick={() => setActiveTab('sessions')}
          >
            Sessions
          </button>
        </div>

        <div className="user-profile-body">
          {error && (
            <div className="error-message">
              <span>⚠️ {error}</span>
            </div>
          )}

          {success && (
            <div className="success-message">
              <span>✅ {success}</span>
            </div>
          )}

          {activeTab === 'profile' && (
            <div className="profile-tab">
              {!isEditing ? (
                <div className="profile-view">
                  <div className="profile-info">
                    <div className="info-item">
                      <label>Username:</label>
                      <span>{user.username}</span>
                    </div>
                    <div className="info-item">
                      <label>Email:</label>
                      <span>{user.email}</span>
                    </div>
                    <div className="info-item">
                      <label>Full Name:</label>
                      <span>{user.full_name}</span>
                    </div>
                    <div className="info-item">
                      <label>Member Since:</label>
                      <span>{new Date(user.created_at).toLocaleDateString()}</span>
                    </div>
                    <div className="info-item">
                      <label>Status:</label>
                      <span className={`status ${user.is_active ? 'active' : 'inactive'}`}>
                        {user.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </div>
                    {user.is_admin && (
                      <div className="info-item">
                        <label>Role:</label>
                        <span className="admin-badge">Administrator</span>
                      </div>
                    )}
                  </div>
                  <button
                    className="edit-btn"
                    onClick={() => setIsEditing(true)}
                  >
                    Edit Profile
                  </button>
                </div>
              ) : (
                <form onSubmit={handleProfileSubmit} className="profile-form">
                  <div className="form-group">
                    <label htmlFor="username">Username</label>
                    <input
                      type="text"
                      id="username"
                      name="username"
                      value={profileData.username}
                      onChange={handleProfileChange}
                      className={errors.username ? 'error' : ''}
                      disabled={isLoading}
                    />
                    {errors.username && <span className="field-error">{errors.username}</span>}
                  </div>

                  <div className="form-group">
                    <label htmlFor="email">Email</label>
                    <input
                      type="email"
                      id="email"
                      name="email"
                      value={profileData.email}
                      onChange={handleProfileChange}
                      className={errors.email ? 'error' : ''}
                      disabled={isLoading}
                    />
                    {errors.email && <span className="field-error">{errors.email}</span>}
                  </div>

                  <div className="form-group">
                    <label htmlFor="full_name">Full Name</label>
                    <input
                      type="text"
                      id="full_name"
                      name="full_name"
                      value={profileData.full_name}
                      onChange={handleProfileChange}
                      className={errors.full_name ? 'error' : ''}
                      disabled={isLoading}
                    />
                    {errors.full_name && <span className="field-error">{errors.full_name}</span>}
                  </div>

                  <div className="form-actions">
                    <button
                      type="button"
                      className="cancel-btn"
                      onClick={() => {
                        setIsEditing(false);
                        setErrors({});
                        setError('');
                      }}
                      disabled={isLoading}
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      className="save-btn"
                      disabled={isLoading}
                    >
                      {isLoading ? 'Saving...' : 'Save Changes'}
                    </button>
                  </div>
                </form>
              )}
            </div>
          )}

          {activeTab === 'security' && (
            <div className="security-tab">
              {!isChangingPassword ? (
                <div className="security-view">
                  <h4>Password & Security</h4>
                  <p>Keep your account secure by updating your password regularly.</p>
                  <button
                    className="change-password-btn"
                    onClick={() => setIsChangingPassword(true)}
                  >
                    Change Password
                  </button>
                </div>
              ) : (
                <form onSubmit={handlePasswordSubmit} className="password-form">
                  <h4>Change Password</h4>
                  
                  <div className="form-group">
                    <label htmlFor="current_password">Current Password</label>
                    <input
                      type="password"
                      id="current_password"
                      name="current_password"
                      value={passwordData.current_password}
                      onChange={handlePasswordChange}
                      className={errors.current_password ? 'error' : ''}
                      disabled={isLoading}
                    />
                    {errors.current_password && <span className="field-error">{errors.current_password}</span>}
                  </div>

                  <div className="form-group">
                    <label htmlFor="new_password">New Password</label>
                    <input
                      type="password"
                      id="new_password"
                      name="new_password"
                      value={passwordData.new_password}
                      onChange={handlePasswordChange}
                      className={errors.new_password ? 'error' : ''}
                      disabled={isLoading}
                    />
                    {errors.new_password && <span className="field-error">{errors.new_password}</span>}
                  </div>

                  <div className="form-group">
                    <label htmlFor="confirm_password">Confirm New Password</label>
                    <input
                      type="password"
                      id="confirm_password"
                      name="confirm_password"
                      value={passwordData.confirm_password}
                      onChange={handlePasswordChange}
                      className={errors.confirm_password ? 'error' : ''}
                      disabled={isLoading}
                    />
                    {errors.confirm_password && <span className="field-error">{errors.confirm_password}</span>}
                  </div>

                  <div className="form-actions">
                    <button
                      type="button"
                      className="cancel-btn"
                      onClick={() => {
                        setIsChangingPassword(false);
                        setPasswordData({
                          current_password: '',
                          new_password: '',
                          confirm_password: ''
                        });
                        setErrors({});
                        setError('');
                      }}
                      disabled={isLoading}
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      className="save-btn"
                      disabled={isLoading}
                    >
                      {isLoading ? 'Changing...' : 'Change Password'}
                    </button>
                  </div>
                </form>
              )}
            </div>
          )}

          {activeTab === 'sessions' && (
            <div className="sessions-tab">
              <h4>Active Sessions</h4>
              <p>Manage your active sessions and security.</p>
              
              <div className="session-actions">
                <button
                  className="logout-btn"
                  onClick={handleLogout}
                >
                  Logout Current Session
                </button>
                <button
                  className="logout-all-btn"
                  onClick={handleLogoutAll}
                >
                  Logout All Sessions
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default UserProfile;
