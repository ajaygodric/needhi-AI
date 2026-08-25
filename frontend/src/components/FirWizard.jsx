import { useState } from "react";
import { generateFir, downloadPdf } from "../utils/api";
import { FaFileSignature, FaUserAlt, FaMapMarkerAlt, FaFileAlt, FaUsers, FaArrowRight, FaArrowLeft, FaDownload } from "react-icons/fa";

const FirWizard = ({ language }) => {
  const [currentStep, setCurrentStep] = useState(1);
  
  // Step 1: Complainant
  const [complainantName, setComplainantName] = useState("");
  const [complainantAge, setComplainantAge] = useState("");
  const [complainantParentName, setComplainantParentName] = useState("");
  const [complainantNationality, setComplainantNationality] = useState("Indian");
  const [complainantPhone, setComplainantPhone] = useState("");
  const [complainantAddress, setComplainantAddress] = useState("");
  const [complainantState, setComplainantState] = useState("Tamil Nadu");
  
  // Step 2: Date & Location
  const [incidentDate, setIncidentDate] = useState("");
  const [incidentTime, setIncidentTime] = useState("");
  const [incidentLocation, setIncidentLocation] = useState("");
  const [incidentDistrict, setIncidentDistrict] = useState("");
  const [policeStation, setPoliceStation] = useState("");

  // Step 3: Incident Details
  const [incidentDetails, setIncidentDetails] = useState("");
  const [firCategory, setFirCategory] = useState("General");
  const [categoryFields, setCategoryFields] = useState({});

  const handleCategoryFieldChange = (key, value) => {
    setCategoryFields((prev) => ({
      ...prev,
      [key]: value,
    }));
  };

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

    // Build category description block for narrative
    let categoryNarrative = "";
    if (firCategory !== "General") {
      categoryNarrative = `Incident Category: ${firCategory}\nCategory-specific details:\n` + 
        Object.entries(categoryFields)
          .filter(([_, v]) => v)
          .map(([k, v]) => ` - ${k}: ${v}`)
          .join("\n") + "\n\n";
    }

    // Package incident detailed structure
    const detailedNarrative = `
${categoryNarrative}Incident details: ${incidentDetails}
Accused details: ${accusedDetails || "Unknown accused"}
Witness details: ${witnessDetails || "No witnesses listed"}
Incident date & time: ${incidentDate} around ${incidentTime}
Incident location: ${incidentLocation}${incidentDistrict ? `, District: ${incidentDistrict}` : ""}
Complainant address: ${complainantAddress}
Complainant contact phone: ${complainantPhone}
Complainant age: ${complainantAge || "not specified"}
Complainant parent/husband name: ${complainantParentName || "not specified"}
Complainant nationality: ${complainantNationality || "Indian"}
Declaration place: ${incidentLocation || complainantAddress || "________________________"}
Declaration date: ${incidentDate || "________________________"}
    `.trim();

    try {
      const res = await generateFir(
        detailedNarrative,
        complainantState,
        policeStation,
        complainantName,
        firCategory === "General" ? null : firCategory,
        firCategory === "General" ? null : categoryFields
      );
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
                  placeholder="e.g. Ajay Kumar"
                  value={complainantName}
                  onChange={(e) => setComplainantName(e.target.value)}
                />
              </div>
              <div className="input-group">
                <label className="input-label">{language === "Tamil" ? "வயது" : "Age (years)"}</label>
                <input
                  type="number"
                  className="input-control"
                  placeholder="e.g. 32"
                  min="1"
                  max="120"
                  value={complainantAge}
                  onChange={(e) => setComplainantAge(e.target.value)}
                />
              </div>
            </div>
            <div className="grid-2">
              <div className="input-group">
                <label className="input-label">{language === "Tamil" ? "தந்தை / கணவர் பெயர்" : "Father's / Husband's Name"}</label>
                <input
                  type="text"
                  className="input-control"
                  placeholder="e.g. Ramesh Kumar (Father)"
                  value={complainantParentName}
                  onChange={(e) => setComplainantParentName(e.target.value)}
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
                <label className="input-label">{language === "Tamil" ? "முகவரி" : "Residential Address"}</label>
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
            <div className="grid-2">
              <div className="input-group">
                <label className="input-label">{language === "Tamil" ? "தேசியம்" : "Nationality"}</label>
                <input
                  type="text"
                  className="input-control"
                  placeholder="e.g. Indian"
                  value={complainantNationality}
                  onChange={(e) => setComplainantNationality(e.target.value)}
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
                <label className="input-label">{language === "Tamil" ? "மாவட்டம்" : "District"}</label>
                <input
                  type="text"
                  className="input-control"
                  placeholder="e.g. Chennai"
                  value={incidentDistrict}
                  onChange={(e) => setIncidentDistrict(e.target.value)}
                />
              </div>
            </div>
            <div className="grid-2">
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

            {/* Category Selector */}
            <div className="input-group" style={{ maxWidth: "400px" }}>
              <label className="input-label">
                {language === "Tamil" ? "சம்பவத்தின் வகை" : "Select Incident Category"}
              </label>
              <select 
                className="input-control" 
                value={firCategory} 
                onChange={(e) => {
                  setFirCategory(e.target.value);
                  setCategoryFields({});
                }}
              >
                <option value="General">{language === "Tamil" ? "பொதுவானவை / பிற" : "General / Other"}</option>
                <option value="Domestic Violence">{language === "Tamil" ? "குடும்ப வன்முறை (Domestic Violence)" : "Domestic Violence"}</option>
                <option value="Cyber Fraud">{language === "Tamil" ? "சைபர் மோசடி (Cyber Fraud)" : "Cyber Fraud"}</option>
                <option value="Property Dispute">{language === "Tamil" ? "சொத்து தகராறு (Property Dispute)" : "Property Dispute"}</option>
                <option value="Motor Accident">{language === "Tamil" ? "வாகன விபத்து (Motor Accident)" : "Motor Accident"}</option>
              </select>
            </div>

            {/* Category Specific Guided Fields */}
            {firCategory === "Domestic Violence" && (
              <div className="card" style={{ marginBottom: "20px", background: "rgba(255,255,255,0.01)" }}>
                <h4 style={{ fontFamily: "var(--font-serif)", marginBottom: "15px", color: "var(--accent-gold)" }}>
                  {language === "Tamil" ? "குடும்ப வன்முறை விவரங்கள்" : "Domestic Violence Guided Details"}
                </h4>
                <div className="grid-2">
                  <div className="input-group">
                    <label className="input-label">{language === "Tamil" ? "எதிரியுடனான உறவுமுறை" : "Relationship with Accused"}</label>
                    <select className="input-control" value={categoryFields.relationship || ""} onChange={(e) => handleCategoryFieldChange("relationship", e.target.value)}>
                      <option value="">-- Select --</option>
                      <option value="Husband">{language === "Tamil" ? "கணவர்" : "Husband"}</option>
                      <option value="Father-in-law">{language === "Tamil" ? "மாமனார்" : "Father-in-law"}</option>
                      <option value="Mother-in-law">{language === "Tamil" ? "மாமியார்" : "Mother-in-law"}</option>
                      <option value="Sister-in-law">{language === "Tamil" ? "நாத்தனார் / கணவரின் சகோதரி" : "Sister-in-law"}</option>
                      <option value="Other Relative">{language === "Tamil" ? "இதர உறவினர்" : "Other Relative"}</option>
                    </select>
                  </div>
                  <div className="input-group">
                    <label className="input-label">{language === "Tamil" ? "வன்முறையின் வகை" : "Type of Abuse"}</label>
                    <select className="input-control" value={categoryFields.abuseType || ""} onChange={(e) => handleCategoryFieldChange("abuseType", e.target.value)}>
                      <option value="">-- Select --</option>
                      <option value="Physical & Verbal">{language === "Tamil" ? "உடலளவிலான & வார்த்தை வன்முறை" : "Physical & Verbal"}</option>
                      <option value="Mental & Emotional">{language === "Tamil" ? "மனதளவிலான & உணர்வுப்பூர்வ வன்முறை" : "Mental & Emotional"}</option>
                      <option value="Dowry Harassment">{language === "Tamil" ? "வரதட்சணை கொடுமை" : "Dowry Harassment"}</option>
                      <option value="Economic Deprivation">{language === "Tamil" ? "பொருளாதார உரிமை பறிப்பு" : "Economic Deprivation"}</option>
                    </select>
                  </div>
                </div>
                <div className="grid-2">
                  <div className="input-group">
                    <label className="input-label">{language === "Tamil" ? "வன்முறையின் அதிர்வெண்" : "Frequency of Abuse"}</label>
                    <select className="input-control" value={categoryFields.frequency || ""} onChange={(e) => handleCategoryFieldChange("frequency", e.target.value)}>
                      <option value="">-- Select --</option>
                      <option value="First Time">{language === "Tamil" ? "முதல் முறை" : "First Time"}</option>
                      <option value="Occasional">{language === "Tamil" ? "அவ்வப்போது" : "Occasional"}</option>
                      <option value="Continuous / Chronic">{language === "Tamil" ? "தொடர்ச்சியான கொடுமை" : "Continuous / Chronic"}</option>
                    </select>
                  </div>
                  <div className="input-group">
                    <label className="input-label">{language === "Tamil" ? "மருத்துவ பரிசோதனை செய்யப்பட்டுள்ளதா?" : "Medical Exam Conducted?"}</label>
                    <input type="text" className="input-control" placeholder="e.g. Yes, at Govt Hospital Chennai / G.H. No." value={categoryFields.medicalExam || ""} onChange={(e) => handleCategoryFieldChange("medicalExam", e.target.value)} />
                  </div>
                </div>
                <div className="input-group">
                  <label className="input-label">{language === "Tamil" ? "வரதட்சணை கோரிக்கைகள் (ஏதேனும் இருப்பின்)" : "Dowry Demands Details (If any)"}</label>
                  <input type="text" className="input-control" placeholder="e.g. Demanded 10 sovereigns of gold / ₹5 Lakhs cash" value={categoryFields.dowryDetails || ""} onChange={(e) => handleCategoryFieldChange("dowryDetails", e.target.value)} />
                </div>
              </div>
            )}

            {firCategory === "Cyber Fraud" && (
              <div className="card" style={{ marginBottom: "20px", background: "rgba(255,255,255,0.01)" }}>
                <h4 style={{ fontFamily: "var(--font-serif)", marginBottom: "15px", color: "var(--accent-gold)" }}>
                  {language === "Tamil" ? "சைபர் மோசடி விவரங்கள்" : "Cyber Fraud Guided Details"}
                </h4>
                <div className="grid-2">
                  <div className="input-group">
                    <label className="input-label">{language === "Tamil" ? "இழந்த தொகை (₹)" : "Defrauded Amount (₹)"}</label>
                    <input type="number" className="input-control" placeholder="e.g. 50000" value={categoryFields.amount || ""} onChange={(e) => handleCategoryFieldChange("amount", e.target.value)} />
                  </div>
                  <div className="input-group">
                    <label className="input-label">{language === "Tamil" ? "மோசடி நடந்த தேதி & நேரம்" : "Date & Time of Transaction"}</label>
                    <input type="text" className="input-control" placeholder="e.g. 15th May 2026, 4:30 PM" value={categoryFields.transactionTime || ""} onChange={(e) => handleCategoryFieldChange("transactionTime", e.target.value)} />
                  </div>
                </div>
                <div className="grid-2">
                  <div className="input-group">
                    <label className="input-label">{language === "Tamil" ? "பரிவர்த்தனை குறிப்பு எண் (UPI/Txn ID)" : "Transaction Reference / UPI ID"}</label>
                    <input type="text" className="input-control" placeholder="e.g. UPI Ref: 615283920192" value={categoryFields.txnId || ""} onChange={(e) => handleCategoryFieldChange("txnId", e.target.value)} />
                  </div>
                  <div className="input-group">
                    <label className="input-label">{language === "Tamil" ? "சந்தேகத்திற்குரிய கணக்கு / எண்" : "Suspect Account / Phone / UPI"}</label>
                    <input type="text" className="input-control" placeholder="e.g. WhatsApp: +91-9876543210, UPI: scammer@okaxis" value={categoryFields.suspectInfo || ""} onChange={(e) => handleCategoryFieldChange("suspectInfo", e.target.value)} />
                  </div>
                </div>
                <div className="grid-2">
                  <div className="input-group">
                    <label className="input-label">{language === "Tamil" ? "மோசடி முறை (Modus Operandi)" : "Modus Operandi"}</label>
                    <select className="input-control" value={categoryFields.modusOperandi || ""} onChange={(e) => handleCategoryFieldChange("modusOperandi", e.target.value)}>
                      <option value="">-- Select --</option>
                      <option value="OTP / KYC Fraud">{language === "Tamil" ? "OTP / KYC மோசடி" : "OTP / KYC Fraud"}</option>
                      <option value="Phishing Link / Malicious Website">{language === "Tamil" ? "போலி இணையதள லிங்க்" : "Phishing Link / Malicious Website"}</option>
                      <option value="Part-time Job / Task Scam">{language === "Tamil" ? "பகுதி நேர வேலை மோசடி" : "Part-time Job / Task Scam"}</option>
                      <option value="Lottery / Prize Scam">{language === "Tamil" ? "பரிசு விழுந்ததாக ஏமாற்றுதல்" : "Lottery / Prize Scam"}</option>
                      <option value="OLX / Fake Buyer / Seller">{language === "Tamil" ? "OLX / போலி வாங்குபவர் மோசடி" : "OLX / Fake Buyer / Seller"}</option>
                      <option value="Crypto Investment Scam">{language === "Tamil" ? "கிரிப்டோ முதலீட்டு மோசடி" : "Crypto Investment Scam"}</option>
                    </select>
                  </div>
                  <div className="input-group">
                    <label className="input-label">{language === "Tamil" ? "சைபர் செல் புகார் எண் (இருப்பின்)" : "National Cyber Crime Complaint ID"}</label>
                    <input type="text" className="input-control" placeholder="e.g. 303052600123" value={categoryFields.cyberCellId || ""} onChange={(e) => handleCategoryFieldChange("cyberCellId", e.target.value)} />
                  </div>
                </div>
              </div>
            )}

            {firCategory === "Property Dispute" && (
              <div className="card" style={{ marginBottom: "20px", background: "rgba(255,255,255,0.01)" }}>
                <h4 style={{ fontFamily: "var(--font-serif)", marginBottom: "15px", color: "var(--accent-gold)" }}>
                  {language === "Tamil" ? "சொத்து தகராறு விவரங்கள்" : "Property Dispute Guided Details"}
                </h4>
                <div className="grid-2">
                  <div className="input-group">
                    <label className="input-label">{language === "Tamil" ? "சொத்தின் முகவரி & எல்லைகள்" : "Property Location & Address"}</label>
                    <input type="text" className="input-control" placeholder="e.g. Survey No. 45/2, Adyar, Chennai" value={categoryFields.propertyLocation || ""} onChange={(e) => handleCategoryFieldChange("propertyLocation", e.target.value)} />
                  </div>
                  <div className="input-group">
                    <label className="input-label">{language === "Tamil" ? "சர்வே / பட்டா / பத்திரம் எண்" : "Survey / Patta / Document Number"}</label>
                    <input type="text" className="input-control" placeholder="e.g. Patta No. 1204, Document: 456/2018" value={categoryFields.documentNo || ""} onChange={(e) => handleCategoryFieldChange("documentNo", e.target.value)} />
                  </div>
                </div>
                <div className="grid-2">
                  <div className="input-group">
                    <label className="input-label">{language === "Tamil" ? "தகராறின் தன்மை" : "Nature of Dispute"}</label>
                    <select className="input-control" value={categoryFields.disputeNature || ""} onChange={(e) => handleCategoryFieldChange("disputeNature", e.target.value)}>
                      <option value="">-- Select --</option>
                      <option value="Illegal Encroachment">{language === "Tamil" ? "ஆக்கிரமிப்பு" : "Illegal Encroachment"}</option>
                      <option value="Unauthorized Trespassing">{language === "Tamil" ? "அத்துமீறி நுழைதல்" : "Unauthorized Trespassing"}</option>
                      <option value="Property Damage / Mischief">{language === "Tamil" ? "சொத்து சேதப்படுத்துதல்" : "Property Damage / Mischief"}</option>
                      <option value="Forged Land Documents">{language === "Tamil" ? "போலி ஆவணங்கள் தயாரித்தல்" : "Forged Land Documents"}</option>
                      <option value="Boundary Alteration">{language === "Tamil" ? "எல்லை கல்லை மாற்றுதல்" : "Boundary Alteration"}</option>
                    </select>
                  </div>
                  <div className="input-group">
                    <label className="input-label">{language === "Tamil" ? "உரிமை ஆவண வகை" : "Ownership Document Type"}</label>
                    <select className="input-control" value={categoryFields.ownershipDoc || ""} onChange={(e) => handleCategoryFieldChange("ownershipDoc", e.target.value)}>
                      <option value="">-- Select --</option>
                      <option value="Registered Sale Deed">{language === "Tamil" ? "பதிவு செய்யப்பட்ட கிரையப் பத்திரம்" : "Registered Sale Deed"}</option>
                      <option value="Patta Chitta">{language === "Tamil" ? "பட்டா சிட்டா" : "Patta Chitta"}</option>
                      <option value="Registered Will">{language === "Tamil" ? "உயில் சாசனம்" : "Registered Will"}</option>
                      <option value="Gift Deed / Partition Deed">{language === "Tamil" ? "தான செட்டில்மென்ட் / பாகப்பிரிவினை" : "Gift Deed / Partition Deed"}</option>
                      <option value="Possession/Ancestral Land">{language === "Tamil" ? "பரம்பரை சொத்து / அனுபவ பாத்தியதை" : "Possession/Ancestral Land"}</option>
                    </select>
                  </div>
                </div>
                <div className="grid-2">
                  <div className="input-group">
                    <label className="input-label">{language === "Tamil" ? "அத்துமீறல் நடந்த தேதி" : "Date of Trespass/Encroachment"}</label>
                    <input type="text" className="input-control" placeholder="e.g. 10th May 2026" value={categoryFields.disputeDate || ""} onChange={(e) => handleCategoryFieldChange("disputeDate", e.target.value)} />
                  </div>
                  <div className="input-group">
                    <label className="input-label">{language === "Tamil" ? "சேதம் / இழப்பு விவரங்கள்" : "Details of Damage/Loss (if any)"}</label>
                    <input type="text" className="input-control" placeholder="e.g. Demolished the compound wall costing ₹50,000" value={categoryFields.damageDetails || ""} onChange={(e) => handleCategoryFieldChange("damageDetails", e.target.value)} />
                  </div>
                </div>
              </div>
            )}

            {firCategory === "Motor Accident" && (
              <div className="card" style={{ marginBottom: "20px", background: "rgba(255,255,255,0.01)" }}>
                <h4 style={{ fontFamily: "var(--font-serif)", marginBottom: "15px", color: "var(--accent-gold)" }}>
                  {language === "Tamil" ? "வாகன விபத்து விவரங்கள்" : "Motor Accident Guided Details"}
                </h4>
                <div className="grid-2">
                  <div className="input-group">
                    <label className="input-label">{language === "Tamil" ? "உங்கள் வாகன எண்" : "Your Vehicle Number"}</label>
                    <input type="text" className="input-control" placeholder="e.g. TN-07-BY-1234" value={categoryFields.victimVehicle || ""} onChange={(e) => handleCategoryFieldChange("victimVehicle", e.target.value)} />
                  </div>
                  <div className="input-group">
                    <label className="input-label">{language === "Tamil" ? "விபத்தை ஏற்படுத்திய வாகன எண் & வகை" : "Accused Vehicle Number & Make"}</label>
                    <input type="text" className="input-control" placeholder="e.g. TN-01-AB-5678 (White Swift Car)" value={categoryFields.accusedVehicle || ""} onChange={(e) => handleCategoryFieldChange("accusedVehicle", e.target.value)} />
                  </div>
                </div>
                <div className="grid-2">
                  <div className="input-group">
                    <label className="input-label">{language === "Tamil" ? "காயத்தின் விவரம்" : "Nature of Injury"}</label>
                    <select className="input-control" value={categoryFields.injuryNature || ""} onChange={(e) => handleCategoryFieldChange("injuryNature", e.target.value)}>
                      <option value="">-- Select --</option>
                      <option value="Minor Injuries (abrasions, bruises)">{language === "Tamil" ? "சிறு காயங்கள்" : "Minor Injuries (abrasions, bruises)"}</option>
                      <option value="Grievous Hurt (fractures, severe cuts)">{language === "Tamil" ? "கொடுங்காயம் / எலும்பு முறிவு" : "Grievous Hurt (fractures, severe cuts)"}</option>
                      <option value="Fatal Injury / Death occurred">{language === "Tamil" ? "உயிரிழப்பு / மரணம்" : "Fatal Injury / Death occurred"}</option>
                    </select>
                  </div>
                  <div className="input-group">
                    <label className="input-label">{language === "Tamil" ? "ஓட்டுநரின் விவரம் (தெரிந்தால்)" : "Driver Details (if known)"}</label>
                    <input type="text" className="input-control" placeholder="e.g. Drunk, fled the spot, or driver name" value={categoryFields.driverDetails || ""} onChange={(e) => handleCategoryFieldChange("driverDetails", e.target.value)} />
                  </div>
                </div>
                <div className="grid-2">
                  <div className="input-group">
                    <label className="input-label">{language === "Tamil" ? "அனுமதிக்கப்பட்ட மருத்துவமனை" : "Hospital Admitted"}</label>
                    <input type="text" className="input-control" placeholder="e.g. Apollo Hospital, Greams Road / Wound Certificate No." value={categoryFields.hospitalName || ""} onChange={(e) => handleCategoryFieldChange("hospitalName", e.target.value)} />
                  </div>
                  <div className="input-group">
                    <label className="input-label">{language === "Tamil" ? "அதிவேகம் / கவனக்குறைவு விவரம்" : "Speed / Negligence Description"}</label>
                    <select className="input-control" value={categoryFields.negligenceType || ""} onChange={(e) => handleCategoryFieldChange("negligenceType", e.target.value)}>
                      <option value="">-- Select --</option>
                      <option value="Over-speeding / Rash Driving">{language === "Tamil" ? "அதிவேகம் / அஜாக்கிரதை" : "Over-speeding / Rash Driving"}</option>
                      <option value="Drunk Driving">{language === "Tamil" ? "மது அருந்திவிட்டு ஓட்டுதல்" : "Drunk Driving"}</option>
                      <option value="Wrong-side Driving / Lane violation">{language === "Tamil" ? "தவறான பாதையில் ஓட்டுதல்" : "Wrong-side Driving / Lane violation"}</option>
                      <option value="Jumping Red Light / Negligent Overtaking">{language === "Tamil" ? "சிக்னல் மீறல் / தவறான முந்திச் செல்லல்" : "Jumping Red Light / Negligent Overtaking"}</option>
                    </select>
                  </div>
                </div>
              </div>
            )}

            {/* General narrative text box */}
            <div className="input-group">
              <label className="input-label">
                {language === "Tamil" 
                  ? "சம்பவத்தை உங்கள் சொந்த வார்த்தைகளில் விவரிக்கவும் (தேதிகள், சாட்சிகள், என்ன நடந்தது போன்ற முழு தகவல்களுடன்):"
                  : "Describe the incident in your own words (provide chronological details, actions, and specific events):"}
              </label>
              <textarea
                rows="6"
                className="input-control"
                placeholder={
                  language === "Tamil"
                    ? "எ.கா. 15 மே அன்று என்ன நடந்தது என்று கூடுதல் விவரங்களை இங்கே எழுதுங்கள்..."
                    : "e.g. Detail additional facts of the occurrence here to complete the legal narrative..."
                }
                value={incidentDetails}
                onChange={(e) => setIncidentDetails(e.target.value)}
                required
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
                <span className="val">{complainantName || "________________________"}{complainantAge ? `, Age: ${complainantAge}` : ""}</span>
              </div>
              {complainantParentName && (
                <div className="review-row">
                  <span className="label">Father/Husband:</span>
                  <span className="val">{complainantParentName}</span>
                </div>
              )}
              <div className="review-row">
                <span className="label">Contact Info:</span>
                <span className="val">{complainantPhone || "________________________"}</span>
              </div>
              <div className="review-row">
                <span className="label">Nationality:</span>
                <span className="val">{complainantNationality || "Indian"}</span>
              </div>
              <div className="review-row">
                <span className="label">Incident Date:</span>
                <span className="val">{incidentDate ? `${incidentDate} @ ${incidentTime}` : "________________________"}</span>
              </div>
              <div className="review-row">
                <span className="label">Jurisdiction PS:</span>
                <span className="val">{policeStation || "________________________"}{incidentDistrict ? `, District: ${incidentDistrict}` : ""} ({complainantState})</span>
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
