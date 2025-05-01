// honeypot/frontend/src/static/js/login.js
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FaSpider, FaLock, FaExclamationTriangle } from 'react-icons/fa'; 
import { setCsrfToken } from '../../components/csrfHelper'; 
import '../css/login.css';

const Login = () => {
  const [adminKey, setAdminKey] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [csrfToken, setCsrfTokenState] = useState('');
  const navigate = useNavigate();

  // Get CSRF token on component mount
  useEffect(() => {
    const fetchCsrfToken = async () => {
      try {
        console.log("Fetching CSRF token...");
        const response = await fetch('/api/honeypot/angela/csrf-token', {
          credentials: 'include',
          headers: {
            'Accept': 'application/json',
            'Cache-Control': 'no-cache'
          }
        });
        
        const text = await response.text();
        console.log("Raw CSRF response:", text.substring(0, 50) + '...');
        
        try {
          const data = JSON.parse(text);
          console.log("CSRF token received:", data.csrf_token.substring(0, 5) + '...');
          setCsrfToken(data.csrf_token); // Store in localStorage
          setCsrfTokenState(data.csrf_token); // Update component state
        } catch (e) {
          console.error("Failed to parse CSRF token response", e);
          setError("Server configuration error. Please contact admin.");
        }
      } catch (err) {
        console.error('CSRF token fetch error:', err);
        setError('Connection error. Please refresh the page.');
      }
    };

    fetchCsrfToken();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
  
    try {
      // Get the current CSRF token
      const token = localStorage.getItem('csrf_token');
      console.log("Using CSRF token:", token ? token.substring(0, 5) + "..." : "none");
      
      // Use direct fetch with debug logging
      const response = await fetch('/api/honeypot/angela/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          'X-CSRF-TOKEN': token
        },
        credentials: 'include',
        body: JSON.stringify({ adminKey, role: 'basic' })
      });
      
      let responseText;
      try {
        responseText = await response.text();
        console.log("Raw login response:", responseText.substring(0, 100));
        const data = JSON.parse(responseText);
        
        if (response.ok) {
          console.log("Login successful!");
          
          // Verify the session was created
          try {
            const verifyResponse = await fetch('/api/honeypot/angela/honey/angela', {
              credentials: 'include',
              headers: {
                'X-CSRF-TOKEN': token,
                'Accept': 'application/json'
              }
            });
            const verifyData = await verifyResponse.json();
            console.log("Session verification:", verifyData);
          } catch (e) {
            console.warn("Session verification failed:", e);
          }
          
          navigate('/honey/dashboard');
        } else {
          console.error("Login failed:", data);
          setError(data.error || 'Invalid login credentials');
        }
      } catch (parseError) {
        console.error("Failed to parse login response", parseError);
        console.log("Response text:", responseText);
        setError("Server returned invalid response. Please try again.");
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
            disabled={loading}
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
