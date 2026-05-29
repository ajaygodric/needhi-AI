import { useState } from "react";
import { generateFir, downloadPdf } from "../utils/api";
import { FaFileSignature, FaUserAlt, FaMapMarkerAlt, FaFileAlt, FaUsers, FaArrowRight, FaArrowLeft, FaDownload } from "react-icons/fa";

const FirWizard = ({ language }) => {
  const [currentStep, setCurrentStep] = useState(1);
  
  // Step 1: Complainant
  const [complainantName, setComplainantName] = useState("");
  const [complainantPhone, setComplainantPhone] = useState("");
  const [complainantAddress, setComplainantAddress] = useState("");
  const [complainantState, setComplainantState] = useState("Tamil Nadu");
  
  // Step 2: Date & Location
  const [incidentDate, setIncidentDate] = useState("");
  const [incidentTime, setIncidentTime] = useState("");
  const [incidentLocation, setIncidentLocation] = useState("");
  const [policeStation, setPoliceStation] = useState("");

  // Step 3: Incident Details
  const [incidentDetails, setIncidentDetails] = useState("");

  // Step 4: Accused & Witness
  const [accusedDetails, setAccusedDetails] = useState("");
  const [witnessDetails, setWitnessDetails] = useState("");

  // Generation result states
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedDraft, setGeneratedDraft] = useState("");

  const steps = [
    { id: 1, label: { English: "Complainant", Tamil: "புகார்தாரர்" }, icon: <FaUserAlt /> },
    { id: 2, label: { English: "Date & Place", Tamil: "இடம் & தேதி" }, icon: <FaMapMarkerAlt /> },
    { id: 3, label: { English: "Incident Details", Tamil: "சம்பவம்" }, icon: <FaFileAlt /> },
    { id: 4, label: { English: "Suspect/Witness", Tamil: "சாட்சிகள்" }, icon: <FaUsers /> },
    { id: 5, label: { English: "Review & Generate", Tamil: "சரிபார்ப்பு" }, icon: <FaFileSignature /> }
  ];

  const handleNextStep = () => {
    if (currentStep < 5) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handlePrevStep = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleGenerateDraft = async () => {
    setIsGenerating(true);
    setGeneratedDraft("");

    // Package incident detailed structure
    const detailedNarrative = `
Incident details: ${incidentDetails}
Accused details: ${accusedDetails || "Unknown accused"}
Witness details: ${witnessDetails || "No witnesses listed"}
Incident date & time: ${incidentDate} around ${incidentTime}
Incident location: ${incidentLocation}
Complainant address: ${complainantAddress}
Complainant contact phone: ${complainantPhone}
    `.trim();

    try {
      const res = await generateFir(detailedNarrative, complainantState, policeStation, complainantName);
      setGeneratedDraft(res.draft);
    } catch (err) {
      console.error(err);
      setGeneratedDraft(`Error generating draft: ${err.message}`);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleDownloadPdf = () => {
    if (!generatedDraft) return;
    downloadPdf("First Information Report (FIR) Draft", generatedDraft, "FIR_Draft_Needhi.pdf");
  };

  return (
    <div>
      <div className="section-header">
        <h2 className="section-title">
          {language === "Tamil" ? "முதன்மை தகவல் அறிக்கை (FIR) எழுதுபவர்" : "FIR Draft Generator Wizard"}
        </h2>
        <p className="section-subtitle">
          {language === "Tamil"
            ? "உங்கள் வழக்கை விவரிக்கவும். காவல்துறை சமர்ப்பிப்பிற்கான முறையான எஃப்.ஐ.ஆர் (FIR) வரைவை எளிய படிகளில் தயார் செய்யுங்கள்."
            : "Describe what happened in a step-by-step wizard. Needhi AI generates a structured, legally formatted FIR ready for printing."}
        </p>
      </div>

      {/* Stepper Header */}
      <div className="stepper-header">
        {steps.map(step => (
          <div
            key={step.id}
            className={`step-indicator ${
              currentStep === step.id ? "active" : currentStep > step.id ? "completed" : ""
            }`}
          >
            <div className="step-circle">
              {currentStep > step.id ? "✓" : step.id}
            </div>
            <div className="step-label">{step.label[language]}</div>
          </div>
        ))}
      </div>

      {/* Step Contents */}
      <div className="card" style={{ marginBottom: "25px" }}>
        
        {/* Step 1: Complainant details */}
        {currentStep === 1 && (
          <div className="step-card">
            <h3 style={{ fontFamily: "var(--font-serif)", marginBottom: "20px" }}>
              1. {language === "Tamil" ? "புகார்தாரர் விவரங்கள்" : "Complainant Identification"}
            </h3>
            <div className="grid-2">
              <div className="input-group">
                <label className="input-label">{language === "Tamil" ? "முழு பெயர்" : "Full Name"}</label>
                <input
                  type="text"
                  className="input-control"
                  placeholder="e.g. Rajesh Kumar"
                  value={complainantName}
                  onChange={(e) => setComplainantName(e.target.value)}
                />
              </div>
              <div className="input-group">
                <label className="input-label">{language === "Tamil" ? "கைபேசி எண்" : "Mobile Phone Number"}</label>
                <input
                  type="text"
                  className="input-control"
                  placeholder="e.g. 9876543210"
                  value={complainantPhone}
                  onChange={(e) => setComplainantPhone(e.target.value)}
                />
              </div>
            </div>
            <div className="grid-2">
              <div className="input-group">
                <label className="input-label">{language === "Tamil" ? "முகவரி" : "Address"}</label>
                <input
                  type="text"
                  className="input-control"
                  placeholder="Street, Area, City"
                  value={complainantAddress}
                  onChange={(e) => setComplainantAddress(e.target.value)}
                />
              </div>
              <div className="input-group">
                <label className="input-label">{language === "Tamil" ? "மாநிலம்" : "State"}</label>
                <input
                  type="text"
                  className="input-control"
                  placeholder="e.g. Tamil Nadu"
                  value={complainantState}
                  onChange={(e) => setComplainantState(e.target.value)}
                />
              </div>
            </div>
          </div>
        )}

        {/* Step 2: Date, Time & Location */}
        {currentStep === 2 && (
          <div className="step-card">
            <h3 style={{ fontFamily: "var(--font-serif)", marginBottom: "20px" }}>
              2. {language === "Tamil" ? "சம்பவ தேதி மற்றும் இடம்" : "Incident Date & Place of Occurrence"}
            </h3>
            <div className="grid-2">
              <div className="input-group">
                <label className="input-label">{language === "Tamil" ? "சம்பவ தேதி" : "Incident Date"}</label>
                <input
                  type="date"
                  className="input-control"
                  value={incidentDate}
                  onChange={(e) => setIncidentDate(e.target.value)}
                />
              </div>
              <div className="input-group">
                <label className="input-label">{language === "Tamil" ? "சம்பவ நேரம்" : "Approximate Time"}</label>
                <input
                  type="text"
                  className="input-control"
                  placeholder="e.g. Around 8:30 PM"
                  value={incidentTime}
                  onChange={(e) => setIncidentTime(e.target.value)}
                />
              </div>
            </div>
            <div className="grid-2">
              <div className="input-group">
                <label className="input-label">{language === "Tamil" ? "சம்பவம் நடந்த இடம்" : "Specific Place of Occurrence"}</label>
                <input
                  type="text"
                  className="input-control"
                  placeholder="e.g. Near T-Nagar Metro Gate A, Chennai"
                  value={incidentLocation}
                  onChange={(e) => setIncidentLocation(e.target.value)}
                />
              </div>
              <div className="input-group">
                <label className="input-label">{language === "Tamil" ? "காவல் நிலையம்" : "Jurisdictional Police Station"}</label>
                <input
                  type="text"
                  className="input-control"
                  placeholder="e.g. R4 Pondy Bazaar Police Station"
                  value={policeStation}
                  onChange={(e) => setPoliceStation(e.target.value)}
                />
              </div>
            </div>
          </div>
        )}

        {/* Step 3: Narrative */}
        {currentStep === 3 && (
          <div className="step-card">
            <h3 style={{ fontFamily: "var(--font-serif)", marginBottom: "20px" }}>
              3. {language === "Tamil" ? "சம்பவத்தின் விவரங்கள்" : "Detailed Description (Statement of Facts)"}
            </h3>
            <div className="input-group">
              <label className="input-label">
                {language === "Tamil" 
                  ? "நடந்த சம்பவத்தை விரிவாக விளக்கவும் (என்ன நடந்தது? யார் செய்தது? என்ன பொருட்கள் திருடுபோனது?)"
                  : "Explain clearly what transpired (who did what, chronological events, items lost, weapons used if any):"}
              </label>
              <textarea
                rows="6"
                className="input-control"
                placeholder={
                  language === "Tamil"
                    ? "எ.கா. 15 மே மாலை 8 மணிக்கு, இரண்டு அடையாளம் தெரியாத நபர்கள் என் மொபைல் போனை பறித்துவிட்டு தப்பினர்..."
                    : "e.g. Two unknown bike-borne individuals approached me from behind. The pillion rider snatched my phone (iPhone 14) from my hand and fled towards..."
                }
                value={incidentDetails}
                onChange={(e) => setIncidentDetails(e.target.value)}
              ></textarea>
            </div>
          </div>
        )}

        {/* Step 4: Accused & Witness */}
        {currentStep === 4 && (
          <div className="step-card">
            <h3 style={{ fontFamily: "var(--font-serif)", marginBottom: "20px" }}>
              4. {language === "Tamil" ? "எதிரி மற்றும் சாட்சிகள் விவரம்" : "Accused (Suspects) & Witness Identification"}
            </h3>
            <div className="input-group">
              <label className="input-label">{language === "Tamil" ? "எதிரி/சந்தேகத்திற்குரியவர்கள் விவரம் (தெரிந்தால்)" : "Accused/Suspect Details (Name, physical features, vehicle number, clothing)"}</label>
              <input
                type="text"
                className="input-control"
                placeholder="e.g. Two young males, bike model: Black Splendor TN-01-AB-1234, rider wearing red helmet"
                value={accusedDetails}
                onChange={(e) => setAccusedDetails(e.target.value)}
              />
            </div>
            <div className="input-group">
              <label className="input-label">{language === "Tamil" ? "சாட்சிகள் விவரம் (ஏதேனும் இருப்பின்)" : "Witness Details (Name, address, contact if any eye-witnesses were present)"}</label>
              <textarea
                rows="3"
                className="input-control"
                placeholder="e.g. Shopkeeper Murugan (Tea Shop nearby) witnessed the incident..."
                value={witnessDetails}
                onChange={(e) => setWitnessDetails(e.target.value)}
              ></textarea>
            </div>
          </div>
        )}

        {/* Step 5: Review & Final Output */}
        {currentStep === 5 && (
          <div className="step-card">
            <h3 style={{ fontFamily: "var(--font-serif)", marginBottom: "20px" }}>
              5. {language === "Tamil" ? "பிரிவு சரிபார்ப்பு & வரைவு உருவாக்கம்" : "Review Inputs & Generate Official Draft"}
            </h3>

            <div style={{ marginBottom: "25px", border: "1px solid var(--border-gold)", borderRadius: "10px", padding: "16px", background: "rgba(255,255,255,0.01)" }}>
              <div className="review-row">
                <span className="label">Complainant:</span>
                <span className="val">{complainantName || "________________________"}</span>
              </div>
              <div className="review-row">
                <span className="label">Contact Info:</span>
                <span className="val">{complainantPhone || "________________________"}</span>
              </div>
              <div className="review-row">
                <span className="label">Incident Date:</span>
                <span className="val">{incidentDate ? `${incidentDate} @ ${incidentTime}` : "________________________"}</span>
              </div>
              <div className="review-row">
                <span className="label">Jurisdiction PS:</span>
                <span className="val">{policeStation || "________________________"} ({complainantState})</span>
              </div>
              <div className="review-row" style={{ borderBottom: "none" }}>
                <span className="label">Description Summary:</span>
                <span className="val" style={{ overflow: "hidden", textOverflow: "ellipsis", display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical" }}>
                  {incidentDetails || "No incident description provided."}
                </span>
              </div>
            </div>

            <button className="btn btn-primary" onClick={handleGenerateDraft} disabled={isGenerating || !incidentDetails.trim()} style={{ width: "100%", marginBottom: "20px" }}>
              {isGenerating ? (language === "Tamil" ? "எஃப்.ஐ.ஆர் வரைவு தயாரிக்கப்படுகிறது..." : "Generating Legal Draft...") : (language === "Tamil" ? "எஃப்.ஐ.ஆர் வரைவை உருவாக்கு" : "Generate FIR Draft")}
            </button>

            {generatedDraft && (
              <div>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
                  <h4 style={{ fontFamily: "var(--font-serif)" }}>{language === "Tamil" ? "உருவாக்கப்பட்ட எஃப்.ஐ.ஆர் வரைவு" : "Generated FIR Document Draft"}</h4>
                  <button className="btn btn-small" onClick={handleDownloadPdf}>
                    <FaDownload /> {language === "Tamil" ? "PDF பதிவிறக்கு" : "Download PDF"}
                  </button>
                </div>
                <div style={{ background: "rgba(255,255,255,0.03)", border: "1px solid var(--border-gold)", borderRadius: "10px", padding: "20px", fontSize: "0.93rem", fontFamily: "monospace", whiteSpace: "pre-wrap", overflowX: "auto" }}>
                  {generatedDraft}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Stepper Buttons */}
        <div style={{ display: "flex", justifyContent: "space-between", borderTop: "1px solid rgba(201,168,76,0.15)", paddingTop: "20px", marginTop: "20px" }}>
          <button className="btn" onClick={handlePrevStep} disabled={currentStep === 1}>
            <FaArrowLeft /> {language === "Tamil" ? "முந்தையது" : "Previous"}
          </button>
          
          {currentStep < 5 ? (
            <button className="btn btn-primary" onClick={handleNextStep}>
              {language === "Tamil" ? "அடுத்தது" : "Next"} <FaArrowRight />
            </button>
          ) : null}
        </div>
      </div>
    </div>
  );
};

export default FirWizard;
