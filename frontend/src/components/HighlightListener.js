import { useCallback, useEffect, useRef } from 'react';

const HighlightListener = ({ onHighlight }) => {
  const buttonRef = useRef(null);
  const selectionRef = useRef(null);

  const hideButton = useCallback(() => {
    if (buttonRef.current) {
      buttonRef.current.style.display = 'none';
    }
  }, []);

  const handleButtonClick = useCallback(() => {
    if (!selectionRef.current) {
      return;
    }

    onHighlight(selectionRef.current.text, selectionRef.current.conversationId);
    hideButton();
    selectionRef.current = null;
    const selection = window.getSelection();
    if (selection) {
      selection.removeAllRanges();
    }
  }, [onHighlight, hideButton]);

  const handleButtonBlur = useCallback((event) => {
    if (event.relatedTarget) {
      return;
    }
    hideButton();
  }, [hideButton]);

  const showButton = useCallback((left, top) => {
    if (!buttonRef.current) {
      const button = document.createElement('button');
      button.innerText = 'Ask Model';
      button.type = 'button';
      button.className = 'highlight-ask-button';
      button.style.position = 'absolute';
      button.style.zIndex = 1000;
      button.style.padding = '0.5rem 0.75rem';
      button.style.background = '#3d5c7a';
      button.style.color = '#fff';
      button.style.borderRadius = '9999px';
      button.style.fontSize = '0.875rem';
      button.style.cursor = 'pointer';
      button.style.boxShadow = '0 10px 30px rgba(61, 92, 122, 0.3)';
      button.style.border = '1px solid rgba(61, 92, 122, 0.2)';
      button.style.transition = 'all 0.2s ease';
      button.style.outline = 'none';
      button.tabIndex = 0;

      button.addEventListener('click', handleButtonClick);
      button.addEventListener('blur', handleButtonBlur, true);
      button.addEventListener('mouseenter', () => {
        button.style.background = '#2d4a5f';
        button.style.transform = 'scale(1.05)';
        button.style.boxShadow = '0 12px 35px rgba(61, 92, 122, 0.4)';
      });
      button.addEventListener('mouseleave', () => {
        button.style.background = '#3d5c7a';
        button.style.transform = 'scale(1)';
        button.style.boxShadow = '0 10px 30px rgba(61, 92, 122, 0.3)';
      });
      document.body.appendChild(button);
      buttonRef.current = button;
    }

    buttonRef.current.style.left = `${left}px`;
    buttonRef.current.style.top = `${top + 12}px`;
    buttonRef.current.style.display = 'inline-flex';
    buttonRef.current.focus({ preventScroll: true });
  }, [handleButtonBlur, handleButtonClick]);

  useEffect(() => {
    const handleMouseUp = (event) => {
      const selection = window.getSelection();
      if (!selection || selection.isCollapsed) {
        hideButton();
        selectionRef.current = null;
        return;
      }

      const selectedText = selection.toString().trim();
      if (!selectedText) {
        hideButton();
        selectionRef.current = null;
        return;
      }

      // Check if selection is within a chat message
      const range = selection.getRangeAt(0);
      const commonAncestor = range.commonAncestorContainer;
      
      // Find the chat message element that contains the selection
      let messageElement = null;
      let node = commonAncestor.nodeType === Node.TEXT_NODE ? commonAncestor.parentElement : commonAncestor;
      
      while (node && node !== document.body) {
        // Check if this is a chat message element
        if (node.classList && node.classList.contains('message')) {
          messageElement = node;
          break;
        }
        node = node.parentElement;
      }

      // If no message element found, hide button
      if (!messageElement) {
        hideButton();
        selectionRef.current = null;
        return;
      }

      // Check if the message has user or assistant role
      const messageRole = messageElement.classList.contains('user') ? 'user' : 
                         messageElement.classList.contains('assistant') ? 'assistant' : null;
      
      if (!messageRole) {
        hideButton();
        selectionRef.current = null;
        return;
      }

      // Check if selection is within input, textarea, or contenteditable elements
      const activeElement = document.activeElement;
      if (activeElement && (
        activeElement.tagName === 'INPUT' ||
        activeElement.tagName === 'TEXTAREA' ||
        activeElement.contentEditable === 'true'
      )) {
        hideButton();
        selectionRef.current = null;
        return;
      }

      // Check if selection spans multiple messages
      const startContainer = range.startContainer;
      const endContainer = range.endContainer;
      
      // Find message elements for start and end containers
      const findMessageElement = (container) => {
        let node = container.nodeType === Node.TEXT_NODE ? container.parentElement : container;
        while (node && node !== document.body) {
          if (node.classList && node.classList.contains('message')) {
            return node;
          }
          node = node.parentElement;
        }
        return null;
      };

      const startMessage = findMessageElement(startContainer);
      const endMessage = findMessageElement(endContainer);

      // If selection spans multiple messages, hide button
      if (startMessage !== endMessage) {
        hideButton();
        selectionRef.current = null;
        return;
      }

      // Get conversation ID from the message element
      let conversationId = null;
      const messageContent = messageElement.querySelector('.message-content');
      if (messageContent && messageContent.dataset?.conversationId) {
        conversationId = messageContent.dataset.conversationId;
      }

      selectionRef.current = {
        text: selectedText,
        conversationId,
      };

      const rect = range.getBoundingClientRect();
      showButton(rect.x + window.scrollX, rect.y + rect.height + window.scrollY);
    };

    const handleKeyUp = (event) => {
      if (event.key === 'Escape') {
        hideButton();
        selectionRef.current = null;
      }
    };

    document.addEventListener('mouseup', handleMouseUp);
    document.addEventListener('keyup', handleKeyUp);

    return () => {
      document.removeEventListener('mouseup', handleMouseUp);
      document.removeEventListener('keyup', handleKeyUp);
    };
  }, [hideButton, showButton]);

  return null;
};

export default HighlightListener;

