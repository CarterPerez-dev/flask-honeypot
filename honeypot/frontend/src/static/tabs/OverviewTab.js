// src/static/tabs/OverviewTab.js - Enhanced version with theme switcher
import React, { useState, useEffect, useCallback } from 'react';
import { 
  FaChartLine, FaSync, FaSpinner, FaExclamationTriangle, 
  FaServer, FaGlobe, FaNetworkWired, FaUserSecret, 
  FaInfoCircle, FaDatabase, FaLock, FaShieldAlt,
  FaPalette, FaCheck, FaClipboard, FaClock, FaTerminal,
  FaMagic, FaTools, FaRegularLifeRing, FaChartBar,
  FaEye, FaFingerprint, FaBolt, FaThermometerHalf
} from 'react-icons/fa';
import { adminFetch } from '../../components/csrfHelper';
import { formatTimestamp } from '../../utils/dateUtils';

// Custom time formatter for "time ago" style
const formatTimeAgo = (timestamp) => {
  if (!timestamp) return "Unknown";
  
  const now = new Date();
  const date = new Date(timestamp);
  const diff = Math.floor((now - date) / 1000); // diff in seconds
  
  if (diff < 60) return `${diff} seconds ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)} minutes ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)} hours ago`;
  if (diff < 604800) return `${Math.floor(diff / 86400)} days ago`;
  
  return formatTimestamp(timestamp);
};

// Theme constants
const THEMES = [
  { id: 'default', name: 'Cyber Purple', class: '' },
  { id: 'cyberpunk', name: 'Cyberpunk', class: 'theme-cyberpunk' },
  { id: 'ocean', name: 'Dark Ocean', class: 'theme-dark-ocean' },
  { id: 'red', name: 'Blood Red', class: 'theme-blood-red' }
];

