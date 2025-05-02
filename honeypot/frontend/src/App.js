// honeypot/frontend/src/App.js - Enhanced version with theme support
import React, { useState, useEffect, useCallback } from 'react'; 
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { getCsrfToken } from './components/csrfHelper';
import Login from './static/js/login';
import AdminDashboard from './static/js/admin';
import './index.css';

const ProtectedRoute = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const location = useLocation();

  useEffect(() => {
    const verifySession = async () => {
      setIsLoading(true); 
      try {
        const headers = {};
        const token = getCsrfToken(); 
        if (token) {
          headers['X-CSRF-TOKEN'] = token;
        }

        console.log("Checking auth status with headers:", headers);
        const response = await fetch('/api/honeypot/angela/honey/angela', {
          credentials: 'include',
          headers: headers 
        });

        if (response.ok) { 
          const data = await response.json();
          console.log("Auth status response:", data);
          setIsAuthenticated(data.isAuthenticated); 
        } else if (response.status === 401) { 
          console.log("Not authenticated (401)");
          setIsAuthenticated(false);
        } else {
          console.error('Auth check failed with status:', response.status);
          setIsAuthenticated(false);
        }
      } catch (error) {
        console.error("Network error during authentication check:", error);
        setIsAuthenticated(false);
      } finally {
        setIsLoading(false);
      }
    };

    verifySession();
  }, [location.pathname]); 

  if (isLoading) {
    return (
      <div className="honeypot-loading-screen">
        <div className="honeypot-loading-spinner"></div>
        <p>Verifying authentication...</p>
      </div>
    ); 
  }

  if (!isAuthenticated) {
    return <Navigate to="/honey/login" replace />;
  }

  return children;
};

function App() {
  useEffect(() => {
    const savedTheme = localStorage.getItem('honeypotTheme');
    if (savedTheme) {
      const themeMap = {
        'default': '',
        'cyberpunk': 'theme-cyberpunk',
        'ocean': 'theme-dark-ocean',
        'red': 'theme-blood-red'
      };
      

      document.body.classList.remove(
        'theme-cyberpunk', 
        'theme-dark-ocean', 
        'theme-blood-red'
      );
      

      const themeClass = themeMap[savedTheme];
      if (themeClass) {
        document.body.classList.add(themeClass);
      }
    }
  }, []);

  return (
    <Router>
      <Routes>
        <Route path="/honey/login" element={<Login />} />
        <Route 
          path="/honey/dashboard/*" 
          element={
            <ProtectedRoute>
              <AdminDashboard />
            </ProtectedRoute>
          } 
        />
        <Route path="/" element={<Navigate to="/honey/dashboard" replace />} />
        <Route path="*" element={<Navigate to="/honey/dashboard" replace />} />
      </Routes>
    </Router>
  );
}

export default App;
