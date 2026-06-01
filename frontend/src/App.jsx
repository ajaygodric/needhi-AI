import { useState } from "react";
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
  const [activeTab, setActiveTab] = useState("home");
  const [language, setLanguage] = useState("English"); // "English" or "Tamil"
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  // Render view dynamically
  const renderActiveView = () => {
    switch (activeTab) {
      case "home":
        return <HomeChat language={language} />;
      case "rights":
        return <RightsExplorer language={language} />;
      case "bns":
        return <BnsLookup language={language} />;
      case "fir":
        return <FirWizard language={language} />;
      case "templates":
        return <DocStudio language={language} />;
      case "predictor":
        return <CasePredictor language={language} />;
      case "simplifier":
        return <LegalSimplifier language={language} />;
      case "limitations":
        return <LimitationsChecker language={language} />;
      case "checklist":
        return <FilingChecklist language={language} />;
      case "lawyers":
        return <LawyerBooking language={language} />;
      case "case":
        return <CaseTracker language={language} />;
      case "about":
        return <AboutContact language={language} />;
      default:
        return <HomeChat language={language} />;
    }
  };

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
        activeTab={activeTab}
        setActiveTab={setActiveTab}
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
          {renderActiveView()}
        </main>
      </div>
    </div>
  );
}

export default App;
