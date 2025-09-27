import React, { useEffect, useRef, useState } from 'react';
import './AskModelModal.css';
import { apiService } from '../services/apiService';

const AskModelModal = ({
  isOpen,
  onClose,
  conversationId,
  initialHighlight,
  onResponse,
}) => {
  const [highlight, setHighlight] = useState(initialHighlight || '');
  const [question, setQuestion] = useState('');
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const modalRef = useRef(null);
  const firstFieldRef = useRef(null);
  const lastFocusableRef = useRef(null);

  useEffect(() => {
    if (isOpen) {
      setHighlight(initialHighlight || '');
      setQuestion('');
      setError(null);
      setIsLoading(false);
    }
  }, [isOpen, initialHighlight]);

  useEffect(() => {
    if (!isOpen) {
      return;
    }

    const focusable = modalRef.current?.querySelectorAll(
      'button, [href], input, textarea, select, [tabindex]:not([tabindex="-1"])'
    );
    if (focusable && focusable.length > 0) {
      firstFieldRef.current = focusable[0];
      lastFocusableRef.current = focusable[focusable.length - 1];
      firstFieldRef.current.focus();
    }

    const handleKeyDown = (event) => {
      if (event.key === 'Escape') {
        event.preventDefault();
        onClose();
      }

      if (event.key === 'Tab' && focusable?.length > 0) {
        if (event.shiftKey && document.activeElement === firstFieldRef.current) {
          event.preventDefault();
          lastFocusableRef.current.focus();
        } else if (!event.shiftKey && document.activeElement === lastFocusableRef.current) {
          event.preventDefault();
          firstFieldRef.current.focus();
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen, onClose]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!highlight.trim() || !question.trim()) {
      setError('Both highlight and follow-up question are required.');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await apiService.sendChatMessage(
        question.trim(),
        conversationId,
        3,
        true,
        highlight.trim()
      );
      
      // Convert response to expected format
      const assistantMessage = {
        id: response.message_id,
        role: 'assistant',
        content: response.answer,
        timestamp: response.timestamp,
        metadata: {
          research_result: response.research_result,
          context_used: response.context_used,
          source: 'ask_model',
          highlights: [highlight.trim()]
        }
      };
      
      onResponse(assistantMessage, { highlight: highlight.trim(), question: question.trim() });
      onClose();
    } catch (err) {
      setError(err.message || 'Failed to ask the model.');
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) {
    return null;
  }

  return (
    <div className="ask-model-modal" role="dialog" aria-modal="true">
      <div className="ask-model-overlay" onClick={onClose} />
      <div className="ask-model-content" ref={modalRef}>
        <div className="ask-model-header">
          <h3>Ask Model About Highlight</h3>
          <button type="button" className="ask-model-close" onClick={onClose}>
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit}
          onClick={(event) => {
            event.stopPropagation();
          }}
        >
          <label htmlFor="highlight-context">Highlighted Context</label>
          <textarea
            id="highlight-context"
            value={highlight}
            readOnly
            className="ask-model-highlight"
            ref={firstFieldRef}
          />

          <label htmlFor="follow-up-question">Follow-up Question</label>
          <textarea
            id="follow-up-question"
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            placeholder="What would you like to ask about this highlight?"
            className="ask-model-question"
          />

          {error && <div className="ask-model-error">⚠️ {error}</div>}

          <div className="ask-model-actions">
            <button type="button" className="ask-model-secondary" onClick={onClose}>
              Cancel
            </button>
            <button
              type="submit"
              className="ask-model-primary"
              disabled={isLoading}
              ref={lastFocusableRef}
            >
              {isLoading ? 'Sending…' : 'Send'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AskModelModal;

