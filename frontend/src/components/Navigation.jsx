import { NavLink } from "react-router-dom";
import {
  FaHome,
  FaBalanceScale,
  FaSearch,
  FaCalendarAlt,
  FaFileAlt,
  FaPenNib,
  FaShieldAlt,
  FaInfoCircle,
  FaGavel,
  FaClipboardList,
  FaBookOpen,
  FaClock
} from "react-icons/fa";

const Navigation = ({ language, isOpen, setIsOpen }) => {
  const menuItems = [
    { id: "home", path: "/", label: { English: "Home", Tamil: "முகப்பு" }, icon: <FaHome /> },
    { id: "bns", path: "/bns", label: { English: "BNS vs IPC Map", Tamil: "BNS vs IPC வரைபடம்" }, icon: <FaBalanceScale /> },
    { id: "predictor", path: "/predictor", label: { English: "Outcome Predictor", Tamil: "முடிவு கணிப்பாளர்" }, icon: <FaGavel /> },
    { id: "fir", path: "/fir", label: { English: "FIR Draft Wizard", Tamil: "FIR வரைவு வழிகாட்டி" }, icon: <FaPenNib /> },
    { id: "templates", path: "/templates", label: { English: "Document Studio", Tamil: "ஆவண ஸ்டுடியோ" }, icon: <FaFileAlt /> },
    { id: "checklist", path: "/checklist", label: { English: "Filing Checklist", Tamil: "தாக்கல் சரிபார்ப்பு" }, icon: <FaClipboardList /> },
    { id: "simplifier", path: "/simplifier", label: { English: "Legal Simplifier", Tamil: "சட்ட எளிமையாக்கி" }, icon: <FaBookOpen /> },
    { id: "limitations", path: "/limitations", label: { English: "Limitation Checker", Tamil: "காலவரம்பு சரிபார்ப்பான்" }, icon: <FaClock /> },
    { id: "rights", path: "/rights", label: { English: "Know Your Rights", Tamil: "உங்கள் உரிமைகள்" }, icon: <FaShieldAlt /> },
    { id: "lawyers", path: "/lawyers", label: { English: "Book a Lawyer", Tamil: "வழக்கறிஞர் முன்பதிவு" }, icon: <FaCalendarAlt /> },
    { id: "case", path: "/case", label: { English: "Case Tracker", Tamil: "வழக்கு கண்காணிப்பாளர்" }, icon: <FaSearch /> },
    { id: "about", path: "/about", label: { English: "About & Helpline", Tamil: "விவரம் & உதவி எண்கள்" }, icon: <FaInfoCircle /> },
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
          <NavLink
            key={item.id}
            to={item.path}
            className={({ isActive }) => `menu-item ${isActive ? "active" : ""}`}
            onClick={() => {
              setIsOpen(false); // Close sidebar on mobile select
            }}
            end={item.path === "/"}
          >
            <span className="menu-icon">{item.icon}</span>
            <span className="menu-text">{item.label[language]}</span>
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div style={{ fontSize: "0.72rem", color: "var(--text-muted)", letterSpacing: "0.5px" }}>
          Needhi AI © 2026
        </div>
      </div>
    </aside>
  );
};

export default Navigation;


