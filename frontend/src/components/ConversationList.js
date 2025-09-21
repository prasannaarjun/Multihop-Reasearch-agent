import React, { useState } from 'react';
import './ConversationList.css';
import { apiService } from '../services/apiService';

const ConversationList = ({ 
  conversations, 
  currentConversation, 
  onSelectConversation, 
  onDeleteConversation 
}) => {
  const [editingId, setEditingId] = useState(null);
  const [editTitle, setEditTitle] = useState('');

  const handleEditStart = (conversation) => {
    setEditingId(conversation.id);
    setEditTitle(conversation.title);
  };

  const handleEditSave = async (conversationId) => {
    if (editTitle.trim()) {
      try {
        await apiService.updateConversationTitle(conversationId, editTitle.trim());
        setEditingId(null);
        setEditTitle('');
      } catch (error) {
        console.error('Failed to update title:', error);
      }
    }
  };

  const handleEditCancel = () => {
    setEditingId(null);
    setEditTitle('');
  };

  const handleKeyPress = (e, conversationId) => {
    if (e.key === 'Enter') {
      handleEditSave(conversationId);
    } else if (e.key === 'Escape') {
      handleEditCancel();
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInHours = (now - date) / (1000 * 60 * 60);
    
    if (diffInHours < 24) {
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } else if (diffInHours < 168) { // 7 days
      return date.toLocaleDateString([], { weekday: 'short' });
    } else {
      return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
    }
  };

  if (conversations.length === 0) {
    return (
      <div className="conversation-list">
        <div className="empty-conversations">
          <div className="empty-icon">💬</div>
          <p>No conversations yet</p>
          <p>Start a new conversation to begin</p>
        </div>
      </div>
    );
  }

  return (
    <div className="conversation-list">
      {conversations.map((conversation) => (
        <div
          key={conversation.id}
          className={`conversation-item ${
            currentConversation?.conversation_id === conversation.id ? 'active' : ''
          }`}
          onClick={() => onSelectConversation(conversation.id)}
        >
          <div className="conversation-content">
            {editingId === conversation.id ? (
              <input
                type="text"
                value={editTitle}
                onChange={(e) => setEditTitle(e.target.value)}
                onKeyPress={(e) => handleKeyPress(e, conversation.id)}
                onBlur={() => handleEditSave(conversation.id)}
                className="conversation-title-input"
                autoFocus
              />
            ) : (
              <div className="conversation-title">
                {conversation.title}
              </div>
            )}
            
            <div className="conversation-meta">
              <span className="message-count">
                {conversation.message_count} messages
              </span>
              <span className="conversation-date">
                {formatDate(conversation.updated_at)}
              </span>
            </div>
          </div>
          
          <div className="conversation-actions">
            <button
              className="edit-btn"
              onClick={(e) => {
                e.stopPropagation();
                handleEditStart(conversation);
              }}
              title="Edit title"
            >
              ✏️
            </button>
            <button
              className="delete-btn"
              onClick={(e) => {
                e.stopPropagation();
                if (window.confirm('Delete this conversation?')) {
                  onDeleteConversation(conversation.id);
                }
              }}
              title="Delete conversation"
            >
              🗑️
            </button>
          </div>
        </div>
      ))}
    </div>
  );
};

export default ConversationList;
