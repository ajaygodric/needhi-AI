import { useState, useEffect } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import Navigation from "./components/Navigation";
import Auth from "./components/Auth";
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
  const [user, setUser] = useState(null);
  const [authChecking, setAuthChecking] = useState(true);
  const [themeMode, setThemeMode] = useState(() => {
    return localStorage.getItem("needhi_theme_mode") || "system";
  });

  // Dynamic system theme detection & listener
  useEffect(() => {
    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");

    const applyTheme = () => {
      let resolvedTheme = "dark";
      if (themeMode === "light") {
        resolvedTheme = "light";
      } else if (themeMode === "dark") {
        resolvedTheme = "dark";
      } else {
        // System mode: sync with OS color scheme
        resolvedTheme = mediaQuery.matches ? "dark" : "light";
      }

      document.documentElement.setAttribute("data-theme", resolvedTheme);
      document.documentElement.style.colorScheme = resolvedTheme;
    };

    applyTheme();
    localStorage.setItem("needhi_theme_mode", themeMode);

    const handleSystemThemeChange = () => {
      if (themeMode === "system") {
        applyTheme();
      }
    };

    mediaQuery.addEventListener("change", handleSystemThemeChange);
    return () => mediaQuery.removeEventListener("change", handleSystemThemeChange);
  }, [themeMode]);

  useEffect(() => {
    const cachedToken = localStorage.getItem("needhi_token");
    const cachedName = localStorage.getItem("needhi_name");
    const cachedEmail = localStorage.getItem("needhi_email");

    if (cachedToken && cachedName && cachedEmail) {
      fetch("/api/auth/me", {
        headers: {
          "Authorization": `Bearer ${cachedToken}`
        }
      })
      .then(res => {
        if (res.ok) {
          setUser({ token: cachedToken, name: cachedName, email: cachedEmail });
        } else {
          localStorage.removeItem("needhi_token");
          localStorage.removeItem("needhi_name");
          localStorage.removeItem("needhi_email");
        }
      })
      .catch(() => {
        // Safe offline fallback
        setUser({ token: cachedToken, name: cachedName, email: cachedEmail });
      })
      .finally(() => {
        setAuthChecking(false);
      });
    } else {
      setAuthChecking(false);
    }
  }, []);

  const handleAuthSuccess = (data) => {
    localStorage.setItem("needhi_token", data.token);
    localStorage.setItem("needhi_name", data.name);
    localStorage.setItem("needhi_email", data.email);
    setUser(data);
  };

  const handleLogout = () => {
    const token = localStorage.getItem("needhi_token");
    if (token) {
      fetch("/api/auth/logout", {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`
        }
      }).catch(err => console.error(err));
    }
    localStorage.removeItem("needhi_token");
    localStorage.removeItem("needhi_name");
    localStorage.removeItem("needhi_email");
    setUser(null);
  };

  // Sticky helplines for banner
  const bannerHelplines = [
    { label: "Police", num: "100", icon: <FaShieldAlt /> },
    { label: "Women", num: "1091", icon: <FaUserShield /> },
    { label: "Cyber", num: "1930", icon: <FaLaptop /> },
    { label: "Medical", num: "108", icon: <FaHeartbeat /> }
  ];

  if (authChecking) {
    return (
      <div style={{ display: "flex", justifyContent: "center", alignItems: "center", width: "100vw", height: "100vh", backgroundColor: "var(--bg-primary)", color: "var(--accent-gold)", flexDirection: "column", gap: "20px" }}>
        <FaBalanceScale style={{ fontSize: "4rem", animation: "pulse 1.5s infinite" }} />
        <p style={{ fontFamily: "Inter, sans-serif", fontSize: "1.1rem", letterSpacing: "1px" }}>Loading Needhi AI...</p>
      </div>
    );
  }

  if (!user) {
    return (
      <Auth 
        onAuthSuccess={handleAuthSuccess} 
        language={language} 
        themeMode={themeMode}
        setThemeMode={setThemeMode}
      />
    );
  }

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
        user={user}
        onLogout={handleLogout}
        themeMode={themeMode}
        setThemeMode={setThemeMode}
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
            <Route path="/" element={<HomeChat language={language} user={user} />} />
            <Route path="/bns" element={<BnsLookup language={language} />} />
            <Route path="/predictor" element={<CasePredictor language={language} />} />
            <Route path="/fir" element={<FirWizard language={language} />} />
            <Route path="/templates" element={<DocStudio language={language} />} />
            <Route path="/checklist" element={<FilingChecklist language={language} />} />
            <Route path="/simplifier" element={<LegalSimplifier language={language} />} />
            <Route path="/limitations" element={<LimitationsChecker language={language} />} />
            <Route path="/rights" element={<RightsExplorer language={language} />} />
            <Route path="/lawyers" element={<LawyerBooking language={language} user={user} />} />
            <Route path="/case" element={<CaseTracker language={language} user={user} />} />
            <Route path="/about" element={<AboutContact language={language} />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}

export default App;

