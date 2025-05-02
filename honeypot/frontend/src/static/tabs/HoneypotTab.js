// HoneypotTab.js
import React, { useState, useEffect, useCallback, useMemo } from "react";
import { 
  FaSpider, FaSync, FaSpinner, FaExclamationTriangle, FaFilter, 
  FaNetworkWired, FaGlobe, FaTimes, FaSort, FaDownload, FaChartBar,
  FaSortUp, FaSortDown, FaUserSecret, FaAngleRight, FaClock,
  FaLocationArrow, FaFingerprint, FaUser, FaBug, FaShieldAlt,
  FaEye, FaLock, FaKey, FaDatabase, FaTerminal, FaCode, FaDesktop,
  FaServer, FaArrowLeft, FaSearch, FaExclamationCircle, FaQuestionCircle,
  FaInfoCircle, FaClipboard, FaChartLine, FaChartPie, FaLink, FaFileAlt,
  FaHistory, FaSatelliteDish, FaMagic, FaTools, FaLaptopCode, FaMicrochip, FaRobot
} from "react-icons/fa";
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, 
  ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line, 
  AreaChart, Area
} from 'recharts';
import { adminFetch } from '../../components/csrfHelper';
import LoadingPlaceholder from '../../components/LoadingPlaceholder';
import JsonSyntaxHighlighter from '../../components/JsonSyntaxHighlighter';
import { formatTimestamp } from '../../utils/dateUtils';


const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="honeypot-custom-tooltip">
        <p className="honeypot-tooltip-label">{label}</p>
        <p className="honeypot-tooltip-value">
          <span className="honeypot-tooltip-count">{payload[0].value}</span> interactions
        </p>
      </div>
    );
  }
  return null;
};


const EmptyState = ({ message, icon: Icon = FaExclamationCircle }) => (
  <div className="honeypot-empty-state">
    <div className="honeypot-empty-state-icon">
      <Icon />
    </div>
    <p className="honeypot-empty-state-message">{message}</p>
  </div>
);

