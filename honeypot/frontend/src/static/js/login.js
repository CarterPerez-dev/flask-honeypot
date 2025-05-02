// src/static/js/login.js
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FaSpider, FaLock, FaExclamationTriangle, FaEye, FaEyeSlash, FaUserSecret, FaSignInAlt } from 'react-icons/fa'; 
import { setCsrfToken } from '../../components/csrfHelper'; 
import '../css/login.css';

const Login = () => {
  const [adminKey, setAdminKey] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [csrfToken, setCsrfTokenState] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const navigate = useNavigate();

  // Particle effect
  useEffect(() => {
    const particlesContainer = document.querySelector('.honeypot-login-particles');
    if (particlesContainer) {
      for (let i = 0; i < 30; i++) {
        const particle = document.createElement('div');
        particle.classList.add('honeypot-login-particle');
        

        particle.style.left = `${Math.random() * 100}%`;
        particle.style.top = `${Math.random() * 100}%`;
        particle.style.width = `${2 + Math.random() * 4}px`;
        particle.style.height = particle.style.width;
        particle.style.animationDelay = `${Math.random() * 5}s`;
        particle.style.animationDuration = `${8 + Math.random() * 10}s`;
        
        particlesContainer.appendChild(particle);
      }
    }
  }, []);

  // Get CSRF token on component mount
  useEffect(() => {
    const fetchCsrfToken = async () => {
      try {
        console.log("Fetching CSRF token...");
        setLoading(true);
        const response = await fetch('/api/honeypot/angela/csrf-token', {
          credentials: 'include',
          headers: {
            'Accept': 'application/json',
            'Cache-Control': 'no-cache'
          }
        });
        
        const text = await response.text();
        
        try {
          const data = JSON.parse(text);
          console.log("CSRF token received");
          setCsrfToken(data.csrf_token); 
          setCsrfTokenState(data.csrf_token); 
          setLoading(false);
        } catch (e) {
          console.error("Failed to parse CSRF token response", e);
          setError("Server configuration error. Please contact admin.");
          setLoading(false);
        }
      } catch (err) {
        console.error('CSRF token fetch error:', err);
        setError('Connection error. Please refresh the page.');
        setLoading(false);
      }
    };

    fetchCsrfToken();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
  
    try {
      const token = localStorage.getItem('csrf_token');
      

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
        const data = JSON.parse(responseText);
        
        if (response.ok) {
          console.log("Login successful!");
          

          const loginCard = document.querySelector('.honeypot-login-card');
          if (loginCard) {
            loginCard.classList.add('login-success-animation');
          }
          
          setTimeout(() => {
            navigate('/honey/dashboard');
          }, 800);
        } else {
          console.error("Login failed:", data);
          setError(data.error || 'Invalid login credentials');
          

          const loginCard = document.querySelector('.honeypot-login-card');
          if (loginCard) {
            loginCard.classList.add('login-error-animation');
            setTimeout(() => {
              loginCard.classList.remove('login-error-animation');
            }, 500);
          }
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

  const togglePasswordVisibility = () => {
    setShowPassword(!showPassword);
  };

  return (
    <div className="honeypot-login-container">
      {/* Animated background */}
      <div className="honeypot-login-background">
        <div className="honeypot-login-grid"></div>
        <div className="honeypot-login-particles"></div>
        <div className="honeypot-login-glow"></div>
      </div>
      
      <div className="honeypot-login-content">
        <div className="honeypot-login-card">
          <div className="honeypot-login-header">
            <div className="honeypot-login-logo-container">
              <FaSpider className="honeypot-login-logo" />
            </div>
            <h1 className="honeypot-login-title">Honeypot Console</h1>
            <p className="honeypot-login-subtitle">Access Gateway</p>
          </div>

          {error && (
            <div className="honeypot-login-error">
              <FaExclamationTriangle /> {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="honeypot-login-form">
            <div className="honeypot-login-field">
              <label htmlFor="adminKey">
                <FaUserSecret /> Admin Key
              </label>
              <div className="honeypot-login-input-wrapper">
                <input
                  type={showPassword ? "text" : "password"}
                  id="adminKey"
                  value={adminKey}
                  onChange={(e) => setAdminKey(e.target.value)}
                  placeholder="Authorize Admin"
                  required
                  disabled={loading} 
                  className="honeypot-login-input"
                />
                <button 
                  type="button" 
                  className="honeypot-login-toggle-password"
                  onClick={togglePasswordVisibility}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? <FaEyeSlash /> : <FaEye />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              className="honeypot-login-button"
              disabled={loading}
            >
              {loading ? (
                <span className="honeypot-login-button-loading">
                  <span className="honeypot-login-spinner"></span>
                  Authenticating...
                </span>
              ) : (
                <span className="honeypot-login-button-text">
                  <FaSignInAlt /> Initiate Console
                </span>
              )}
            </button>
          </form>

          <div className="honeypot-login-footer">
            <p>Advanced Honeypot Surveillance Grid</p>
            <div className="honeypot-login-security-badge">
              <FaLock /> Secure Tunnel
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
