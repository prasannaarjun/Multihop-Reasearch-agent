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
      button.style.background = '#1f2937';
      button.style.color = '#fff';
      button.style.borderRadius = '9999px';
      button.style.fontSize = '0.875rem';
      button.style.cursor = 'pointer';
      button.style.boxShadow = '0 10px 30px rgba(15, 23, 42, 0.12)';
      button.style.border = '1px solid rgba(255, 255, 255, 0.05)';
      button.style.outline = 'none';
      button.tabIndex = 0;

      button.addEventListener('click', handleButtonClick);
      button.addEventListener('blur', handleButtonBlur, true);
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

      let node = event.target;
      let conversationId = null;
      while (node) {
        if (node.dataset?.conversationId) {
          conversationId = node.dataset.conversationId;
          break;
        }
        node = node.parentElement;
      }

      selectionRef.current = {
        text: selectedText,
        conversationId,
      };

      const range = selection.getRangeAt(0);
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

