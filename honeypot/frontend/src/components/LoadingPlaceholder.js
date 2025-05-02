// src/components/common/LoadingPlaceholder.js
import React from 'react';
import { FaSpinner } from 'react-icons/fa';

// Simple placeholder component
const LoadingPlaceholder = ({ height = '100px', message = "Loading...", className = '' }) => {
    const combinedClassName = `honeypot-loading-placeholder ${className}`.trim();

    return (
        <div className={combinedClassName} style={{ minHeight: height }}>
            <FaSpinner className="honeypot-spinner" />
            {message && <span>{message}</span>}
        </div>
    );
};

export default LoadingPlaceholder;
