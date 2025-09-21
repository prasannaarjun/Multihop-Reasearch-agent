// API service for communicating with the FastAPI backend
const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

class ApiService {
  async request(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      
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
}

export const apiService = new ApiService();
