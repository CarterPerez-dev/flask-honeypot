// src/components/JsonSyntaxHighlighter.js
import React, { useState, useMemo } from 'react';
import '../static/css/JsonSyntaxHighlighter.css';

const JsonSyntaxHighlighter = ({ json, maxHeight = '400px' }) => {
  const [copyStatus, setCopyStatus] = useState('idle'); // idle, copying, success
  
  // Parse the JSON if it's a string, otherwise use as is
  const parsedJson = useMemo(() => {
    if (typeof json === 'string') {
      try {
        return JSON.parse(json);
      } catch (e) {
        console.error('Failed to parse JSON:', e);
        return null;
      }
    }
    return json;
  }, [json]);

  // Format the JSON with proper indentation
  const formattedJson = useMemo(() => {
    if (!parsedJson) return '';
    try {
      return JSON.stringify(parsedJson, null, 2);
    } catch (e) {
      console.error('Failed to stringify JSON:', e);
      return '';
    }
  }, [parsedJson]);

  // Apply syntax highlighting
  const highlightSyntax = (text) => {
    if (!text) return '';
    
    // Replace patterns with HTML spans for styling
    return text
      // Highlight keys (property names)
      .replace(/"([^"]+)":/g, '<span class="json-key">"$1"</span>:')
      // Highlight string values
      .replace(/: "([^"]+)"/g, ': <span class="json-string">"$1"</span>')
      // Highlight numbers
      .replace(/: ([0-9]+(\.[0-9]+)?)/g, ': <span class="json-number">$1</span>')
      // Highlight booleans
      .replace(/: (true|false)/g, ': <span class="json-boolean">$1</span>')
      // Highlight null values
      .replace(/: null/g, ': <span class="json-null">null</span>')
      // Highlight brackets and braces
      .replace(/([{}\[\]])/g, '<span class="json-bracket">$1</span>')
      // Highlight commas
      .replace(/,/g, '<span class="json-comma">,</span>');
  };

  // Safe copy to clipboard with fallback for HTTP
  const copyToClipboard = (text) => {
    setCopyStatus('copying');
    
    // Try the modern Clipboard API first
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text)
        .then(() => {
          setCopyStatus('success');
          setTimeout(() => setCopyStatus('idle'), 2000);
        })
        .catch(err => {
          console.error('Clipboard API failed:', err);
          fallbackCopyToClipboard(text);
        });
    } else {
      // Fall back to the older execCommand method
      fallbackCopyToClipboard(text);
    }
  };

  // Fallback copy method for browsers without Clipboard API
  const fallbackCopyToClipboard = (text) => {
    try {
      // Create a temporary textarea element
      const textArea = document.createElement('textarea');
      textArea.value = text;
      
      // Make the textarea non-visible but present in the DOM
      textArea.style.position = 'fixed';
      textArea.style.left = '-9999px';
      textArea.style.top = '0';
      textArea.style.opacity = '0';
      
      document.body.appendChild(textArea);
      textArea.focus();
      textArea.select();
      
      // Execute the copy command
      const success = document.execCommand('copy');
      
      // Clean up
      document.body.removeChild(textArea);
      
      if (!success) {
        console.error('execCommand copy failed');
        setCopyStatus('idle');
      } else {
        setCopyStatus('success');
        setTimeout(() => setCopyStatus('idle'), 2000);
      }
    } catch (err) {
      console.error('Fallback clipboard method failed:', err);
      setCopyStatus('idle');
    }
  };

  // Handle errors
  if (!formattedJson) {
    return (
      <div className="json-syntax-error">
        Invalid JSON format
      </div>
    );
  }

  return (
    <div className="json-syntax-highlighter">
      <div className="json-syntax-header">
        <div className="json-syntax-controls">
          <button 
            className={`json-copy-btn ${copyStatus === 'success' ? 'json-copy-success' : ''}`}
            onClick={() => copyToClipboard(formattedJson)}
            disabled={copyStatus === 'copying'}
          >
            {copyStatus === 'success' ? 'Copied!' : 'Copy JSON'}
          </button>
        </div>
      </div>
      <div className="json-syntax-content" style={{ maxHeight }}>
        <pre dangerouslySetInnerHTML={{ __html: highlightSyntax(formattedJson) }} />
      </div>
    </div>
  );
};

export default JsonSyntaxHighlighter;
