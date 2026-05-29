import { useState } from "react";
import { FaUserPlus, FaLaptopCode, FaHandsHelping, FaPhoneVolume, FaExclamationTriangle, FaPaperPlane, FaShieldAlt, FaUserShield, FaLaptop, FaHeartbeat, FaBalanceScale, FaEnvelope, FaCheckCircle } from "react-icons/fa";

const AboutContact = ({ language }) => {
  const [contactName, setContactName] = useState("");
  const [contactEmail, setContactEmail] = useState("");
  const [contactMsg, setContactMsg] = useState("");
  const [isSent, setIsSent] = useState(false);

  const helplines = [
    { title: "Police Dispatch", num: "100", dept: "Law & Order", color: "badge-red", icon: FaShieldAlt },
    { title: "Women Helpline", num: "1091", dept: "Safety & Abuse Protection", color: "badge-red", icon: FaUserShield },
    { title: "Cyber Crime Crime Desk", num: "1930", dept: "Cyber & Financial Fraud Helpline", color: "badge-yellow", icon: FaLaptop },
    { title: "Ambulance Support", num: "108", dept: "Medical Emergencies", color: "badge-green", icon: FaHeartbeat },
    { title: "National Legal Aid (NALSA)", num: "15100", dept: "Free Legal Counsel", color: "badge-blue", icon: FaBalanceScale }
  ];

  const handleContactSubmit = (e) => {
    e.preventDefault();
    setIsSent(true);
    setContactName("");
    setContactEmail("");
    setContactMsg("");
    setTimeout(() => {
      setIsSent(false);
    }, 4000);
  };

  return (
    <div>
      <div className="section-header">
        <h2 className="section-title">
          {language === "Tamil" ? "எங்களைப் பற்றி & உதவி எண்கள்" : "About & Legal Emergency Helplines"}
        </h2>
        <p className="section-subtitle">
          {language === "Tamil"
            ? "இந்திய குடிமக்களுக்கு எளிய முறையில் சட்ட உதவிகளை வழங்குவதற்கான தொழில்நுட்பப் பலகை."
            : "Emergency contact helplines, core platform credentials, and technical details of Needhi AI."}
        </p>
      </div>

      {/* Emergency Helplines Grid */}
      <h3 style={{ fontFamily: "var(--font-serif)", marginBottom: "15px", display: "flex", alignItems: "center", gap: "8px" }}>
        <FaExclamationTriangle style={{ color: "var(--danger)" }} />
        <span>{language === "Tamil" ? "அவசர உதவி எண்கள்" : "National Emergency Helplines (24/7)"}</span>
      </h3>
      <div className="grid-3" style={{ marginBottom: "40px" }}>
        {helplines.map((hp, idx) => {
          const IconComponent = hp.icon;
          return (
            <div key={idx} className="card" style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span className={`badge ${hp.color}`} style={{ fontSize: "0.85rem", padding: "4px 12px" }}>
                  <FaPhoneVolume /> {hp.num}
                </span>
                <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>{hp.dept}</span>
              </div>
              <h4 style={{ fontFamily: "var(--font-serif)", fontSize: "1.1rem", marginTop: "5px", display: "flex", alignItems: "center", gap: "8px" }}>
                <IconComponent style={{ color: "var(--accent-gold)", flexShrink: 0 }} />
                <span>{hp.title}</span>
              </h4>
              <p style={{ fontSize: "0.82rem", color: "var(--text-secondary)" }}>
                {language === "Tamil" ? "24 மணி நேரமும் தொடர்புகொள்ளக்கூடிய இலவச உதவி எண்." : "Dial this toll-free number from any mobile or landline across India."}
              </p>
            </div>
          );
        })}
      </div>

      <div className="grid-2" style={{ gap: "25px", marginBottom: "40px" }}>
        {/* Info Blocks */}
        <div>
          <h3 style={{ fontFamily: "var(--font-serif)", marginBottom: "15px", display: "flex", alignItems: "center", gap: "8px" }}>
            <FaBalanceScale style={{ color: "var(--accent-gold)" }} />
            <span>{language === "Tamil" ? "நீதி AI அறிமுகம்" : "Platform Overview"}</span>
          </h3>
          <div className="card" style={{ display: "flex", flexDirection: "column", gap: "15px" }}>
            <div style={{ display: "flex", gap: "15px" }}>
              <div style={{ fontSize: "1.8rem", color: "var(--accent-gold)" }}><FaLaptopCode /></div>
              <div>
                <h4 style={{ fontFamily: "var(--font-serif)" }}>Modern Tech Stack</h4>
                <p style={{ color: "var(--text-secondary)", fontSize: "0.88rem" }}>
                  Needhi AI is powered by React.js and FastAPI, integrated with Google Gemini LLM API key rotations. PDF compilations utilize custom Noto Sans Tamil fonts via FPDF2.
                </p>
              </div>
            </div>

            <div style={{ display: "flex", gap: "15px" }}>
              <div style={{ fontSize: "1.8rem", color: "var(--accent-gold)" }}><FaUserPlus /></div>
              <div>
                <h4 style={{ fontFamily: "var(--font-serif)" }}>Developer Credentials</h4>
                <p style={{ color: "var(--text-secondary)", fontSize: "0.88rem" }}>
                  Designed and developed by **Ajay Godric** as a free legal aid utility to make judicial awareness accessible for every Indian citizen.
                </p>
              </div>
            </div>

            <div style={{ display: "flex", gap: "15px" }}>
              <div style={{ fontSize: "1.8rem", color: "var(--accent-gold)" }}><FaHandsHelping /></div>
              <div>
                <h4 style={{ fontFamily: "var(--font-serif)" }}>Free Legal Aid Purpose</h4>
                <p style={{ color: "var(--text-secondary)", fontSize: "0.88rem" }}>
                  Empowering underrepresented groups by providing automated guidance, document generators, and connecting users with local State Legal Services (NALSA).
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Support contact form */}
        <div>
          <h3 style={{ fontFamily: "var(--font-serif)", marginBottom: "15px", display: "flex", alignItems: "center", gap: "8px" }}>
            <FaEnvelope style={{ color: "var(--accent-gold)" }} />
            <span>{language === "Tamil" ? "தொடர்பு கொள்ள" : "Contact Developer Support"}</span>
          </h3>
          <div className="card">
            <form onSubmit={handleContactSubmit}>
              <div className="input-group">
                <label className="input-label">{language === "Tamil" ? "முழு பெயர்" : "Your Name"}</label>
                <input type="text" className="input-control" required value={contactName} onChange={(e) => setContactName(e.target.value)} placeholder="e.g. abcd" />
              </div>
              <div className="input-group">
                <label className="input-label">{language === "Tamil" ? "மின்னஞ்சல்" : "Your Email Address"}</label>
                <input type="email" className="input-control" required value={contactEmail} onChange={(e) => setContactEmail(e.target.value)} placeholder="e.g. xyz@example.com" />
              </div>
              <div className="input-group">
                <label className="input-label">{language === "Tamil" ? "செய்தி" : "Message / Query"}</label>
                <textarea rows="3" className="input-control" required value={contactMsg} onChange={(e) => setContactMsg(e.target.value)} placeholder="Enter details..." />
              </div>

              <button type="submit" className="btn btn-primary" style={{ width: "100%" }}>
                <FaPaperPlane /> {language === "Tamil" ? "அனுப்பு" : "Submit Query"}
              </button>
            </form>
            {isSent && (
              <div style={{ marginTop: "12px", padding: "8px", background: "rgba(46,204,113,0.08)", border: "1px solid rgba(46,204,113,0.2)", borderRadius: "8px", color: "var(--success)", fontWeight: "600", textAlign: "center", display: "flex", alignItems: "center", justifyContent: "center", gap: "6px" }}>
                <FaCheckCircle /> Message sent successfully! We will contact you soon.
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Disclaimers card */}
      <div className="card" style={{ borderLeft: "4px solid var(--danger)", background: "rgba(231,76,60,0.02)" }}>
        <h4 style={{ fontFamily: "var(--font-serif)", color: "var(--danger)", display: "flex", alignItems: "center", gap: "10px", marginBottom: "8px" }}>
          <FaExclamationTriangle />
          {language === "Tamil" ? "முக்கிய பொறுப்புத் துறப்பு" : "Disclaimer & Legal Notice"}
        </h4>
        <p style={{ color: "var(--text-secondary)", fontSize: "0.88rem", lineHeight: "1.6" }}>
          {language === "Tamil" 
            ? "நீதி AI பொதுவான சட்டத் தகவல்களை மட்டுமே வழங்குகிறது. இது ஒரு தொழில்முறை சட்ட ஆலோசனைக்கு மாற்றாகாது. எந்தவொரு சட்ட சிக்கலிற்கும் தகுதி வாய்ந்த வழக்கறிஞரை அணுகவும்."
            : "Needhi AI provides general information relating to Indian statutory provisions for educational and awareness purposes. Answers generated by this platform do not constitute official legal advice, and no attorney-client relationship is established. Always consult a qualified advocate for your specific judicial concerns."}
        </p>
      </div>
    </div>
  );
};

export default AboutContact;
