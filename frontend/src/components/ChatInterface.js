import React, { useState, useEffect, useRef, useCallback } from 'react';
import './ChatInterface.css';
import ChatMessage from './ChatMessage';
import ConversationList from './ConversationList';
import FileUpload from './FileUpload';
import HighlightListener from './HighlightListener';
import AskModelModal from './AskModelModal';
import UserProfile from './UserProfile';
import ModelSelector from './ModelSelector';
import { useAuth } from '../contexts/AuthContext';
import { apiService } from '../services/apiService';

const ChatInterface = ({ onToggleMode, isResearchMode }) => {
  const { logout } = useAuth();
  const [conversations, setConversations] = useState([]);
  const [currentConversation, setCurrentConversation] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showFileUpload, setShowFileUpload] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(null);
  const [askModelModalOpen, setAskModelModalOpen] = useState(false);
  const [askModelHighlight, setAskModelHighlight] = useState('');
  const [showUserProfile, setShowUserProfile] = useState(false);
  const [currentModel, setCurrentModel] = useState('');
  const messagesEndRef = useRef(null);

  useEffect(() => {
    loadConversations();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);


  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadConversations = async () => {
    try {
      const convs = await apiService.getConversations();
      setConversations(convs);
    } catch (err) {
      setError('Failed to load conversations');
    }
  };

  const loadConversation = async (conversationId) => {
    try {
      const history = await apiService.getConversationHistory(conversationId);
      setCurrentConversation(history);
      setMessages(history.messages);
    } catch (err) {
      setError('Failed to load conversation');
    }
  };

  const createNewConversation = async () => {
    try {
      const newConv = await apiService.createConversation();
      setCurrentConversation({
        conversation_id: newConv.conversation_id,
        title: newConv.title,
        messages: []
      });
      setMessages([]);
      loadConversations();
    } catch (err) {
      setError('Failed to create conversation');
    }
  };

  const sendMessage = async (selectedText = null) => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: inputMessage,
      timestamp: new Date().toISOString(),
      metadata: {}
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await apiService.sendChatMessage(
        inputMessage,
        currentConversation?.conversation_id,
        3,
        true,
        selectedText
      );

      const assistantMessage = {
        id: response.message_id,
        role: 'assistant',
        content: response.answer,
        timestamp: response.timestamp,
        metadata: {
          research_result: response.research_result,
          context_used: response.context_used
        }
      };

      setMessages(prev => [...prev, assistantMessage]);
      
      // Update current conversation if it's a new one
      if (!currentConversation) {
        setCurrentConversation({
          conversation_id: response.conversation_id,
          title: response.conversation_title,
          messages: [userMessage, assistantMessage]
        });
        loadConversations();
      }

    } catch (err) {
      setError(err.message || 'Failed to send message');
    } finally {
      setIsLoading(false);
      // Clear highlight after sending message
      if (selectedText) {
        setAskModelHighlight('');
      }
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage(askModelHighlight);
    }
  };

  const deleteConversation = async (conversationId) => {
    try {
      await apiService.deleteConversation(conversationId);
      if (currentConversation?.conversation_id === conversationId) {
        setCurrentConversation(null);
        setMessages([]);
      }
      loadConversations();
    } catch (err) {
      setError('Failed to delete conversation');
    }
  };

  const handleUploadSuccess = (result) => {
    setUploadSuccess(result);
    setShowFileUpload(false);
    // Clear success message after 5 seconds
    setTimeout(() => setUploadSuccess(null), 5000);
  };

  const handleUploadError = (errorMessage) => {
    setError(errorMessage);
    setShowFileUpload(false);
  };

  const handleHighlight = (highlightText, conversationId) => {
    if (!highlightText) {
      return;
    }

    // Only check conversation ID if we have one
    if (conversationId && currentConversation && currentConversation.conversation_id !== conversationId) {
      return;
    }

    setAskModelHighlight(highlightText);
    setAskModelModalOpen(false);
  };

  const handleAskModelResponse = (assistantMessage) => {
    if (!assistantMessage) {
      return;
    }

    setMessages((prev) => [...prev, assistantMessage]);
    setTimeout(() => scrollToBottom(), 50);
    loadConversations();
    // Clear the highlight once response is received
    setAskModelHighlight('');
    setAskModelModalOpen(false);
  };

  const handleAskModelModalClose = () => {
    setAskModelModalOpen(false);
  };

  const clearHighlight = () => {
    setAskModelHighlight('');
    setAskModelModalOpen(false);
  };

  const handleModelChange = useCallback((newModel) => {
    setCurrentModel(newModel);
    // Show a success notification
    setError(`Model successfully changed to ${newModel}`);
    setTimeout(() => setError(null), 3000);
  }, []); // Empty dependency array since it only uses setState functions

  const handleLogout = async () => {
    try {
      await logout();
    } catch (err) {
      setError('Failed to logout');
    }
  };

  return (
    <div className="chat-interface">
      <HighlightListener onHighlight={handleHighlight} />
      <div className="chat-sidebar">
        <div className="chat-sidebar-header">
          <h3>💬 Conversations</h3>
          <button 
            className="new-conversation-btn"
            onClick={createNewConversation}
            title="New Conversation"
          >
            ➕
          </button>
        </div>
        
        <ConversationList
          conversations={conversations}
          currentConversation={currentConversation}
          onSelectConversation={loadConversation}
          onDeleteConversation={deleteConversation}
        />
      </div>

      <div className="chat-main">
        <div className="chat-main-header">
          <h3>💬 Chat</h3>
          <div className="chat-header-actions">
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
        <div className="chat-messages">
          {messages.length === 0 ? (
            <div className="empty-chat">
              <div className="empty-icon">💬</div>
              <p>Start a conversation with the research agent</p>
              <p>Ask questions and get comprehensive answers based on your documents</p>
              <div className="empty-chat-actions">
                <p>Use the 📁 button below to upload documents and start chatting!</p>
              </div>
            </div>
          ) : (
            messages.map((message) => (
              <ChatMessage
                key={message.id}
                message={message}
                conversationId={currentConversation?.conversation_id}
              />
            ))
          )}
          
          {isLoading && (
            <div className="message assistant">
              <div className="message-content">
                <div className="loading-message">
                  <div className="loading-icon">🔍</div>
                  <div className="loading-text">Generating response...</div>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {uploadSuccess && (
          <div className="upload-success">
            <h4>✅ Upload Successful!</h4>
            <p>{uploadSuccess.message}</p>
            <p>File: {uploadSuccess.filename} ({uploadSuccess.file_type})</p>
            <p>Words: {uploadSuccess.word_count} | Chunks: {uploadSuccess.chunks_added}</p>
          </div>
        )}

        {error && (
          <div className="chat-error">
            <span>⚠️ {error}</span>
            <button onClick={() => setError(null)}>✕</button>
          </div>
        )}

        {showFileUpload && (
          <div className="file-upload-modal">
            <div className="file-upload-overlay" onClick={() => setShowFileUpload(false)}></div>
            <h3>Upload Documents</h3>
            <button 
              className="close-btn"
              onClick={() => setShowFileUpload(false)}
              title="Close"
            >
              ✕
            </button>
            <FileUpload 
              onUploadSuccess={handleUploadSuccess}
              onUploadError={handleUploadError}
              disabled={false}
            />
          </div>
        )}

        {askModelHighlight && (
          <div className="selected-text-box">
            <div className="selected-text-header">
              <span className="selected-text-label">Selected Text</span>
              <button
                type="button"
                className="selected-text-clear"
                onClick={clearHighlight}
                title="Clear selection"
              >
                ✕
              </button>
            </div>
            <div className="selected-text-content">
              {askModelHighlight}
            </div>
          </div>
        )}

        <div className="chat-input">
          <div className="chat-input-main">
            <div className="chat-input-left">
              <div className="chat-input-actions">
                <button
                  className="mode-toggle-btn-input"
                  onClick={onToggleMode}
                  title="Switch to Research Mode"
                  disabled={isLoading}
                >
                  🔍
                </button>
                <button
                  className="upload-small-btn"
                  onClick={() => setShowFileUpload(true)}
                  title="Upload Documents"
                  disabled={isLoading}
                >
                  📁
                </button>
              </div>
              <textarea
                id="chat-message-input"
                name="message"
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder={askModelHighlight ? "Ask a question about the selected text..." : "Ask a question or start a conversation... (Tip: Upload documents with 📁 button)"}
                disabled={isLoading}
                rows="3"
              />
            </div>
            <div className="chat-input-right">
              <ModelSelector
                key="model-selector" // Add key for debugging
                currentModel={currentModel}
                onModelChange={handleModelChange}
                disabled={isLoading}
              />
              <button
                onClick={() => sendMessage(askModelHighlight)}
                disabled={!inputMessage.trim() || isLoading}
                className="send-btn"
              >
                Send
              </button>
            </div>
          </div>
        </div>
        <AskModelModal
          isOpen={askModelModalOpen}
          onClose={handleAskModelModalClose}
          conversationId={currentConversation?.conversation_id}
          initialHighlight={askModelHighlight}
          onResponse={handleAskModelResponse}
        />
        {showUserProfile && (
          <UserProfile onClose={() => setShowUserProfile(false)} />
        )}
      </div>
    </div>
  );
};

export default ChatInterface;
