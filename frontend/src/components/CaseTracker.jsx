import { useState, useEffect } from "react";
import { searchCases, downloadPdf, subscribeToCase } from "../utils/api";
import { FaSearch, FaHistory, FaGavel, FaHourglassHalf, FaRegFolderOpen, FaMapMarkerAlt, FaDownload, FaEnvelope } from "react-icons/fa";

const CaseTracker = ({ language, user }) => {
  const [searchVal, setSearchVal] = useState("");
  const [searchType, setSearchType] = useState("CNR Number");
  const [courtType, setCourtType] = useState("District Court");
  const [selectedState, setSelectedState] = useState("Tamil Nadu");
  const [cases, setCases] = useState([]);
  const [hasSearched, setHasSearched] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  // Email alerts subscription and PDF states
  const [activeSubCnr, setActiveSubCnr] = useState(null);
  const [subLoading, setSubLoading] = useState(false);
  const [subscribedCnrs, setSubscribedCnrs] = useState({});
  const [mySubscriptions, setMySubscriptions] = useState([]);
  const [isMySubsLoading, setIsMySubsLoading] = useState(false);

  const fetchMySubscriptions = async () => {
    if (!user) return;
    setIsMySubsLoading(true);
    try {
      const response = await fetch("/api/cases/my-subscriptions", {
        headers: {
          "Authorization": `Bearer ${user.token}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setMySubscriptions(data || []);
        
        const cnrMap = {};
        data.forEach(sub => {
          cnrMap[sub.cnr] = true;
        });
        setSubscribedCnrs(cnrMap);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsMySubsLoading(false);
    }
  };

  useEffect(() => {
    fetchMySubscriptions();
  }, [user]);


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
    if (!user) return;
    setSubLoading(true);
    try {
      await subscribeToCase(cnr, user.email, user.name, language);
      setSubscribedCnrs(prev => ({ ...prev, [cnr]: user.email }));
      setActiveSubCnr(null);
      await fetchMySubscriptions();
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
        <div style={{ margin: "6px 0 12px 0" }}>
          <span style={{ 
            display: "inline-block", 
            background: "rgba(201, 168, 76, 0.12)", 
            color: "var(--accent-gold-light)", 
            border: "1px solid rgba(201, 168, 76, 0.3)", 
            padding: "4px 10px", 
            borderRadius: "6px", 
            fontSize: "0.78rem", 
            fontWeight: "600",
            textTransform: "uppercase",
            letterSpacing: "0.5px"
          }}>
            ⚠️ {language === "Tamil" ? "அமைப்பு கட்டுமானத்தில் உள்ளது (டெமோ தரவு)" : "System Under Construction (Running on Sandbox Demo Data)"}
          </span>
        </div>
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
                      onClick={() => handleSubscribe(item.cnr)}
                      disabled={subLoading}
                      style={{ padding: "6px 12px", fontSize: "0.82rem", display: "inline-flex", alignItems: "center", gap: "6px", background: "rgba(255,255,255,0.04)" }}
                    >
                      <FaEnvelope /> {subLoading ? "..." : (language === "Tamil" ? "விழிப்பூட்டல்" : "Subscribe")}
                    </button>
                  )}
                </div>
              </div>
            </div>

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

      {!hasSearched && !isLoading && (
        <div style={{ marginTop: "20px", animation: "fadeIn 0.3s ease" }}>
          <h3 style={{ fontFamily: "var(--font-serif)", color: "var(--accent-gold-light)", marginBottom: "15px", display: "flex", alignItems: "center", gap: "10px", borderBottom: "1px solid rgba(255,255,255,0.06)", paddingBottom: "10px" }}>
            <FaHistory style={{ color: "var(--accent-gold)" }} />
            {language === "Tamil" ? "கண்காணிக்கப்படும் வழக்குகள்" : "Your Tracked Cases"}
          </h3>
          
          {isMySubsLoading ? (
            <div className="card loading-pulse" style={{ height: "150px" }}></div>
          ) : mySubscriptions.length === 0 ? (
            <div className="card" style={{ padding: "40px", textAlign: "center" }}>
              <FaRegFolderOpen style={{ fontSize: "2.5rem", color: "var(--border-gold)", marginBottom: "12px" }} />
              <p style={{ color: "var(--text-secondary)", fontSize: "0.95rem" }}>
                {language === "Tamil" 
                  ? "நீங்கள் இன்னும் எந்த வழக்கையும் கண்காணிக்கவில்லை. தேடல் முடிவுகளில் 'விழிப்பூட்டல்' ஐக் கிளிக் செய்க." 
                  : "You are not tracking any cases yet. Search for a case and click 'Subscribe' to receive email alerts."}
              </p>
            </div>
          ) : (
            <div className="grid-2" style={{ gap: "20px" }}>
              {mySubscriptions.map((sub) => (
                <div key={sub.cnr} className="card" style={{ border: "1px solid var(--border-gold)", padding: "18px", display: "flex", flexDirection: "column", gap: "10px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                    <div>
                      <span className="badge badge-blue" style={{ fontSize: "0.72rem", marginBottom: "4px" }}>
                        {sub.case_details.case_no}
                      </span>
                      <h4 style={{ fontFamily: "var(--font-serif)", fontSize: "1.1rem", margin: 0, color: "var(--text-primary)" }}>
                        {language === "Tamil" ? sub.case_details.tamil_title || sub.case_details.title : sub.case_details.title}
                      </h4>
                    </div>
                    <button 
                      className="btn btn-small" 
                      onClick={() => handleDownloadCasePdf(sub.case_details)}
                      style={{ padding: "4px 8px", fontSize: "0.78rem" }}
                    >
                      <FaDownload />
                    </button>
                  </div>
                  
                  <div style={{ display: "flex", flexDirection: "column", gap: "6px", fontSize: "0.82rem", borderTop: "1px solid rgba(255,255,255,0.06)", paddingTop: "8px", marginTop: "5px" }}>
                    <div style={{ display: "flex", justifyContent: "space-between" }}>
                      <span style={{ color: "var(--text-secondary)" }}>CNR:</span>
                      <span style={{ fontFamily: "monospace", color: "var(--accent-gold)" }}>{sub.cnr}</span>
                    </div>
                    <div style={{ display: "flex", justifyContent: "space-between" }}>
                      <span style={{ color: "var(--text-secondary)" }}>Next Hearing:</span>
                      <span style={{ fontWeight: "600", color: "var(--accent-gold-light)" }}>
                        {sub.case_details.next_hearing}
                      </span>
                    </div>
                    <div style={{ display: "flex", justifyContent: "space-between" }}>
                      <span style={{ color: "var(--text-secondary)" }}>Current Stage:</span>
                      <span>{language === "Tamil" ? sub.case_details.tamil_stage || sub.case_details.current_stage : sub.case_details.current_stage}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default CaseTracker;
