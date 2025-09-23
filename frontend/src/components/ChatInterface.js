import React, { useState, useEffect, useRef } from 'react';
import './ChatInterface.css';
import ChatMessage from './ChatMessage';
import ConversationList from './ConversationList';
import FileUpload from './FileUpload';
import SubqueryDisplay from './SubqueryDisplay';
import { apiService } from '../services/apiService';

const ChatInterface = ({ onToggleMode, isResearchMode }) => {
  const [conversations, setConversations] = useState([]);
  const [currentConversation, setCurrentConversation] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showFileUpload, setShowFileUpload] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(null);
  const [loadingSubqueries, setLoadingSubqueries] = useState([]);
  const [visibleSubqueries, setVisibleSubqueries] = useState(0);
  const messagesEndRef = useRef(null);
  const subqueryTimeouts = useRef([]);

  useEffect(() => {
    loadConversations();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Cleanup timeouts on unmount
  useEffect(() => {
    return () => {
      subqueryTimeouts.current.forEach(timeout => clearTimeout(timeout));
    };
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const generateMockSubqueries = (question) => {
    // Simple mock subquery generation based on common patterns
    const questionLower = question.toLowerCase().trim();
    const mockSubqueries = [];
    
    // Extract the main topic by removing question words
    const cleanQuestion = question.replace(/^(what|how|why|when|where|define|explain|describe|tell me about)\s+/i, '').replace(/\?$/, '').trim();
    
    // Generate contextual subqueries based on question type
    if (questionLower.startsWith('what')) {
      mockSubqueries.push(`What is ${cleanQuestion}?`);
      mockSubqueries.push(`How does ${cleanQuestion} work?`);
      mockSubqueries.push(`What are the key features of ${cleanQuestion}?`);
    } else if (questionLower.startsWith('how')) {
      mockSubqueries.push(`How does ${cleanQuestion} work?`);
      mockSubqueries.push(`What are the steps involved in ${cleanQuestion}?`);
      mockSubqueries.push(`What are the requirements for ${cleanQuestion}?`);
    } else if (questionLower.startsWith('why')) {
      mockSubqueries.push(`Why is ${cleanQuestion} important?`);
      mockSubqueries.push(`What are the benefits of ${cleanQuestion}?`);
      mockSubqueries.push(`What problems does ${cleanQuestion} solve?`);
    } else if (questionLower.startsWith('when')) {
      mockSubqueries.push(`When should ${cleanQuestion} be used?`);
      mockSubqueries.push(`What is the history of ${cleanQuestion}?`);
      mockSubqueries.push(`What are the current trends in ${cleanQuestion}?`);
    } else if (questionLower.startsWith('where')) {
      mockSubqueries.push(`Where is ${cleanQuestion} used?`);
      mockSubqueries.push(`What are the applications of ${cleanQuestion}?`);
      mockSubqueries.push(`What industries use ${cleanQuestion}?`);
    } else {
      // Generic subqueries for any other question type
      mockSubqueries.push(`What is ${cleanQuestion}?`);
      mockSubqueries.push(`How does ${cleanQuestion} work?`);
      mockSubqueries.push(`What are the benefits of ${cleanQuestion}?`);
      mockSubqueries.push(`What are examples of ${cleanQuestion}?`);
    }
    
    // Add additional contextual subqueries if we have space
    if (mockSubqueries.length < 4) {
      if (!questionLower.includes('benefit') && !questionLower.includes('advantage')) {
        mockSubqueries.push(`What are the benefits of ${cleanQuestion}?`);
      }
      if (!questionLower.includes('example') && !questionLower.includes('case')) {
        mockSubqueries.push(`What are examples of ${cleanQuestion}?`);
      }
    }
    
    return mockSubqueries.slice(0, 4); // Limit to 4 subqueries
  };

  const simulateProgressiveSubqueries = (subqueries) => {
    // Clear any existing timeouts
    subqueryTimeouts.current.forEach(timeout => clearTimeout(timeout));
    subqueryTimeouts.current = [];
    
    setVisibleSubqueries(0);
    let currentIndex = 0;
    
    const processNext = () => {
      if (currentIndex < subqueries.length) {
        setVisibleSubqueries(currentIndex + 1);
        currentIndex++;
        
        // Random delay between 1-3 seconds for each subquery
        const delay = Math.random() * 2000 + 1000;
        const timeout = setTimeout(processNext, delay);
        subqueryTimeouts.current.push(timeout);
      }
    };
    
    // Start processing after a short delay
    const initialTimeout = setTimeout(processNext, 800);
    subqueryTimeouts.current.push(initialTimeout);
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

  const sendMessage = async () => {
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
    
    // Generate and show mock subqueries during loading
    const mockSubqueries = generateMockSubqueries(inputMessage);
    setLoadingSubqueries(mockSubqueries);
    simulateProgressiveSubqueries(mockSubqueries);

    try {
      const response = await apiService.sendChatMessage(
        inputMessage,
        currentConversation?.conversation_id,
        3,
        true
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
      // Clear all subquery timeouts
      subqueryTimeouts.current.forEach(timeout => clearTimeout(timeout));
      subqueryTimeouts.current = [];
      
      setIsLoading(false);
      setLoadingSubqueries([]);
      setVisibleSubqueries(0);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
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

  return (
    <div className="chat-interface">
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
          <div className="chat-title">
            {currentConversation ? currentConversation.title : 'Select a conversation'}
          </div>
          <div className="chat-actions">
            <button 
              className="upload-btn"
              onClick={() => setShowFileUpload(true)}
              title="Upload Documents"
            >
              📁 Upload
            </button>
            <button 
              className="mode-toggle-btn"
              onClick={onToggleMode}
              title="Switch to Research Mode"
            >
              🔍 Research
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
                <button
                  className="upload-empty-btn"
                  onClick={() => setShowFileUpload(true)}
                  title="Upload Documents"
                >
                  📁 Upload Documents
                </button>
              </div>
            </div>
          ) : (
            messages.map((message) => (
              <ChatMessage key={message.id} message={message} />
            ))
          )}
          
          {isLoading && (
            <div className="message assistant">
              <div className="message-content">
                <SubqueryDisplay 
                  subqueries={loadingSubqueries} 
                  visibleCount={visibleSubqueries}
                  isProcessing={true} 
                />
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
            <div className="file-upload-content">
              <div className="file-upload-header">
                <h3>Upload Documents</h3>
                <button 
                  className="close-btn"
                  onClick={() => setShowFileUpload(false)}
                  title="Close"
                >
                  ✕
                </button>
              </div>
              <FileUpload 
                onUploadSuccess={handleUploadSuccess}
                onUploadError={handleUploadError}
                disabled={false}
              />
            </div>
          </div>
        )}

        <div className="chat-input">
          <div className="chat-input-actions">
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
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask a question or start a conversation... (Tip: Upload documents with 📁 button)"
            disabled={isLoading}
            rows="3"
          />
          <button
            onClick={sendMessage}
            disabled={!inputMessage.trim() || isLoading}
            className="send-btn"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;
