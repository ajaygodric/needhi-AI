import { useState } from "react";
import { generateTemplate, downloadPdf } from "../utils/api";
import { FaFilePdf, FaBookOpen, FaExclamationCircle, FaTicketAlt, FaPenNib, FaUsers } from "react-icons/fa";

const DocStudio = ({ language }) => {
  const [templateType, setTemplateType] = useState("Rent Agreement");
  const [fields, setFields] = useState({});
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedDoc, setGeneratedDoc] = useState("");

  const templates = [
    "Rent Agreement",
    "Legal Notice",
    "Affidavit",
    "Bail Application",
    "Consumer Complaint",
    "Non-Disclosure Agreement (NDA)",
    "Promissory Note",
    "Power of Attorney"
  ];

  // Stamp Duty guides for each template
  const stampGuides = {
    "Rent Agreement": {
      stamp: "₹100 or ₹200 Non-Judicial Stamp Paper",
      notary: "Recommended, but registration is mandatory if tenancy exceeds 11 months.",
      witnesses: "2 witnesses with ID proofs required.",
      note: "Rent agreements for 11 months are standard to avoid high registration charges."
    },
    "Legal Notice": {
      stamp: "Not Required (Plain paper or Advocate Letterhead)",
      notary: "Not Required.",
      witnesses: "Not Required.",
      note: "Must be sent via Speed Post or Registered Post AD to maintain proof of delivery."
    },
    "Affidavit": {
      stamp: "₹20 or ₹50 Stamp Paper / E-Stamp",
      notary: "Mandatory. Must be attested by an Oath Commissioner, Notary Public, or Magistrate.",
      witnesses: "1 witness or identifier required.",
      note: "Commonly used for name changes, address proofs, declarations, and lost certificates."
    },
    "Bail Application": {
      stamp: "Court Fee Stamps (varies from ₹10 to ₹50 depending on court)",
      notary: "Requires verification affidavit signed by close relative if accused is in custody.",
      witnesses: "Sureties (usually 2 local sureties with asset proofs) required if bail is granted.",
      note: "Submitted directly to the concerned Magistrate or Sessions Court under BNSS Sec 480/482."
    },
    "Consumer Complaint": {
      stamp: "Not Required. Nominal Court fee paid online via e-daakhil portal.",
      notary: "Not Required. Simple declaration/index verification is sufficient.",
      witnesses: "Not Required during filing, affidavits may be submitted during evidence stage.",
      note: "Can be filed online at edaakhil.nic.in for claims up to ₹50 Lakhs (District Commission)."
    },
    "Non-Disclosure Agreement (NDA)": {
      stamp: "₹100 or ₹200 Non-Judicial Stamp Paper",
      notary: "Optional, but recommended for commercial use.",
      witnesses: "2 witnesses recommended.",
      note: "Governed under the Indian Contract Act, 1872."
    },
    "Promissory Note": {
      stamp: "Revenue Stamp of Rs. 1/- to Rs. 5/- pasted and crossed.",
      notary: "Not mandatory, but recommended if loan is substantial.",
      witnesses: "2 witnesses recommended for evidentiary value.",
      note: "Governed under the Negotiable Instruments Act, 1881."
    },
    "Power of Attorney": {
      stamp: "Non-Judicial Stamp Paper (varies by state, typically ₹100 to ₹500).",
      notary: "Mandatory if dealing with immovable property or court presentation.",
      witnesses: "2 witnesses with ID proofs mandatory.",
      note: "Must be registered at the Sub-Registrar's Office if granting power to sell property."
    }
  };

  const handleFieldChange = (key, val) => {
    setFields({
      ...fields,
      [key]: val
    });
  };

  // Reset fields when template changes
  const handleTemplateChange = (type) => {
    setTemplateType(type);
    setFields({});
    setGeneratedDoc("");
  };

  const handleGenerate = async (e) => {
    e.preventDefault();
    setIsGenerating(true);
    setGeneratedDoc("");

    try {
      const res = await generateTemplate(templateType, fields);
      setGeneratedDoc(res.draft);
    } catch (err) {
      console.error(err);
      setGeneratedDoc(`Error: ${err.message}`);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleDownloadPdf = () => {
    if (!generatedDoc) return;
    downloadPdf(`${templateType.toUpperCase()} - NEEDHI AI`, generatedDoc, `${templateType.replace(/\s+/g, "_")}_Draft.pdf`);
  };

  return (
    <div>
      <div className="section-header">
        <h2 className="section-title">
          {language === "Tamil" ? "சட்ட ஆவண வடிவங்கள் & ஸ்டுடி‌யோ" : "Legal Document Templates Studio"}
        </h2>
        <p className="section-subtitle">
          {language === "Tamil"
            ? "வாடகை ஒப்பந்தம், பிரமாணப் பத்திரம், நுகர்வோர் புகார்கள் போன்ற ஆவணங்களை எளிதாக நிரப்பி பதிவிறக்கம் செய்யுங்கள்."
            : "Select a standard legal template, input your custom parameters, and generate ready-to-print legal drafts with stamp duty guidelines."}
        </p>
      </div>

      <div className="grid-3" style={{ gap: "25px", alignItems: "start" }}>
        
        {/* Forms Selector & Inputs */}
        <div className="doc-studio-form-container">
          <div className="card" style={{ marginBottom: "25px" }}>
            <div className="input-group" style={{ maxWidth: "300px" }}>
              <label className="input-label">{language === "Tamil" ? "ஆவண வார்ப்புருவைத் தேர்ந்தெடுக்கவும்" : "Select Document Template"}</label>
              <select className="input-control" value={templateType} onChange={(e) => handleTemplateChange(e.target.value)}>
                {templates.map(t => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
            </div>
            
            <hr style={{ border: "none", borderTop: "1px solid rgba(255,255,255,0.06)", margin: "20px 0" }} />

            <form onSubmit={handleGenerate}>
              <h4 style={{ fontFamily: "var(--font-serif)", marginBottom: "15px" }}>
                {language === "Tamil" ? "விவரங்களை நிரப்பவும்" : "Required Details"}
              </h4>
              
              {templateType === "Rent Agreement" && (
                <div className="grid-2">
                  <div className="input-group">
                    <label className="input-label">Landlord Full Name</label>
                    <input type="text" className="input-control" placeholder="e.g. abcd" required value={fields.landlord || ""} onChange={(e) => handleFieldChange("landlord", e.target.value)} />
                  </div>
                  <div className="input-group">
                    <label className="input-label">Tenant Full Name</label>
                    <input type="text" className="input-control" placeholder="e.g. xyz" required value={fields.tenant || ""} onChange={(e) => handleFieldChange("tenant", e.target.value)} />
                  </div>
                  <div className="input-group">
                    <label className="input-label">Property Address</label>
                    <input type="text" className="input-control" placeholder="Complete address of property" required value={fields.address || ""} onChange={(e) => handleFieldChange("address", e.target.value)} />
                  </div>
                  <div className="input-group">
                    <label className="input-label">Monthly Rent (₹)</label>
                    <input type="text" className="input-control" placeholder="e.g. 1000" required value={fields.rent || ""} onChange={(e) => handleFieldChange("rent", e.target.value)} />
                  </div>
                  <div className="input-group">
                    <label className="input-label">Security Deposit (₹)</label>
                    <input type="text" className="input-control" placeholder="e.g. 5000" required value={fields.deposit || ""} onChange={(e) => handleFieldChange("deposit", e.target.value)} />
                  </div>
                  <div className="input-group">
                    <label className="input-label">Duration (Months)</label>
                    <input type="text" className="input-control" placeholder="e.g. 11" required value={fields.duration || ""} onChange={(e) => handleFieldChange("duration", e.target.value)} />
                  </div>
                </div>
              )}

              {templateType === "Legal Notice" && (
                <div>
                  <div className="grid-2">
                    <div className="input-group">
                      <label className="input-label">Sender Name</label>
                      <input type="text" className="input-control" placeholder="e.g. abcd" required value={fields.sender || ""} onChange={(e) => handleFieldChange("sender", e.target.value)} />
                    </div>
                    <div className="input-group">
                      <label className="input-label">Receiver Name</label>
                      <input type="text" className="input-control" placeholder="e.g. xyz" required value={fields.receiver || ""} onChange={(e) => handleFieldChange("receiver", e.target.value)} />
                    </div>
                    <div className="input-group">
                      <label className="input-label">Sender Address</label>
                      <input type="text" className="input-control" placeholder="Sender address" required value={fields.sender_addr || ""} onChange={(e) => handleFieldChange("sender_addr", e.target.value)} />
                    </div>
                    <div className="input-group">
                      <label className="input-label">Receiver Address</label>
                      <input type="text" className="input-control" placeholder="Receiver address" required value={fields.receiver_addr || ""} onChange={(e) => handleFieldChange("receiver_addr", e.target.value)} />
                    </div>
                  </div>
                  <div className="input-group">
                    <label className="input-label">Notice Subject</label>
                    <input type="text" className="input-control" placeholder="e.g. Notice for recovery of dues" required value={fields.subject || ""} onChange={(e) => handleFieldChange("subject", e.target.value)} />
                  </div>
                  <div className="input-group">
                    <label className="input-label">Grievance Details & Cause of Action</label>
                    <textarea rows="4" className="input-control" placeholder="Describe chronological transaction details, defaults, and breaches..." required value={fields.details || ""} onChange={(e) => handleFieldChange("details", e.target.value)}></textarea>
                  </div>
                </div>
              )}

              {templateType === "Affidavit" && (
                <div>
                  <div className="grid-3">
                    <div className="input-group">
                      <label className="input-label">Deponent Name</label>
                      <input type="text" className="input-control" placeholder="e.g. abcd" required value={fields.name || ""} onChange={(e) => handleFieldChange("name", e.target.value)} />
                    </div>
                    <div className="input-group">
                      <label className="input-label">Age</label>
                      <input type="text" className="input-control" placeholder="e.g. 1234" required value={fields.age || ""} onChange={(e) => handleFieldChange("age", e.target.value)} />
                    </div>
                    <div className="input-group">
                      <label className="input-label">State</label>
                      <input type="text" className="input-control" placeholder="e.g. Tamil Nadu" required value={fields.state || ""} onChange={(e) => handleFieldChange("state", e.target.value)} />
                    </div>
                  </div>
                  <div className="input-group">
                    <label className="input-label">Permanent Address</label>
                    <input type="text" className="input-control" placeholder="Permanent address" required value={fields.address || ""} onChange={(e) => handleFieldChange("address", e.target.value)} />
                  </div>
                  <div className="input-group">
                    <label className="input-label">Declaration Statement / Purpose</label>
                    <textarea rows="4" className="input-control" placeholder="I state that I have lost my degree certificate / changed my name..." required value={fields.content || ""} onChange={(e) => handleFieldChange("content", e.target.value)}></textarea>
                  </div>
                </div>
              )}

              {templateType === "Bail Application" && (
                <div>
                  <div className="grid-2">
                    <div className="input-group">
                      <label className="input-label">Accused Name</label>
                      <input type="text" className="input-control" placeholder="e.g. abcd" required value={fields.accused || ""} onChange={(e) => handleFieldChange("accused", e.target.value)} />
                    </div>
                    <div className="input-group">
                      <label className="input-label">Concerned Court Name</label>
                      <input type="text" className="input-control" placeholder="e.g. High Court of Madras" required value={fields.court || ""} onChange={(e) => handleFieldChange("court", e.target.value)} />
                    </div>
                    <div className="input-group">
                      <label className="input-label">FIR / Crime Number</label>
                      <input type="text" className="input-control" placeholder="e.g. Crime No. 1234/2026" required value={fields.case_no || ""} onChange={(e) => handleFieldChange("case_no", e.target.value)} />
                    </div>
                    <div className="input-group">
                      <label className="input-label">Police Station & State</label>
                      <input type="text" className="input-control" placeholder="e.g. PS Name, State" required value={fields.ps || ""} onChange={(e) => handleFieldChange("ps", e.target.value)} />
                    </div>
                  </div>
                  <div className="input-group">
                    <label className="input-label">Grounds for Bail</label>
                    <textarea rows="4" className="input-control" placeholder="Describe grounds for bail application..." required value={fields.grounds || ""} onChange={(e) => handleFieldChange("grounds", e.target.value)}></textarea>
                  </div>
                </div>
              )}

              {templateType === "Consumer Complaint" && (
                <div>
                  <div className="grid-2">
                    <div className="input-group">
                      <label className="input-label">Complainant Name</label>
                      <input type="text" className="input-control" placeholder="e.g. abcd" required value={fields.complainant || ""} onChange={(e) => handleFieldChange("complainant", e.target.value)} />
                    </div>
                    <div className="input-group">
                      <label className="input-label">Opposite Party (Company)</label>
                      <input type="text" className="input-control" placeholder="e.g. xyz Company Ltd." required value={fields.opposite_party || ""} onChange={(e) => handleFieldChange("opposite_party", e.target.value)} />
                    </div>
                    <div className="input-group">
                      <label className="input-label">Complainant Address</label>
                      <input type="text" className="input-control" placeholder="Complainant address" required value={fields.complainant_addr || ""} onChange={(e) => handleFieldChange("complainant_addr", e.target.value)} />
                    </div>
                    <div className="input-group">
                      <label className="input-label">Opposite Party Address</label>
                      <input type="text" className="input-control" placeholder="Opposite party address" required value={fields.opposite_addr || ""} onChange={(e) => handleFieldChange("opposite_addr", e.target.value)} />
                    </div>
                  </div>
                  <div className="grid-2">
                    <div className="input-group">
                      <label className="input-label">Transaction Amount (₹)</label>
                      <input type="text" className="input-control" placeholder="e.g. 1000" required value={fields.amount || ""} onChange={(e) => handleFieldChange("amount", e.target.value)} />
                    </div>
                    <div className="input-group">
                      <label className="input-label">Purchase Date</label>
                      <input type="text" className="input-control" placeholder="e.g. 10th Jan 2026" required value={fields.date || ""} onChange={(e) => handleFieldChange("date", e.target.value)} />
                    </div>
                  </div>
                  <div className="input-group">
                    <label className="input-label">Details of Deficiency of Service</label>
                    <textarea rows="4" className="input-control" placeholder="Explain deficiency of service..." required value={fields.complaint || ""} onChange={(e) => handleFieldChange("complaint", e.target.value)}></textarea>
                  </div>
                </div>
              )}

              {templateType === "Non-Disclosure Agreement (NDA)" && (
                <div>
                  <div className="grid-2">
                    <div className="input-group">
                      <label className="input-label">Disclosing Party</label>
                      <input type="text" className="input-control" placeholder="e.g. abcd" required value={fields.disclosing_party || ""} onChange={(e) => handleFieldChange("disclosing_party", e.target.value)} />
                    </div>
                    <div className="input-group">
                      <label className="input-label">Receiving Party</label>
                      <input type="text" className="input-control" placeholder="e.g. xyz" required value={fields.receiving_party || ""} onChange={(e) => handleFieldChange("receiving_party", e.target.value)} />
                    </div>
                    <div className="input-group">
                      <label className="input-label">Confidentiality Term (Years)</label>
                      <input type="text" className="input-control" placeholder="e.g. 1234" required value={fields.term_years || ""} onChange={(e) => handleFieldChange("term_years", e.target.value)} />
                    </div>
                    <div className="input-group">
                      <label className="input-label">Governing Jurisdiction (City)</label>
                      <input type="text" className="input-control" placeholder="e.g. Chennai" required value={fields.jurisdiction || ""} onChange={(e) => handleFieldChange("jurisdiction", e.target.value)} />
                    </div>
                  </div>
                  <div className="input-group">
                    <label className="input-label">Purpose of Information Disclosure</label>
                    <textarea rows="4" className="input-control" placeholder="Describe the business collaboration or project discussion for which information is shared..." required value={fields.purpose || ""} onChange={(e) => handleFieldChange("purpose", e.target.value)}></textarea>
                  </div>
                </div>
              )}

              {templateType === "Promissory Note" && (
                <div>
                  <div className="grid-2">
                    <div className="input-group">
                      <label className="input-label">Borrower Full Name</label>
                      <input type="text" className="input-control" placeholder="e.g. abcd" required value={fields.borrower || ""} onChange={(e) => handleFieldChange("borrower", e.target.value)} />
                    </div>
                    <div className="input-group">
                      <label className="input-label">Lender Full Name</label>
                      <input type="text" className="input-control" placeholder="e.g. xyz" required value={fields.lender || ""} onChange={(e) => handleFieldChange("lender", e.target.value)} />
                    </div>
                    <div className="input-group">
                      <label className="input-label">Principal Amount (₹)</label>
                      <input type="text" className="input-control" placeholder="e.g. 1000" required value={fields.amount || ""} onChange={(e) => handleFieldChange("amount", e.target.value)} />
                    </div>
                    <div className="input-group">
                      <label className="input-label">Interest Rate (% Per Annum)</label>
                      <input type="text" className="input-control" placeholder="e.g. 1234" required value={fields.interest_rate || ""} onChange={(e) => handleFieldChange("interest_rate", e.target.value)} />
                    </div>
                  </div>
                  <div className="grid-2">
                    <div className="input-group">
                      <label className="input-label">Repayment Due Date</label>
                      <input type="text" className="input-control" placeholder="e.g. 31st December 2026 or On Demand" required value={fields.due_date || ""} onChange={(e) => handleFieldChange("due_date", e.target.value)} />
                    </div>
                    <div className="input-group">
                      <label className="input-label">Execution City & State</label>
                      <input type="text" className="input-control" placeholder="e.g. Chennai, Tamil Nadu" required value={fields.city_state || ""} onChange={(e) => handleFieldChange("city_state", e.target.value)} />
                    </div>
                  </div>
                </div>
              )}

              {templateType === "Power of Attorney" && (
                <div>
                  <div className="grid-2">
                    <div className="input-group">
                      <label className="input-label">Principal Name (You)</label>
                      <input type="text" className="input-control" placeholder="e.g. abcd" required value={fields.principal || ""} onChange={(e) => handleFieldChange("principal", e.target.value)} />
                    </div>
                    <div className="input-group">
                      <label className="input-label">Attorney Agent Name</label>
                      <input type="text" className="input-control" placeholder="e.g. xyz" required value={fields.agent || ""} onChange={(e) => handleFieldChange("agent", e.target.value)} />
                    </div>
                    <div className="input-group">
                      <label className="input-label">Principal Address</label>
                      <input type="text" className="input-control" placeholder="Principal address" required value={fields.principal_addr || ""} onChange={(e) => handleFieldChange("principal_addr", e.target.value)} />
                    </div>
                    <div className="input-group">
                      <label className="input-label">Attorney Address</label>
                      <input type="text" className="input-control" placeholder="Attorney address" required value={fields.agent_addr || ""} onChange={(e) => handleFieldChange("agent_addr", e.target.value)} />
                    </div>
                  </div>
                  <div className="input-group">
                    <label className="input-label">Schedule of Property (If any)</label>
                    <textarea rows="3" className="input-control" placeholder="Describe the physical bounds, survey number, and address of the property..." value={fields.property_schedule || ""} onChange={(e) => handleFieldChange("property_schedule", e.target.value)}></textarea>
                  </div>
                  <div className="input-group">
                    <label className="input-label">Specific Powers to Delegate</label>
                    <textarea rows="4" className="input-control" placeholder="Describe the specific actions the attorney is authorized to take..." required value={fields.powers || ""} onChange={(e) => handleFieldChange("powers", e.target.value)}></textarea>
                  </div>
                </div>
              )}

              <button type="submit" className="btn btn-primary" style={{ width: "100%" }} disabled={isGenerating}>
                {isGenerating ? (language === "Tamil" ? "தயாரிக்கப்படுகிறது..." : "Generating Document...") : (language === "Tamil" ? "ஆவணத்தை உருவாக்கு" : `Generate ${templateType}`)}
              </button>
            </form>
          </div>
        </div>

        {/* Notary & Stamp duty panel guide */}
        <div>
          <div className="card" style={{ borderLeft: "4px solid var(--accent-gold)" }}>
            <div className="card-title">
              <span><FaBookOpen /></span>
              {language === "Tamil" ? "முத்திரைக் கட்டணம்" : "Stamp & Notary Guide"}
            </div>
            <div style={{ fontSize: "0.85rem", color: "var(--text-secondary)", display: "flex", flexDirection: "column", gap: "12px" }}>
              <div>
                <strong style={{ color: "var(--text-primary)", display: "inline-flex", alignItems: "center", gap: "6px", marginBottom: "4px" }}>
                  <FaTicketAlt style={{ color: "var(--accent-gold)" }} />
                  <span>Stamp Value:</span>
                </strong>
                <div style={{ paddingLeft: "20px" }}>{stampGuides[templateType].stamp}</div>
              </div>
              <div>
                <strong style={{ color: "var(--text-primary)", display: "inline-flex", alignItems: "center", gap: "6px", marginBottom: "4px" }}>
                  <FaPenNib style={{ color: "var(--accent-gold)" }} />
                  <span>Notarization:</span>
                </strong>
                <div style={{ paddingLeft: "20px" }}>{stampGuides[templateType].notary}</div>
              </div>
              <div>
                <strong style={{ color: "var(--text-primary)", display: "inline-flex", alignItems: "center", gap: "6px", marginBottom: "4px" }}>
                  <FaUsers style={{ color: "var(--accent-gold)" }} />
                  <span>Witnesses:</span>
                </strong>
                <div style={{ paddingLeft: "20px" }}>{stampGuides[templateType].witnesses}</div>
              </div>
              <div style={{ background: "rgba(241,196,15,0.06)", border: "1px solid rgba(241,196,15,0.2)", borderRadius: "8px", padding: "10px", color: "var(--text-primary)", display: "flex", gap: "8px", alignItems: "flex-start", marginTop: "8px" }}>
                <FaExclamationCircle style={{ color: "var(--warning)", flexShrink: 0, marginTop: "3px" }} />
                <span>{stampGuides[templateType].note}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Generated parchment document container */}
      {generatedDoc && (
        <div className="card step-card" style={{ marginTop: "30px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "15px" }}>
            <h4 style={{ fontFamily: "var(--font-serif)" }}>{language === "Tamil" ? "முன்னோட்டம் & பதிவிறக்கம்" : "Document Preview & Compilation"}</h4>
            <button className="btn" onClick={handleDownloadPdf}>
              <FaFilePdf /> {language === "Tamil" ? "PDF கோப்பாக பதிவிறக்கு" : "Download PDF Document"}
            </button>
          </div>
          
          <div className="parchment-container">
            <div className="parchment-watermark">NEEDHI AI</div>
            <div style={{ whiteSpace: "pre-line" }}>{generatedDoc}</div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DocStudio;
