// src/App.js
import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Login from './static/js/login';
import AdminDashboard from './static/js/admin';
import './index.css';

// Protected route component
const ProtectedRoute = ({ children }) => {
  // Check if the user is authenticated
  const isAuthenticated = document.cookie.includes('honeypot_admin_session=');
  
  // If not authenticated, redirect to login
  if (!isAuthenticated) {
    return <Navigate to="/honey/login" replace />;
  }
  
  // Otherwise, render the children
  return children;
};

function App() {
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
