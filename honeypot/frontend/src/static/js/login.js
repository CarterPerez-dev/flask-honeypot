// src/components/Login.js
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FaSpider, FaLock, FaUser, FaExclamationTriangle } from 'react-icons/fa';
import { getCsrfToken, setCsrfToken } from './csrfHelper';
import './static/css/login.css';

const Login = () => {
  const [adminKey, setAdminKey] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [csrfToken, setCsrfTokenState] = useState('');
  const navigate = useNavigate();

  // Fetch CSRF token on component mount
  useEffect(() => {
    const fetchCsrfToken = async () => {
      try {
        const response = await fetch('/honeypot/admin/csrf-token', { 
          credentials: 'include'
        });
        
        if (response.ok) {
          const data = await response.json();
          setCsrfToken(data.csrf_token);
          setCsrfTokenState(data.csrf_token);
        }
      } catch (err) {
        console.error('Error fetching CSRF token:', err);
        setError('Failed to load security token. Please refresh the page.');
      }
    };

    fetchCsrfToken();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/honeypot/admin/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRF-TOKEN': csrfToken
        },
        body: JSON.stringify({ adminKey }),
        credentials: 'include'
      });

      const data = await response.json();

      if (response.ok) {
        // Successful login
        navigate('/honey/dashboard');
      } else {
        // Failed login
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
