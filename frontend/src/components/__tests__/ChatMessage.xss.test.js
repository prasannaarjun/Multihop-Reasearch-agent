/**
 * XSS Protection Tests for ChatMessage Component
 * 
 * These tests verify that malicious content is properly sanitized
 * and cannot execute JavaScript in the browser.
 */

import React from 'react';
import { render } from '@testing-library/react';
import ChatMessage from '../ChatMessage';

describe('ChatMessage XSS Protection', () => {
  const mockTimestamp = new Date('2024-01-01T12:00:00Z').toISOString();

  test('should remove script tags completely', () => {
    const message = {
      id: 'test-1',
      role: 'user',
      content: '<script>alert("XSS Attack!")</script>Hello World',
      timestamp: mockTimestamp,
    };

    const { container } = render(<ChatMessage message={message} />);
    
    // Script tags should be completely removed
    const scriptTags = container.querySelectorAll('script');
    expect(scriptTags.length).toBe(0);
    
    // Content should still be visible (but without the script)
    expect(container.textContent).toContain('Hello World');
    expect(container.textContent).not.toContain('<script>');
  });

  test('should remove inline event handlers', () => {
    const message = {
      id: 'test-2',
      role: 'user',
      content: '<img src="x" onerror="alert(\'XSS\')"><div onclick="alert(\'XSS\')">Click me</div>',
      timestamp: mockTimestamp,
    };

    const { container } = render(<ChatMessage message={message} />);
    
    // Check no elements have dangerous event handlers
    const allElements = container.querySelectorAll('*');
    allElements.forEach(element => {
      expect(element.getAttribute('onerror')).toBeNull();
      expect(element.getAttribute('onclick')).toBeNull();
      expect(element.getAttribute('onload')).toBeNull();
      expect(element.getAttribute('onmouseover')).toBeNull();
    });
  });

  test('should remove javascript: protocol URLs', () => {
    const message = {
      id: 'test-3',
      role: 'user',
      content: '<a href="javascript:alert(\'XSS\')">Click me</a>',
      timestamp: mockTimestamp,
    };

    const { container } = render(<ChatMessage message={message} />);
    
    // Link should be removed or javascript: URL should be stripped
    const links = container.querySelectorAll('a[href*="javascript:"]');
    expect(links.length).toBe(0);
  });

  test('should remove iframe tags', () => {
    const message = {
      id: 'test-4',
      role: 'user',
      content: '<iframe src="https://evil.com"></iframe>Normal content',
      timestamp: mockTimestamp,
    };

    const { container } = render(<ChatMessage message={message} />);
    
    // Iframes should be completely removed
    const iframes = container.querySelectorAll('iframe');
    expect(iframes.length).toBe(0);
    expect(container.textContent).toContain('Normal content');
  });

  test('should remove object and embed tags', () => {
    const message = {
      id: 'test-5',
      role: 'user',
      content: '<object data="data:text/html,<script>alert(1)</script>"></object><embed src="evil.swf">',
      timestamp: mockTimestamp,
    };

    const { container } = render(<ChatMessage message={message} />);
    
    // Object and embed tags should be removed
    expect(container.querySelectorAll('object').length).toBe(0);
    expect(container.querySelectorAll('embed').length).toBe(0);
  });

  test('should preserve safe markdown formatting', () => {
    const message = {
      id: 'test-6',
      role: 'assistant',
      content: '**Bold text** and *italic text* with line\nbreak',
      timestamp: mockTimestamp,
    };

    const { container } = render(<ChatMessage message={message} />);
    
    // Safe HTML formatting should be preserved
    expect(container.querySelector('strong')).toBeTruthy();
    expect(container.querySelector('em')).toBeTruthy();
    expect(container.querySelector('br')).toBeTruthy();
    
    // Text content should be intact
    expect(container.textContent).toContain('Bold text');
    expect(container.textContent).toContain('italic text');
  });

  test('should handle mixed safe and malicious content', () => {
    const message = {
      id: 'test-7',
      role: 'user',
      content: '**Safe bold** <script>alert("XSS")</script> *safe italic* <img src=x onerror="alert(1)">',
      timestamp: mockTimestamp,
    };

    const { container } = render(<ChatMessage message={message} />);
    
    // Malicious parts should be removed
    expect(container.querySelectorAll('script').length).toBe(0);
    const images = container.querySelectorAll('img');
    images.forEach(img => {
      expect(img.getAttribute('onerror')).toBeNull();
    });
    
    // Safe formatting should be preserved
    expect(container.querySelector('strong')).toBeTruthy();
    expect(container.querySelector('em')).toBeTruthy();
    expect(container.textContent).toContain('Safe bold');
    expect(container.textContent).toContain('safe italic');
  });

  test('should handle data URIs that could contain scripts', () => {
    const message = {
      id: 'test-8',
      role: 'user',
      content: '<img src="data:text/html,<script>alert(1)</script>">',
      timestamp: mockTimestamp,
    };

    const { container } = render(<ChatMessage message={message} />);
    
    // Data URIs with scripts should be blocked or sanitized
    const images = container.querySelectorAll('img');
    images.forEach(img => {
      const src = img.getAttribute('src');
      if (src) {
        expect(src).not.toContain('<script>');
        expect(src).not.toContain('alert');
      }
    });
  });

  test('should handle style attribute attacks', () => {
    const message = {
      id: 'test-9',
      role: 'user',
      content: '<div style="position:fixed;top:0;left:0;width:100%;height:100%;background:red">Overlay attack</div>',
      timestamp: mockTimestamp,
    };

    const { container } = render(<ChatMessage message={message} />);
    
    // Style attributes should be removed (only 'class' is allowed)
    const divs = container.querySelectorAll('div.message-text div');
    divs.forEach(div => {
      expect(div.getAttribute('style')).toBeNull();
    });
  });

  test('should handle SVG-based XSS attempts', () => {
    const message = {
      id: 'test-10',
      role: 'user',
      content: '<svg onload="alert(\'XSS\')"><script>alert(1)</script></svg>',
      timestamp: mockTimestamp,
    };

    const { container } = render(<ChatMessage message={message} />);
    
    // SVG with scripts should be removed or sanitized
    const svgs = container.querySelectorAll('svg');
    svgs.forEach(svg => {
      expect(svg.getAttribute('onload')).toBeNull();
    });
    expect(container.querySelectorAll('script').length).toBe(0);
  });

  test('should not break on empty or null content', () => {
    const emptyMessage = {
      id: 'test-11',
      role: 'user',
      content: '',
      timestamp: mockTimestamp,
    };

    expect(() => {
      render(<ChatMessage message={emptyMessage} />);
    }).not.toThrow();
  });

  test('should handle very long malicious payloads', () => {
    const longPayload = '<script>alert("XSS")</script>'.repeat(1000);
    const message = {
      id: 'test-12',
      role: 'user',
      content: longPayload,
      timestamp: mockTimestamp,
    };

    const { container } = render(<ChatMessage message={message} />);
    
    // All script tags should be removed, regardless of length
    expect(container.querySelectorAll('script').length).toBe(0);
  });
});

