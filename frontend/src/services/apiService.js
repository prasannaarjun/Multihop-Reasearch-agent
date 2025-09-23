// API service for communicating with the FastAPI backend
// For ngrok, we need to use the backend ngrok URL
const getApiBase = () => {
  if (process.env.REACT_APP_API_URL) {
    console.log('Using REACT_APP_API_URL:', process.env.REACT_APP_API_URL);
    return process.env.REACT_APP_API_URL;
  }
  
  // If we're running on ngrok, we need to get the backend URL dynamically
  if (window.location.hostname.includes('ngrok') || window.location.hostname.includes('ngrok-free.app')) {
    // For free ngrok plan, we need to get the backend URL from ngrok API
    // This is a temporary solution - you should set REACT_APP_API_URL instead
    console.warn('⚠️  Using ngrok free plan - URLs change on restart!');
    console.warn('⚠️  Please set REACT_APP_API_URL environment variable with your backend ngrok URL');
    console.warn('⚠️  Current backend URL: Check your ngrok dashboard at http://localhost:4040');
    
    // Try to get the backend URL from localStorage (set manually)
    const storedBackendUrl = localStorage.getItem('ngrok_backend_url');
    if (storedBackendUrl) {
      console.log('Using stored backend URL:', storedBackendUrl);
      return storedBackendUrl;
    }
    
    // Fallback: prompt user to set the URL
    const backendUrl = prompt('Please enter your backend ngrok URL (e.g., https://abc123.ngrok-free.app):');
    if (backendUrl) {
      localStorage.setItem('ngrok_backend_url', backendUrl);
      console.log('Stored backend URL:', backendUrl);
      return backendUrl;
    }
    
    // If no URL provided, use localhost (won't work with ngrok)
    console.error('No backend URL provided, falling back to localhost (will not work with ngrok)');
    return 'http://localhost:8000';
  }
  
  // Default to localhost for development
  const localhostUrl = 'http://localhost:8000';
  console.log('Using localhost API URL:', localhostUrl);
  return localhostUrl;
};

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
    const apiBase = getApiBase();
    const url = `${apiBase}${endpoint}`;
    console.log('Making API request to:', url);
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
    const response = await this.request('/ask', {
      method: 'POST',
      body: JSON.stringify({
        question,
        per_sub_k: perSubK,
      }),
    });
    
    // Convert to legacy format for backward compatibility
    return {
      question: response.question,
      answer: response.answer,
      subqueries: response.subqueries,
      citations: response.citations,
      total_documents: response.total_documents
    };
  }

  async exportReport(question) {
    const apiBase = getApiBase();
    const response = await fetch(`${apiBase}/export?question=${encodeURIComponent(question)}`);
    
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
    const apiBase = getApiBase();
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${apiBase}/upload`, {
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
    const response = await this.request('/chat', {
      method: 'POST',
      body: JSON.stringify({
        message,
        conversation_id: conversationId,
        per_sub_k: perSubK,
        include_context: includeContext
      }),
    });
    
    // Convert to legacy format for backward compatibility
    return {
      conversation_id: response.conversation_id,
      message_id: response.message_id,
      answer: response.answer,
      conversation_title: response.conversation_title,
      message_count: response.message_count,
      context_used: response.context_used,
      timestamp: response.timestamp,
      research_result: response.research_result,
      error: response.error
    };
  }

  async getConversations() {
    const conversations = await this.request('/conversations');
    // Convert to legacy format for backward compatibility
    return conversations.map(conv => ({
      conversation_id: conv.id,
      title: conv.title,
      created_at: conv.created_at,
      updated_at: conv.updated_at,
      message_count: conv.message_count,
      is_active: conv.is_active
    }));
  }

  async getConversationHistory(conversationId, maxMessages = 50) {
    const response = await this.request(`/conversations/${conversationId}?max_messages=${maxMessages}`);
    // Convert to legacy format for backward compatibility
    return {
      conversation_id: response.conversation_id,
      title: response.title,
      message_count: response.message_count,
      messages: response.messages.map(msg => ({
        id: msg.id,
        role: msg.role,
        content: msg.content,
        timestamp: msg.timestamp,
        metadata: msg.metadata || {}
      }))
    };
  }

  async createConversation(title = 'New Conversation') {
    const response = await this.request('/conversations', {
      method: 'POST',
      body: JSON.stringify({ title }),
    });
    // Convert to legacy format for backward compatibility
    return {
      conversation_id: response.conversation_id,
      title: response.title
    };
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

    const apiBase = getApiBase();
    const response = await fetch(`${apiBase}/auth/refresh`, {
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
        const apiBase = getApiBase();
        await fetch(`${apiBase}/auth/logout`, {
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
