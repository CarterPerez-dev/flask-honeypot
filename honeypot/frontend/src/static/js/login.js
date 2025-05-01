// src/components/Login.js
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FaSpider, FaLock, FaExclamationTriangle } from 'react-icons/fa'; 
import { setCsrfToken, adminFetch } from '../../components/csrfHelper'; 
import '../css/login.css';

const Login = () => {
  const [adminKey, setAdminKey] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [csrfToken, setCsrfTokenState] = useState(''); 
  const navigate = useNavigate();


  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
  
    try {
      // First, get a fresh CSRF token
      const tokenResponse = await fetch('/api/honeypot/angela/csrf-token', {
        credentials: 'include'
      });
      
      if (tokenResponse.ok) {
        const tokenData = await tokenResponse.json();
        setCsrfToken(tokenData.csrf_token);
      } else {
        throw new Error('Failed to get CSRF token');
      }
      
      // Now try login with the fresh token
      const response = await adminFetch('/api/honeypot/angela/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ adminKey }),
      });
  
      const data = await response.json();
  
      if (response.ok) {
        navigate('/honey/dashboard');
      } else {
        setError(data.error || 'Invalid login credentials');
      }
    } catch (err) {
      console.error('Login error:', err);
      setError('Connection error. Please try again.');
    } finally {
      setLoading(false);
    }
  };


  return (
    <div className="honeypot-login-container">
      <div className="honeypot-login-box">
        <div className="honeypot-login-header">
          <FaSpider className="honeypot-login-logo" />
          <h1>Honeypot Admin</h1>
        </div>

        {error && (
          <div className="honeypot-login-error">
            <FaExclamationTriangle /> {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="honeypot-login-form">
          <div className="honeypot-login-field">
            <label htmlFor="adminKey">
              <FaLock /> Admin Key
            </label>
            <input
              type="password"
              id="adminKey"
              value={adminKey}
              onChange={(e) => setAdminKey(e.target.value)}
              placeholder="Enter admin key"
              required
              disabled={loading} 
            />
          </div>

          <button
            type="submit"
            className="honeypot-login-button"
            disabled={loading || !csrfToken}
          >
            {loading ? 'Authenticating...' : 'Login'}
          </button>
        </form>

        <div className="honeypot-login-footer">
          <p>Secure Honeypot Administration</p>
        </div>
      </div>
    </div>
  );
};

export default Login;
