import React, { useState, useEffect } from 'react';
import './App.css';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import Header from './components/Header';
import QuestionForm from './components/QuestionForm';
import LoadingSpinner from './components/LoadingSpinner';
import Results from './components/Results';
import ErrorMessage from './components/ErrorMessage';
import FileUpload from './components/FileUpload';
import CollectionStats from './components/CollectionStats';
import ChatInterface from './components/ChatInterface';
import Login from './components/Login';
import Register from './components/Register';
import { apiService } from './services/apiService';

// Main App Content Component
function AppContent() {
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [agentStatus, setAgentStatus] = useState(null);
  const [uploadSuccess, setUploadSuccess] = useState(null);
  const [refreshStats, setRefreshStats] = useState(0);
  const [isResearchMode, setIsResearchMode] = useState(true);
  const [authMode, setAuthMode] = useState('login'); // 'login' or 'register'
  const { isAuthenticated, isLoading: authLoading } = useAuth();

  useEffect(() => {
    checkAgentStatus();
  }, []);

  const checkAgentStatus = async () => {
    try {
      const status = await apiService.checkHealth();
      setAgentStatus(status);
      if (!status.agent_initialized) {
        setError('Research agent not initialized. Please build the Chroma index first.');
      }
    } catch (err) {
      setError('Cannot connect to the API server. Make sure the server is running.');
    }
  };

  const handleAskQuestion = async (question, perSubK) => {
    setIsLoading(true);
    setError(null);
    setResults(null);

    try {
      const response = await apiService.askQuestion(question, perSubK);
      setResults(response);
    } catch (err) {
      setError(err.message || 'Failed to process question');
    } finally {
      setIsLoading(false);
    }
  };

  const handleExportReport = async (question) => {
    try {
      await apiService.exportReport(question);
    } catch (err) {
      setError(err.message || 'Failed to export report');
    }
  };

  const handleUploadSuccess = (result) => {
    setUploadSuccess(result);
    setRefreshStats(prev => prev + 1);
    // Clear success message after 5 seconds
    setTimeout(() => setUploadSuccess(null), 5000);
  };

  const handleUploadError = (errorMessage) => {
    setError(errorMessage);
  };

  const toggleMode = () => {
    setIsResearchMode(!isResearchMode);
  };

  // Show loading while checking authentication
  if (authLoading) {
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

  // Show authentication forms if not logged in
  if (!isAuthenticated) {
    return (
      <div className="app">
        <div className="auth-container">
          {authMode === 'login' ? (
            <Login onSwitchToRegister={() => setAuthMode('register')} />
          ) : (
            <Register onSwitchToLogin={() => setAuthMode('login')} />
          )}
        </div>
      </div>
    );
  }

  // Show chat mode
  if (!isResearchMode) {
    return (
      <div className="app">
        <ChatInterface 
          onToggleMode={toggleMode}
          isResearchMode={isResearchMode}
        />
      </div>
    );
  }

  // Show research mode (main app)
  return (
    <div className="app">
      <div className="container">
        <Header onToggleMode={toggleMode} isResearchMode={isResearchMode} />
        
        <main>
          <CollectionStats refreshTrigger={refreshStats} />
          
          <FileUpload 
            onUploadSuccess={handleUploadSuccess}
            onUploadError={handleUploadError}
            disabled={!agentStatus?.agent_initialized}
          />

          {uploadSuccess && (
            <div className="success-message">
              <h4>✅ Upload Successful!</h4>
              <p>{uploadSuccess.message}</p>
              <p>File: {uploadSuccess.filename} ({uploadSuccess.file_type})</p>
              <p>Words: {uploadSuccess.word_count} | Chunks: {uploadSuccess.chunks_added}</p>
            </div>
          )}

          <QuestionForm 
            onAskQuestion={handleAskQuestion}
            onExportReport={handleExportReport}
            disabled={isLoading || !agentStatus?.agent_initialized}
          />

          {isLoading && <LoadingSpinner />}

          {error && (
            <ErrorMessage 
              message={error} 
              onDismiss={() => setError(null)} 
            />
          )}

          {results && <Results data={results} />}
        </main>

        <footer>
          <p>Powered by Chroma DB and FastAPI</p>
        </footer>
      </div>
    </div>
  );
}

// Main App Component with AuthProvider
function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;
