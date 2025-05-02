// frontend/my-react-app/src/components/csrfHelper.js

/**
 * Helper to manage CSRF tokens for admin requests
 */
export const getCsrfToken = () => {
  // First try to get from meta tag
  const metaTag = document.querySelector('meta[name="csrf-token"]');
  if (metaTag) {
    return metaTag.getAttribute('content');
  }
  
  // Then try localStorage
  return localStorage.getItem('csrf_token');
};

export const setCsrfToken = (token) => {
  if (token) {
    localStorage.setItem('csrf_token', token);
    console.log("CSRF token set in localStorage:", token.substring(0, 5) + "...");
  }
};

/**
 * Fetch wrapper that automatically adds CSRF token headers for admin routes
 * and handles common error scenarios
 */
export const adminFetch = async (url, options = {}) => {
  const method = options.method || 'GET';
  let headers = { ...options.headers || {} };
  
  // Always add Content-Type for JSON requests if not specified
  if (!headers['Content-Type'] && 
      (method.toUpperCase() === 'POST' || method.toUpperCase() === 'PUT')) {
    headers['Content-Type'] = 'application/json';
  }
  
  // Add CSRF token header for all modifying requests
  if (['POST', 'PUT', 'DELETE', 'PATCH'].includes(method.toUpperCase())) {
    const token = getCsrfToken();
    console.log("Using CSRF token for request:", token ? (token.substring(0, 5) + "...") : "none");
    
    // Add CSRF header
    headers['X-CSRF-TOKEN'] = token;
  }
  
  // Add request timeout and error handling
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout
  
  try {
    // Make the fetch request with credentials and timeout
    const response = await fetch(url, {
      ...options,
      headers,
      credentials: 'include',
      signal: controller.signal
    });
    
    // Clear the timeout
    clearTimeout(timeoutId);
    
    // Handle 401 Unauthorized - session may have expired
    if (response.status === 401) {
      console.error("Authentication error - session may have expired");
      
      // If we're not already on the login page, we might want to redirect
      if (!window.location.pathname.includes('/login')) {
        console.log("Session expired, redirecting to login");
        // Optional: Redirect to login page
        // window.location.href = '/honey/login';
      }
    }
    
    // Handle 403 Forbidden - likely CSRF token mismatch
    if (response.status === 403) {
      console.error("Forbidden - possible CSRF token mismatch");
      
      // Try to get a new CSRF token
      try {
        const tokenResponse = await fetch('/api/honeypot/angela/csrf-token', {
          credentials: 'include'
        });
        
        if (tokenResponse.ok) {
          const data = await tokenResponse.json();
          if (data.csrf_token) {
            setCsrfToken(data.csrf_token);
            console.log("Refreshed CSRF token after 403 error");
          }
        }
      } catch (tokenError) {
        console.error("Failed to refresh CSRF token:", tokenError);
      }
    }
    
    // Log all server errors for debugging
    if (response.status >= 500) {
      console.error(`Server error (${response.status}):`, url);
      try {
        const errorText = await response.clone().text();
        console.error("Error response:", errorText);
      } catch (e) {
        console.error("Could not extract error text");
      }
    }
    
    return response;
  } catch (error) {
    // Clear the timeout
    clearTimeout(timeoutId);
    
    // Handle AbortError differently (timeout)
    if (error.name === 'AbortError') {
      console.error(`Request timeout for ${url}`);
      throw new Error(`Request timed out: ${url}`);
    }
    
    // Network errors, etc.
    console.error(`Fetch error for ${url}:`, error);
    throw error;
  }
};
