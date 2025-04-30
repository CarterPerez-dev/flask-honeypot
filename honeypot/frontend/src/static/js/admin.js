// src/components/admin.js
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import '../css/admin.css';
import '../css/HoneypotTab.css';
import '../css/HtmlInteractionsTab.css';

// Import tab components
import HoneypotTab from '../../components/HoneypotTab';
import HtmlInteractionsTab from '../../components/HtmlInteractionsTab';
import OverviewTab from '../../components/OverviewTab';

// Import icons
import { 
  FaHome, FaSpider, FaCode, FaSignOutAlt, 
  FaBars, FaTimes, FaChevronRight, FaChevronDown 
} from 'react-icons/fa';

function AdminDashboard() {
  const [isNavCollapsed, setIsNavCollapsed] = useState(false);
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const navigate = useNavigate();

  // Get active tab from localStorage or default to overview
  const [activeTab, setActiveTab] = useState(() => {
    return localStorage.getItem('honeypotAdminActiveTab') || "overview";
  });
  
  // Save active tab to localStorage when it changes
  const switchTab = (tabName) => {
    localStorage.setItem('honeypotAdminActiveTab', tabName);
    setActiveTab(tabName);
    setMobileNavOpen(false);
  };
  
  // Handle logout
  const handleLogout = async () => {
    try {
      const response = await fetch("/api/honeypot/admin/logout", {
        method: "POST",
        credentials: "include"
      });
      
      if (response.ok) {
        navigate("/honey/login");
      }
    } catch (err) {
      console.error("Logout error:", err);
    }
  };

  // Render the appropriate tab content
  const renderTabContent = () => {
    switch(activeTab) {
      case 'overview': return <OverviewTab />;
      case 'honeypot': return <HoneypotTab />;
      case 'html': return <HtmlInteractionsTab />;
      default: return <OverviewTab />;
    }
  };

  return (
    <div className={`honeypot-admin-dashboard ${isNavCollapsed ? 'nav-collapsed' : ''}`}>
      {/* Sidebar */}
      <div className="honeypot-admin-sidebar">
        <div className="honeypot-admin-sidebar-header">
          <div className="honeypot-admin-logo">
            <FaSpider />
            <h1>Honeypot Admin</h1>
          </div>
          <button 
            className="honeypot-admin-collapse-btn"
            onClick={() => setIsNavCollapsed(!isNavCollapsed)}
            title={isNavCollapsed ? "Expand Navigation" : "Collapse Navigation"}
          >
            {isNavCollapsed ? <FaChevronRight /> : <FaChevronDown />}
          </button>
        </div>
        
        <nav className="honeypot-admin-nav">
          <ul className="honeypot-admin-nav-list">
            <li className={activeTab === "overview" ? "active" : ""}>
              <button onClick={() => switchTab("overview")}>
                <FaHome />
                <span>Overview</span>
              </button>
            </li>
            <li className={activeTab === "honeypot" ? "active" : ""}>
              <button onClick={() => switchTab("honeypot")}>
                <FaSpider />
                <span>Honeypot</span>
              </button>
            </li>
            <li className={activeTab === "html" ? "active" : ""}>
              <button onClick={() => switchTab("html")}>
                <FaCode />
                <span>HTML Interactions</span>
              </button>
            </li>
          </ul>
        </nav>
        
        <div className="honeypot-admin-sidebar-footer">
          <button className="honeypot-admin-logout-btn" onClick={handleLogout}>
            <FaSignOutAlt />
            <span>Logout</span>
          </button>
        </div>
      </div>
      
      {/* Mobile Header */}
      <div className="honeypot-admin-mobile-header">
        <button 
          className="honeypot-admin-mobile-menu-toggle"
          onClick={() => setMobileNavOpen(!mobileNavOpen)}
        >
          {mobileNavOpen ? <FaTimes /> : <FaBars />}
        </button>
        <div className="honeypot-admin-mobile-logo">
          <FaSpider />
          <h1>Honeypot Admin</h1>
        </div>
      </div>
      
      {/* Mobile Navigation Overlay */}
      <div className={`honeypot-admin-mobile-nav ${mobileNavOpen ? 'active' : ''}`}>
        <nav>
          <ul>
            <li>
              <button onClick={() => switchTab("overview")}>
                <FaHome /> Overview
              </button>
            </li>
            <li>
              <button onClick={() => switchTab("honeypot")}>
                <FaSpider /> Honeypot
              </button>
            </li>
            <li>
              <button onClick={() => switchTab("html")}>
                <FaCode /> HTML Interactions
              </button>
            </li>
            <li>
              <button onClick={handleLogout} className="honeypot-mobile-logout-btn">
                <FaSignOutAlt /> Logout
              </button>
            </li>
          </ul>
        </nav>
      </div>
      
      {/* Main Content */}
      <div className="honeypot-admin-main-content">
        {renderTabContent()}
      </div>
    </div>
  );
}

export default AdminDashboard;
