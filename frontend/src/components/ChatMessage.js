import React, { useState, useEffect } from 'react';
import DOMPurify from 'dompurify';
import './ChatMessage.css';

const ChatMessage = ({ message, conversationId, isStreaming = false, streamingContent = '', onStopStreaming = null, requestId = null }) => {
  const [isSubqueriesExpanded, setIsSubqueriesExpanded] = useState(false);
  const [displayContent, setDisplayContent] = useState('');

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const formatContent = (content) => {
    // Simple markdown-like formatting
    const formatted = content
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/\n/g, '<br>');
    
    // Sanitize HTML to prevent XSS attacks
    // Allow only safe tags and attributes
    return DOMPurify.sanitize(formatted, {
      ALLOWED_TAGS: ['strong', 'em', 'br', 'p', 'span', 'div', 'ul', 'ol', 'li', 'code', 'pre'],
      ALLOWED_ATTR: ['class'],
      KEEP_CONTENT: true
    });
  };

  // Update display content when streaming content changes
  useEffect(() => {
    if (isStreaming && streamingContent) {
      setDisplayContent(streamingContent);
    } else if (message.content) {
      setDisplayContent(message.content);
    } else if (streamingContent) {
      setDisplayContent(streamingContent);
    }
  }, [isStreaming, streamingContent, message.content, message.id, message.role]);

  const isUser = message.role === 'user';
  const hasResearchData = message.metadata?.research_result;
  const contextUsed = message.metadata?.context_used;
  const highlights = message.metadata?.highlights;
  const highlightTruncated = message.metadata?.highlight_truncated;
  const conversationMetaId = message.metadata?.conversation_id;

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
      
      <div
        className="message-content"
        data-message-id={message.id}
        data-conversation-id={conversationMetaId || message.conversation_id || conversationId}
      >
        {/* Content is sanitized via DOMPurify in formatContent() to prevent XSS */}
        <div className="message-text">
          {(() => {
            const contentToShow = displayContent || message.content || streamingContent || '';
            const formattedContent = formatContent(contentToShow);
            
            return isStreaming ? (
              <div className="streaming-content">
                <div 
                  dangerouslySetInnerHTML={{ 
                    __html: formattedContent 
                  }}
                />
                <span className="streaming-cursor">|</span>
                {onStopStreaming && requestId && (
                  <button 
                    onClick={() => onStopStreaming(requestId)}
                    className="stop-streaming-btn"
                    title="Stop streaming"
                  >
                    ⏹️ Stop
                  </button>
                )}
              </div>
            ) : (
              <div>
                <div 
                  dangerouslySetInnerHTML={{ 
                    __html: formattedContent 
                  }}
                />
              </div>
            );
          })()}
        </div>
        
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
                
                {message.metadata.research_result.subqueries && message.metadata.research_result.subqueries.length > 0 && (
                  <div className="subqueries-display">
                    <div className="subqueries-header" onClick={() => setIsSubqueriesExpanded(!isSubqueriesExpanded)}>
                      <h4>Research Subqueries:</h4>
                      <button className="subqueries-toggle">
                        {isSubqueriesExpanded ? '▼' : '▶'}
                      </button>
                    </div>
                    {isSubqueriesExpanded && (
                      <div className="subqueries-list">
                        {message.metadata.research_result.subqueries.map((subquery, index) => (
                          <div key={index} className="subquery-item">
                            <span className="subquery-number">{index + 1}.</span>
                            <span className="subquery-text">
                              {typeof subquery === 'string' ? subquery : subquery.subquery || subquery.summary}
                            </span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {highlights && highlights.length > 0 && (
          <div className="highlight-context">
            <h4>Highlight context</h4>
            <ul>
              {highlights.map((item, index) => (
                <li key={index}>{item}</li>
              ))}
            </ul>
            {highlightTruncated && (
              <div className="highlight-warning">Note: highlight truncated due to length limits.</div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default ChatMessage;
