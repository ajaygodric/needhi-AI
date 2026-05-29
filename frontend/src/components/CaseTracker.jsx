import { useState } from "react";
import { searchCases, downloadPdf, subscribeToCase } from "../utils/api";
import { FaSearch, FaHistory, FaGavel, FaHourglassHalf, FaRegFolderOpen, FaMapMarkerAlt, FaDownload, FaEnvelope } from "react-icons/fa";

const CaseTracker = ({ language }) => {
  const [searchVal, setSearchVal] = useState("");
  const [searchType, setSearchType] = useState("CNR Number");
  const [courtType, setCourtType] = useState("District Court");
  const [selectedState, setSelectedState] = useState("Tamil Nadu");
  const [cases, setCases] = useState([]);
  const [hasSearched, setHasSearched] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  // Email alerts subscription and PDF states
  const [activeSubCnr, setActiveSubCnr] = useState(null);
  const [subName, setSubName] = useState("");
  const [subEmail, setSubEmail] = useState("");
  const [subLoading, setSubLoading] = useState(false);
  const [subscribedCnrs, setSubscribedCnrs] = useState({});

  const handleDownloadCasePdf = (item) => {
    const isTamil = language === "Tamil";
    const title = isTamil ? `வழக்கு நிலை அறிக்கை - ${item.case_no}` : `Case Status Report - ${item.case_no}`;
    
    let content = "";
    if (isTamil) {
      content = `### வழக்கு விவரங்கள் (Case Details)
**வழக்கு எண் (Case No):** ${item.case_no}
**சி.என்.ஆர் எண் (CNR No):** ${item.cnr}
**நீதிமன்றம் (Court):** ${item.tamil_court || item.court}
**நீதிபதி (Judge):** ${item.judge}
**வழக்கு தாக்கல் தேதி (Filing Date):** ${item.filing_date}
**வழக்கின் நிலை (Current Stage):** ${item.tamil_stage || item.current_stage}

**மனுதாரர் (Petitioner):** ${item.petitioner}
**மனுதாரர் வழக்கறிஞர் (Petitioner Advocate):** ${item.petitioner_adv}
**எதிர்மனுதாரர் (Respondent):** ${item.respondent}
**எதிர்மனுதாரர் வழக்கறிஞர் (Respondent Advocate):** ${item.respondent_adv}

### விசாரணை காலவரிசை (Hearing Timeline)
`;
      item.timeline.forEach((event) => {
        const eventStatus = event.status === "completed" ? "முடிந்தது" : event.status === "current" ? "தற்போதைய" : "நிலுவையில் உள்ளது";
        content += `\n**தேதி (Date):** ${event.date}\n**நடவடிக்கை (Action):** ${event.action}\n**விளக்கம் (Description):** ${event.description}\n**நிலை (Status):** ${eventStatus}\n-----------------------------------\n`;
      });
    } else {
      content = `### Case Details
**Case Number:** ${item.case_no}
**CNR Number:** ${item.cnr}
**Court:** ${item.court}
**Judge Presiding:** ${item.judge}
**Filing Date:** ${item.filing_date}
**Current Stage:** ${item.current_stage}

**Petitioner:** ${item.petitioner}
**Petitioner Advocate:** ${item.petitioner_adv}
**Respondent:** ${item.respondent}
**Respondent Advocate:** ${item.respondent_adv}

### Hearing Timeline & Case Progress
`;
      item.timeline.forEach((event) => {
        content += `\n**Date:** ${event.date}\n**Action:** ${event.action}\n**Description:** ${event.description}\n**Status:** ${event.status.toUpperCase()}\n-----------------------------------\n`;
      });
    }

    downloadPdf(title, content, `Case_Status_${item.cnr}.pdf`);
  };

  const handleSubscribe = async (cnr) => {
    if (!subName.trim() || !subEmail.trim()) return;
    setSubLoading(true);
    try {
      await subscribeToCase(cnr, subEmail, subName, language);
      setSubscribedCnrs(prev => ({ ...prev, [cnr]: subEmail }));
      setActiveSubCnr(null);
      setSubName("");
      setSubEmail("");
      alert(language === "Tamil" 
        ? "மின்னஞ்சல் விழிப்பூட்டல்களுக்கு வெற்றிகரமாக பதிவு செய்யப்பட்டுள்ளது! உறுதிப்படுத்தல் மின்னஞ்சல் அனுப்பப்பட்டது." 
        : "Successfully subscribed to email alerts! A confirmation email has been sent.");
    } catch (err) {
      console.error(err);
      alert(err.message || "Failed to subscribe to alerts");
    } finally {
      setSubLoading(false);
    }
  };

  const searchTypes = ["CNR Number", "Party Name", "FIR Number", "Advocate Name"];
  
  const courtTypes = ["District Court", "High Court", "Supreme Court"];
  
  const states = ["Tamil Nadu", "Maharashtra", "Delhi", "Karnataka", "Uttar Pradesh", "West Bengal", "Rajasthan", "Gujarat", "Madhya Pradesh", "Kerala", "Andhra Pradesh", "Telangana", "Punjab", "Haryana", "Bihar", "Odisha", "Assam", "Jharkhand"];

  const handleSearch = async () => {
    if (!searchVal.trim()) return;
    setIsLoading(true);
    setHasSearched(true);
    
    try {
      const data = await searchCases(searchVal, searchType);
      setCases(data);
    } catch (err) {
      console.error(err);
      setCases([]);
    } finally {
      setIsLoading(false);
    }
  };

  // Helper to draw horizontal pipeline nodes
  const renderPipeline = (timeline) => {
    // Collect active step index
    let activeIdx = timeline.findIndex(t => t.status === "current");
    if (activeIdx === -1) {
      // If decided
      activeIdx = timeline.length;
    }

    const steps = [
      { id: 0, label: { English: "Filing", Tamil: "வழக்கு தாக்கல்" } },
      { id: 1, label: { English: "Admission", Tamil: "ஏற்பு" } },
      { id: 2, label: { English: "Evidence", Tamil: "சாட்சியம்" } },
      { id: 3, label: { English: "Arguments", Tamil: "வாதம்" } },
      { id: 4, label: { English: "Judgment", Tamil: "தீர்ப்பு" } }
    ];

    // Map case steps to indices:
    // Filing -> index 0
    // Summons/First hearing -> index 1
    // Evidence/PW1/Statement -> index 2
    // Arguments/Final -> index 3
    // Judgment/Pronounced -> index 4
    
    const getStepStatusClass = (stepId) => {
      let mappedActiveStep = 0;
      
      const activeAction = timeline[activeIdx]?.action?.toLowerCase() || "";
      if (activeAction.includes("file")) mappedActiveStep = 0;
      else if (activeAction.includes("hear") || activeAction.includes("admit") || activeAction.includes("summon")) mappedActiveStep = 1;
      else if (activeAction.includes("evidence") || activeAction.includes("witness") || activeAction.includes("pw1")) mappedActiveStep = 2;
      else if (activeAction.includes("argument")) mappedActiveStep = 3;
      else if (activeAction.includes("judgment") || activeAction.includes("decide") || activeAction.includes("sentence")) mappedActiveStep = 4;
      
      if (stepId < mappedActiveStep) return "completed";
      if (stepId === mappedActiveStep) return "active";
      return "pending";
    };

    return (
      <div className="pipeline">
        {steps.map((step) => {
          const status = getStepStatusClass(step.id);
          return (
            <div key={step.id} className={`pipeline-step ${status}`}>
              <div className="pipeline-node">
                {status === "completed" ? "✓" : step.id + 1}
              </div>
              <div className="pipeline-label">{step.label[language]}</div>
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <div>
      <div className="section-header">
        <h2 className="section-title">
          {language === "Tamil" ? "வழக்கு கண்காணிப்பகம் (eCourts)" : "eCourts Case Status Tracker"}
        </h2>
        <p className="section-subtitle">
          {language === "Tamil"
            ? "வழக்கு எண், சி.என்.ஆர் (CNR) எண், அல்லது வழக்கறிஞர் பெயரைப் பயன்படுத்தி உங்கள் வழக்குகளைக் கண்காணிக்கலாம்."
            : "Search and monitor your active legal proceedings using CNR number, party name, or FIR index."}
        </p>
      </div>

      <div className="card" style={{ marginBottom: "30px" }}>
        <div style={{ display: "flex", flexWrap: "wrap", gap: "15px", marginBottom: "15px" }}>
          <div style={{ flex: 1, minWidth: "150px" }}>
            <label className="input-label">{language === "Tamil" ? "தேடல் முறை" : "Search Type"}</label>
            <select className="input-control" value={searchType} onChange={(e) => setSearchType(e.target.value)}>
              {searchTypes.map(t => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </div>
          <div style={{ flex: 1, minWidth: "150px" }}>
            <label className="input-label">{language === "Tamil" ? "நீதிமன்ற வகை" : "Court Type"}</label>
            <select className="input-control" value={courtType} onChange={(e) => setCourtType(e.target.value)}>
              {courtTypes.map(c => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>
          {courtType !== "Supreme Court" && (
            <div style={{ flex: 1, minWidth: "150px" }}>
              <label className="input-label">{language === "Tamil" ? "மாநிலம்" : "State"}</label>
              <select className="input-control" value={selectedState} onChange={(e) => setSelectedState(e.target.value)}>
                {states.map(s => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>
          )}
        </div>

        <div style={{ display: "flex", gap: "10px" }}>
          <input
            type="text"
            className="input-control"
            placeholder={
              searchType === "CNR Number" 
                ? "e.g. TNCH01-008942-2024"
                : searchType === "Party Name" 
                ? "e.g. abcd" 
                : "Enter search value..."
            }
            value={searchVal}
            onChange={(e) => setSearchVal(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
          />
          <button className="btn btn-primary" onClick={handleSearch} disabled={isLoading || !searchVal.trim()}>
            <FaSearch /> {language === "Tamil" ? "தேடு" : "Search"}
          </button>
        </div>
      </div>

      {isLoading ? (
        <div className="card loading-pulse" style={{ height: "300px" }}></div>
      ) : hasSearched && cases.length === 0 ? (
        <div className="card" style={{ textAlign: "center", padding: "50px" }}>
          <FaRegFolderOpen style={{ fontSize: "3rem", color: "var(--accent-gold)", marginBottom: "15px" }} />
          <h3>{language === "Tamil" ? "வழக்கு எதுவும் கண்டறியப்படவில்லை" : "No Cases Found"}</h3>
          <p style={{ color: "var(--text-secondary)", maxWidth: "450px", margin: "10px auto 0 auto" }}>
            {language === "Tamil" 
              ? "சி.என்.ஆர் (CNR) எண் சரியாக உள்ளதா என்று சரிபார்க்கவும். உதாரணத்திற்கு TNCH01-008942-2024 ஐப் பயன்படுத்தவும்."
              : "We couldn't locate any records matching your search. Please check the spelling, format, or try searching for: 'TNCH01-008942-2024' or 'abcd'."}
          </p>
        </div>
      ) : (
        cases.map((item, idx) => (
          <div key={idx} className="card" style={{ marginBottom: "30px", borderTop: "4px solid var(--accent-gold)" }}>
            
            {/* Case Header */}
            <div style={{ display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: "15px", borderBottom: "1px solid rgba(255,255,255,0.06)", paddingBottom: "15px" }}>
              <div>
                <span className="badge badge-blue" style={{ marginBottom: "8px" }}>{item.case_no}</span>
                <h3 style={{ fontFamily: "var(--font-serif)", fontSize: "1.4rem" }}>
                  {language === "Tamil" ? item.tamil_title : item.title}
                </h3>
                <p style={{ color: "var(--text-secondary)", fontSize: "0.88rem", marginTop: "4px", display: "inline-flex", alignItems: "center", gap: "6px" }}>
                  <FaMapMarkerAlt style={{ color: "var(--accent-gold-light)" }} /> <span>{language === "Tamil" ? item.tamil_court : item.court}</span>
                </p>
              </div>
              <div style={{ textAlign: "right", display: "flex", flexDirection: "column", alignItems: "flex-end", gap: "10px" }}>
                <div>
                  <span style={{ fontSize: "0.78rem", color: "var(--text-muted)", display: "block" }}>CNR Number</span>
                  <span style={{ fontFamily: "monospace", fontSize: "1.1rem", fontWeight: "700", color: "var(--accent-gold)" }}>{item.cnr}</span>
                </div>
                <div style={{ display: "flex", gap: "8px", marginTop: "5px" }}>
                  <button 
                    className="btn btn-small" 
                    onClick={() => handleDownloadCasePdf(item)}
                    title={language === "Tamil" ? "வழக்கு அறிக்கையை பதிவிறக்கவும்" : "Download Case PDF Report"}
                    style={{ padding: "6px 12px", fontSize: "0.82rem", display: "inline-flex", alignItems: "center", gap: "6px" }}
                  >
                    <FaDownload /> {language === "Tamil" ? "PDF" : "PDF Report"}
                  </button>
                  
                  {subscribedCnrs[item.cnr] ? (
                    <span style={{ color: "var(--success)", fontSize: "0.85rem", display: "inline-flex", alignItems: "center", gap: "4px", padding: "6px" }}>
                      ✓ {language === "Tamil" ? "பதிவு செய்யப்பட்டது" : "Subscribed"}
                    </span>
                  ) : (
                    <button 
                      className="btn btn-small btn-secondary" 
                      onClick={() => setActiveSubCnr(activeSubCnr === item.cnr ? null : item.cnr)}
                      style={{ padding: "6px 12px", fontSize: "0.82rem", display: "inline-flex", alignItems: "center", gap: "6px", background: "rgba(255,255,255,0.04)" }}
                    >
                      <FaEnvelope /> {language === "Tamil" ? "விழிப்பூட்டல்" : "Subscribe"}
                    </button>
                  )}
                </div>
              </div>
            </div>

            {/* Subscription Form Panel */}
            {activeSubCnr === item.cnr && (
              <div style={{ 
                background: "rgba(201, 168, 76, 0.04)", 
                border: "1px solid var(--border-gold)", 
                borderRadius: "8px", 
                padding: "15px", 
                margin: "15px 0"
              }}>
                <h5 style={{ color: "var(--accent-gold-light)", marginBottom: "8px", fontSize: "0.9rem", display: "flex", alignItems: "center", gap: "8px" }}>
                  <FaEnvelope /> {language === "Tamil" ? "வழக்கு விழிப்பூட்டல்களுக்கு பதிவு செய்யவும்" : "Subscribe to Case Email Alerts"}
                </h5>
                <p style={{ fontSize: "0.78rem", color: "var(--text-secondary)", marginBottom: "12px" }}>
                  {language === "Tamil" 
                    ? "விசாரணை தேதிகள் மற்றும் நிலை புதுப்பிக்கப்படும் போது உங்கள் மின்னஞ்சலுக்கு அறிவிப்புகளைப் பெறுங்கள்."
                    : "Receive automated email updates whenever next hearing dates or stages are updated for this case."}
                </p>
                <div style={{ display: "flex", flexWrap: "wrap", gap: "10px" }}>
                  <input
                    type="text"
                    className="input-control"
                    placeholder={language === "Tamil" ? "உங்கள் பெயர்" : "Your Name"}
                    value={subName}
                    onChange={(e) => setSubName(e.target.value)}
                    style={{ flex: 1, minWidth: "150px", fontSize: "0.85rem", padding: "8px 12px" }}
                  />
                  <input
                    type="email"
                    className="input-control"
                    placeholder={language === "Tamil" ? "மின்னஞ்சல் முகவரி" : "Email Address"}
                    value={subEmail}
                    onChange={(e) => setSubEmail(e.target.value)}
                    style={{ flex: 1, minWidth: "150px", fontSize: "0.85rem", padding: "8px 12px" }}
                  />
                  <button 
                    className="btn btn-primary" 
                    onClick={() => handleSubscribe(item.cnr)}
                    disabled={subLoading || !subName.trim() || !subEmail.trim()}
                    style={{ padding: "8px 16px", fontSize: "0.85rem" }}
                  >
                    {subLoading ? (language === "Tamil" ? "பதிவு செய்யப்படுகிறது..." : "Subscribing...") : (language === "Tamil" ? "உறுதி செய்" : "Confirm")}
                  </button>
                  <button 
                    className="btn" 
                    onClick={() => { setActiveSubCnr(null); setSubName(""); setSubEmail(""); }}
                    style={{ padding: "8px 16px", fontSize: "0.85rem", background: "rgba(255,255,255,0.05)" }}
                  >
                    {language === "Tamil" ? "ரத்து" : "Cancel"}
                  </button>
                </div>
              </div>
            )}

            {/* Pipeline Stage */}
            {renderPipeline(item.timeline)}

            {/* Details Panel */}
            <div className="grid-3" style={{ margin: "25px 0" }}>
              <div style={{ background: "rgba(255,255,255,0.02)", border: "1px solid var(--border-gold)", borderRadius: "10px", padding: "15px" }}>
                <span style={{ fontSize: "0.72rem", textTransform: "uppercase", color: "var(--text-muted)", display: "block" }}>
                  {language === "Tamil" ? "நீதிபதி" : "Judge Presiding"}
                </span>
                <span style={{ fontSize: "0.9rem", fontWeight: "600", color: "var(--text-primary)", display: "inline-flex", alignItems: "center", gap: "6px" }}><FaGavel /> {item.judge}</span>
              </div>
              <div style={{ background: "rgba(255,255,255,0.02)", border: "1px solid var(--border-gold)", borderRadius: "10px", padding: "15px" }}>
                <span style={{ fontSize: "0.72rem", textTransform: "uppercase", color: "var(--text-muted)", display: "block" }}>
                  {language === "Tamil" ? "அடுத்த விசாரணை தேதி" : "Next Hearing Date"}
                </span>
                <span style={{ fontSize: "0.9rem", fontWeight: "600", color: "var(--accent-gold-light)", display: "inline-flex", alignItems: "center", gap: "6px" }}><FaHourglassHalf /> {item.next_hearing} ({item.courtroom})</span>
              </div>
              <div style={{ background: "rgba(255,255,255,0.02)", border: "1px solid var(--border-gold)", borderRadius: "10px", padding: "15px" }}>
                <span style={{ fontSize: "0.72rem", textTransform: "uppercase", color: "var(--text-muted)", display: "block" }}>
                  {language === "Tamil" ? "தரப்புகள் (வழக்கறிஞர்கள்)" : "Advocates Representing"}
                </span>
                <span style={{ fontSize: "0.85rem", color: "var(--text-primary)", display: "block" }}>Petitioner: {item.petitioner_adv}</span>
                <span style={{ fontSize: "0.85rem", color: "var(--text-secondary)", display: "block" }}>Respondent: {item.respondent_adv}</span>
              </div>
            </div>

            {/* Hearing Timeline History */}
            <div>
              <h4 style={{ fontFamily: "var(--font-serif)", display: "flex", alignItems: "center", gap: "10px", marginBottom: "15px" }}>
                <FaHistory style={{ color: "var(--accent-gold)" }} />
                {language === "Tamil" ? "விசாரணை வரலாறு & ஆவணங்கள்" : "Hearing History & Timeline"}
              </h4>
              <div className="timeline-container">
                {item.timeline.map((event, eventIdx) => (
                  <div key={eventIdx} className={`timeline-item ${event.status}`}>
                    <div className="timeline-date">{event.date}</div>
                    <div className={`timeline-card ${event.status === "current" ? "current" : ""}`}>
                      <h4 style={{ display: "flex", justifyContent: "space-between" }}>
                        <span>{event.action}</span>
                        {event.status === "completed" && <span style={{ color: "var(--success)", fontSize: "0.85rem" }}>✓ Done</span>}
                        {event.status === "current" && <span style={{ color: "var(--info)", fontSize: "0.85rem", display: "inline-flex", alignItems: "center", gap: "4px" }}><FaHourglassHalf /> Next hearing</span>}
                      </h4>
                      <p style={{ marginTop: "4px" }}>{event.description}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            
          </div>
        ))
      )}
    </div>
  );
};

export default CaseTracker;
