import { useState } from "react";
import { FaBuilding, FaFileAlt, FaFileInvoiceDollar, FaCalendarTimes, FaMapMarkerAlt, FaLightbulb, FaCheckCircle, FaRegCircle } from "react-icons/fa";

const FilingChecklist = ({ language }) => {
  const [selectedCourt, setSelectedCourt] = useState("High Court");
  const [selectedCaseType, setSelectedCaseType] = useState("Writ Petition (Article 226)");
  const [completedDocs, setCompletedDocs] = useState({});

  const courts = [
    "High Court",
    "District Court",
    "Consumer Forum",
    "Labour Tribunal"
  ];

  const caseTypesByCourt = {
    "High Court": [
      "Writ Petition (Article 226)",
      "Anticipatory Bail Application",
      "Criminal Appeal / Revision",
      "Civil First Appeal"
    ],
    "District Court": [
      "Civil Suit (Property/Recovery)",
      "Bail Application",
      "Private Criminal Complaint",
      "Matrimonial/Family Dispute"
    ],
    "Consumer Forum": [
      "Consumer Complaint (District Commission)",
      "Consumer Appeal (State Commission)"
    ],
    "Labour Tribunal": [
      "Industrial Dispute Claim",
      "Gratuity / Wages Claim",
      "Workman Compensation"
    ]
  };

  const caseTypes = caseTypesByCourt[selectedCourt] || [];
  const currentCaseType = caseTypes.includes(selectedCaseType) ? selectedCaseType : (caseTypes[0] || "");

  const checklistData = {
    "High Court": {
      "Writ Petition (Article 226)": {
        docs: [
          "Writ Petition (duly drafted and signed by petitioner and counsel)",
          "Verification Affidavit of the Petitioner (duly notarized)",
          "Vakalatnama (stamped and signed by petitioner and advocate)",
          "Index and Synopsis of the case",
          "Chronological List of Dates and Events",
          "Annexures / Supporting Documents (e.g. impugned order, notices)",
          "Court Fee stamps of ₹250/-",
          "Welfare Fund Stamp (₹100/-) and Advocate Clerk Association Stamp (₹20/-)",
          "Copy of Petition served to Government Pleader/opposite counsel (proof of service)"
        ],
        fees: "₹250/- basic court fee. Nominal scanning charges (₹2 per page) and Welfare Fund stamp charges.",
        limitation: "No strict timeline, but should be filed without 'laches' (unreasonable delay) - usually within 90 days from the cause of action.",
        address: "Madras High Court Complex, NSC Bose Road, George Town, Chennai - 600104 | Madurai Bench of Madras High Court, Madurai - 625023",
        tips: "Make sure all annexures are clearly readable. If any document is in Tamil, a certified English translation must be attached."
      },
      "Anticipatory Bail Application": {
        docs: [
          "Anticipatory Bail Petition under Section 482 of BNSS (formerly Sec 438 CrPC)",
          "Affidavit of the Petitioner/Accused",
          "Copy of the FIR (if registered) or Police complaint details",
          "Vakalatnama (duly stamped and signed)",
          "Memo of Appearance",
          "Copy of Aadhaar Card / ID Proof of petitioner",
          "Court fee stamp of ₹25/-",
          "Welfare stamp of ₹100/-"
        ],
        fees: "₹25/- court fee stamps + ₹100/- Welfare stamp on Vakalatnama.",
        limitation: "Can be filed at any time after reasonable apprehension of arrest in a non-bailable offence.",
        address: "Madras High Court Complex, NSC Bose Road, George Town, Chennai - 600104 | Madurai Bench of Madras High Court, Madurai - 625023",
        tips: "Ensure you state that the petitioner has no prior criminal records (if true) and is willing to abide by any bail conditions and submit local sureties."
      },
      "Criminal Appeal / Revision": {
        docs: [
          "Memo of Appeal or Revision Petition under BNSS",
          "Certified Copy of the impugned Judgment/Order of the lower court",
          "Application for suspension of sentence (if appellant is in jail)",
          "Petition for condonation of delay (if filing after limitation period)",
          "Vakalatnama & Welfare stamp",
          "Index, Synopsis, and Dates/Events list",
          "Affidavit of the appellant or a relative",
          "Court fee stamps (₹250/- for appeal, ₹50/- for revision)"
        ],
        fees: "₹250/- for Appeal, ₹50/- for Criminal Revision. Additional ₹100/- for Vakalatnama Welfare stamp.",
        limitation: "90 days from the date of the lower court's sentence/judgment for Criminal Appeal; 90 days for Revision.",
        address: "Madras High Court Complex, NSC Bose Road, George Town, Chennai - 600104 | Madurai Bench of Madras High Court, Madurai - 625023",
        tips: "Always apply for a certified copy of the judgment immediately upon pronouncement to prevent the limitation period from running out."
      },
      "Civil First Appeal": {
        docs: [
          "Memo of Appeal under Section 96 of CPC",
          "Certified copy of the decree and judgment of the trial court",
          "Vakalatnama with stamps",
          "Valuation Statement of the suit value",
          "Ad-valorem Court Fee (varies based on the suit claim amount)",
          "Application for stay of decree execution (if applicable)",
          "Index, Synopsis, and list of dates"
        ],
        fees: "Ad-valorem court fee as per the Tamil Nadu Court Fees and Suits Valuation Act, 1955 (usually specified percentages of the disputed property/money value).",
        limitation: "90 days from the date of the decree/judgment of the Trial Court.",
        address: "Madras High Court Complex, NSC Bose Road, George Town, Chennai - 600104 | Madurai Bench of Madras High Court, Madurai - 625023",
        tips: "A Decree is separate from a Judgment. Ensure that the trial court has drafted and signed the Decree before you obtain the certified copy."
      }
    },
    "District Court": {
      "Civil Suit (Property/Recovery)": {
        docs: [
          "Plaint under Order VII Rule 1 of CPC",
          "Vakalatnama (signed by Plaintiff and Advocate)",
          "List of Documents (Order VII Rule 14 CPC)",
          "Original documents or certified copies relied upon (Sale deeds, invoices, letters)",
          "Affidavit in support of plaint",
          "Court fee stamp (as per suit valuation)",
          "Summons Forms (in duplicate for each defendant) with postal covers",
          "Valuation slip calculating court fees"
        ],
        fees: "Valued under TN Court Fees Act. Usually 3% to 7.5% of the suit property/recovery value.",
        limitation: "3 years from the date the cause of action arose (e.g. date of default, date of trespass, breach of contract).",
        address: "District Civil Courts, Egmore / George Town / Saidapet Court Complexes, Chennai | Local District Headquarter Courts.",
        tips: "Submit separate copies of the plaint for each defendant along with appropriate register post covers for dispatching summons."
      },
      "Bail Application": {
        docs: [
          "Bail Petition under Section 480 of BNSS (formerly Sec 437/439 CrPC)",
          "Affidavit of the deponent (relative of the accused)",
          "Copy of FIR (certified copy or download)",
          "Vakalatnama signed by the accused or by authorized relative",
          "Court fee stamps (₹10/- or ₹20/-)",
          "Copies of previous rejection orders (if any)"
        ],
        fees: "₹10 to ₹25 in Court fee stamps + ₹50-₹100 Welfare stamps.",
        limitation: "Can be filed at any time after arrest or custody.",
        address: "Principal Sessions Court / Metropolitan Magistrate Courts in respective District Headquarters.",
        tips: "Keep details of two local sureties ready (property tax receipt or salary slip) as magistrates require them if bail is granted."
      },
      "Private Criminal Complaint": {
        docs: [
          "Written Complaint under Section 223 of BNSS (formerly Sec 200 CrPC)",
          "List of Witnesses and their details",
          "List of Documents and evidence annexed (audio, video, letters, emails)",
          "Vakalatnama and Welfare stamps",
          "Affidavit verifying the complaint contents",
          "Process fee stamps for issuing summons to accused"
        ],
        fees: "Nominal court fee stamps (₹10-₹50). Process fee for summoning: ₹20-₹50 per accused.",
        limitation: "Matches the maximum limitation of the offense (e.g. 6 months if fine only, 1 year if jail < 1 year, 3 years if jail 1-3 years).",
        address: "Jurisdictional Judicial Magistrate Court / Metropolitan Magistrate Court.",
        tips: "Complainant must be present in court for the sworn statement recording under Section 223 BNSS on the first day of hearing."
      },
      "Matrimonial/Family Dispute": {
        docs: [
          "Petition (e.g., Divorce, Maintenance, Child Custody, Restitution of Conjugal Rights)",
          "Vakalatnama & Welfare stamp",
          "Affidavit of assets and liabilities (mandatory in maintenance cases)",
          "Marriage Registration Certificate or wedding invitation card/photo",
          "Proof of residence of parties",
          "Court fee stamps (usually ₹50/- to ₹100/-)",
          "Index and list of annexures"
        ],
        fees: "Fixed nominal fee of ₹100/- for divorce/maintenance petitions. Additional summons/process fee.",
        limitation: "No specific limitation, but under Hindu Marriage Act, certain grounds like desertion require a minimum of 1-2 years of separation.",
        address: "Jurisdictional Family Court Complex (e.g., High Court Complex Family Courts, Chennai).",
        tips: "Parties must attend counselling/mediation sessions on the initial court dates as directed by the Family Court Judge."
      }
    },
    "Consumer Forum": {
      "Consumer Complaint (District Commission)": {
        docs: [
          "Consumer Complaint under Section 35 of CPA, 2019",
          "Affidavit of the Complainant verifying facts",
          "Original Bill / Invoice, Warranty Card, Receipts",
          "Copy of Legal Notice sent to builder/seller and proof of delivery",
          "Index of documents and list of dates",
          "Fees payment receipt (paid online on e-Daakhil)",
          "4 copies of complaint + 1 copy for each opposite party"
        ],
        fees: "Free up to ₹5 Lakhs claim. ₹250 for ₹5-10L. ₹500 for ₹10-20L. ₹1000 for ₹20-50L. Paid online via e-daakhil.nic.in.",
        limitation: "2 years from the date the defect in goods or deficiency in service arose.",
        address: "District Consumer Disputes Redressal Commission (e.g. Chennai North/South/Central at Chennai).",
        tips: "Do not forget to file proof that you sent a demand notice to the opposite party before filing, giving them 15 days to resolve."
      },
      "Consumer Appeal (State Commission)": {
        docs: [
          "Memo of Appeal under Section 41 of CPA, 2019",
          "Certified copy of the order of the District Commission",
          "Application for stay of District Commission order (if applicable)",
          "Affidavit of the appellant",
          "Proof of statutory deposit (50% of the ordered amount or ₹25,000, whichever is less)",
          "Index, synopsis, and documents list",
          "4 copies of appeal + 1 for each respondent"
        ],
        fees: "No court fee for filing appeal. However, statutory deposit of 50% of the awarded amount must be deposited in the commission's bank.",
        limitation: "45 days from the date of receipt of the District Commission's order.",
        address: "State Consumer Disputes Redressal Commission, Tamil Nadu (SCDRC), Poonamallee High Road, Chennai - 600010.",
        tips: "The limitation period is strict (45 days). Any delay requires filing a separate Condonation of Delay petition with valid medical/factual reasons."
      }
    },
    "Labour Tribunal": {
      "Industrial Dispute Claim": {
        docs: [
          "Claim Petition under Section 2-A or 10 of Industrial Disputes Act",
          "Failure Report issued by Conciliation Officer / Labour Inspector",
          "Appointment letter, ID card, pay slips or bank statements proving employment",
          "Termination letter / show cause notice (if applicable)",
          "Representation letter sent to management and proof of delivery",
          "Index and list of dates"
        ],
        fees: "Exempted / Zero court fee for workmen. Nominal process fees.",
        limitation: "3 years from the date of discharge, dismissal, retrenchment, or termination of service.",
        address: "Labour Court / Industrial Tribunal (e.g. Poonamallee High Road, Chennai).",
        tips: "Before approaching the Labour Court, you must file a grievance before the Labour Conciliation Officer. Only if conciliation fails, can you file in tribunal."
      },
      "Gratuity / Wages Claim": {
        docs: [
          "Application Form N or Form I under Payment of Gratuity Act / Payment of Wages Act",
          "Calculation sheet showing gratuity/wages due",
          "Employment contract, pay slips, Form 16 or EPF records proving length of service",
          "Written demand sent to employer and receipt acknowledgment",
          "Affidavit of the applicant"
        ],
        fees: "No court fee for workmen. Process fee of ₹5/- per respondent.",
        limitation: "1 year for wages from the date wages became due; 90 days for gratuity from the date of rejection of claim by employer.",
        address: "Office of the Controlling Authority under Payment of Gratuity Act / Assistant Commissioner of Labour.",
        tips: "Gratuity is mandatory for any employee who completes 5 continuous years of service in an establishment with 10 or more employees."
      },
      "Workman Compensation": {
        docs: [
          "Claim Application under Employee's Compensation Act, 1923",
          "Medical Board Disability Certificate showing percentage of loss of earning capacity",
          "Police FIR and accident report (if road/industrial accident occurred)",
          "Notice of accident served to employer and delivery proof",
          "Proof of age, wage slips, and bank statements",
          "Death Certificate & Legal Heir Certificate (if claiming for fatal accident)"
        ],
        fees: "Nominal application fee (₹10 to ₹50). Paid via treasury challan.",
        limitation: "2 years from the date of occurrence of the accident or death.",
        address: "Court of the Commissioner for Employee's Compensation / Labour Commissioner Office.",
        tips: "Compensation is calculated based on age, monthly salary (capped at statutory limits), and the percentage of permanent disability certified by a government doctor."
      }
    }
  };

  const handleSelectCourt = (court) => {
    setSelectedCourt(court);
    const defaultCase = caseTypesByCourt[court][0];
    setSelectedCaseType(defaultCase);
    setCompletedDocs({});
  };

  const toggleDocComplete = (doc) => {
    const key = `${selectedCourt}-${currentCaseType}-${doc}`;
    setCompletedDocs(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  const activeChecklist = checklistData[selectedCourt]?.[currentCaseType] || {
    docs: [], fees: "", limitation: "", address: "", tips: ""
  };

  const completedCount = activeChecklist.docs.filter(
    doc => completedDocs[`${selectedCourt}-${currentCaseType}-${doc}`]
  ).length;

  const totalCount = activeChecklist.docs.length;
  const progressPercent = totalCount > 0 ? Math.round((completedCount / totalCount) * 100) : 0;

  return (
    <div>
      <div className="section-header">
        <h2 className="section-title">
          {language === "Tamil" ? "நீதிமன்ற வழக்கு தாக்கல் சரிபார்ப்பு" : "Court Filing Checklist & Guide"}
        </h2>
        <p className="section-subtitle">
          {language === "Tamil"
            ? "வழக்கு வகை மற்றும் நீதிமன்றத்தின்படி தேவையான ஆவணங்கள், கட்டணங்கள் மற்றும் காலவரம்புகளை சரிபார்க்கவும்."
            : "Select a court and case type to get a structured interactive checklist of required documents, fees, deadlines, and procedural tips."}
        </p>
      </div>

      <div className="grid-3" style={{ gap: "25px", alignItems: "start" }}>
        
        {/* Court & Case Type Selectors Panel */}
        <div className="card" style={{ gridColumn: "span 1" }}>
          <h4 style={{ fontFamily: "var(--font-serif)", marginBottom: "20px", color: "var(--accent-gold-light)" }}>
            {language === "Tamil" ? "தேர்வுகள்" : "Filing Selection"}
          </h4>

          {/* Court Selector */}
          <div className="input-group">
            <label className="input-label">
              {language === "Tamil" ? "நீதிமன்றம்" : "Court Forum"}
            </label>
            <select 
              className="input-control" 
              value={selectedCourt} 
              onChange={(e) => handleSelectCourt(e.target.value)}
            >
              {courts.map(c => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>

          {/* Case Type Selector */}
          <div className="input-group">
            <label className="input-label">
              {language === "Tamil" ? "வழக்கு வகை" : "Case Type"}
            </label>
            <select 
              className="input-control" 
              value={currentCaseType} 
              onChange={(e) => {
                setSelectedCaseType(e.target.value);
                setCompletedDocs({});
              }}
            >
              {caseTypes.map(ct => (
                <option key={ct} value={ct}>{ct}</option>
              ))}
            </select>
          </div>

          {/* Progress Card */}
          {totalCount > 0 && (
            <div style={{ marginTop: "30px", background: "rgba(255,255,255,0.02)", border: "1px solid var(--border-gold)", borderRadius: "10px", padding: "16px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "8px", fontSize: "0.85rem" }}>
                <span>{language === "Tamil" ? "ஆவண தயாரிப்பு" : "Documents Ready"}</span>
                <strong>{completedCount} / {totalCount} ({progressPercent}%)</strong>
              </div>
              <div style={{ height: "6px", background: "rgba(255,255,255,0.05)", borderRadius: "3px", overflow: "hidden" }}>
                <div style={{ width: `${progressPercent}%`, height: "100%", background: "var(--accent-gold)", transition: "width 0.3s ease" }}></div>
              </div>
            </div>
          )}
        </div>

        {/* Checklist details panel */}
        <div style={{ gridColumn: "span 2", display: "flex", flexDirection: "column", gap: "25px" }}>
          
          {/* Documents Checklist Card */}
          <div className="card">
            <div className="card-title">
              <span><FaFileAlt /></span>
              {language === "Tamil" ? "தேவையான ஆவணங்களின் பட்டியல்" : "Required Documents Checklist"}
            </div>
            <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", marginBottom: "20px" }}>
              {language === "Tamil"
                ? "கோப்புகளை தாக்கல் செய்வதற்கு முன் ஒவ்வொரு ஆவணத்தையும் தயாரித்து கீழே குறிக்கவும்:"
                : "Check off each document as you compile your case bundle before presenting it to the court filing counter:"}
            </p>

            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              {activeChecklist.docs.map((doc, idx) => {
                const isDone = completedDocs[`${selectedCourt}-${currentCaseType}-${doc}`];
                return (
                  <div 
                    key={idx} 
                    onClick={() => toggleDocComplete(doc)}
                    style={{ 
                      display: "flex", 
                      alignItems: "flex-start", 
                      gap: "12px", 
                      padding: "12px", 
                      borderRadius: "8px", 
                      background: isDone ? "rgba(201, 168, 76, 0.05)" : "rgba(255,255,255,0.01)",
                      border: isDone ? "1px solid var(--accent-gold)" : "1px solid rgba(255,255,255,0.03)",
                      cursor: "pointer",
                      transition: "all 0.2s ease"
                    }}
                  >
                    <span style={{ color: isDone ? "var(--accent-gold)" : "var(--text-muted)", fontSize: "1.15rem", marginTop: "2px", flexShrink: 0 }}>
                      {isDone ? <FaCheckCircle /> : <FaRegCircle />}
                    </span>
                    <span style={{ fontSize: "0.92rem", color: isDone ? "var(--text-primary)" : "var(--text-secondary)", textDecoration: isDone ? "line-through" : "none" }}>
                      {doc}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Quick Legal Guidelines Grid */}
          <div className="grid-2">
            
            {/* Fees & Limitation */}
            <div className="card" style={{ borderLeft: "4px solid var(--accent-gold)" }}>
              <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                <div>
                  <h5 style={{ display: "inline-flex", alignItems: "center", gap: "8px", color: "var(--text-primary)", fontSize: "0.95rem", marginBottom: "6px" }}>
                    <FaFileInvoiceDollar style={{ color: "var(--accent-gold)" }} />
                    {language === "Tamil" ? "நீதிமன்ற கட்டணங்கள்" : "Filing Fees & Costs"}
                  </h5>
                  <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", paddingLeft: "24px" }}>
                    {activeChecklist.fees}
                  </p>
                </div>
                <div>
                  <h5 style={{ display: "inline-flex", alignItems: "center", gap: "8px", color: "var(--text-primary)", fontSize: "0.95rem", marginBottom: "6px" }}>
                    <FaCalendarTimes style={{ color: "var(--danger)" }} />
                    {language === "Tamil" ? "காலவரம்பு (Limitation)" : "Limitation Period"}
                  </h5>
                  <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", paddingLeft: "24px" }}>
                    {activeChecklist.limitation}
                  </p>
                </div>
              </div>
            </div>

            {/* Jurisdiction & Tips */}
            <div className="card" style={{ borderLeft: "4px solid var(--info)" }}>
              <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                <div>
                  <h5 style={{ display: "inline-flex", alignItems: "center", gap: "8px", color: "var(--text-primary)", fontSize: "0.95rem", marginBottom: "6px" }}>
                    <FaMapMarkerAlt style={{ color: "var(--info)" }} />
                    {language === "Tamil" ? "நீதிமன்ற முகவரி" : "Filing Jurisdiction / Address"}
                  </h5>
                  <p style={{ fontSize: "0.82rem", color: "var(--text-secondary)", paddingLeft: "24px", lineHeight: "1.4" }}>
                    {activeChecklist.address}
                  </p>
                </div>
                <div>
                  <h5 style={{ display: "inline-flex", alignItems: "center", gap: "8px", color: "var(--text-primary)", fontSize: "0.95rem", marginBottom: "6px" }}>
                    <FaLightbulb style={{ color: "var(--warning)" }} />
                    {language === "Tamil" ? "நடைமுறை குறிப்புகள்" : "Procedural Advice"}
                  </h5>
                  <p style={{ fontSize: "0.82rem", color: "var(--text-secondary)", paddingLeft: "24px", lineHeight: "1.4" }}>
                    {activeChecklist.tips}
                  </p>
                </div>
              </div>
            </div>

          </div>

        </div>

      </div>
    </div>
  );
};

export default FilingChecklist;
