import { useState, useRef, useEffect } from "react";
import {
  FaShieldAlt,
  FaUserShield,
  FaLaptop,
  FaHeartbeat,
  FaBalanceScale,
  FaSun,
  FaMoon,
  FaChevronDown,
  FaSignOutAlt,
  FaCheckCircle
} from "react-icons/fa";

function TopBar({ language, setLanguage, themeMode, setThemeMode, user, onLogout }) {
  const [profileOpen, setProfileOpen] = useState(false);
  const dropdownRef = useRef(null);

  const bannerHelplines = [
    { label: "Police", num: "100", icon: <FaShieldAlt /> },
    { label: "Women", num: "1091", icon: <FaUserShield /> },
    { label: "Cyber", num: "1930", icon: <FaLaptop /> },
    { label: "Medical", num: "108", icon: <FaHeartbeat /> }
  ];

  // Close dropdown on click outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setProfileOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const firstLetter = user?.name ? user.name.charAt(0).toUpperCase() : "U";

  return (
    <header className="app-topbar">
      {/* Left: Helplines */}
      <div className="topbar-helplines">
        <span className="emergency-title">
          <FaShieldAlt style={{ color: "var(--accent-gold)" }} />
          <span>{language === "Tamil" ? "உதவி எண்கள்:" : "Helplines:"}</span>
        </span>
        {bannerHelplines.map((hp, idx) => (
          <span key={idx} className="emergency-item">
            {hp.icon} {hp.label}: {hp.num}
          </span>
        ))}
        <span className="emergency-item gold">
          <FaBalanceScale /> {language === "Tamil" ? "இலவச சட்ட உதவி:" : "Legal Aid:"} 15100
        </span>
      </div>

      {/* Right Controls: Theme, Lang & User Profile Dropdown */}
      <div className="topbar-controls">
        {/* Language Switcher */}
        <div className="topbar-lang-toggle">
          <button
            type="button"
            className={`topbar-toggle-btn ${language === "English" ? "active" : ""}`}
            onClick={() => setLanguage("English")}
          >
            EN
          </button>
          <button
            type="button"
            className={`topbar-toggle-btn ${language === "Tamil" ? "active" : ""}`}
            onClick={() => setLanguage("Tamil")}
          >
            தமிழ்
          </button>
        </div>

        {/* User Profile Button with Popover */}
        {user && (
          <div className="topbar-user-wrapper" ref={dropdownRef}>
            <button
              type="button"
              className={`topbar-user-pill ${profileOpen ? "active" : ""}`}
              onClick={() => setProfileOpen(!profileOpen)}
              title="User Account"
            >
              <div className="topbar-avatar">{firstLetter}</div>
              <span className="topbar-user-name">{user.name}</span>
              <FaChevronDown className={`topbar-chevron ${profileOpen ? "rotated" : ""}`} />
            </button>

            {/* Profile Dropdown Menu */}
            {profileOpen && (
              <div className="topbar-profile-dropdown">
                <div className="dropdown-user-header">
                  <div className="dropdown-avatar-lg">{firstLetter}</div>
                  <div className="dropdown-user-details">
                    <div className="dropdown-name">{user.name}</div>
                    <div className="dropdown-email">{user.email}</div>
                    <div className="dropdown-badge">
                      <FaCheckCircle style={{ fontSize: "0.75rem", color: "var(--success)" }} /> Verified Account
                    </div>
                  </div>
                </div>

                <div className="dropdown-divider"></div>

                <div className="dropdown-theme-row">
                  <span className="dropdown-row-label">
                    {language === "Tamil" ? "தோற்றம் (Theme):" : "Appearance:"}
                  </span>
                  <div className="topbar-theme-toggle">
                    <button
                      type="button"
                      className={`topbar-toggle-btn ${themeMode === "system" ? "active" : ""}`}
                      onClick={() => setThemeMode("system")}
                    >
                      <FaLaptop />
                    </button>
                    <button
                      type="button"
                      className={`topbar-toggle-btn ${themeMode === "light" ? "active" : ""}`}
                      onClick={() => setThemeMode("light")}
                    >
                      <FaSun />
                    </button>
                    <button
                      type="button"
                      className={`topbar-toggle-btn ${themeMode === "dark" ? "active" : ""}`}
                      onClick={() => setThemeMode("dark")}
                    >
                      <FaMoon />
                    </button>
                  </div>
                </div>

                <div className="dropdown-divider"></div>

                <button
                  type="button"
                  className="dropdown-logout-btn"
                  onClick={() => {
                    setProfileOpen(false);
                    onLogout();
                  }}
                >
                  <FaSignOutAlt />
                  <span>{language === "Tamil" ? "வெளியேறுக (Logout)" : "Sign Out"}</span>
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </header>
  );
}

export default TopBar;
