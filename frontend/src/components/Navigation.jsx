import { 
  FaHome, 
  FaBalanceScale, 
  FaSearch, 
  FaCalendarAlt, 
  FaFileAlt, 
  FaPenNib, 
  FaShieldAlt, 
  FaInfoCircle,
  FaListAlt,
  FaGavel,
  FaLanguage,
  FaCalendarCheck
} from "react-icons/fa";

const Navigation = ({ activeTab, setActiveTab, language, setLanguage, isOpen, setIsOpen }) => {
  const menuItems = [
    { id: "home", label: { English: "Home", Tamil: "முகப்பு" }, icon: <FaHome /> },
    { id: "predictor", label: { English: "Outcome Predictor", Tamil: "வழக்கு கணிப்பு" }, icon: <FaGavel /> },
    { id: "simplifier", label: { English: "Legal Simplifier", Tamil: "சட்ட மொழியாக்கம்" }, icon: <FaLanguage /> },
    { id: "fir", label: { English: "FIR Draft Wizard", Tamil: "FIR எழுதுபவர்" }, icon: <FaPenNib /> },
    { id: "templates", label: { English: "Document Studio", Tamil: "ஆவணங்கள்" }, icon: <FaFileAlt /> },
    { id: "limitations", label: { English: "Limitation Checker", Tamil: "காலவரம்பு" }, icon: <FaCalendarCheck /> },
    { id: "bns", label: { English: "BNS vs IPC Map", Tamil: "BNS vs IPC ஒப்பீடு" }, icon: <FaBalanceScale /> },
    { id: "rights", label: { English: "Know Your Rights", Tamil: "உரிமைகள்" }, icon: <FaShieldAlt /> },
    { id: "checklist", label: { English: "Filing Checklist", Tamil: "தாக்கல் சரிபார்ப்பு" }, icon: <FaListAlt /> },
    { id: "case", label: { English: "Case Tracker", Tamil: "வழக்கு கண்காணிப்பு" }, icon: <FaSearch /> },
    { id: "lawyers", label: { English: "Book Lawyer", Tamil: "வழக்கறிஞர்கள்" }, icon: <FaCalendarAlt /> },
    { id: "about", label: { English: "About & Helplines", Tamil: "உதவி எண்கள்" }, icon: <FaInfoCircle /> },
  ];

  return (
    <aside className={`sidebar ${isOpen ? "open" : ""}`}>
      <div className="sidebar-header">
        <img src="/needhi.png" alt="Needhi AI Logo" className="sidebar-logo-img" />
        <div className="sidebar-brand">
          <h1>NEEDHI</h1>
          <p>AI Legal Assistant</p>
        </div>
      </div>

      <nav className="sidebar-menu">
        {menuItems.map((item) => (
          <div
            key={item.id}
            className={`menu-item ${activeTab === item.id ? "active" : ""}`}
            onClick={() => {
              setActiveTab(item.id);
              setIsOpen(false); // Close sidebar on mobile select
            }}
          >
            <span className="menu-icon">{item.icon}</span>
            <span className="menu-text">{item.label[language]}</span>
          </div>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className="lang-toggle">
          <button
            className={`lang-btn ${language === "English" ? "active" : ""}`}
            onClick={() => setLanguage("English")}
          >
            English
          </button>
          <button
            className={`lang-btn ${language === "Tamil" ? "active" : ""}`}
            onClick={() => setLanguage("Tamil")}
          >
            தமிழ்
          </button>
        </div>
        <div style={{ fontSize: "0.68rem", color: "var(--text-muted)", marginTop: "4px" }}>
          Needhi AI © 2026
        </div>
      </div>
    </aside>
  );
};

export default Navigation;
