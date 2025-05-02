// src/components/LoadingPlaceholder.js
import React from 'react';
import { FaSpinner, FaCircleNotch, FaAtom } from 'react-icons/fa';
import '../static/css/LoadingPlaceholder.css';

const LoadingPlaceholder = ({ 
  height = '100px', 
  message = "Loading...", 
  className = '',
  type = 'default',
  showSpinner = true
}) => {
    const combinedClassName = `honeypot-loading-placeholder ${className} ${type}-loader`.trim();
    

    const renderSpinner = () => {
        if (!showSpinner) return null;
        
        switch(type) {
            case 'pulse':
                return <div className="honeypot-pulse-spinner"></div>;
            case 'wave':
                return (
                    <div className="honeypot-wave-spinner">
                        {[...Array(5)].map((_, i) => (
                            <div key={i} className="honeypot-wave-bar"></div>
                        ))}
                    </div>
                );
            case 'dot-pulse':
                return (
                    <div className="honeypot-dot-pulse-spinner">
                        {[...Array(3)].map((_, i) => (
                            <div key={i} className="honeypot-dot"></div>
                        ))}
                    </div>
                );
            case 'atom':
                return <FaAtom className="honeypot-atom-spinner" />;
            case 'circle':
                return <FaCircleNotch className="honeypot-spinner" />;
            default:
                return <FaSpinner className="honeypot-spinner" />;
        }
    };

    return (
        <div className={combinedClassName} style={{ minHeight: height }}>
            {renderSpinner()}
            {message && <span className="honeypot-loading-message">{message}</span>}
        </div>
    );
};

export default LoadingPlaceholder;
