import { useState } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import Navigation from "./components/Navigation";
import HomeChat from "./components/HomeChat";
import BnsLookup from "./components/BnsLookup";
import CaseTracker from "./components/CaseTracker";
import LawyerBooking from "./components/LawyerBooking";
import FirWizard from "./components/FirWizard";
import DocStudio from "./components/DocStudio";
import RightsExplorer from "./components/RightsExplorer";
import AboutContact from "./components/AboutContact";
import FilingChecklist from "./components/FilingChecklist";
import CasePredictor from "./components/CasePredictor";
import LegalSimplifier from "./components/LegalSimplifier";
import LimitationsChecker from "./components/LimitationsChecker";
import { FaBars, FaTimes, FaExclamationTriangle, FaShieldAlt, FaUserShield, FaLaptop, FaHeartbeat, FaBalanceScale } from "react-icons/fa";
import "./App.css";

function App() {
  const [language, setLanguage] = useState("English"); // "English" or "Tamil"
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  // Sticky helplines for banner
  const bannerHelplines = [
    { label: "Police", num: "100", icon: <FaShieldAlt /> },
    { label: "Women", num: "1091", icon: <FaUserShield /> },
    { label: "Cyber", num: "1930", icon: <FaLaptop /> },
    { label: "Medical", num: "108", icon: <FaHeartbeat /> }
  ];

  return (
    <div className="app-container">
      {/* Background logo watermark */}
      <div className="app-watermark"></div>

      {/* Sidebar Navigation */}
      <Navigation
        language={language}
        setLanguage={setLanguage}
        isOpen={isSidebarOpen}
        setIsOpen={setIsSidebarOpen}
      />

      {/* Mobile Drawer Header */}
      <header className="mobile-header">
        <button className="menu-toggle" onClick={() => setIsSidebarOpen(!isSidebarOpen)}>
          {isSidebarOpen ? <FaTimes /> : <FaBars />}
        </button>
        <div style={{ fontFamily: "var(--font-serif)", fontSize: "1.2rem", fontWeight: "700", letterSpacing: "1px", color: "var(--accent-gold-light)" }}>
          NEEDHI AI
        </div>
        <div className="lang-toggle" style={{ margin: 0, padding: "2px" }}>
          <button 
            className={`lang-btn ${language === "English" ? "active" : ""}`} 
            onClick={() => setLanguage("English")}
            style={{ padding: "4px 8px", fontSize: "0.7rem" }}
          >
            EN
          </button>
          <button 
            className={`lang-btn ${language === "Tamil" ? "active" : ""}`} 
            onClick={() => setLanguage("Tamil")}
            style={{ padding: "4px 8px", fontSize: "0.7rem" }}
          >
            த
          </button>
        </div>
      </header>

      {/* Workspace Panel */}
      <div className="main-content">
        {/* Sticky Helplines Banner */}
        <div className="emergency-banner">
          <span className="emergency-title" style={{ display: "inline-flex", alignItems: "center", gap: "5px" }}>
            <FaExclamationTriangle /> Helplines:
          </span>
          {bannerHelplines.map((hp, idx) => (
            <span key={idx} className="emergency-item" style={{ display: "inline-flex", alignItems: "center", gap: "5px" }}>
              {hp.icon} {hp.label}: {hp.num}
            </span>
          ))}
          <span className="emergency-item gold" style={{ display: "inline-flex", alignItems: "center", gap: "5px" }}>
            <FaBalanceScale /> Free Legal Aid: 15100
          </span>
        </div>

        {/* View Component */}
        <main style={{ flex: 1, position: "relative", zIndex: 1 }}>
          <Routes>
            <Route path="/" element={<HomeChat language={language} />} />
            <Route path="/bns" element={<BnsLookup language={language} />} />
            <Route path="/predictor" element={<CasePredictor language={language} />} />
            <Route path="/fir" element={<FirWizard language={language} />} />
            <Route path="/templates" element={<DocStudio language={language} />} />
            <Route path="/checklist" element={<FilingChecklist language={language} />} />
            <Route path="/simplifier" element={<LegalSimplifier language={language} />} />
            <Route path="/limitations" element={<LimitationsChecker language={language} />} />
            <Route path="/rights" element={<RightsExplorer language={language} />} />
            <Route path="/lawyers" element={<LawyerBooking language={language} />} />
            <Route path="/case" element={<CaseTracker language={language} />} />
            <Route path="/about" element={<AboutContact language={language} />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}

export default App;

