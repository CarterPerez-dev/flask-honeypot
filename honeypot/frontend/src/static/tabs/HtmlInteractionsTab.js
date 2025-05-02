// Enhanced HtmlInteractionsTab.js
import React, { useState, useEffect, useCallback } from "react";
import { 
  FaCode, FaSync, FaSpinner, FaExclamationTriangle, 
  FaFilter, FaSearch, FaTable, FaChartBar, FaDownload, 
  FaAngleRight, FaClock, FaLocationArrow, FaFingerprint, 
  FaUser, FaKey, FaShieldAlt, FaSortUp, FaSortDown, FaSort,
  FaEye, FaGlobe, FaLock, FaDatabase, FaBullseye, FaTimes,
  FaArrowLeft, FaServer, FaNetworkWired, FaSignature, 
  FaMagic, FaLaptopCode, FaBug
} from "react-icons/fa";
import { adminFetch } from '../../components/csrfHelper';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, 
  ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line, 
  AreaChart, Area
} from 'recharts';
import { formatTimestamp } from '../../utils/dateUtils';
import JsonSyntaxHighlighter from '../../components/JsonSyntaxHighlighter';

// Custom tooltip component for charts
const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="html-custom-tooltip">
        <p className="html-tooltip-label">{label}</p>
        <p className="html-tooltip-value">
          <span className="html-tooltip-count">{payload[0].value}</span> interactions
        </p>
      </div>
    );
  }
  return null;
};

// Component to display when data is loading
const LoadingIndicator = ({ message = "Loading data..." }) => (
  <div className="html-loading-container">
    <FaSpinner className="html-spinner" />
    <p>{message}</p>
  </div>
);

// Component for empty states
const EmptyState = ({ message = "No data available" }) => (
  <div className="html-no-data">
    <FaExclamationTriangle />
    <p>{message}</p>
  </div>
);