const HoneypotTab = () => {
  const [honeypotData, setHoneypotData] = useState(null);
  const [detailedStats, setDetailedStats] = useState(null);
  const [interactions, setInteractions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statsLoading, setStatsLoading] = useState(true);
  const [interactionsLoading, setInteractionsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState("");
  const [filterCategory, setFilterCategory] = useState("all");
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(20);
  const [totalInteractions, setTotalInteractions] = useState(0);
  const [sortField, setSortField] = useState("timestamp");
  const [sortOrder, setSortOrder] = useState("desc");
  const [selectedInteraction, setSelectedInteraction] = useState(null);
  const [viewMode, setViewMode] = useState("overview"); 
  const [retryCount, setRetryCount] = useState(0);
  const [isFilterVisible, setIsFilterVisible] = useState(false);
  const [lastRefreshTime, setLastRefreshTime] = useState(null);
  const [animationsEnabled, setAnimationsEnabled] = useState(true);
  

  const CHART_COLORS = [
    '#291efc', '#02d63b', '#e89a02', '#ff6114', '#f20202', 
    '#0fa7fc', '#fa1b6a', '#972ffa', '#f7d111', '#3dfcca'
  ];


  useEffect(() => {
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    setAnimationsEnabled(!prefersReducedMotion);
  }, []);


  const fetchHoneypotData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      console.log("Fetching honeypot analytics data...");
      

      setLastRefreshTime(new Date());
      
      const response = await adminFetch("/api/honeypot/combined-analytics");
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error("Error response:", errorText);
        throw new Error(`Failed to fetch honeypot analytics: ${response.status} ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log("Honeypot analytics data:", data);
      setHoneypotData(data);
      
      if (data && typeof data.total_attempts === 'number') {
        setTotalInteractions(data.total_attempts);
      } else if (data && Array.isArray(data.recent_activity)) {
        setTotalInteractions(data.recent_activity.length);
      }
      
    } catch (err) {
      console.error("Error fetching honeypot data:", err);
      setError(err.message || "Failed to fetch honeypot data");
      
      if (retryCount < 3) {
        setTimeout(() => {
          setRetryCount(prevCount => prevCount + 1);
          fetchHoneypotData();
        }, 3000); 
      }
    } finally {
      setLoading(false);
    }
  }, [retryCount]);


  const fetchDetailedStats = useCallback(async () => {
    setStatsLoading(true);
    try {
      console.log("Fetching detailed stats...");
      const response = await adminFetch("/api/honeypot/detailed-stats");
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error("Error response:", errorText);
        throw new Error(`Failed to fetch detailed statistics: ${response.status} ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log("Detailed stats data:", data);
      

      if (data.time_series && Array.isArray(data.time_series)) {
        data.time_series = data.time_series
          .map(item => ({
            ...item,
            date: typeof item.date === 'string' ? item.date : new Date(item.date).toISOString().split('T')[0],
            count: Number(item.count) || 0
          }))
          .sort((a, b) => new Date(a.date) - new Date(b.date));
      }
      
      setDetailedStats(data);
    } catch (err) {
      console.error("Error fetching detailed stats:", err);
    } finally {
      setStatsLoading(false);
    }
  }, []);


  const fetchInteractions = useCallback(async () => {
    setInteractionsLoading(true);
    try {
      const queryParams = new URLSearchParams({
        page,
        limit,
        sort_field: sortField,
        sort_order: sortOrder,
      });
      
      if (filter) {
        queryParams.append('filter', filter);
      }
      
      if (filterCategory !== "all") {
        queryParams.append('page_type', filterCategory);
      }
      
      const response = await adminFetch(`/api/honeypot/interactions?${queryParams.toString()}`);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error("Error response:", errorText);
        throw new Error(`Failed to fetch interactions: ${response.status} ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log("Interactions data:", data);
      

      if (data.interactions) {
        setInteractions(data.interactions);
        setTotalInteractions(data.total || data.interactions.length);
      } else if (Array.isArray(data)) {
        setInteractions(data);
        setTotalInteractions(data.length);
      } else {
        console.error("Unexpected data format:", data);
        setInteractions([]);
      }
    } catch (err) {
      console.error("Error fetching interactions:", err);
    } finally {
      setInteractionsLoading(false);
    }
  }, [page, limit, sortField, sortOrder, filter, filterCategory]);


  const fetchInteractionDetails = useCallback(async (id) => {
    try {
      setLoading(true);
      const response = await adminFetch(`/api/honeypot/interactions/${id}`);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error("Error response:", errorText);
        throw new Error(`Failed to fetch interaction details: ${response.status} ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log("Interaction details:", data);
      

      setViewMode("details");
      setSelectedInteraction(data);
    } catch (err) {
      console.error("Error fetching interaction details:", err);

      setError(`Error loading details: ${err.message || "Unknown error"}`);
    } finally {
      setLoading(false);
    }
  }, []);


  useEffect(() => {
    let refreshInterval;
    
    if (viewMode === "overview") {
      refreshInterval = setInterval(() => {
        console.log("Auto-refreshing honeypot data...");
        fetchHoneypotData();
        fetchDetailedStats();
      }, 5 * 60 * 1000); 
    }
    
    return () => {
      if (refreshInterval) clearInterval(refreshInterval);
    };
  }, [viewMode, fetchHoneypotData, fetchDetailedStats]);


  useEffect(() => {
    return () => {
      setRetryCount(0);
    };
  }, []);


  useEffect(() => {
    console.log("Component mounted - fetching initial data");
    fetchHoneypotData();
    fetchDetailedStats();
  }, [fetchHoneypotData, fetchDetailedStats]);


  useEffect(() => {
    if (viewMode === "interactions") {
      console.log("Fetching interactions - mode is 'interactions'");
      fetchInteractions();
    }
  }, [fetchInteractions, viewMode, page, limit, sortField, sortOrder, filter, filterCategory]);


  const handleFilterChange = (e) => {
    setFilter(e.target.value);
  };


  const applyFilter = () => {
    setPage(1); 
    fetchInteractions();
  };


  const clearFilter = () => {
    setFilter("");
    setFilterCategory("all");
    setPage(1);
    fetchInteractions();
  };

  const handleSort = (field) => {
    if (sortField === field) {
      setSortOrder(sortOrder === "asc" ? "desc" : "asc");
    } else {
      setSortField(field);
      setSortOrder("desc");
    }
  };


  const exportData = () => {
    try {
      const jsonData = JSON.stringify(interactions, null, 2);
      const blob = new Blob([jsonData], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      

      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      

      const link = document.createElement("a");
      link.href = url;
      link.download = `honeypot-interactions-${timestamp}.json`;
      document.body.appendChild(link);
      link.click();
      

      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Error exporting data:", err);
      setError("Failed to export data: " + err.message);
    }
  };


  const renderSortIndicator = (field) => {
    if (sortField !== field) return <FaSort className="honeypot-sort-icon" />;
    return sortOrder === "asc" ? 
      <FaSortUp className="honeypot-sort-icon honeypot-sort-active" /> : 
      <FaSortDown className="honeypot-sort-icon honeypot-sort-active" />;
  };


  const handlePageChange = (newPage) => {
    setPage(newPage);
  };


  const formatRelativeTime = (timestamp) => {
    if (!timestamp) return 'Unknown';
    
    const now = new Date();
    const date = new Date(timestamp);
    const diffMs = now - date;
    const diffSec = Math.floor(diffMs / 1000);
    
    if (diffSec < 60) return 'Just now';
    if (diffSec < 3600) return `${Math.floor(diffSec / 60)} minutes ago`;
    if (diffSec < 86400) return `${Math.floor(diffSec / 3600)} hours ago`;
    if (diffSec < 604800) return `${Math.floor(diffSec / 86400)} days ago`;
    
    return formatTimestamp(timestamp);
  };


  const getThreatLevel = (interaction) => {
    let level = 'low';
    

    if (interaction.is_tor_or_proxy) level = 'medium';
    if (interaction.is_scanner || interaction.is_port_scan) level = 'high';
    if (interaction.suspicious_params) level = 'high';
    if (interaction.bot_indicators && interaction.bot_indicators.length > 2) level = 'medium';
    if (interaction.interaction_type === 'login_attempt') level = 'medium';
    if (interaction.interaction_type === 'sql_injection_attempt') level = 'high';
    

    if (interaction.notes && Array.isArray(interaction.notes) && interaction.notes.length > 0) {
      level = 'high'; 
    }
    
    return level;
  };
  

  const getThreatIcon = (level) => {
    switch(level) {
      case 'high': return <FaExclamationTriangle className="honeypot-threat-icon honeypot-threat-high" />;
      case 'medium': return <FaExclamationCircle className="honeypot-threat-icon honeypot-threat-medium" />;
      case 'low': return <FaInfoCircle className="honeypot-threat-icon honeypot-threat-low" />;
      default: return <FaQuestionCircle className="honeypot-threat-icon" />;
    }
  };


  const prepareChartData = useCallback(() => {
    if (!honeypotData) return { pathData: [], ipData: [] };

    console.log("Preparing chart data from:", honeypotData);


    let pathData = [];
    if (honeypotData.top_paths && Array.isArray(honeypotData.top_paths)) {
      pathData = honeypotData.top_paths.map(item => ({
        name: item._id ? (item._id.length > 20 ? item._id.substring(0, 20) + '...' : item._id) : "unknown",
        value: item.count || 0,
        fullPath: item._id || "unknown"
      }));
    }


    let ipData = [];
    if (honeypotData.top_ips && Array.isArray(honeypotData.top_ips)) {
      ipData = honeypotData.top_ips.map(item => ({
        name: item._id || "unknown",
        value: item.count || 0
      }));
    }

    return { pathData, ipData };
  }, [honeypotData]);


  const { pathData, ipData } = useMemo(() => prepareChartData(), [prepareChartData]);


  const timeSeriesData = useMemo(() => {
    if (!detailedStats?.time_series || !Array.isArray(detailedStats.time_series)) {
      return [];
    }
    return detailedStats.time_series;
  }, [detailedStats]);


  const getInteractionSummary = (interaction) => {
    if (!interaction) return "No details available";
    
    const additionalData = interaction.additional_data || {};
    

    switch(interaction.interaction_type) {
      case "login_attempt":
        return `Login attempt with username: ${additionalData.username || "unknown"}, password: ${additionalData.password || "unknown"}`;
      case "form_submission":
        return `Form data submitted with ${Object.keys(additionalData).length} fields`;
      case "download_attempt":
        return `Attempted to download: ${additionalData.filename || "unknown file"}`;
      case "button_click":
        return `Clicked on ${additionalData.button_text || "a button"}`;
      case "sql_injection_attempt":
        return `SQL injection attempt detected in ${additionalData.input_field || "input"}`; 
      case "api_keys_viewed":
        return `Viewed API keys section`;
      default:
        return interaction.interaction_type 
          ? `${interaction.interaction_type.replace(/_/g, ' ')}`
          : "Unknown interaction";
    }
  };


  const renderContent = () => {
    if (loading && !honeypotData) {
      return (
        <LoadingPlaceholder 
          height="300px" 
          message="Loading honeypot data..." 
          type="pulse"
        />
      );
    }

    if (error) {
      return (
        <div className="honeypot-error-message">
          <FaExclamationTriangle className="honeypot-error-icon" /> 
          <div className="honeypot-error-content">
            <h3 className="honeypot-error-title">Error Encountered</h3>
            <p className="honeypot-error-details">{error}</p>
          </div>
          <button 
            className="honeypot-retry-btn" 
            onClick={() => {
              setRetryCount(0); 
              fetchHoneypotData();
            }}
          >
            <FaSync /> Retry
          </button>
        </div>
      );
    }


    switch (viewMode) {
      case "overview":
        return renderOverviewContent();
      case "interactions":
        return renderInteractionsContent();
      case "details":
        return renderDetailsContent();
      default:
        return renderOverviewContent();
    }
  };


  const renderOverviewContent = () => {
    const dataToUse = honeypotData || {
      total_attempts: 0,
      unique_ips: 0,
      unique_clients: 0,
      threats_detected: 0,
      top_paths: [],
      top_ips: [],
      recent_activity: []
    };
    
    const NoDataMessage = ({ message }) => (
      <div className="honeypot-no-chart-data">
        <FaExclamationCircle className="honeypot-no-data-icon" />
        <p>{message || "No data available yet."}</p>
      </div>
    );
    
    return (
      <div className="honeypot-overview-container">
        <div className="honeypot-stats-cards">
          <div className="honeypot-stat-card">
            <div className="honeypot-stat-icon">
              <FaSpider />
            </div>
            <div className="honeypot-stat-content">
              <div className="honeypot-stat-value">{dataToUse.total_attempts.toLocaleString()}</div>
              <div className="honeypot-stat-label">Total Interactions</div>
            </div>
          </div>
          
          <div className="honeypot-stat-card">
            <div className="honeypot-stat-icon">
              <FaGlobe />
            </div>
            <div className="honeypot-stat-content">
              <div className="honeypot-stat-value">{dataToUse.unique_ips.toLocaleString()}</div>
              <div className="honeypot-stat-label">Unique IPs</div>
            </div>
          </div>
          
          <div className="honeypot-stat-card">
            <div className="honeypot-stat-icon">
              <FaUserSecret />
            </div>
            <div className="honeypot-stat-content">
              <div className="honeypot-stat-value">{dataToUse.unique_clients.toLocaleString()}</div>
              <div className="honeypot-stat-label">Unique Clients</div>
            </div>
          </div>
          
          <div className="honeypot-stat-card">
            <div className="honeypot-stat-icon"><FaBug /></div>
            <div className="honeypot-stat-content">
              {statsLoading ? (
                <LoadingPlaceholder height="40px" message="" />
              ) : detailedStats ? (
                <>
                  <div className="honeypot-stat-value">{detailedStats.threats_detected.toLocaleString()}</div>
                  <div className="honeypot-stat-label">Threat Indicators</div>
                </>
              ) : (
                <>
                  <div className="honeypot-stat-value">-</div>
                  <div className="honeypot-stat-label">Threat Indicators</div>
                </>
              )}
            </div>
          </div>
        </div>
        
        {/* LastRefresh Info */}
        {lastRefreshTime && (
          <div className="honeypot-last-refreshed">
            <FaClock className="honeypot-refresh-icon" />
            <span>Last updated: {formatRelativeTime(lastRefreshTime)}</span>
            <button 
              className="honeypot-refresh-now-btn" 
              onClick={() => {
                fetchHoneypotData();
                fetchDetailedStats();
              }}
              disabled={loading || statsLoading}
            >
              {loading || statsLoading ? <FaSpinner className="honeypot-spinner" /> : <FaSync />}
              Refresh now
            </button>
          </div>
        )}
        
        {/* Charts section */}
        <div className="honeypot-charts-container">
          {/* Top Paths Chart */}
          <div className="honeypot-chart-card">
            <h3 className="honeypot-chart-title">
              <FaLink className="honeypot-chart-icon" />
              Most Targeted Paths
            </h3>
            <div className="honeypot-chart-content">
              {loading ? (
                <LoadingPlaceholder height="300px" />
              ) : pathData && pathData.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart 
                    data={pathData} 
                    margin={{ top: 20, right: 30, left: 20, bottom: 70 }}
                    barSize={36}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                    <XAxis 
                      dataKey="name" 
                      angle={-45} 
                      textAnchor="end" 
                      tick={{fill: 'var(--hp-text-secondary)'}}
                      height={70}
                      tickFormatter={(value) => value.length > 15 ? `${value.substring(0, 12)}...` : value}
                    />
                    <YAxis tick={{fill: 'var(--hp-text-secondary)'}} />
                    <Tooltip 
                      content={<CustomTooltip />}
                      cursor={{fill: 'rgba(255, 255, 255, 0.1)'}}
                    />
                    <Bar 
                      dataKey="value" 
                      name="Interactions" 
                      fill="url(#pathGradient)"
                      radius={[4, 4, 0, 0]}
                      animationDuration={animationsEnabled ? 1000 : 0}
                    >
                      {pathData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                      ))}
                    </Bar>
                    <defs>
                      <linearGradient id="pathGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#8884d8" stopOpacity={0.8}/>
                        <stop offset="100%" stopColor="#8884d8" stopOpacity={0.4}/>
                      </linearGradient>
                    </defs>
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <NoDataMessage message="No path data available yet. This will populate as your honeypot captures more interactions." />
              )}
            </div>
          </div>
          
          {/* Top IPs Chart */}
          <div className="honeypot-chart-card">
            <h3 className="honeypot-chart-title">
              <FaNetworkWired className="honeypot-chart-icon" />
              Top Source IPs
            </h3>
            <div className="honeypot-chart-content">
              {loading ? (
                <LoadingPlaceholder height="300px" />
              ) : ipData && ipData.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={ipData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={100}
                      fill="#FFFFFF"
                      dataKey="value"
                      nameKey="name"
                      label={({name, percent}) => `${name}: ${(percent * 100).toFixed(0)}%`}
                      labelLine={true}
                      animationDuration={animationsEnabled ? 1000 : 0}
                      animationBegin={animationsEnabled ? 200 : 0}
                    >
                      {ipData.map((entry, index) => (
                        <Cell 
                          key={`cell-${index}`} 
                          fill={CHART_COLORS[index % CHART_COLORS.length]}
                          stroke="rgba(0,0,0,0.2)"
                          strokeWidth={1}
                        />
                      ))}
                    </Pie>
                    <Tooltip 
                      formatter={(value) => [`${value} interactions`, 'Count']}
                      contentStyle={{
                        backgroundColor: '#FFF',
                        border: '1px solid var(--hp-border-light)',
                        borderRadius: '8px',
                        color: '#FFFFFF',
                      }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <NoDataMessage message="No IP data available yet. This chart will populate as your honeypot gathers more data." />
              )}
            </div>
          </div>

          {/* Chart: Interactions Over Time (from detailed stats) */}
          <div className="honeypot-chart-card honeypot-full-width">
            <h3 className="honeypot-chart-title">
              <FaChartLine className="honeypot-chart-icon" />
              Interactions Over Time (Last 30 Days)
            </h3>
            <div className="honeypot-chart-content">
              {statsLoading ? (
                <LoadingPlaceholder height="300px" />
              ) : timeSeriesData && timeSeriesData.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart
                    data={timeSeriesData}
                    margin={{ top: 20, right: 30, left: 20, bottom: 20 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                    <XAxis 
                      dataKey="date" 
                      tick={{fill: 'var(--hp-text-secondary)'}}
                      tickFormatter={(date) => {
                        const d = new Date(date);
                        return `${d.getMonth()+1}/${d.getDate()}`;
                      }}
                    />
                    <YAxis tick={{fill: 'var(--hp-text-secondary)'}} />
                    <Tooltip 
                      formatter={(value) => [`${value} interactions`, 'Count']}
                      contentStyle={{
                        backgroundColor: 'var(--hp-bg-card)',
                        border: '1px solid var(--hp-border-light)',
                        borderRadius: '8px',
                        color: 'var(--hp-text-primary)'
                      }}
                      labelFormatter={(label) => {
                        const date = new Date(label);
                        return date.toLocaleDateString(undefined, {
                          weekday: 'long',
                          year: 'numeric',
                          month: 'long',
                          day: 'numeric'
                        });
                      }}
                    />
                    <Area 
                      type="monotone" 
                      dataKey="count" 
                      stroke="#8884d8" 
                      fill="url(#timeSeriesGradient)" 
                      activeDot={{ r: 8 }}
                      animationDuration={animationsEnabled ? 1500 : 0}
                    />
                    <defs>
                      <linearGradient id="timeSeriesGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#8884d8" stopOpacity={0.8}/>
                        <stop offset="95%" stopColor="#8884d8" stopOpacity={0.1}/>
                      </linearGradient>
                    </defs>
                  </AreaChart>
                </ResponsiveContainer>
              ) : (
                <NoDataMessage message="No time series data available yet. This chart will show interaction patterns over time as your honeypot collects more data." />
              )}
            </div>
          </div>
        </div>
        
        {/* Recent Activity Table */}
        <div className="honeypot-recent-activity">
          <div className="honeypot-section-header">
            <h3>
              <FaHistory className="honeypot-section-icon" />
              Recent Honeypot Activity
            </h3>
            <button 
              className="honeypot-view-all-btn"
              onClick={() => {
                setViewMode("interactions");
                fetchInteractions();
              }}
            >
              View All <FaAngleRight />
            </button>
          </div>
          
          <div className="honeypot-table-container">
            {dataToUse.recent_activity && dataToUse.recent_activity.length > 0 ? (
              <table className="honeypot-data-table">
                <thead>
                  <tr>
                    <th>Time</th>
                    <th>IP Address</th>
                    <th>Path</th>
                    <th>Type</th>
                    <th>Threat</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {dataToUse.recent_activity.slice(0, 10).map((activity, index) => {

                    const threatLevel = getThreatLevel(activity);
                    const threatIcon = getThreatIcon(threatLevel);
                    
                    return (
                      <tr key={index} className={`honeypot-activity-row honeypot-threat-level-${threatLevel}`}>
                        <td data-label="Time">
                          <div className="honeypot-timestamp">
                            <FaClock className="honeypot-timestamp-icon" />
                            {formatRelativeTime(activity.timestamp)}
                          </div>
                        </td>
                        <td data-label="IP Address">
                          <div className="honeypot-ip-address">
                            <FaGlobe className="honeypot-ip-icon" />
                            {activity.ip || activity.ip_address}
                          </div>
                        </td>
                        <td data-label="Path" className="honeypot-path-cell">
                          <div className="honeypot-path-container" title={activity.path}>
                            <FaLink className="honeypot-path-icon" />
                            <span className="honeypot-path-text">{activity.path}</span>
                          </div>
                        </td>
                        <td data-label="Type">
                          <span className={`honeypot-type-badge ${activity.interaction_type || activity.type || 'page_view'}`}>
                            {activity.interaction_type || activity.type || "page_view"}
                          </span>
                        </td>
                        <td data-label="Threat">
                          <div className="honeypot-threat-indicator">
                            {threatIcon}
                            <span className={`honeypot-threat-label honeypot-threat-${threatLevel}`}>
                              {threatLevel}
                            </span>
                          </div>
                        </td>
                        <td data-label="Action">
                          <button 
                            className="honeypot-action-btn"
                            onClick={() => {
                              console.log("Viewing details for activity:", activity._id);
                              fetchInteractionDetails(activity._id);
                            }}
                            title="View complete details"
                          >
                            <FaEye className="honeypot-action-icon" />
                            <span>Details</span>
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            ) : (
              <EmptyState 
                message="No recent activity found. The honeypot might not have captured any interactions yet."
                icon={FaSpider}
              />
            )}
          </div>
        </div>
      </div>
    );
  };

  const renderInteractionsContent = () => {
    return (
      <div className="honeypot-interactions-container">
        <div className="honeypot-interactions-header">
          <h3 className="honeypot-interactions-title">
            <FaSpider className="honeypot-header-icon" />
            Honeypot Interactions
          </h3>
          <div className="honeypot-interactions-actions">
            <button 
              className="honeypot-back-btn" 
              onClick={() => setViewMode("overview")}
            >
              <FaArrowLeft /> Back to Overview
            </button>
            <button 
              className="honeypot-filter-toggle-btn"
              onClick={() => setIsFilterVisible(!isFilterVisible)}
              title={isFilterVisible ? "Hide filters" : "Show filters"}
            >
              <FaFilter /> {isFilterVisible ? "Hide Filters" : "Show Filters"}
            </button>
            <button 
              className="honeypot-export-btn" 
              onClick={exportData}
              disabled={interactions.length === 0}
              title="Export data as JSON file"
            >
              <FaDownload /> Export Data
            </button>
          </div>
        </div>
        
        {/* Filters - Collapsible */}
        <div className={`honeypot-filter-section ${isFilterVisible ? 'visible' : 'hidden'}`}>
          <div className="honeypot-filter-container">
            <div className="honeypot-filter-field">
              <label>Filter By:</label>
              <div className="honeypot-filter-input-wrapper">
                <FaSearch className="honeypot-filter-icon" />
                <input 
                  type="text" 
                  className="honeypot-filter-input" 
                  placeholder="IP, path, user agent..." 
                  value={filter}
                  onChange={handleFilterChange}
                  onKeyDown={(e) => e.key === 'Enter' && applyFilter()}
                />
                {filter && (
                  <button 
                    className="honeypot-clear-filter-btn" 
                    onClick={() => setFilter("")}
                    title="Clear search text"
                  >
                    <FaTimes />
                  </button>
                )}
              </div>
              <button 
                className="honeypot-apply-filter-btn" 
                onClick={applyFilter}
                title="Apply filter to results"
              >
                Apply Filter
              </button>
            </div>
            
            <div className="honeypot-filter-field">
              <label>Category:</label>
              <select 
                className="honeypot-filter-select"
                value={filterCategory}
                onChange={(e) => setFilterCategory(e.target.value)}
                title="Filter by interaction type"
              >
                <option value="all">All Categories</option>
                <option value="admin_panel">Admin Panel</option>
                <option value="wordpress">WordPress</option>
                <option value="phpmyadmin">phpMyAdmin</option>
                <option value="cpanel">cPanel</option>
                <option value="database_endpoints">Database</option>
                <option value="remote_access">Remote Access</option>
                <option value="backdoors_and_shells">Backdoors/Shells</option>
                <option value="injection_attempts">Injection Attempts</option>
              </select>
              <button 
                className="honeypot-reset-filter-btn" 
                onClick={clearFilter}
                title="Reset all filters"
              >
                <FaSync className="honeypot-reset-icon" /> Reset
              </button>
            </div>
          </div>
          
          <div className="honeypot-results-info">
            Showing {interactions.length} of {totalInteractions.toLocaleString()} interactions
          </div>
        </div>
        
        {/* Interactions Table */}
        <div className="honeypot-interactions-table-container">
          {interactionsLoading ? (
            <LoadingPlaceholder
              height="300px"
              message="Loading interactions..."
              type="wave"
            />
          ) : interactions.length > 0 ? (
            <>
              <table className="honeypot-data-table">
                <thead>
                  <tr>
                    <th 
                      className="honeypot-sortable-header" 
                      onClick={() => handleSort("timestamp")}
                      title="Sort by timestamp"
                    >
                      Time {renderSortIndicator("timestamp")}
                    </th>
                    <th 
                      className="honeypot-sortable-header" 
                      onClick={() => handleSort("ip_address")}
                      title="Sort by IP address"
                    >
                      IP Address {renderSortIndicator("ip_address")}
                    </th>
                    <th 
                      className="honeypot-sortable-header" 
                      onClick={() => handleSort("page_type")}
                      title="Sort by page type"
                    >
                      Page Type {renderSortIndicator("page_type")}
                    </th>
                    <th 
                      className="honeypot-sortable-header" 
                      onClick={() => handleSort("interaction_type")}
                      title="Sort by interaction type"
                    >
                      Interaction {renderSortIndicator("interaction_type")}
                    </th>
                    <th>Details</th>
                    <th>Threat</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {interactions.map((interaction, index) => {
                    // Determine threat level
                    const threatLevel = getThreatLevel(interaction);
                    const threatIcon = getThreatIcon(threatLevel);
                    const summary = getInteractionSummary(interaction);
                    
                    return (
                      <tr key={index} className={`honeypot-interaction-row honeypot-threat-level-${threatLevel}`}>
                        <td data-label="Time">
                          <div className="honeypot-timestamp">
                            <FaClock className="honeypot-timestamp-icon" />
                            {formatTimestamp(interaction.timestamp)}
                          </div>
                        </td>
                        <td data-label="IP Address">
                          <div className="honeypot-ip-address">
                            <FaGlobe className="honeypot-ip-icon" />
                            {interaction.ip_address}
                            {interaction.is_tor_or_proxy && (
                              <span className="honeypot-tor-proxy-tag" title="TOR/Proxy detected">
                                <FaUserSecret />
                              </span>
                            )}
                          </div>
                        </td>
                        <td data-label="Page Type">
                          <span className={`honeypot-page-type-badge ${interaction.page_type}`}>
                            {interaction.page_type || "unknown"}
                          </span>
                        </td>
                        <td data-label="Interaction">
                          <span className={`honeypot-interaction-type-badge ${interaction.interaction_type}`}>
                            {interaction.interaction_type || "unknown"}
                          </span>
                        </td>
                        <td data-label="Details" className="honeypot-details-summary">
                          {summary}
                        </td>
                        <td data-label="Threat">
                          <div className="honeypot-threat-indicator">
                            {threatIcon}
                            <span className={`honeypot-threat-label honeypot-threat-${threatLevel}`}>
                              {threatLevel}
                            </span>
                          </div>
                        </td>
                        <td data-label="Action">
                          <button 
                            className="honeypot-view-details-btn"
                            onClick={() => {
                              console.log("View details clicked for:", interaction._id);
                              fetchInteractionDetails(interaction._id);
                            }}
                            title="View complete details"
                          >
                            <FaEye className="honeypot-action-icon" />
                            Details
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
              
              {/* Pagination */}
              <div className="honeypot-pagination">
                <button 
                  className="honeypot-page-btn" 
                  disabled={page === 1}
                  onClick={() => handlePageChange(1)}
                  title="Go to first page"
                >
                  First
                </button>
                <button 
                  className="honeypot-page-btn" 
                  disabled={page === 1}
                  onClick={() => handlePageChange(page - 1)}
                  title="Go to previous page"
                >
                  Previous
                </button>
                
                <span className="honeypot-page-info">
                  Page {page} of {Math.ceil(totalInteractions / limit) || 1}
                </span>
                
                <button 
                  className="honeypot-page-btn" 
                  disabled={page >= Math.ceil(totalInteractions / limit)}
                  onClick={() => handlePageChange(page + 1)}
                  title="Go to next page"
                >
                  Next
                </button>
                <button 
                  className="honeypot-page-btn" 
                  disabled={page >= Math.ceil(totalInteractions / limit)}
                  onClick={() => handlePageChange(Math.ceil(totalInteractions / limit) || 1)}
                  title="Go to last page"
                >
                  Last
                </button>
                
                <select 
                  className="honeypot-limit-select"
                  value={limit}
                  onChange={(e) => setLimit(Number(e.target.value))}
                  title="Items per page"
                >
                  <option value="10">10 per page</option>
                  <option value="20">20 per page</option>
                  <option value="50">50 per page</option>
                  <option value="100">100 per page</option>
                </select>
              </div>
            </>
          ) : (
            <EmptyState 
              message="No interactions found matching your criteria. Try adjusting your filters or check back after your honeypot has collected more data."
              icon={FaSpider}
            />
          )}
        </div>
      </div>
    );
  };

  const renderDetailsContent = () => {
    if (!selectedInteraction) {
      return (
        <div className="honeypot-no-selection">
          <FaExclamationTriangle className="honeypot-no-selection-icon" />
          <p>No interaction selected.</p>
          <button 
            className="honeypot-back-btn"
            onClick={() => setViewMode("interactions")}
          >
            <FaArrowLeft /> Back to Interactions
          </button>
        </div>
      );
    }
    
    const additionalData = selectedInteraction.additional_data || {};
    const explanations = selectedInteraction.explanations || {};
    const threatLevel = getThreatLevel(selectedInteraction);
    
    return (
      <div className="honeypot-details-container">
        <div className="honeypot-details-header">
          <h3 className="honeypot-details-title">
            {getThreatIcon(threatLevel)}
            Interaction Details
            <span className={`honeypot-details-id-badge honeypot-threat-${threatLevel}`}>
              ID: {selectedInteraction._id.substring(0, 8)}...
            </span>
          </h3>
          <div className="honeypot-details-actions">
            <button 
              className="honeypot-back-btn"
              onClick={() => setViewMode("interactions")}
            >
              <FaArrowLeft /> Back to Interactions
            </button>
            <button
              className="honeypot-copy-btn"
              onClick={() => {
                const jsonStr = JSON.stringify(selectedInteraction, null, 2);
                navigator.clipboard.writeText(jsonStr);
              }}
              title="Copy full interaction data as JSON"
            >
              <FaClipboard /> Copy JSON
            </button>
          </div>
        </div>
        
        {/* Interaction metadata */}
        <div className="honeypot-details-meta">
          <div className="honeypot-meta-item">
            <span className="honeypot-meta-label">Timestamp:</span>
            <span className="honeypot-meta-value">
              {formatTimestamp(selectedInteraction.timestamp)}
            </span>
          </div>
          <div className="honeypot-meta-item">
            <span className="honeypot-meta-label">IP Address:</span>
            <span className="honeypot-meta-value honeypot-meta-ip">
              {selectedInteraction.ip_address}
              {selectedInteraction.is_tor_or_proxy && (
                <span className="honeypot-tor-badge" title="Using TOR/Proxy">
                  <FaUserSecret />
                </span>
              )}
            </span>
          </div>
          <div className="honeypot-meta-item">
            <span className="honeypot-meta-label">Page Type:</span>
            <span className="honeypot-meta-value">
              <span className={`honeypot-page-type-badge ${selectedInteraction.page_type}`}>
                {selectedInteraction.page_type || "unknown"}
              </span>
            </span>
          </div>
          <div className="honeypot-meta-item">
            <span className="honeypot-meta-label">Interaction Type:</span>
            <span className="honeypot-meta-value">
              <span className={`honeypot-interaction-type-badge ${selectedInteraction.interaction_type}`}>
                {selectedInteraction.interaction_type || "unknown"}
              </span>
            </span>
          </div>
          {selectedInteraction.geoInfo && (
            <div className="honeypot-meta-item">
              <span className="honeypot-meta-label">Location:</span>
              <span className="honeypot-meta-value honeypot-meta-location">
                <FaGlobe className="honeypot-meta-icon" />
                {selectedInteraction.geoInfo.country || "Unknown"} 
                {selectedInteraction.geoInfo.asn && ` (${selectedInteraction.geoInfo.asn})`}
              </span>
            </div>
          )}
          <div className="honeypot-meta-item">
            <span className="honeypot-meta-label">Threat Level:</span>
            <span className={`honeypot-meta-value honeypot-threat-${threatLevel}`}>
              {getThreatIcon(threatLevel)}
              {threatLevel.toUpperCase()}
            </span>
          </div>
        </div>
        
        {/* Human-readable explanation */}
        {explanations && Object.keys(explanations).length > 0 && (
          <div className="honeypot-details-section">
            <h4 className="honeypot-section-title">
              <FaShieldAlt className="honeypot-section-icon" />
              Security Analysis
            </h4>
            <div className="honeypot-explanation-box">
              <p><strong>What happened:</strong> {explanations.summary}</p>
              
              <p><strong>Page Type:</strong> {explanations.page_type}</p>
              
              <p><strong>Interaction Type:</strong> {explanations.interaction_type}</p>
              
              <h5>Security Analysis:</h5>
              <ul className="honeypot-suspicious-factors">
                {explanations.suspicious_factors.map((factor, index) => (
                  <li key={index}>{factor}</li>
                ))}
              </ul>
              
              <p><em>{explanations.technical_details}</em></p>
            </div>
          </div>
        )}

        {/* Browser Information Section */}
        <div className="honeypot-details-section">
          <h4 className="honeypot-section-title">
            <FaUser className="honeypot-section-icon" />
            Browser Information
          </h4>
          <div className="honeypot-details-table-container">
            <table className="honeypot-details-table">
              <tbody>
                <tr>
                  <td>User Agent</td>
                  <td>{selectedInteraction.user_agent || "Unknown"}</td>
                </tr>
                <tr>
                  <td>Referer</td>
                  <td>{selectedInteraction.referer || "None"}</td>
                </tr>
                <tr>
                  <td>Path</td>
                  <td>
                    <div className="honeypot-request-path">
                      <FaLink className="honeypot-path-icon" />
                      {selectedInteraction.path || "Unknown"}
                    </div>
                  </td>
                </tr>
                <tr>
                  <td>HTTP Method</td>
                  <td>
                    <span className="honeypot-http-method">
                      {selectedInteraction.http_method || "Unknown"}
                    </span>
                  </td>
                </tr>
                {selectedInteraction.ua_info && (
                  <>
                    <tr>
                      <td>Browser</td>
                      <td>
                        {selectedInteraction.ua_info.browser?.family || "Unknown"} 
                        {selectedInteraction.ua_info.browser?.version && 
                          ` (${selectedInteraction.ua_info.browser.version})`}
                      </td>
                    </tr>
                    <tr>
                      <td>Operating System</td>
                      <td>
                        {selectedInteraction.ua_info.os?.family || "Unknown"}
                        {selectedInteraction.ua_info.os?.version && 
                          ` (${selectedInteraction.ua_info.os.version})`}
                      </td>
                    </tr>
                    <tr>
                      <td>Device Type</td>
                      <td>
                        {selectedInteraction.ua_info.is_mobile ? "Mobile" : 
                         selectedInteraction.ua_info.is_tablet ? "Tablet" : 
                         selectedInteraction.ua_info.is_pc ? "Desktop" : "Unknown"}
                      </td>
                    </tr>
                    <tr>
                      <td>Is Bot</td>
                      <td>{selectedInteraction.ua_info.is_bot ? "Yes" : "No"}</td>
                    </tr>
                  </>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Threat Intelligence Section */}
        <div className="honeypot-details-section">
          <h4 className="honeypot-section-title">
            <FaShieldAlt className="honeypot-section-icon" />
            Threat Intelligence
          </h4>
          <div className="honeypot-details-table-container">
            <table className="honeypot-details-table">
              <tbody>
                <tr>
                  <td>Using Proxy/Tor</td>
                  <td>
                    <span className={`honeypot-status-indicator ${selectedInteraction.is_tor_or_proxy ? 'warning' : 'safe'}`}>
                      {selectedInteraction.is_tor_or_proxy ? "Yes" : "No"}
                    </span>
                  </td>
                </tr>
                <tr>
                  <td>Bot Indicators</td>
                  <td>
                    {selectedInteraction.bot_indicators && selectedInteraction.bot_indicators.length ? (
                      <ul className="honeypot-bot-indicators-list">
                        {selectedInteraction.bot_indicators.map((indicator, idx) => (
                          <li key={idx} className="honeypot-bot-indicator-item">
                            <FaRobot className="honeypot-bot-icon" />
                            {indicator}
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <span className="honeypot-status-indicator safe">None detected</span>
                    )}
                  </td>
                </tr>
                <tr>
                  <td>Is Scanner</td>
                  <td>
                    <span className={`honeypot-status-indicator ${selectedInteraction.is_scanner ? 'danger' : 'safe'}`}>
                      {selectedInteraction.is_scanner ? "Yes" : "No"}
                    </span>
                  </td>
                </tr>
                <tr>
                  <td>Port Scan</td>
                  <td>
                    <span className={`honeypot-status-indicator ${selectedInteraction.is_port_scan ? 'danger' : 'safe'}`}>
                      {selectedInteraction.is_port_scan ? "Yes" : "No"}
                    </span>
                  </td>
                </tr>
                <tr>
                  <td>Suspicious Parameters</td>
                  <td>
                    <span className={`honeypot-status-indicator ${selectedInteraction.suspicious_params ? 'danger' : 'safe'}`}>
                      {selectedInteraction.suspicious_params ? "Yes" : "No"}
                    </span>
                  </td>
                </tr>
                {selectedInteraction.notes && selectedInteraction.notes.length > 0 && (
                  <tr>
                    <td>Security Notes</td>
                    <td>
                      <ul className="honeypot-security-notes">
                        {Array.isArray(selectedInteraction.notes) 
                          ? selectedInteraction.notes.map((note, idx) => (
                              <li key={idx} className="honeypot-security-note-item">{note}</li>
                            ))
                          : selectedInteraction.notes
                        }
                      </ul>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
        
        {/* Location Information */}
        <div className="honeypot-details-section">
          <h4 className="honeypot-section-title">
            <FaLocationArrow className="honeypot-section-icon" />
            Location Information
          </h4>
          <div className="honeypot-details-table-container">
            <table className="honeypot-details-table">
              <tbody>
                <tr>
                  <td>Country</td>
                  <td>
                    <div className="honeypot-country-info">
                      <FaGlobe className="honeypot-country-icon" />
                      {selectedInteraction.geoInfo?.country || "Unknown"}
                    </div>
                  </td>
                </tr>
                <tr>
                  <td>ASN</td>
                  <td>{selectedInteraction.geoInfo?.asn || "Unknown"}</td>
                </tr>
                <tr>
                  <td>Organization</td>
                  <td>{selectedInteraction.geoInfo?.org || "Unknown"}</td>
                </tr>
                <tr>
                  <td>Hostname</td>
                  <td>
                    <div className="honeypot-hostname">
                      <FaServer className="honeypot-hostname-icon" />
                      {selectedInteraction.hostname || "Not resolved"}
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        
        {/* Additional Details */}
        {additionalData && Object.keys(additionalData).length > 0 && (
          <div className="honeypot-details-section">
            <h4 className="honeypot-section-title">
              <FaDatabase className="honeypot-section-icon" />
              Additional Data
            </h4>
            <div className="honeypot-details-table-container">
              <table className="honeypot-details-table">
                <tbody>
                  {Object.entries(additionalData).map(([key, value]) => (
                    <tr key={key}>
                      <td>{key.replace(/_/g, ' ')}</td>
                      <td>
                        {typeof value === 'object' ? (
                          <pre className="honeypot-json-snippet">
                            {JSON.stringify(value, null, 2)}
                          </pre>
                        ) : (
                          String(value)
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
        
        {/* Request Headers */}
        {selectedInteraction.headers && Object.keys(selectedInteraction.headers).length > 0 && (
          <div className="honeypot-details-section">
            <h4 className="honeypot-section-title">
              <FaCode className="honeypot-section-icon" />
              HTTP Headers
            </h4>
            <div className="honeypot-details-table-container">
              <table className="honeypot-details-table">
                <tbody>
                  {Object.entries(selectedInteraction.headers).map(([key, value]) => (
                    <tr key={key}>
                      <td>{key}</td>
                      <td>{value}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
        
        {/* Raw JSON Viewer */}
        <div className="honeypot-details-section">
          <h4 className="honeypot-section-title">
            <FaFileAlt className="honeypot-section-icon" />
            Raw JSON Data
          </h4>
          <div className="honeypot-details-json">
            <JsonSyntaxHighlighter json={selectedInteraction} maxHeight="500px" />
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="admin-tab-content honeypot-tab">
      <div className="admin-content-header">
        <h2><FaSpider /> Honeypot Dashboard</h2>
        <div className="honeypot-header-actions">
          <button 
            className={`honeypot-action-btn ${viewMode === "overview" ? "active" : ""}`}
            onClick={() => setViewMode("overview")}
          >
            <FaChartBar /> Overview
          </button>
          <button 
            className={`honeypot-action-btn ${viewMode === "interactions" ? "active" : ""}`}
            onClick={() => {
              console.log("Switching to interactions view");
              setViewMode("interactions");
              fetchInteractions();
            }}
          >
            <FaSpider /> Interactions
          </button>
          <button 
            className="honeypot-refresh-btn" 
            onClick={() => {
              console.log("Refresh button clicked");
              setRetryCount(0); 
              fetchHoneypotData();
              fetchDetailedStats();
              if (viewMode === "interactions") {
                fetchInteractions();
              }
            }}
            disabled={loading}
          >
            {loading ? <FaSpinner className="honeypot-spinner" /> : <FaSync />} Refresh
          </button>
        </div>
      </div>
      
      {renderContent()}
    </div>
  );
};

export default HoneypotTab;
