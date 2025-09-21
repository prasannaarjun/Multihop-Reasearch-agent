import React from 'react';
import './ChatMessage.css';

const ChatMessage = ({ message }) => {
  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const formatContent = (content) => {
    // Simple markdown-like formatting
    return content
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/\n/g, '<br>');
  };

  const isUser = message.role === 'user';
  const hasResearchData = message.metadata?.research_result;
  const contextUsed = message.metadata?.context_used;

  return (
    <div className={`message ${message.role}`}>
      <div className="message-header">
        <div className="message-role">
          {isUser ? '👤 You' : '🤖 Research Agent'}
        </div>
        <div className="message-time">
          {formatTimestamp(message.timestamp)}
        </div>
      </div>
      
      <div className="message-content">
        <div 
          className="message-text"
          dangerouslySetInnerHTML={{ 
            __html: formatContent(message.content) 
          }}
        />
        
        {hasResearchData && (
          <div className="message-metadata">
            <div className="research-info">
              <span className="research-badge">
                📚 Research-based answer
              </span>
              {contextUsed && (
                <span className="context-badge">
                  🧠 Used conversation context
                </span>
              )}
            </div>
            
            {message.metadata.research_result && (
              <div className="research-details">
                <div className="research-stats">
                  <span>
                    📄 {message.metadata.research_result.total_documents || 0} documents
                  </span>
                  <span>
                    🔍 {message.metadata.research_result.subqueries?.length || 0} subqueries
                  </span>
                  <span>
                    📝 {message.metadata.research_result.citations?.length || 0} citations
                  </span>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default ChatMessage;
