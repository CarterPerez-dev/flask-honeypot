// src/App.js
import React, { useState, useEffect } from 'react'; 
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { getCsrfToken } from './components/csrfHelper';
import Login from './static/js/login';
import AdminDashboard from './static/js/admin';
import './index.css';

  const ProtectedRoute = ({ children }) => {
   const [isAuthenticated, setIsAuthenticated] = useState(null);
   const [isLoading, setIsLoading] = useState(true);
 
   useEffect(() => {
     const verifySession = async () => {
       setIsLoading(true); 
       try {
         const headers = {};
         const token = getCsrfToken(); 
         if (token) {
              headers['X-CSRF-TOKEN'] = token;
          }

         const response = await fetch('/api/honeypot/angela/honey/angela', {
            credentials: 'include',
            headers: headers 
         });
 
         if (response.ok) { 
           const data = await response.json();
           setIsAuthenticated(data.isAuthenticated); 
         } else if (response.status === 401) { 
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
 
   }, []); 


   if (isLoading) {
     return <div>Checking authentication...</div>; 
   }
 

   if (!isAuthenticated) {
     return <Navigate to="/honey/login" replace />;
   }

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