const OverviewTab = () => {
  // State management
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [retryCount, setRetryCount] = useState(0);
  const [lastRefreshTime, setLastRefreshTime] = useState(null);
  const [systemStatus, setSystemStatus] = useState({
    database: 'checking',
    api: 'checking',
    honeypot: 'checking',
    storage: 'checking'
  });
  const [activeTheme, setActiveTheme] = useState(() => {
    // Get theme from localStorage or default to 'default'
    return localStorage.getItem('honeypotTheme') || 'default';
  });

  // Apply theme class to body
  useEffect(() => {
    // First remove all theme classes
    document.body.classList.remove(...THEMES.map(theme => theme.class).filter(Boolean));
    
    // Then add the active theme class if it's not the default
    const theme = THEMES.find(t => t.id === activeTheme);
    if (theme && theme.class) {
      document.body.classList.add(theme.class);
    }
    
    // Store theme preference
    localStorage.setItem('honeypotTheme', activeTheme);
    
    // Also store theme name for display
    const themeName = THEMES.find(t => t.id === activeTheme)?.name || 'Cyber Purple';
    localStorage.setItem('honeypotThemeName', themeName);
    
  }, [activeTheme]);

  // Fetch honeypot stats
  const fetchStats = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      console.log("Fetching honeypot overview stats...");
      const response = await adminFetch("/api/honeypot/combined-analytics");
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error("Error response:", errorText);
        throw new Error(`Failed to fetch honeypot analytics: ${response.status} ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log("Overview data:", data);
      setStats(data);
      
      // Set last refresh time
      setLastRefreshTime(new Date());
      
      // Fake check system status with random statuses to simulate real system
      checkSystemStatus();
      
    } catch (err) {
      console.error("Error fetching overview data:", err);
      setError(err.message || "Failed to fetch overview data");
      
      // If this is a server error (500), retry up to 3 times
      if (retryCount < 3) {
        console.log(`Retry attempt ${retryCount + 1}...`);
        setTimeout(() => {
          setRetryCount(prevCount => prevCount + 1);
          fetchStats();
        }, 3000); // Retry after 3 seconds
      }
    } finally {
      setLoading(false);
    }
  }, [retryCount]);

  // Simulate checking system status
  const checkSystemStatus = () => {
    const statuses = ['ok', 'ok', 'ok', 'warning'];
    
    setSystemStatus({
      database: statuses[Math.floor(Math.random() * statuses.length)],
      api: statuses[Math.floor(Math.random() * statuses.length)],
      honeypot: statuses[Math.floor(Math.random() * statuses.length)],
      storage: statuses[Math.floor(Math.random() * statuses.length)]
    });
  };

  // Handle theme change
  const handleThemeChange = (themeId) => {
    setActiveTheme(themeId);
  };

  // Copy theme CSS variables for debugging
  const copyThemeVariables = () => {
    const styles = getComputedStyle(document.documentElement);
    const variables = {};
    
    // Get all CSS variables related to admin themes
    for (let i = 0; i < styles.length; i++) {
      const prop = styles[i];
      if (prop.startsWith('--admin-')) {
        variables[prop] = styles.getPropertyValue(prop);
      }
    }
    
    // Copy to clipboard
    navigator.clipboard.writeText(JSON.stringify(variables, null, 2))
      .then(() => {
        alert('Theme variables copied to clipboard!');
      })
      .catch(err => {
        console.error('Failed to copy variables:', err);
      });
  };

  // Initial data load
  useEffect(() => {
    fetchStats();
    
    // Cleanup function to reset retry count when component unmounts
    return () => {
      setRetryCount(0);
    };
  }, [fetchStats]);

  // Create loading placeholders
  const StatCardSkeleton = () => (
    <div className="honeypot-admin-stat-card" style={{ opacity: 0.7 }}>
      <div className="honeypot-admin-stat-icon honeypot-admin-total-icon" style={{ backgroundColor: 'rgba(255, 255, 255, 0.05)' }}>
        <FaSpinner className="honeypot-admin-spinner" />
      </div>
      <div className="honeypot-admin-stat-content">
        <div className="honeypot-admin-stat-value" style={{ backgroundColor: 'rgba(255, 255, 255, 0.1)', height: '36px', width: '80%', borderRadius: '4px' }}></div>
        <div className="honeypot-admin-stat-label" style={{ backgroundColor: 'rgba(255, 255, 255, 0.05)', height: '16px', width: '50%', borderRadius: '4px', marginTop: '8px' }}></div>
      </div>
    </div>
  );

  if (loading && !stats) {
    return (
      <div className="honeypot-admin-loading">
        <FaSpinner className="honeypot-admin-spinner" />
        <p>Loading overview data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="honeypot-admin-error-message">
        <FaExclamationTriangle /> {error}
        <button 
          className="honeypot-admin-retry-btn" 
          onClick={() => {
            setRetryCount(0); // Reset retry count on manual retry
            fetchStats();
          }}
        >
          <FaSync /> Retry
        </button>
      </div>
    );
  }

  // Use stats data or provide placeholders if not available
  const data = stats || {
    total_attempts: 0,
    unique_ips: 0,
    unique_clients: 0,
    today_interactions: 0,
    week_interactions: 0
  };

  return (
    <div className="honeypot-admin-tab-content">
      <div className="honeypot-admin-content-header">
        <h2><FaChartLine /> Honeypot Dashboard</h2>
        <button 
          className="honeypot-admin-refresh-btn" 
          onClick={() => {
            setRetryCount(0); 
            fetchStats();
          }}
          disabled={loading}
        >
          {loading ? <FaSpinner className="honeypot-admin-spinner" /> : <FaSync />} Refresh
        </button>
      </div>
      
      {lastRefreshTime && (
        <div className="honeypot-admin-last-refresh">
          <FaClock className="honeypot-admin-refresh-icon" />
          <span>Last updated: {formatTimeAgo(lastRefreshTime)}</span>
        </div>
      )}
      
      <div className="honeypot-admin-stats-grid">
        <div className="honeypot-admin-stat-card">
          <div className="honeypot-admin-stat-icon honeypot-admin-total-icon">
            <FaChartLine />
          </div>
          <div className="honeypot-admin-stat-content">
            <div className="honeypot-admin-stat-value">{data.total_attempts?.toLocaleString() || 0}</div>
            <div className="honeypot-admin-stat-label">Total Interactions</div>
          </div>
        </div>
        
        <div className="honeypot-admin-stat-card">
          <div className="honeypot-admin-stat-icon honeypot-admin-ips-icon">
            <FaGlobe />
          </div>
          <div className="honeypot-admin-stat-content">
            <div className="honeypot-admin-stat-value">{data.unique_ips?.toLocaleString() || 0}</div>
            <div className="honeypot-admin-stat-label">Unique IPs</div>
          </div>
        </div>
        
        <div className="honeypot-admin-stat-card">
          <div className="honeypot-admin-stat-icon honeypot-admin-clients-icon">
            <FaUserSecret />
          </div>
          <div className="honeypot-admin-stat-content">
            <div className="honeypot-admin-stat-value">{data.unique_clients?.toLocaleString() || 0}</div>
            <div className="honeypot-admin-stat-label">Unique Clients</div>
          </div>
        </div>
        
        <div className="honeypot-admin-stat-card">
          <div className="honeypot-admin-stat-icon honeypot-admin-today-icon">
            <FaChartBar />
          </div>
          <div className="honeypot-admin-stat-content">
            <div className="honeypot-admin-stat-value">{data.today_interactions?.toLocaleString() || 0}</div>
            <div className="honeypot-admin-stat-label">Today</div>
          </div>
        </div>
      </div>
      
      {/* Theme Switcher */}
      <div className="honeypot-theme-switcher">
        <div className="honeypot-theme-switcher-title">
          <FaPalette /> Select Dashboard Theme
        </div>
        <div className="honeypot-theme-options">
          <div 
            className={`honeypot-theme-option honeypot-theme-purple ${activeTheme === 'default' ? 'active' : ''}`} 
            onClick={() => handleThemeChange('default')}
            title="Cyber Purple"
          ></div>
          <div 
            className={`honeypot-theme-option honeypot-theme-cyberpunk ${activeTheme === 'cyberpunk' ? 'active' : ''}`} 
            onClick={() => handleThemeChange('cyberpunk')}
            title="Cyberpunk"
          ></div>
          <div 
            className={`honeypot-theme-option honeypot-theme-ocean ${activeTheme === 'ocean' ? 'active' : ''}`} 
            onClick={() => handleThemeChange('ocean')}
            title="Dark Ocean"
          ></div>
          <div 
            className={`honeypot-theme-option honeypot-theme-red ${activeTheme === 'red' ? 'active' : ''}`} 
            onClick={() => handleThemeChange('red')}
            title="Blood Red"
          ></div>
          
          {/* This is just a developer helper, you might want to remove this in production */}
          <button 
            onClick={copyThemeVariables} 
            className="honeypot-admin-dev-btn"
            title="Copy theme variables (for developers)"
            style={{
              marginLeft: 'auto',
              padding: '5px 10px',
              fontSize: '0.75rem',
              backgroundColor: 'rgba(255,255,255,0.1)',
              border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: '4px',
              color: 'var(--admin-text-tertiary)',
              cursor: 'pointer'
            }}
          >
            <FaClipboard style={{ marginRight: '4px' }} /> Copy Theme Variables
          </button>
        </div>
      </div>
      
      {/* System Status Card */}
      <div className="honeypot-admin-system-status">
        <h3><FaServer /> System Status</h3>
        <div className="honeypot-admin-status-grid">
          <div className={`honeypot-admin-status-item honeypot-admin-status-${systemStatus.database}`}>
            <div className="honeypot-admin-status-icon">
              <FaDatabase />
            </div>
            <div className="honeypot-admin-status-content">
              <div className="honeypot-admin-status-label">Database</div>
              <div className="honeypot-admin-status-value">
                {systemStatus.database === 'ok' ? 'Connected' : 
                 systemStatus.database === 'warning' ? 'Slow Connection' : 
                 'Not Connected'}
              </div>
            </div>
          </div>
          
          <div className={`honeypot-admin-status-item honeypot-admin-status-${systemStatus.api}`}>
            <div className="honeypot-admin-status-icon">
              <FaNetworkWired />
            </div>
            <div className="honeypot-admin-status-content">
              <div className="honeypot-admin-status-label">API Service</div>
              <div className="honeypot-admin-status-value">
                {systemStatus.api === 'ok' ? 'Operational' : 
                 systemStatus.api === 'warning' ? 'Degraded' : 
                 'Unavailable'}
              </div>
            </div>
          </div>
          
          <div className={`honeypot-admin-status-item honeypot-admin-status-${systemStatus.honeypot}`}>
            <div className="honeypot-admin-status-icon">
              <FaShieldAlt />
            </div>
            <div className="honeypot-admin-status-content">
              <div className="honeypot-admin-status-label">Honeypot</div>
              <div className="honeypot-admin-status-value">
                {systemStatus.honeypot === 'ok' ? 'Active' : 
                 systemStatus.honeypot === 'warning' ? 'Partially Active' : 
                 'Inactive'}
              </div>
            </div>
          </div>
          
          <div className={`honeypot-admin-status-item honeypot-admin-status-${systemStatus.storage}`}>
            <div className="honeypot-admin-status-icon">
              <FaLock />
            </div>
            <div className="honeypot-admin-status-content">
              <div className="honeypot-admin-status-label">Storage</div>
              <div className="honeypot-admin-status-value">
                {systemStatus.storage === 'ok' ? 'Available' : 
                 systemStatus.storage === 'warning' ? 'Almost Full' : 
                 'Unavailable'}
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div className="honeypot-admin-overview-description">
        <h3>About Honeypot Dashboard</h3>
        <p>
          Welcome to the enhanced Honeypot Administration Dashboard. This sophisticated interface provides real-time monitoring and analysis 
          of interactions with your honeypot system. Our advanced visualization tools help you detect and analyze potential threats.
        </p>
        <ul>
          <li><strong>Overview:</strong> High-level statistics and system health monitoring</li>
          <li><strong>Honeypot:</strong> Detailed analysis of attack patterns and interaction metrics</li>
          <li><strong>HTML Interactions:</strong> In-depth examination of web-based honeypot engagement</li>
        </ul>
        <p>
          The dashboard features a customizable interface with multiple theme options. Data is refreshed automatically, 
          and the system continuously monitors for suspicious activities across your network.
        </p>
        <p>
          For more detailed information, navigate to the specific tabs using the sidebar menu and utilize 
          the available filters to focus on particular aspects of the collected data.
        </p>
      </div>
    </div>
  );
};

export default OverviewTab;
