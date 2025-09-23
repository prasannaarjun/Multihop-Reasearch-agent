// API service for communicating with the FastAPI backend
const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

class ApiService {
  constructor() {
    this.token = localStorage.getItem('access_token');
    this.refreshToken = localStorage.getItem('refresh_token');
  }

  setTokens(accessToken, refreshToken) {
    this.token = accessToken;
    this.refreshToken = refreshToken;
    localStorage.setItem('access_token', accessToken);
    localStorage.setItem('refresh_token', refreshToken);
  }

  clearTokens() {
    this.token = null;
    this.refreshToken = null;
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  }

  async request(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    // Add authorization header if token exists
    if (this.token) {
      config.headers.Authorization = `Bearer ${this.token}`;
    }

    try {
      const response = await fetch(url, config);
      
      // Handle token expiration
      if (response.status === 401 && this.refreshToken) {
        try {
          await this.refreshAccessToken();
          // Retry the original request with new token
          config.headers.Authorization = `Bearer ${this.token}`;
          const retryResponse = await fetch(url, config);
          
          if (!retryResponse.ok) {
            const errorData = await retryResponse.json().catch(() => ({}));
            throw new Error(errorData.detail || `HTTP error! status: ${retryResponse.status}`);
          }
          
          return await retryResponse.json();
        } catch (refreshError) {
          // Refresh failed, clear tokens and redirect to login
          this.clearTokens();
          window.location.href = '/login';
          throw new Error('Session expired. Please log in again.');
        }
      }
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      if (error.name === 'TypeError' && error.message.includes('fetch')) {
        throw new Error('Cannot connect to the API server. Make sure the server is running.');
      }
      throw error;
    }
  }

  async checkHealth() {
    return this.request('/health');
  }

  async askQuestion(question, perSubK = 3) {
    return this.request('/ask', {
      method: 'POST',
      body: JSON.stringify({
        question,
        per_sub_k: perSubK,
      }),
    });
  }

  async exportReport(question) {
    const response = await fetch(`${API_BASE}/export?question=${encodeURIComponent(question)}`);
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Failed to export report');
    }
    
    // Download the file
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `research_report_${new Date().toISOString().slice(0,19).replace(/:/g, '-')}.md`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  }

  async getStats() {
    return this.request('/stats');
  }

  async uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE}/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || 'Upload failed');
    }

    return await response.json();
  }

  async getCollectionStats() {
    return this.request('/collection-stats');
  }

  async getSupportedFileTypes() {
    return this.request('/supported-file-types');
  }

  // Chat API methods
  async sendChatMessage(message, conversationId = null, perSubK = 3, includeContext = true) {
    return this.request('/chat', {
      method: 'POST',
      body: JSON.stringify({
        message,
        conversation_id: conversationId,
        per_sub_k: perSubK,
        include_context: includeContext
      }),
    });
  }

  async getConversations() {
    return this.request('/conversations');
  }

  async getConversationHistory(conversationId, maxMessages = 50) {
    return this.request(`/conversations/${conversationId}?max_messages=${maxMessages}`);
  }

  async createConversation(title = 'New Conversation') {
    return this.request('/conversations', {
      method: 'POST',
      body: JSON.stringify({ title }),
    });
  }

  async updateConversationTitle(conversationId, title) {
    return this.request(`/conversations/${conversationId}/title`, {
      method: 'PUT',
      body: JSON.stringify({ title }),
    });
  }

  async deleteConversation(conversationId) {
    return this.request(`/conversations/${conversationId}`, {
      method: 'DELETE',
    });
  }

  // Authentication methods
  async register(userData) {
    return this.request('/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  }

  async login(credentials) {
    const response = await this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });
    
    // Store tokens
    this.setTokens(response.access_token, response.refresh_token);
    return response;
  }

  async refreshAccessToken() {
    if (!this.refreshToken) {
      throw new Error('No refresh token available');
    }

    const response = await fetch(`${API_BASE}/auth/refresh`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ refresh_token: this.refreshToken }),
    });

    if (!response.ok) {
      throw new Error('Failed to refresh token');
    }

    const data = await response.json();
    this.setTokens(data.access_token, data.refresh_token);
    return data;
  }

  async logout() {
    if (this.refreshToken) {
      try {
        await fetch(`${API_BASE}/auth/logout`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ refresh_token: this.refreshToken }),
        });
      } catch (error) {
        console.warn('Logout request failed:', error);
      }
    }
    this.clearTokens();
  }

  async logoutAllSessions() {
    const response = await this.request('/auth/logout-all', {
      method: 'POST',
    });
    this.clearTokens();
    return response;
  }

  async getCurrentUser() {
    return this.request('/auth/me');
  }

  async updateUser(userData) {
    return this.request('/auth/me', {
      method: 'PUT',
      body: JSON.stringify(userData),
    });
  }

  async changePassword(passwordData) {
    return this.request('/auth/change-password', {
      method: 'POST',
      body: JSON.stringify(passwordData),
    });
  }

  async getUserSessions() {
    return this.request('/auth/sessions');
  }

  // Admin methods
  async getUsers() {
    return this.request('/auth/users');
  }

  async deactivateUser(userId) {
    return this.request(`/auth/users/${userId}/deactivate`, {
      method: 'PUT',
    });
  }

  async activateUser(userId) {
    return this.request(`/auth/users/${userId}/activate`, {
      method: 'PUT',
    });
  }

  async toggleAdminStatus(userId, isAdmin) {
    return this.request(`/auth/users/${userId}/admin`, {
      method: 'PUT',
      body: JSON.stringify({ is_admin: isAdmin }),
    });
  }

  // Check if user is authenticated
  isAuthenticated() {
    return !!this.token;
  }
}

export const apiService = new ApiService();
