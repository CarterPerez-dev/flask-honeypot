const CSRF_TOKEN_KEY = 'csrfToken'; 

/**
 * Retrieves the CSRF token from sessionStorage.
 * @returns {string | null} The token or null if not found.
 */
export const getCsrfToken = () => {
  try {
    return sessionStorage.getItem(CSRF_TOKEN_KEY);
  } catch (e) {
    console.error("Error reading CSRF token from sessionStorage:", e);
    return null;
  }
};

/**
 * Stores the CSRF token in sessionStorage.
 * @param {string} token The CSRF token to store.
 */
export const setCsrfToken = (token) => {
  if (typeof token !== 'string') {
    console.error("Invalid token passed to setCsrfToken:", token);
    return;
  }
  try {
    sessionStorage.setItem(CSRF_TOKEN_KEY, token);
  } catch (e) {
    console.error("Error writing CSRF token to sessionStorage:", e);
  }
};


export const adminFetch = async (url, options = {}) => {
  const method = options.method || 'GET';
  let headers = { ...options.headers || {} };
  

  if (!headers['Content-Type'] && 
      (method.toUpperCase() === 'POST' || method.toUpperCase() === 'PUT')) {
    headers['Content-Type'] = 'application/json';
  }
  

  if (!headers['Accept']) {
    headers['Accept'] = 'application/json';
  }
  

  if (['POST', 'PUT', 'DELETE', 'PATCH'].includes(method.toUpperCase())) {
    const token = getCsrfToken();
    console.log("Using CSRF token for request:", token ? (token.substring(0, 5) + "...") : "none");
    

    headers['X-CSRF-TOKEN'] = token;
  }
  
  // Add request timeout and error handling
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout
  
  try {
    const response = await fetch(url, {
      ...options,
      headers,
      credentials: 'include',
      signal: controller.signal,
      redirect: 'manual'
    });
    

    clearTimeout(timeoutId);
    

    if (response.status === 302 || response.status === 301) {
      console.warn(`Redirect detected from ${url} to ${response.headers.get('Location')}`);
      return {
        ok: false, 
        status: response.status,
        statusText: `Redirect detected. API endpoints should not redirect.`,
        text: async () => `Redirect to ${response.headers.get('Location')} detected`,
        json: async () => ({ error: 'Redirect detected' })
      };
    }
    
    // Handle 401 Unauthorized - session may have expired
    if (response.status === 401) {
      console.error("Authentication error - session may have expired");
      

      if (!window.location.pathname.includes('/login')) {
        console.log("Session expired, redirecting to login");
        window.location.href = '/honey/login';
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
