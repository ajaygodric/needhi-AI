import { useState } from "react";
import { predictCaseOutcome, downloadPdf } from "../utils/api";
import { renderMarkdown } from "../utils/renderMarkdown";
import { FaGavel, FaInfoCircle, FaFilePdf } from "react-icons/fa";

const CasePredictor = ({ language }) => {
  const [offense, setOffense] = useState("");
  const [narrative, setNarrative] = useState("");
  const [evidence, setEvidence] = useState([]);
  const [priorRecord, setPriorRecord] = useState("None");
  const [jurisdiction, setJurisdiction] = useState("Tamil Nadu");
  
  const [isPredicting, setIsPredicting] = useState(false);
  const [predictionResult, setPredictionResult] = useState("");
  const [errorMessage, setErrorMessage] = useState("");

  const evidenceOptions = [
    { id: "eyewitness", label: { English: "Eyewitness Statements", Tamil: "நேரடி சாட்சிகள்" } },
    { id: "cctv", label: { English: "CCTV / Video Footage", Tamil: "சிசிடிவி / வீடியோ ஆதாரங்கள்" } },
    { id: "audio", label: { English: "Audio Recordings / Call logs", Tamil: "ஆடியோ / தொலைபேசி பதிவுகள்" } },
    { id: "contracts", label: { English: "Written Agreements / Receipts", Tamil: "எழுதப்பட்ட ஒப்பந்தம் / ரசீதுகள்" } },
    { id: "digital", label: { English: "Emails / Chats / Digital Trails", Tamil: "மின்னஞ்சல் / வாட்ஸ்அப் உரையாடல்கள்" } },
    { id: "medical", label: { English: "Medical / Forensic Reports", Tamil: "மருத்துவ / தடயவியல் அறிக்கைகள்" } },
    { id: "none", label: { English: "No Direct Evidence (Circumstantial)", Tamil: "நேரடி ஆதாரங்கள் இல்லை (சூழ்நிலை மட்டுமே)" } }
  ];

  const handleEvidenceChange = (id) => {
    if (evidence.includes(id)) {
      setEvidence(evidence.filter(e => e !== id));
    } else {
      setEvidence([...evidence, id]);
    }
  };

  const handlePredict = async (e) => {
    e.preventDefault();
    if (!offense.trim() || !narrative.trim()) return;

    setIsPredicting(true);
    setPredictionResult("");
    setErrorMessage("");

    try {
      // Map evidence IDs to labels
      const activeEvidenceLabels = evidence.map(evId => {
        const option = evidenceOptions.find(opt => opt.id === evId);
        return option ? option.label.English : evId;
      });

      const res = await predictCaseOutcome(
        offense,
        narrative,
        activeEvidenceLabels,
        priorRecord,
        jurisdiction,
        language
      );
      setPredictionResult(res.prediction);
    } catch (err) {
      console.error(err);
      setErrorMessage(err.message || "Failed to generate prediction outcome.");
    } finally {
      setIsPredicting(false);
    }
  };



  // Extract quick metrics from text
  const getOutcomeBadge = (text) => {
    if (!text) return null;
    const t = text.toLowerCase();
    
    let bailProb = language === "Tamil" ? "நடுத்தர" : "Medium";
    let bailColor = "badge-yellow";
    
    const bailHigh = /bail\s*(probability)?[:\*\s]+high/i.test(t) || /ஜாமீன்.*உயர்/i.test(t) || /வாய்ப்பு.*உயர்/i.test(t);
    const bailLow = /bail\s*(probability)?[:\*\s]+low/i.test(t) || /ஜாமீன்.*(குறைந்த|குறைவு)/i.test(t) || /வாய்ப்பு.*(குறைந்த|குறைவு)/i.test(t);
    
    if (bailHigh) {
      bailProb = language === "Tamil" ? "உயர்" : "High";
      bailColor = "badge-green";
    } else if (bailLow) {
      bailProb = language === "Tamil" ? "குறைந்த" : "Low";
      bailColor = "badge-red";
    }

    let suitStrength = language === "Tamil" ? "நடுத்தரம்" : "Moderate";
    let strengthColor = "badge-yellow";
    
    const strengthStrong = /case\s*(strength)?[:\*\s]+strong/i.test(t) || /வழக்கின்\s*பலம்.*பலமானது/i.test(t) || /பலம்.*பலமானது/i.test(t);
    const strengthWeak = /case\s*(strength)?[:\*\s]+weak/i.test(t) || /வழக்கின்\s*பலம்.*பலவீனமானது/i.test(t) || /பலம்.*பலவீனமானது/i.test(t);
    
    if (strengthStrong) {
      suitStrength = language === "Tamil" ? "பலமானது" : "Strong";
      strengthColor = "badge-green";
    } else if (strengthWeak) {
      suitStrength = language === "Tamil" ? "பலவீனமானது" : "Weak";
      strengthColor = "badge-red";
    }

    return (
      <div className="grid-2" style={{ gap: "15px", marginBottom: "20px" }}>
        <div style={{ background: "rgba(255,255,255,0.02)", border: "1px solid var(--border-gold)", borderRadius: "8px", padding: "12px", textAlign: "center" }}>
          <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)", textTransform: "uppercase", marginBottom: "4px" }}>
            {language === "Tamil" ? "ஜாமீன் பெற வாய்ப்பு" : "Bail Probability"}
          </div>
          <span className={`badge ${bailColor}`} style={{ fontSize: "0.95rem", padding: "6px 16px" }}>{bailProb}</span>
        </div>
        <div style={{ background: "rgba(255,255,255,0.02)", border: "1px solid var(--border-gold)", borderRadius: "8px", padding: "12px", textAlign: "center" }}>
          <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)", textTransform: "uppercase", marginBottom: "4px" }}>
            {language === "Tamil" ? "வழக்கின் பலம்" : "Case Strength"}
          </div>
          <span className={`badge ${strengthColor}`} style={{ fontSize: "0.95rem", padding: "6px 16px" }}>{suitStrength}</span>
        </div>
      </div>
    );
  };

  return (
    <div>
      <div className="section-header">
        <h2 className="section-title">
          {language === "Tamil" ? "வழக்கு விளைவு கணிப்பான்" : "Case Outcome Predictor"}
        </h2>
        <p className="section-subtitle">
          {language === "Tamil"
            ? "வழக்கின் விவரங்கள் மற்றும் சான்றுகளின் அடிப்படையில் ஜாமீன் வாய்ப்பு, வழக்கின் பலம் மற்றும் தண்டனைகளை கணிக்கவும்."
            : "Input case parameters, facts, and available evidence to generate a detailed estimate of potential bail, sentencing, and overall case strength."}
        </p>
      </div>

      <div className="grid-3" style={{ gap: "25px", alignItems: "start" }}>
        
        {/* Facts Input Form */}
        <div className="card" style={{ gridColumn: "span 1" }}>
          <form onSubmit={handlePredict}>
            <h4 style={{ fontFamily: "var(--font-serif)", marginBottom: "20px", color: "var(--accent-gold-light)" }}>
              {language === "Tamil" ? "வழக்கின் விவரங்கள்" : "Case Parameters"}
            </h4>

            {/* Offense Name */}
            <div className="input-group">
              <label className="input-label">
                {language === "Tamil" ? "குற்றம் அல்லது தகராறின் வகை" : "Offense / Dispute Type"}
              </label>
              <input
                type="text"
                className="input-control"
                placeholder={language === "Tamil" ? "எ.கா. திருட்டு, செக் மோசடி, ஒப்பந்த மீறல்" : "e.g. Cheating (Sec 318 BNS), Theft, Breach of Contract"}
                required
                value={offense}
                onChange={(e) => setOffense(e.target.value)}
              />
            </div>

            {/* State Jurisdiction */}
            <div className="input-group">
              <label className="input-label">
                {language === "Tamil" ? "அதிகார வரம்பு (மாநிலம்)" : "State Jurisdiction"}
              </label>
              <input
                type="text"
                className="input-control"
                placeholder="e.g. Tamil Nadu"
                value={jurisdiction}
                onChange={(e) => setJurisdiction(e.target.value)}
              />
            </div>

            {/* Prior Criminal Record */}
            <div className="input-group">
              <label className="input-label">
                {language === "Tamil" ? "முந்தைய குற்றப் பின்னணி" : "Prior Criminal Record"}
              </label>
              <select 
                className="input-control" 
                value={priorRecord} 
                onChange={(e) => setPriorRecord(e.target.value)}
              >
                <option value="None">{language === "Tamil" ? "ஏதுமில்லை (None)" : "None"}</option>
                <option value="Minor offenses">{language === "Tamil" ? "சிறு குற்றங்கள் (Minor Offenses)" : "Minor Offenses"}</option>
                <option value="Similar offenses">{language === "Tamil" ? "ஒத்த குற்றங்கள் (Same/Similar)" : "Same/Similar Offenses"}</option>
                <option value="Multiple major offenses">{language === "Tamil" ? "பல பெரிய குற்றங்கள்" : "Multiple Major Offenses"}</option>
              </select>
            </div>

            {/* Evidence Available */}
            <div className="input-group" style={{ marginBottom: "25px" }}>
              <label className="input-label" style={{ marginBottom: "10px" }}>
                {language === "Tamil" ? "கிடைக்கக்கூடிய ஆதாரங்கள்" : "Evidence Available"}
              </label>
              <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                {evidenceOptions.map(opt => (
                  <label key={opt.id} style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "0.85rem", color: "var(--text-secondary)", cursor: "pointer" }}>
                    <input
                      type="checkbox"
                      checked={evidence.includes(opt.id)}
                      onChange={() => handleEvidenceChange(opt.id)}
                      style={{ accentColor: "var(--accent-gold)" }}
                    />
                    <span>{opt.label[language]}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Factual Narrative */}
            <div className="input-group">
              <label className="input-label">
                {language === "Tamil" ? "சம்பவத்தின் முழு விவரம்" : "Factual Narrative"}
              </label>
              <textarea
                rows="5"
                className="input-control"
                placeholder={
                  language === "Tamil"
                    ? "நடந்த சம்பவத்தை மற்றும் கிடைத்த ஆதாரங்களை இங்கே சுருக்கமாக விவரிக்கவும்..."
                    : "Describe the chronological sequence of events, what actually happened, and context..."
                }
                required
                value={narrative}
                onChange={(e) => setNarrative(e.target.value)}
              ></textarea>
            </div>

            <button type="submit" className="btn btn-primary" style={{ width: "100%" }} disabled={isPredicting}>
              {isPredicting ? (language === "Tamil" ? "கணிக்கப்படுகிறது..." : "Predicting Outcome...") : (language === "Tamil" ? "விளைவை கணி" : "Predict Case Outcome")}
            </button>
          </form>
        </div>

        {/* Prediction Results Panel */}
        <div style={{ gridColumn: "span 2" }}>
          {predictionResult ? (
            <div className="card">
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px", flexWrap: "wrap", gap: "10px" }}>
                <div className="card-title" style={{ margin: 0 }}>
                  <span><FaGavel /></span>
                  {language === "Tamil" ? "சட்ட கணிப்பு அறிக்கை" : "Case Assessment Report"}
                </div>
                <button 
                  className="btn" 
                  onClick={() => downloadPdf(
                    language === "Tamil" ? "சட்ட கணிப்பு அறிக்கை" : "Case Assessment Report", 
                    predictionResult, 
                    "Case_Assessment_Report.pdf"
                  )}
                  style={{ display: "inline-flex", alignItems: "center", gap: "6px", padding: "6px 12px", fontSize: "0.85rem" }}
                >
                  <FaFilePdf /> {language === "Tamil" ? "PDF பதிவிறக்கு" : "Download PDF"}
                </button>
              </div>

              {/* Dynamic Progress Badges */}
              {getOutcomeBadge(predictionResult)}

              {/* Assessment Text */}
              <div 
                style={{ background: "rgba(255,255,255,0.01)", border: "1px solid var(--border-gold)", borderRadius: "10px", padding: "20px", fontSize: "0.93rem", lineHeight: "1.6" }}
              >
                <div 
                  style={{ whiteSpace: "pre-line" }}
                  dangerouslySetInnerHTML={{ __html: renderMarkdown(predictionResult) }}
                />
              </div>
            </div>
          ) : errorMessage ? (
            <div className="card" style={{ borderLeft: "4px solid var(--danger)", color: "var(--danger)" }}>
              <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
                <FaInfoCircle />
                <span>{errorMessage}</span>
              </div>
            </div>
          ) : (
            <div className="card" style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", minHeight: "350px", textAlign: "center", color: "var(--text-secondary)" }}>
              <FaGavel style={{ fontSize: "3rem", color: "var(--border-gold-hover)", marginBottom: "15px" }} />
              <h4 style={{ fontFamily: "var(--font-serif)", color: "var(--text-primary)", marginBottom: "8px" }}>
                {language === "Tamil" ? "முடிவுகள் தயார் நிலை" : "No Assessment Generated Yet"}
              </h4>
              <p style={{ maxWidth: "400px", fontSize: "0.88rem" }}>
                {language === "Tamil"
                  ? "வழக்கின் தகவல்களை இடதுபுறம் உள்ள படிவத்தில் பூர்த்தி செய்து 'விளைவை கணி' பொத்தானை அழுத்தவும்."
                  : "Fill in the case parameters on the left and submit to view likely legal outcomes and case strength metrics."}
              </p>
            </div>
          )}
        </div>

      </div>
    </div>
  );
};

export default CasePredictor;
