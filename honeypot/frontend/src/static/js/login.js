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


  useEffect(() => {
    const fetchCsrfToken = async () => {
      try {
        const response = await fetch('/api/honeypot/admin/csrf-token', {
          credentials: 'include'
        });

        if (response.ok) {
          const data = await response.json();
          setCsrfToken(data.csrf_token);
          setCsrfTokenState(data.csrf_token); 
        } else {
           console.error('Error fetching CSRF token:', response.statusText);
           setError('Failed to load security token. Please refresh the page.');
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
      const response = await adminFetch('/api/honeypot/admin/login', {
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