const HtmlInteractionsTab = () => {
  const [interactions, setInteractions] = useState([]);
  const [stats, setStats] = useState(null);
  const [selectedInteraction, setSelectedInteraction] = useState(null);
  const [loading, setLoading] = useState(true);
  const [statsLoading, setStatsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [viewMode, setViewMode] = useState("overview"); 
  

  const [pageType, setPageType] = useState("all");
  const [interactionType, setInteractionType] = useState("all");
  const [searchTerm, setSearchTerm] = useState("");
  const [pageTypes, setPageTypes] = useState([]);
  const [interactionTypes, setInteractionTypes] = useState([]);
  

  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(20);
  const [total, setTotal] = useState(0);
  

  const [sortField, setSortField] = useState("timestamp");
  const [sortOrder, setSortOrder] = useState("desc");
  

  const CHART_COLORS = [
    '#291efc', '#02d63b', '#e89a02', '#ff6114', '#f20202', 
    '#0fa7fc', '#fa1b6a', '#972ffa', '#f7d111', '#3dfcca'
  ];
  

  const [animationsEnabled, setAnimationsEnabled] = useState(true);

  useEffect(() => {
    console.log("HTML Interactions Tab mounted");
    

    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    setAnimationsEnabled(!prefersReducedMotion);


    window.addEventListener('focus', handleWindowFocus);
    
    return () => {
      console.log("HTML Interactions Tab unmounted");
      window.removeEventListener('focus', handleWindowFocus);
    };
  }, []);
  

  const handleWindowFocus = () => {
    if (viewMode === "overview") {
      const lastRefresh = localStorage.getItem('htmlTabLastRefresh');
      const now = Date.now();
      if (!lastRefresh || now - parseInt(lastRefresh) > 5 * 60 * 1000) {
        fetchStats();
        localStorage.setItem('htmlTabLastRefresh', now.toString());
      }
    }
  };
  
  useEffect(() => {
    console.log("viewMode changed to:", viewMode);
  }, [viewMode]);
  
  useEffect(() => {
    if (stats) {
      console.log("Stats updated:", stats);
    }
  }, [stats]);

  const fetchInteractions = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const queryParams = new URLSearchParams({
        page,
        limit,
        sort_field: sortField,
        sort_order: sortOrder,
        page_type: pageType !== "all" ? pageType : "",
        interaction_type: interactionType !== "all" ? interactionType : "",
        search: searchTerm,
      });
      
      const response = await adminFetch(`/api/honeypot/html-interactions?${queryParams.toString()}`);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch interactions: ${response.status} ${response.statusText}`);
      }
      
      const data = await response.json();
      
      setInteractions(data.interactions || []);
      setTotal(data.total || 0);
      setPageTypes(data.page_types || []);
      setInteractionTypes(data.interaction_types || []);
      
    } catch (err) {
      console.error("Error fetching interactions:", err);
      setError(err.message || "Failed to fetch interactions");
    } finally {
      setLoading(false);
    }
  }, [page, limit, sortField, sortOrder, pageType, interactionType, searchTerm]);


  const fetchStats = useCallback(async () => {
    setStatsLoading(true);
    
    try {
      console.log("Fetching HTML interaction stats...");

      const response = await adminFetch("/api/honeypot/detailed-stats");
      
      if (!response.ok) {
        throw new Error(`Failed to fetch statistics: ${response.status} ${response.statusText}`);
      }
      

      const text = await response.text();
      console.log("Raw stats response:", text);
      
      try {
        const data = JSON.parse(text);
        console.log("Parsed stats data:", data);
        

        if (data.time_series && Array.isArray(data.time_series)) {

          data.time_series = data.time_series
            .map(item => ({
              ...item,
              date: typeof item.date === 'string' ? item.date : new Date(item.date).toISOString().split('T')[0],
              count: Number(item.count) || 0
            }))
            .sort((a, b) => new Date(a.date) - new Date(b.date));
        }
        
        setStats(data);
      } catch (parseError) {
        console.error("Error parsing stats response:", parseError);
        

        setStats({
          total_interactions: 0,
          today_interactions: 0,
          week_interactions: 0,
          month_interactions: 0,
          page_type_stats: [],
          interaction_types: [],
          top_interactors: [],
          credential_attempts: [],
          time_series: []
        });
        
        throw new Error("Failed to parse statistics response");
      }
    } catch (err) {
      console.error("Error fetching statistics:", err);
      

      try {
        console.log("Trying to fetch from regular interactions endpoint as fallback...");
        const fallbackResponse = await adminFetch("/api/honeypot/html-interactions?page=1&limit=100");
        
        if (fallbackResponse.ok) {
          const fallbackData = await fallbackResponse.json();
          console.log("Fallback data:", fallbackData);
          
          if (fallbackData.interactions && fallbackData.interactions.length > 0) {
            const improvStats = {
              total_interactions: fallbackData.total || fallbackData.interactions.length,
              today_interactions: fallbackData.interactions.filter(i => 
                new Date(i.timestamp).toDateString() === new Date().toDateString()
              ).length,
              week_interactions: fallbackData.interactions.length,
              month_interactions: fallbackData.interactions.length,
              credential_attempts: fallbackData.interactions.filter(i => 
                i.interaction_type === "login_attempt"
              ),
              page_types: Array.from(
                new Set(fallbackData.interactions.map(i => i.page_type))
              ).map(type => ({
                _id: type,
                count: fallbackData.interactions.filter(i => i.page_type === type).length
              })),
              interaction_types: Array.from(
                new Set(fallbackData.interactions.map(i => i.interaction_type))
              ).map(type => ({
                _id: type, 
                count: fallbackData.interactions.filter(i => i.interaction_type === type).length
              }))
            };
            
            console.log("Improvised stats:", improvStats);
            setStats(improvStats);
          }
        }
      } catch (fallbackErr) {
        console.error("Fallback stats retrieval also failed:", fallbackErr);
      }
    } finally {
      setStatsLoading(false);
      setLoading(false);
    }
  }, []);

  
  const fetchInteractionDetails = useCallback(async (id) => {
    setLoading(true);
    
    try {
      console.log(`Fetching details for interaction ${id}`);
      
      const url = `/api/honeypot/html-interactions/${id}`;
      
      console.log("Request URL:", url);
      
      const response = await adminFetch(url);
      
      console.log(`Response status: ${response.status} ${response.statusText}`);
      console.log(`Response content type: ${response.headers.get('Content-Type')}`);
      

      const contentType = response.headers.get('Content-Type') || '';
      if (contentType.includes('text/html')) {
        console.error("Received HTML response instead of JSON");
        throw new Error("Server returned HTML instead of JSON. This might be a routing issue.");
      }
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error("Error response:", errorText);
        throw new Error(`Failed to fetch interaction details: ${response.status} ${response.statusText}`);
      }
      

      const text = await response.text();
      console.log("Raw response text:", text.substring(0, 100) + "...");
      
      try {
        const data = JSON.parse(text);
        console.log("Interaction details:", data);
        

        setViewMode("details");
        setSelectedInteraction(data);
      } catch (parseError) {
        console.error("JSON parse error:", parseError);
        console.error("Response was not valid JSON");
        throw new Error("Failed to parse server response as JSON");
      }
    } catch (err) {
      console.error("Error fetching interaction details:", err);
      
      // Fallback
      try {
        console.log("Trying fallback approach to get interaction details");
        const allInteractionsResponse = await adminFetch("/api/honeypot/html-interactions?limit=100");
        if (allInteractionsResponse.ok) {
          const allData = await allInteractionsResponse.json();
          const foundInteraction = allData.interactions.find(item => 
            item._id === id || String(item._id) === id
          );
          
          if (foundInteraction) {
            console.log("Found interaction in all interactions:", foundInteraction);
            setViewMode("details");
            setSelectedInteraction(foundInteraction);
            return; 
          } else {
            console.error("Could not find interaction with ID:", id);
          }
        }
      } catch (fallbackError) {
        console.error("Fallback approach also failed:", fallbackError);
      }
      

      setError(`Error loading details: ${err.message || "Unknown error"}`);
    } finally {
      setLoading(false);
    }
  }, []);


  useEffect(() => {
    fetchStats();
  }, [fetchStats]);


  useEffect(() => {
    if (viewMode === "interactions") {
      fetchInteractions();
    }
  }, [fetchInteractions, viewMode, page, limit, sortField, sortOrder]);


  const applyFilters = () => {
    setPage(1);
    fetchInteractions();
  };


  const handleSearch = (e) => {
    if (e.key === 'Enter') {
      applyFilters();
    }
  };


  const resetFilters = () => {
    setPageType("all");
    setInteractionType("all");
    setSearchTerm("");
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
    

    fetchInteractions();
  };


  const renderSortIndicator = (field) => {
    if (sortField !== field) return <FaSort className="html-sort-icon" />;
    return sortOrder === "asc" ? 
      <FaSortUp className="html-sort-icon html-sort-active" /> : 
      <FaSortDown className="html-sort-icon html-sort-active" />;
  };


  const exportData = () => {
    try {
      const jsonData = JSON.stringify(interactions, null, 2);
      const blob = new Blob([jsonData], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      

      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const filename = `html-interactions-export-${timestamp}.json`;
      

      const link = document.createElement("a");
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      

      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Error exporting data:", err);
      setError("Failed to export data: " + err.message);
    }
  };


  const getInteractionDetails = (interaction) => {
    const additionalData = interaction.additional_data || {};
    
    switch (interaction.interaction_type) {
      case "login_attempt":
        return `Username: ${additionalData.username || "N/A"}, Password: ${additionalData.password || "N/A"}`;
      case "form_submit":
        return `Form data submitted: ${Object.keys(additionalData).length} fields`;
      case "button_click":
        return `Button: ${additionalData.button || additionalData.label || "Unknown"}`;
      case "terminal_command":
        return `Command: ${additionalData.command || "Unknown"}`;
      case "chat_message":
        return `Message: ${additionalData.message || "Unknown"}`;
      case "captcha_attempt":
        return `Captcha: ${additionalData.captcha_entered || "Unknown"}`;
      case "download_attempt":
        return `File: ${additionalData.filename || "Unknown"}`;
      case "sql_injection_attempt":
        return `SQL pattern detected in ${additionalData.input_field || "input"}`;
      default:
        if (additionalData.username && additionalData.password) {
          return `Username: ${additionalData.username}, Password: ${additionalData.password}`;
        }
        return `Additional data: ${Object.keys(additionalData).length} fields`;
    }
  };


  const renderContent = () => {
    if (loading && !interactions.length && !stats) {
      return <LoadingIndicator message="Loading data..." />;
    }

    if (error) {
      return (
        <div className="html-error-message">
          <FaExclamationTriangle /> Error: {error}
          <button 
            className="html-retry-btn" 
            onClick={() => {
              fetchStats();
              if (viewMode === "interactions") fetchInteractions();
            }}
          >
            Retry
          </button>
        </div>
      );
    }

    switch (viewMode) {
      case "overview":
        return renderOverview();
      case "interactions":
        return renderInteractionsList();
      case "details":
        return renderInteractionDetails();
      default:
        return renderOverview();
    }
  };


  const renderOverview = () => {
    if (statsLoading && !stats) {
      return <LoadingIndicator message="Loading statistics..." />;
    }
  
    // Use empty data structure if stats is null
    const statsData = stats || {
      total_interactions: 0,
      today_interactions: 0,
      week_interactions: 0,
      month_interactions: 0,
      page_types: [],
      interaction_types: [],
      top_ips: [],
      credential_attempts: [],
      time_series: []
    };
  

    const NoDataMessage = ({ message }) => (
      <div className="html-no-chart-data">
        <FaExclamationTriangle />
        <p>{message || "No data available yet. Check back after your honeypot has captured some interactions."}</p>
      </div>
    );


    const preparePageTypeData = () => {
      const sourceData = statsData.page_type_stats || statsData.page_types || [];
      
      return sourceData.map(item => ({
        name: (item._id || "unknown").replace(/_/g, ' '),
        value: item.count || 0,
        fullName: item._id || "unknown"
      })).sort((a, b) => b.value - a.value).slice(0, 8);
    };
    
    const prepareInteractionTypeData = () => {
      const sourceData = statsData.interaction_stats || statsData.interaction_types || [];
      
      return sourceData.map(item => ({
        name: (item._id || "unknown").replace(/_/g, ' '),
        value: item.count || 0,
        fullName: item._id || "unknown"
      })).sort((a, b) => b.value - a.value);
    };
    
    const prepareTimeSeriesData = () => {
      if (!statsData.time_series || !Array.isArray(statsData.time_series) || statsData.time_series.length === 0) {
        const today = new Date();
        const data = [];
        for (let i = 30; i >= 0; i--) {
          const date = new Date(today);
          date.setDate(date.getDate() - i);
          data.push({
            date: date.toISOString().split('T')[0],
            count: 0
          });
        }
        return data;
      }
      
      return statsData.time_series.map(item => ({
        date: item.date,
        count: item.count || 0
      }));
    };
    

    const pageTypeData = preparePageTypeData();
    const interactionTypeData = prepareInteractionTypeData();
    const timeSeriesData = prepareTimeSeriesData();

    return (
      <div className="html-overview-container">
        {/* Stats Cards */}
        <div className="html-stats-cards">
          <div className="html-stat-card">
            <div className="html-stat-icon">
              <FaCode />
            </div>
            <div className="html-stat-content">
              <div className="html-stat-value">{statsData.total_interactions.toLocaleString()}</div>
              <div className="html-stat-label">Total Interactions</div>
            </div>
          </div>
          
          <div className="html-stat-card">
            <div className="html-stat-icon">
              <FaClock />
            </div>
            <div className="html-stat-content">
              <div className="html-stat-value">{statsData.today_interactions.toLocaleString()}</div>
              <div className="html-stat-label">Today's Interactions</div>
            </div>
          </div>
          
          <div className="html-stat-card">
            <div className="html-stat-icon">
              <FaUser />
            </div>
            <div className="html-stat-content">
              <div className="html-stat-value">
                {statsData.week_interactions.toLocaleString()}
              </div>
              <div className="html-stat-label">This Week</div>
            </div>
          </div>
          
          <div className="html-stat-card">
            <div className="html-stat-icon">
              <FaKey />
            </div>
            <div className="html-stat-content">
              <div className="html-stat-value">
                {statsData.credential_attempts ? statsData.credential_attempts.length.toLocaleString() : 0}
              </div>
              <div className="html-stat-label">Credential Harvesting</div>
            </div>
          </div>
        </div>
        
        {/* Charts */}
        <div className="html-charts-container">
          {/* Page Types Chart */}
          <div className="html-chart-card">
            <h3 className="html-chart-title">Most Active Pages</h3>
            <div className="html-chart-content">
              {pageTypeData && pageTypeData.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart 
                    data={pageTypeData} 
                    margin={{ top: 20, right: 30, left: 20, bottom: 70 }}
                    barSize={36}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                    <XAxis 
                      dataKey="name" 
                      angle={-45} 
                      textAnchor="end"
                      tick={{fill: 'var(--html-text-secondary)'}}
                      height={70}
                      tickFormatter={(value) => value.length > 15 ? `${value.substring(0, 12)}...` : value}
                    />
                    <YAxis tick={{fill: 'var(--html-text-secondary)'}} />
                    <Tooltip 
                      content={<CustomTooltip />}
                      cursor={{fill: 'rgba(255, 255, 255, 0.1)'}}
                    />
                    <Bar 
                      dataKey="value" 
                      name="Interactions" 
                      fill="url(#pageTypeGradient)"
                      radius={[4, 4, 0, 0]}
                      animationDuration={animationsEnabled ? 1000 : 0}
                    >
                      {pageTypeData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                      ))}
                    </Bar>
                    <defs>
                      <linearGradient id="pageTypeGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#8884d8" stopOpacity={0.8}/>
                        <stop offset="100%" stopColor="#8884d8" stopOpacity={0.4}/>
                      </linearGradient>
                    </defs>
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <NoDataMessage message="No page type data available yet. This will populate as your honeypot captures interactions." />
              )}
            </div>
          </div>
        
          {/* Interaction Types Chart */}
          <div className="html-chart-card">
            <h3 className="html-chart-title">Interaction Types</h3>
            <div className="html-chart-content">
              {interactionTypeData && interactionTypeData.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={interactionTypeData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={100}
                      fill="#8884d8"
                      dataKey="value"
                      nameKey="name"
                      label={({name, percent}) => `${name}: ${(percent * 100).toFixed(0)}%`}
                      labelLine={true}
                      animationDuration={animationsEnabled ? 1000 : 0}
                      animationBegin={animationsEnabled ? 200 : 0}
                    >
                      {interactionTypeData.map((entry, index) => (
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
                        backgroundColor: 'var(--html-bg-card)',
                        border: '1px solid var(--html-border-light)',
                        borderRadius: '8px',
                        color: 'var(--html-text-primary)'
                      }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <NoDataMessage message="No interaction type data available yet. This chart will populate as your honeypot gathers more data." />
              )}
            </div>
          </div>
          
          {/* Time Series Chart */}
          <div className="html-chart-card html-full-width">
            <h3 className="html-chart-title">Interactions Over Time</h3>
            <div className="html-chart-content">
              {timeSeriesData && timeSeriesData.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart
                    data={timeSeriesData}
                    margin={{ top: 20, right: 30, left: 20, bottom: 20 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                    <XAxis 
                      dataKey="date" 
                      tick={{fill: 'var(--html-text-secondary)'}}
                      tickFormatter={(date) => {
                        const d = new Date(date);
                        return `${d.getMonth()+1}/${d.getDate()}`;
                      }}
                    />
                    <YAxis tick={{fill: 'var(--html-text-secondary)'}} />
                    <Tooltip 
                      formatter={(value) => [`${value} interactions`, 'Count']}
                      contentStyle={{
                        backgroundColor: 'var(--html-bg-card)',
                        border: '1px solid var(--html-border-light)',
                        borderRadius: '8px',
                        color: 'var(--html-text-primary)'
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
                      fill="url(#colorGradient)" 
                      activeDot={{ r: 8 }}
                      animationDuration={animationsEnabled ? 1500 : 0}
                    />
                    <defs>
                      <linearGradient id="colorGradient" x1="0" y1="0" x2="0" y2="1">
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
        
        {/* Credential Harvesting Table */}
        <div className="html-credentials-section">
          <h3 className="html-section-title">Recent Credential Harvesting Attempts</h3>
          
          <div className="html-table-container">
            {statsData.credential_attempts && statsData.credential_attempts.length > 0 ? (
              <table className="html-data-table">
                <thead>
                  <tr>
                    <th>Time</th>
                    <th>Page Type</th>
                    <th>Username</th>
                    <th>Password</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {statsData.credential_attempts.slice(0, 10).map((attempt, index) => {
                    const username = attempt.additional_data?.username || "N/A";
                    const password = attempt.additional_data?.password || "N/A";
                    
                    return (
                      <tr key={index}>
                        <td data-label="Time">
                          <div className="html-timestamp">
                            <FaClock className="html-timestamp-icon" />
                            {formatTimestamp(attempt.timestamp)}
                          </div>
                        </td>
                        <td data-label="Page Type">
                          <span className={`html-badge html-page-type-${attempt.page_type ? attempt.page_type.replace(/\s+/g, '_').toLowerCase() : 'unknown'}`}>
                            {attempt.page_type || "unknown"}
                          </span>
                        </td>
                        <td data-label="Username" className="html-credential">{username}</td>
                        <td data-label="Password" className="html-credential">{password}</td>
                        <td data-label="Actions">
                          <button 
                            className="html-view-details-btn"
                            onClick={() => fetchInteractionDetails(attempt._id)}
                            title="View full details of this interaction"
                          >
                            <FaEye /> View Details
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            ) : (
              <EmptyState message="No credential harvesting attempts recorded yet. This table will populate as attackers attempt to login to your honeypot." />
            )}
          </div>
          
          <div className="html-view-all-container">
            <button 
              className="html-view-all-btn"
              onClick={() => {
                setViewMode("interactions");
                setInteractionType("login_attempt");
                setPage(1);
                fetchInteractions();
              }}
            >
              View All Interactions <FaAngleRight />
            </button>
          </div>
        </div>
      </div>
    );
  };

  // Render list of interactions
  const renderInteractionsList = () => {
    return (
      <div className="html-interactions-container">
        <div className="html-interactions-header">
          <h3 className="html-interactions-title">HTML Page Interactions</h3>
          <div className="html-interactions-actions">
            <button 
              className="html-back-btn" 
              onClick={() => setViewMode("overview")}
            >
              <FaArrowLeft /> Back to Overview
            </button>
            <button 
              className="html-export-btn" 
              onClick={exportData}
              disabled={interactions.length === 0}
              title="Export interactions as JSON file"
            >
              <FaDownload /> Export Data
            </button>
          </div>
        </div>
        
        {/* Filters */}
        <div className="html-filter-section">
          <div className="html-filter-container">
            <div className="html-filter-fields">
              <div className="html-filter-field">
                <label>Page Type:</label>
                <select 
                  className="html-filter-select"
                  value={pageType}
                  onChange={(e) => setPageType(e.target.value)}
                >
                  <option value="all">All Pages</option>
                  {pageTypes.map((type, index) => (
                    <option key={index} value={type}>{type || "Unknown"}</option>
                  ))}
                </select>
              </div>
              
              <div className="html-filter-field">
                <label>Interaction Type:</label>
                <select 
                  className="html-filter-select"
                  value={interactionType}
                  onChange={(e) => setInteractionType(e.target.value)}
                >
                  <option value="all">All Interactions</option>
                  {interactionTypes.map((type, index) => (
                    <option key={index} value={type}>{type || "Unknown"}</option>
                  ))}
                </select>
              </div>
              
              <div className="html-filter-field html-search-box">
                <label>Search:</label>
                <div className="html-search-input-wrapper">
                  <FaSearch className="html-search-icon" />
                  <input 
                    type="text" 
                    className="html-search-input" 
                    placeholder="Search by IP, type, details, time..." 
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    onKeyDown={handleSearch}
                  />
                </div>
              </div>
            </div>
            
            <div className="html-filter-buttons">
              <button 
                className="html-apply-filter-btn" 
                onClick={applyFilters}
              >
                <FaFilter /> Apply Filters
              </button>
              <button 
                className="html-reset-filter-btn" 
                onClick={resetFilters}
              >
                <FaSync /> Reset
              </button>
            </div>
          </div>
          
          <div className="html-results-info">
            Showing {interactions.length} of {total.toLocaleString()} interactions
          </div>
        </div>
        
        {/* Interactions Table */}
        <div className="html-table-container">
          {loading ? (
            <LoadingIndicator message="Loading interactions..." />
          ) : interactions.length > 0 ? (
            <>
              <table className="html-data-table">
                <thead>
                  <tr>
                    <th 
                      className="html-sortable-header" 
                      onClick={() => handleSort("timestamp")}
                    >
                      Time {renderSortIndicator("timestamp")}
                    </th>
                    <th 
                      className="html-sortable-header" 
                      onClick={() => handleSort("page_type")}
                    >
                      Page Type {renderSortIndicator("page_type")}
                    </th>
                    <th 
                      className="html-sortable-header" 
                      onClick={() => handleSort("interaction_type")}
                    >
                      Interaction {renderSortIndicator("interaction_type")}
                    </th>
                    <th 
                      className="html-sortable-header" 
                      onClick={() => handleSort("ip_address")}
                    >
                      IP Address {renderSortIndicator("ip_address")}
                    </th>
                    <th>Details</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {interactions.map((interaction, index) => {
                    // Get key details from additional_data
                    const detailsText = getInteractionDetails(interaction);
                    
                    return (
                      <tr key={index} className="html-interaction-row">
                        <td data-label="Time">
                          <div className="html-timestamp">
                            <FaClock className="html-timestamp-icon" />
                            {formatTimestamp(interaction.timestamp)}
                          </div>
                        </td>
                        <td data-label="Page Type">
                          <span className={`html-badge html-page-type-${interaction.page_type ? interaction.page_type.replace(/\s+/g, '_').toLowerCase() : 'unknown'}`}>
                            {interaction.page_type || "unknown"}
                          </span>
                        </td>
                        <td data-label="Interaction">
                          <span className={`html-badge html-interaction-type-${interaction.interaction_type ? interaction.interaction_type.replace(/\s+/g, '_').toLowerCase() : 'unknown'}`}>
                            {interaction.interaction_type || "unknown"}
                          </span>
                        </td>
                        <td data-label="IP Address">{interaction.ip_address}</td>
                        <td data-label="Details" className="html-details-cell">{detailsText}</td>
                        <td data-label="Actions">
                          <button 
                            className="html-view-details-btn"
                            onClick={() => fetchInteractionDetails(interaction._id)}
                            title="View full details of this interaction"
                          >
                            <FaEye /> View
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
              
              {/* Pagination */}
              <div className="html-pagination">
                <button 
                  className="html-page-btn" 
                  disabled={page === 1}
                  onClick={() => setPage(1)}
                >
                  First
                </button>
                <button 
                  className="html-page-btn" 
                  disabled={page === 1}
                  onClick={() => setPage(page - 1)}
                >
                  Previous
                </button>
                
                <span className="html-page-info">
                  Page {page} of {Math.ceil(total / limit) || 1}
                </span>
                
                <button 
                  className="html-page-btn" 
                  disabled={page >= Math.ceil(total / limit)}
                  onClick={() => setPage(page + 1)}
                >
                  Next
                </button>
                <button 
                  className="html-page-btn" 
                  disabled={page >= Math.ceil(total / limit)}
                  onClick={() => setPage(Math.ceil(total / limit) || 1)}
                >
                  Last
                </button>
                
                <select 
                  className="html-limit-select"
                  value={limit}
                  onChange={(e) => setLimit(Number(e.target.value))}
                >
                  <option value="10">10 per page</option>
                  <option value="20">20 per page</option>
                  <option value="50">50 per page</option>
                  <option value="100">100 per page</option>
                </select>
              </div>
            </>
          ) : (
            <EmptyState message="No interactions found matching your criteria. Try adjusting your filters or check back after your honeypot has collected more data." />
          )}
        </div>
      </div>
    );
  };

  // Render detailed view of a single interaction
  const renderInteractionDetails = () => {
    if (!selectedInteraction) {
      return (
        <div className="html-no-selection">
          <FaExclamationTriangle />
          <p>No interaction selected.</p>
          <button 
            className="html-back-btn"
            onClick={() => setViewMode("interactions")}
          >
            <FaArrowLeft /> Back to Interactions
          </button>
        </div>
      );
    }
    
    const additionalData = selectedInteraction.additional_data || {};
    const explanations = selectedInteraction.explanations || {};
    
    return (
      <div className="html-details-container">
        <div className="html-details-header">
          <h3 className="html-details-title">
            Interaction Details
          </h3>
          <div className="html-details-actions">
            <button 
              className="html-back-btn"
              onClick={() => setViewMode("interactions")}
            >
              <FaArrowLeft /> Back to Interactions
            </button>
          </div>
        </div>
        
        {/* Interaction metadata */}
        <div className="html-details-meta">
          <div className="html-meta-item">
            <span className="html-meta-label">Timestamp:</span>
            <span className="html-meta-value">
              {formatTimestamp(selectedInteraction.timestamp)}
            </span>
          </div>
          <div className="html-meta-item">
            <span className="html-meta-label">IP Address:</span>
            <span className="html-meta-value">
              {selectedInteraction.ip_address}
            </span>
          </div>
          <div className="html-meta-item">
            <span className="html-meta-label">Page Type:</span>
            <span className="html-meta-value">
              <span className={`html-badge html-page-type-${selectedInteraction.page_type ? selectedInteraction.page_type.replace(/\s+/g, '_').toLowerCase() : 'unknown'}`}>
                {selectedInteraction.page_type || "unknown"}
              </span>
            </span>
          </div>
          <div className="html-meta-item">
            <span className="html-meta-label">Interaction Type:</span>
            <span className="html-meta-value">
              <span className={`html-badge html-interaction-type-${selectedInteraction.interaction_type ? selectedInteraction.interaction_type.replace(/\s+/g, '_').toLowerCase() : 'unknown'}`}>
                {selectedInteraction.interaction_type || "unknown"}
              </span>
            </span>
          </div>
          {selectedInteraction.geoInfo && (
            <div className="html-meta-item">
              <span className="html-meta-label">Location:</span>
              <span className="html-meta-value">
                {selectedInteraction.geoInfo.country || "Unknown"} 
                {selectedInteraction.geoInfo.asn && ` (${selectedInteraction.geoInfo.asn})`}
              </span>
            </div>
          )}
          {explanations && explanations.risk_level && (
            <div className="html-meta-item">
              <span className="html-meta-label">Risk Level:</span>
              <span className={`html-meta-value html-risk-${explanations.risk_level.level.toLowerCase()}`}>
                {explanations.risk_level.level}
              </span>
            </div>
          )}
        </div>
        
        {/* Human-readable explanation */}
        {explanations && Object.keys(explanations).length > 0 && (
          <div className="html-details-section">
            <h4 className="html-section-title">
              <FaShieldAlt /> Analysis
            </h4>
            <div className="html-explanation-box">
              <p><strong>What happened:</strong> {explanations.summary}</p>
              
              <p><strong>Page Type:</strong> {explanations.page_type}</p>
              
              <p><strong>Interaction Type:</strong> {explanations.interaction_type}</p>
              
              {explanations.risk_level && explanations.risk_level.reasons && (
                <>
                  <h5>Risk Assessment:</h5>
                  <ul className="html-risk-factors">
                    {explanations.risk_level.reasons.map((reason, index) => (
                      <li key={index} className={`html-risk-${explanations.risk_level.level.toLowerCase()}`}>
                        {reason}
                      </li>
                    ))}
                  </ul>
                </>
              )}
              
              <p><em>{explanations.technical_details}</em></p>
            </div>
          </div>
        )}
        
        {/* Browser Information Section */}
        {additionalData.browser_info && (
          <div className="html-details-section">
            <h4 className="html-section-title">
              <FaUser /> Browser Information
            </h4>
            <div className="html-details-table-container">
              <table className="html-details-table">
                <tbody>
                  <tr>
                    <td>User Agent</td>
                    <td>{additionalData.browser_info.userAgent || "Unknown"}</td>
                  </tr>
                  <tr>
                    <td>Language</td>
                    <td>{additionalData.browser_info.language || "Unknown"}</td>
                  </tr>
                  <tr>
                    <td>Platform</td>
                    <td>{additionalData.browser_info.platform || "Unknown"}</td>
                  </tr>
                  <tr>
                    <td>Screen Size</td>
                    <td>{additionalData.browser_info.screenSize || "Unknown"}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        )}
        
        {/* Interaction Data Section */}
        <div className="html-details-section">
          <h4 className="html-section-title">Interaction Data</h4>
          <div className="html-details-table-container">
            <table className="html-details-table">
              <tbody>
                {Object.entries(additionalData)
                  .filter(([key]) => key !== 'browser_info')
                  .map(([key, value]) => (
                    <tr key={key}>
                      <td>{key}</td>
                      <td>
                        {typeof value === 'object' 
                          ? JSON.stringify(value) 
                          : String(value)}
                      </td>
                    </tr>
                  ))
                }
              </tbody>
            </table>
          </div>
        </div>
        
        {/* Raw JSON Viewer */}
        <div className="html-details-section">
          <h4 className="html-section-title">Raw JSON Data</h4>
          <div className="html-details-json">
            <JsonSyntaxHighlighter json={selectedInteraction} maxHeight="500px" />
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="admin-tab-content html-interactions-tab">
      <div className="admin-content-header">
        <h2><FaCode /> HTML Interactions</h2>
        <div className="html-header-actions">
          <button 
            className={`html-action-btn ${viewMode === "overview" ? "active" : ""}`}
            onClick={() => setViewMode("overview")}
          >
            <FaChartBar /> Overview
          </button>
          <button 
            className={`html-action-btn ${viewMode === "interactions" ? "active" : ""}`}
            onClick={() => {
              setViewMode("interactions");
              fetchInteractions();
            }}
          >
            <FaTable /> All Interactions
          </button>
          <button 
            className="html-refresh-btn" 
            onClick={() => {
              if (viewMode === "overview") {
                fetchStats();
              } else if (viewMode === "interactions") {
                fetchInteractions();
              } else if (viewMode === "details" && selectedInteraction) {
                fetchInteractionDetails(selectedInteraction._id);
              }
            }}
            disabled={loading || statsLoading}
          >
            {loading || statsLoading ? <FaSpinner className="html-spinner" /> : <FaSync />} Refresh
          </button>
        </div>
      </div>
      
      {renderContent()}
    </div>
  );
};

export default HtmlInteractionsTab;
