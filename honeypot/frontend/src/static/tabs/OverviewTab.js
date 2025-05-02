// src/components/OverviewTab.js
import React, { useState, useEffect } from 'react';
import { FaChartLine, FaSync, FaSpinner, FaExclamationTriangle } from 'react-icons/fa';
import { adminFetch } from '../../components/csrfHelper';
import { formatTimestamp } from '../../utils/dateUtils';


const OverviewTab = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [retryCount, setRetryCount] = useState(0);

  const fetchStats = async () => {
    setLoading(true);
    setError(null);
    
    try {
      console.log("Fetching combined analytics...");
      const response = await adminFetch("/api/honeypot/combined-analytics");
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error("Error response:", errorText);
        throw new Error(`Failed to fetch honeypot analytics: ${response.status} ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log("Overview data:", data);
      setStats(data);
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
  };

  // Initial data load
  useEffect(() => {
    fetchStats();
    
    // Cleanup function to reset retry count when component unmounts
    return () => {
      setRetryCount(0);
    };
  }, []);

  if (loading) {
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
          Retry
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
        <h2><FaChartLine /> Honeypot Overview</h2>
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
      
      <div className="honeypot-admin-stats-grid">
        <div className="honeypot-admin-stat-card">
          <div className="honeypot-admin-stat-icon honeypot-admin-total-icon">
            <FaChartLine />
          </div>
          <div className="honeypot-admin-stat-content">
            <div className="honeypot-admin-stat-value">{data.total_attempts || 0}</div>
            <div className="honeypot-admin-stat-label">Total Interactions</div>
          </div>
        </div>
        
        <div className="honeypot-admin-stat-card">
          <div className="honeypot-admin-stat-icon honeypot-admin-ips-icon">
            <FaChartLine />
          </div>
          <div className="honeypot-admin-stat-content">
            <div className="honeypot-admin-stat-value">{data.unique_ips || 0}</div>
            <div className="honeypot-admin-stat-label">Unique IPs</div>
          </div>
        </div>
        
        <div className="honeypot-admin-stat-card">
          <div className="honeypot-admin-stat-icon honeypot-admin-clients-icon">
            <FaChartLine />
          </div>
          <div className="honeypot-admin-stat-content">
            <div className="honeypot-admin-stat-value">{data.unique_clients || 0}</div>
            <div className="honeypot-admin-stat-label">Unique Clients</div>
          </div>
        </div>
        
        <div className="honeypot-admin-stat-card">
          <div className="honeypot-admin-stat-icon honeypot-admin-today-icon">
            <FaChartLine />
          </div>
          <div className="honeypot-admin-stat-content">
            <div className="honeypot-admin-stat-value">{data.today_interactions || 0}</div>
            <div className="honeypot-admin-stat-label">Today</div>
          </div>
        </div>
      </div>
      
      <div className="honeypot-admin-overview-description">
        <h3>About Honeypot Dashboard</h3>
        <p>
          Welcome to the Honeypot Administration Dashboard. This interface allows you to monitor and analyze
          interactions with your honeypot system. Use the tabs on the left to navigate between different views:
        </p>
        <ul>
          <li><strong>Overview:</strong> Summary statistics and system health</li>
          <li><strong>Honeypot:</strong> Detailed analysis of honeypot interactions</li>
          <li><strong>HTML Interactions:</strong> Analysis of HTML page interactions</li>
        </ul>
        <p>
          For more detailed information, visit the specific tabs and use the available filters to narrow down
          the data you're interested in.
        </p>
      </div>
    </div>
  );
};

export default OverviewTab;
