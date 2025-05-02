# "
# // src/App.js - Example of integrating the honeypot admin dashboard with an existing React app
#
# # import React, { useState, useEffect } from 'react';
# # import { BrowserRouter as Router, Routes, Route, Navigate, Link } from 'react-router-dom';
# # import { getCsrfToken } from './utils/csrfHelper';
#
# # // Import your existing app components
# # import HomePage from './components/HomePage';
# # import ProductsPage from './components/ProductsPage';
# import AboutPage from './components/AboutPage';
# import UserProfile from './components/UserProfile';
# import MainNavbar from './components/MainNavbar';
#
# // Import the honeypot components (after installing the package)
# import HoneypotLogin from './honeypot/Login';
# import HoneypotDashboard from './honeypot/Dashboard';
#
# // Authentication check for protected routes
# const ProtectedRoute = ({ children }) => {
#   const [isAuthenticated, setIsAuthenticated] = useState(null);
#   const [isLoading, setIsLoading] = useState(true);
#
#   useEffect(() => {
#     const verifySession = async () => {
#       setIsLoading(true);
#       try {
#         const headers = {};
#         const token = getCsrfToken();
#         if (token) {
#           headers['X-CSRF-TOKEN'] = token;
#         }
#
#         // This endpoint comes from the honeypot framework
#         const response = await fetch('/api/honeypot/angela/honey/angela', {
#           credentials: 'include',
#           headers: headers
#         });
#
#         if (response.ok) {
#           const data = await response.json();
#           setIsAuthenticated(data.isAuthenticated);
#         } else if (response.status === 401) {
#           setIsAuthenticated(false);
#         } else {
#           console.error('Auth check failed with status:', response.status);
#           setIsAuthenticated(false);
#         }
#       } catch (error) {
#         console.error("Network error during authentication check:", error);
#         setIsAuthenticated(false);
#       } finally {
#         setIsLoading(false);
#       }
#     };
#
#     verifySession();
#   }, []);
#
#   if (isLoading) {
#     return (
#       <div className="loading-screen">
#         <div className="loading-spinner"></div>
#         <p>Verifying authentication...</p>
#       </div>
#     );
#   }
#
#   if (!isAuthenticated) {
#     return <Navigate to="/security/login" replace />;
#   }
#
#   return children;
# };
#
# const App = () => {
#   // Check if the user is on a honeypot admin route
#   const isHoneypotRoute = window.location.pathname.startsWith('/security');
#
#   return (
#     <Router>
#       {/* Only show your main app navbar when not in honeypot routes */}
#       {!isHoneypotRoute && <MainNavbar />}
#
#       <Routes>
#         {/* Your main application routes */}
#         <Route path="/" element={<HomePage />} />
#         <Route path="/products" element={<ProductsPage />} />
#         <Route path="/about" element={<AboutPage />} />
#         <Route path="/profile" element={<UserProfile />} />
#
#         {/* Honeypot admin routes */}
#         <Route path="/security/login" element={<HoneypotLogin />} />
#         <Route
#           path="/security/dashboard/*"
#           element={
#             <ProtectedRoute>
#               <HoneypotDashboard />
#             </ProtectedRoute>
#           }
#         />
#
#         {/* Additional security-related routes */}
#         <Route path="/security" element={<Navigate to="/security/dashboard" replace />} />
#
#         {/* Fallback route */}
#         <Route path="*" element={<Navigate to="/" replace />} />
#       </Routes>
#
#       {/* Conditionally rendered admin access link for authorized personnel only */}
#       {!isHoneypotRoute && (
#         <div className="admin-access-link" style={{
#           position: 'fixed',
#           bottom: '10px',
#           right: '10px',
#           padding: '5px 10px',
#           background: 'rgba(0,0,0,0.7)',
#           borderRadius: '5px',
#           zIndex: 1000
#         }}>
#           <Link
#             to="/security/login"
#             style={{
#               color: '#aaa',
#               textDecoration: 'none',
#               fontSize: '12px'
#             }}
#           >
#             Security Portal
#           </Link>
#         </div>
#       )}
#     </Router>
#   );
# };
#
# export default App;
#
# // ======================================
# // src/honeypot/Login.js - Wrapper for the honeypot login component
# // ======================================
#
# // Import the honeypot login component
# // Note: You'll need to copy the honeypot CSS and update import paths
# import { useState } from 'react';
# import { useNavigate } from 'react-router-dom';
# import { FaSpider, FaLock, FaExclamationTriangle, FaEye, FaEyeSlash, FaUserSecret, FaSignInAlt } from 'react-icons/fa';
# import { setCsrfToken } from '../utils/csrfHelper';
# import './honeypot.css';
#
# const Login = () => {
#   // Implementation remains the same as honeypot/frontend/src/static/js/login.js
#   // This is a wrapper in case you need to customize it
#
#   // Standard login implementation here
#   const [adminKey, setAdminKey] = useState('');
#   const [loading, setLoading] = useState(false);
#   const [error, setError] = useState(null);
#   const [showPassword, setShowPassword] = useState(false);
#   const navigate = useNavigate();
#
#   // Login form and logic
#   // ...
#
#   return (
#     <div className="honeypot-login-container">
#       {/* Login form implementation */}
#     </div>
#   );
# };
#
# export default Login;
#
# // ======================================
# // src/honeypot/Dashboard.js - Wrapper for the honeypot dashboard
# // ======================================
#
# // Import the honeypot dashboard component
# // This would be a wrapper around the actual honeypot admin dashboard
# import { useState, useEffect } from 'react';
# import { useNavigate } from 'react-router-dom';
# import './honeypot.css';
#
# const Dashboard = () => {
#   // Implementation would integrate honeypot/frontend/src/static/js/admin.js
#   // This is a wrapper in case you need to customize it
#
#   return (
#     <div className="honeypot-admin-dashboard">
#       {/* Dashboard implementation */}
#     </div>
#   );
# };
#
# export default Dashboard;
#
# // ======================================
# // src/utils/csrfHelper.js - CSRF token management
# // ======================================
#
# const CSRF_TOKEN_KEY = 'csrfToken';
#
# export const getCsrfToken = () => {
#   try {
#     return sessionStorage.getItem(CSRF_TOKEN_KEY);
#   } catch (e) {
#     console.error("Error reading CSRF token from sessionStorage:", e);
#     return null;
#   }
# };
#
# export const setCsrfToken = (token) => {
#   if (typeof token !== 'string') {
#     console.error("Invalid token passed to setCsrfToken:", token);
#     return;
#   }
#   try {
#     sessionStorage.setItem(CSRF_TOKEN_KEY, token);
#   } catch (e) {
#     console.error("Error writing CSRF token to sessionStorage:", e);
#   }
# };
#
# // Additional helper function for API requests to your honeypot
# export const honeypotFetch = async (url, options = {}) => {
#   const method = options.method || 'GET';
#   let headers = { ...options.headers || {} };
#
#   // Set content type if not provided
#   if (!headers['Content-Type'] &&
#       (method.toUpperCase() === 'POST' || method.toUpperCase() === 'PUT')) {
#     headers['Content-Type'] = 'application/json';
#   }
#
#   // Set Accept header if not provided
#   if (!headers['Accept']) {
#     headers['Accept'] = 'application/json';
#   }
#
#   // Add CSRF token for state-changing requests
#   if (['POST', 'PUT', 'DELETE', 'PATCH'].includes(method.toUpperCase())) {
#     const token = getCsrfToken();
#     headers['X-CSRF-TOKEN'] = token;
#   }
#
#   // Add request timeout
#   const controller = new AbortController();
#   const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout
#
#   try {
#     const response = await fetch(url, {
#       ...options,
#       headers,
#       credentials: 'include',
#       signal: controller.signal
#     });
#
#     clearTimeout(timeoutId);
#
#     // Handle authentication errors
#     if (response.status === 401) {
#       if (!window.location.pathname.includes('/security/login')) {
#         window.location.href = '/security/login';
#       }
#     }
#
#     return response;
#   } catch (error) {
#     clearTimeout(timeoutId);
#
#     if (error.name === 'AbortError') {
#       throw new Error(`Request timed out: ${url}`);
#     }
#
#     throw error;
#   }
# };
# "
