import { useState, useEffect } from "react";
import { bnsLookup, chatWithNeedhi } from "../utils/api";
import { FaSearch, FaExchangeAlt, FaGavel, FaQuestionCircle, FaPaperPlane, FaLightbulb, FaBalanceScale, FaUserShield } from "react-icons/fa";

const BnsLookup = ({ language }) => {
  const [searchTerm, setSearchTerm] = useState("");
  const [activeCategory, setActiveCategory] = useState(""); // "", "Body", "Property", "Women & Children", "Public Peace", "State Sovereignty"
  const [results, setResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  // AI mini helper state
  const [aiQuery, setAiQuery] = useState("");
  const [aiAnswer, setAiAnswer] = useState("");
  const [isAiLoading, setIsAiLoading] = useState(false);

  const categories = [
    { id: "", label: { English: "All Sections", Tamil: "அனைத்து பிரிவுகள்" } },
    { id: "Body", label: { English: "Offenses Against Body", Tamil: "உடல் சார்ந்த குற்றங்கள்" } },
    { id: "Property", label: { English: "Offenses Against Property", Tamil: "சொத்து சார்ந்த குற்றங்கள்" } },
    { id: "Women & Children", label: { English: "Women & Children", Tamil: "பெண்கள் & குழந்தைகள்" } },
    { id: "Public Peace", label: { English: "Public Peace", Tamil: "பொது அமைதி" } },
    { id: "State Sovereignty", label: { English: "State Sovereignty", Tamil: "தேச பாதுகாப்பு" } },
  ];

  // Fetch results when search term or category changes
  useEffect(() => {
    let active = true;
    const fetchResults = async () => {
      setIsLoading(true);
      try {
        const data = await bnsLookup(searchTerm, activeCategory);
        if (active) {
          setResults(data);
        }
      } catch (err) {
        console.error(err);
      } finally {
        if (active) {
          setIsLoading(false);
        }
      }
    };
    fetchResults();
    return () => {
      active = false;
    };
  }, [searchTerm, activeCategory]);

  // Handle BNS Ask AI
  const handleAiLookup = async () => {
    if (!aiQuery.trim()) return;
    setIsAiLoading(true);
    setAiAnswer("");

    // Create a special prompt tailored to BNS vs IPC
    const queryPrompt = `Provide a comparison of IPC vs BNS laws for: '${aiQuery}'. Explain clearly how the section numbers, definitions, and punishments have changed under the new Bharatiya Nyaya Sanhita (BNS). Keep it brief, accurate, and list relevant section numbers.`;

    chatWithNeedhi(
      queryPrompt,
      language,
      [], // no history for quick lookup
      (chunk, full) => {
        setAiAnswer(full);
      },
      (fullText) => {
        setAiAnswer(fullText);
        setIsAiLoading(false);
      },
      (err) => {
        setAiAnswer(`❌ Error: ${err.message}`);
        setIsAiLoading(false);
      }
    );
  };

  return (
    <div>
      <div className="section-header">
        <h2 className="section-title">
          {language === "Tamil" ? "புதிய BNS vs IPC ஒப்பீட்டு பலகை" : "Bharatiya Nyaya Sanhita (BNS) vs IPC Map"}
        </h2>
        <p className="section-subtitle">
          {language === "Tamil"
            ? "இந்திய தண்டனைச் சட்டம் (IPC) மற்றும் புதிய பாரதிய நியாய சன்ஹிதா (BNS) சட்டப்பிரிவுகளை எளிதாக தேடி ஒப்பிடுங்கள்."
            : "Cross-reference old Indian Penal Code (IPC) sections with the new Bharatiya Nyaya Sanhita (BNS) laws, highlighting key changes."}
        </p>
      </div>

      {/* Search and Category Filters */}
      <div className="lookup-search-container">
        <div style={{ position: "relative", flex: 1 }}>
          <FaSearch style={{ position: "absolute", left: "16px", top: "50%", transform: "translateY(-50%)", color: "var(--accent-gold)" }} />
          <input
            type="text"
            className="input-control"
            style={{ paddingLeft: "45px" }}
            placeholder={
              language === "Tamil"
                ? "சட்டப்பிரிவு அல்லது குற்றத்தின் பெயரைத் தேடுக (எ.கா. கொலை, 302, திருட்டு)..."
                : "Search by IPC section, BNS section, or offense (e.g., murder, 302, theft, cheating)..."
            }
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
      </div>

      <div className="lookup-category-filter">
        {categories.map((cat) => (
          <button
            key={cat.id}
            className={`filter-tag ${activeCategory === cat.id ? "active" : ""}`}
            onClick={() => setActiveCategory(cat.id)}
          >
            {cat.label[language]}
          </button>
        ))}
      </div>

      {/* Search results grid */}
      {isLoading ? (
        <div className="grid-2">
          {[1, 2, 3, 4].map((n) => (
            <div key={n} className="card loading-pulse" style={{ height: "200px" }}></div>
          ))}
        </div>
      ) : results.length === 0 ? (
        <div className="card" style={{ textAlign: "center", padding: "40px" }}>
          <p style={{ color: "var(--text-secondary)" }}>
            {language === "Tamil" ? "முடிவுகள் எதுவும் இல்லை. தேடல் வார்த்தையை மாற்றிப் பார்க்கவும்." : "No matching legal sections found. Try a different search term."}
          </p>
        </div>
      ) : (
        <div className="grid-2" style={{ marginBottom: "40px" }}>
          {results.map((item, idx) => (
            <div key={idx} className="card bns-card">
              <div className="bns-grid">
                <div>
                  <span className="bns-sec-label">IPC Code</span>
                  <span className="bns-sec-num">{item.ipc}</span>
                </div>
                <div className="bns-compare-arrow">
                  <FaExchangeAlt />
                </div>
                <div style={{ textAlign: "right" }}>
                  <span className="bns-sec-label">BNS Code</span>
                  <span className="bns-sec-num" style={{ color: "var(--accent-gold-light)" }}>{item.bns}</span>
                </div>
              </div>

              <h4 style={{ fontFamily: "var(--font-serif)", fontSize: "1.15rem", marginBottom: "15px", color: "var(--text-primary)" }}>
                {item.title}
              </h4>

              <div className="bns-card-details">
                <div className="bns-detail-group">
                  <h5>{language === "Tamil" ? "விளக்கம்" : "Description"}</h5>
                  <p>{language === "Tamil" ? item.tamil_description : item.description}</p>
                </div>
                <div className="bns-detail-group">
                  <h5>{language === "Tamil" ? "தண்டனை" : "Punishment"}</h5>
                  <p style={{ color: "var(--accent-gold)" }}>
                    {language === "Tamil" ? item.tamil_punishment : item.punishment}
                  </p>
                </div>
                {item.changes && (
                  <div className="bns-changes-alert">
                    <strong style={{ color: "var(--accent-gold-light)", display: "flex", alignItems: "center", gap: "6px", marginBottom: "4px" }}>
                      <FaLightbulb /> {language === "Tamil" ? "முக்கிய மாற்றங்கள்" : "Key Transition Details"}
                    </strong>
                    {language === "Tamil" ? item.tamil_changes : item.changes}
                  </div>
                )}
                
                <div style={{ display: "flex", gap: "8px", marginTop: "10px" }}>
                  <span className={`badge ${item.bail.includes("Non") ? "badge-red" : "badge-yellow"}`} style={{ display: "inline-flex", alignItems: "center", gap: "4px" }}>
                    <FaBalanceScale /> {item.bail}
                  </span>
                  <span className="badge badge-blue" style={{ display: "inline-flex", alignItems: "center", gap: "4px" }}>
                    <FaUserShield /> {item.cognizable}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Custom AI Lookup Section */}
      <div className="card" style={{ border: "1px solid var(--border-gold)" }}>
        <div className="card-title">
          <span><FaGavel /></span>
          {language === "Tamil" ? "சட்டமாற்றங்களை AI-யிடம் கேளுங்கள்" : "Ask AI About New Legal Changes"}
        </div>
        <p style={{ color: "var(--text-secondary)", fontSize: "0.88rem", marginBottom: "16px" }}>
          {language === "Tamil"
            ? "இந்திய தண்டனைச் சட்டத்தில் இருந்து புதிய பாரதிய நியாய சன்ஹிதாவிற்கு மாறியுள்ள பிற சட்டப்பிரிவுகள் குறித்து ஏதேனும் சந்தேகங்கள் இருந்தால் கேளுங்கள்."
            : "Have questions about sections not listed above? Ask Needhi AI to retrieve the transition details, definitions, or punishments."}
        </p>

        <div style={{ display: "flex", gap: "10px", marginBottom: "15px" }}>
          <input
            type="text"
            className="input-control"
            placeholder={
              language === "Tamil"
                ? "எ.கா. அவதூறு வழக்கு சட்டத்தில் என்ன மாற்றம் ஏற்பட்டுள்ளது?..."
                : "e.g. How has section 144 or riot definitions changed under BNS?"
            }
            value={aiQuery}
            onChange={(e) => setAiQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleAiLookup()}
          />
          <button className="btn btn-primary" onClick={handleAiLookup} disabled={isAiLoading || !aiQuery.trim()}>
            {isAiLoading ? <FaQuestionCircle className="animate-spin" /> : <FaPaperPlane />}
          </button>
        </div>

        {aiAnswer && (
          <div style={{ background: "rgba(255,255,255,0.03)", border: "1px solid var(--border-gold)", borderRadius: "8px", padding: "16px", fontSize: "0.93rem", whiteSpace: "pre-line" }}>
            {aiAnswer}
          </div>
        )}
      </div>
    </div>
  );
};

export default BnsLookup;
