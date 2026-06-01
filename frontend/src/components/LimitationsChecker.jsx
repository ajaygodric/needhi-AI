import { useState } from "react";
import { FaRegClock, FaCalendarAlt, FaShieldAlt, FaBalanceScale, FaExclamationTriangle, FaCheckCircle, FaUndoAlt } from "react-icons/fa";

const LimitationsChecker = ({ language }) => {
  const [caseType, setCaseType] = useState("Contract Breach");
  const [incidentDate, setIncidentDate] = useState("");
  const [calculated, setCalculated] = useState(null);

  // Reference date: Dynamic local system date
  const TODAY = new Date();

  const limitationRules = {
    "Contract Breach": {
      label: { English: "Civil: Breach of Contract", Tamil: "சிவில்: ஒப்பந்த மீறல்" },
      periodYears: 3,
      periodMonths: 0,
      periodDays: 0,
      act: "Article 55 of the Limitation Act, 1963",
      notes: {
        English: "Limitation starts from the date when the contract was broken. Extension is possible under Sec 5 of Limitation Act for sufficient cause (e.g. medical emergency, fraud by opponent).",
        Tamil: "ஒப்பந்தம் மீறப்பட்ட தேதியிலிருந்து காலக்கெடு தொடங்குகிறது. தகுந்த காரணங்களுக்காக (எ.கா. மருத்துவ அவசரநிலை, ஏமாற்றுதல்) கால நீட்டிப்பு கோரலாம்."
      }
    },
    "Recovery of Money": {
      label: { English: "Civil: Recovery of Money / Debt", Tamil: "சிவில்: பண மீட்பு / கடன்" },
      periodYears: 3,
      periodMonths: 0,
      periodDays: 0,
      act: "Article 19 to 21 of the Limitation Act, 1963",
      notes: {
        English: "Starts from the date the loan was repayable or date of last acknowledgment of debt. Promissory notes expire in 3 years from execution.",
        Tamil: "கடன் திருப்பிச் செலுத்த வேண்டிய தேதியிலிருந்து தொடங்குகிறது. பிராமிசரி நோட்டுகள் எழுதி வாங்கிய தேதியிலிருந்து 3 ஆண்டுகளில் காலாவதியாகிவிடும்."
      }
    },
    "Consumer Complaint (District/State)": {
      label: { English: "Consumer Forum Disputes", Tamil: "நுகர்வோர் மன்ற தகராறுகள்" },
      periodYears: 2,
      periodMonths: 0,
      periodDays: 0,
      act: "Section 69 of the Consumer Protection Act, 2019",
      notes: {
        English: "2 years from the date on which the cause of action (defect in goods or deficiency in service) arose. Condonation of delay petition can be filed if delay is bona-fide.",
        Tamil: "பொருளின் குறைபாடு அல்லது சேவையின் பற்றாக்குறை ஏற்பட்ட தேதியிலிருந்து 2 ஆண்டுகள். தகுந்த காரணமிருந்தால் கால அவகாசம் கோரி மனு தாக்கல் செய்யலாம்."
      }
    },
    "Labour Wages Claim": {
      label: { English: "Labour: Wages Claim", Tamil: "தொழிலாளர்: ஊதியக் கோரிக்கை" },
      periodYears: 1,
      periodMonths: 0,
      periodDays: 0,
      act: "Section 20 of the Payment of Wages Act, 1936",
      notes: {
        English: "Must be filed within 1 year from the date on which the wage payment was due.",
        Tamil: "ஊதியம் வழங்கப்பட வேண்டிய தேதியிலிருந்து 1 ஆண்டுக்குள் வழக்குத் தொடர வேண்டும்."
      }
    },
    "Gratuity Claim": {
      label: { English: "Labour: Gratuity Claim", Tamil: "தொழிலாளர்: பணிக்கொடை (Gratuity)" },
      periodYears: 0,
      periodMonths: 0,
      periodDays: 90,
      act: "Payment of Gratuity (Central) Rules, 1972",
      notes: {
        English: "90 days from the date of occurrence of the cause (e.g. rejection of gratuity claim by employer or date of retirement).",
        Tamil: "பணிக்கொடை கோரிக்கையை முதலாளி நிராகரித்த நாளிலிருந்து அல்லது ஓய்வு பெற்ற நாளிலிருந்து 90 நாட்கள்."
      }
    },
    "RERA Complaint": {
      label: { English: "RERA: Developer Disputes", Tamil: "RERA: பில்டர் / சொத்து தகராறு" },
      periodYears: 0, // No strict time limit
      periodMonths: 0,
      periodDays: 0,
      act: "Real Estate (Regulation and Development) Act, 2016",
      notes: {
        English: "RERA does not prescribe a strict limitation period for filing complaints, but claims must be made within a reasonable time after developer default.",
        Tamil: "RERA சட்டத்தில் புகார்களுக்கு குறிப்பிட்ட காலக்கெடு இல்லை, ஆனால் பில்டர் தவறிழைத்ததில் இருந்து நியாயமான காலத்திற்குள் தாக்கல் செய்யப்பட வேண்டும்."
      }
    },
    "Criminal: Fine Only": {
      label: { English: "Criminal: Offense Punishable with Fine Only", Tamil: "குற்றவியல்: அபராதம் மட்டுமே உள்ள குற்றம்" },
      periodYears: 0,
      periodMonths: 6,
      periodDays: 0,
      act: "Section 513(2)(a) of the BNSS, 2023 (formerly Sec 468 CrPC)",
      notes: {
        English: "Limitation is 6 months from the date of offense if the punishment is fine only.",
        Tamil: "அபராதம் மட்டுமே தண்டனையாக உள்ள குற்றங்களுக்கு, குற்றம் நடந்த நாளிலிருந்து 6 மாதங்கள் மட்டுமே கால வரம்பு."
      }
    },
    "Criminal: Imprisonment <= 1 Year": {
      label: { English: "Criminal: Offense with Jail <= 1 Year", Tamil: "குற்றவியல்: 1 ஆண்டுக்குள் சிறை உள்ள குற்றம்" },
      periodYears: 1,
      periodMonths: 0,
      periodDays: 0,
      act: "Section 513(2)(b) of the BNSS, 2023 (formerly Sec 468 CrPC)",
      notes: {
        English: "Limitation is 1 year if the offense is punishable with imprisonment up to one year.",
        Tamil: "ஓராண்டு வரை சிறைத்தண்டனை உள்ள குற்றங்களுக்கு, கால வரம்பு ஓராண்டு ஆகும்."
      }
    },
    "Criminal: Imprisonment 1 to 3 Years": {
      label: { English: "Criminal: Offense with Jail 1 to 3 Years", Tamil: "குற்றவியல்: 1 முதல் 3 ஆண்டுகள் சிறை உள்ள குற்றம்" },
      periodYears: 3,
      periodMonths: 0,
      periodDays: 0,
      act: "Section 513(2)(c) of the BNSS, 2023 (formerly Sec 468 CrPC)",
      notes: {
        English: "Limitation is 3 years if the offense is punishable with imprisonment between one and three years (e.g. simple theft, criminal trespass).",
        Tamil: "1 முதல் 3 ஆண்டுகள் வரை சிறைத்தண்டனை உள்ள குற்றங்களுக்கு (எ.கா. திருட்டு, அத்துமீறல்), கால வரம்பு 3 ஆண்டுகள் ஆகும்."
      }
    },
    "Criminal: Imprisonment > 3 Years (No Limit)": {
      label: { English: "Criminal: Offense with Jail > 3 Years (No Limitation)", Tamil: "குற்றவியல்: 3 ஆண்டுக்கும் மேல் சிறை உள்ள குற்றம் (கால வரம்பில்லை)" },
      periodYears: 999, // Represents infinity
      periodMonths: 0,
      periodDays: 0,
      act: "Section 513 of the BNSS, 2023 (formerly Sec 468 CrPC)",
      notes: {
        English: "There is no limitation period for major offenses punishable with imprisonment exceeding 3 years (e.g. murder, rape, major cheating, dacoity).",
        Tamil: "3 ஆண்டுகளுக்கு மேல் சிறைத்தண்டனை விதிக்கப்படக்கூடிய பெரிய குற்றங்களுக்கு (எ.கா. கொலை, பெரும் மோசடி) கால வரம்பு ஏதுமில்லை."
      }
    }
  };

  const calculateDeadline = (e) => {
    e.preventDefault();
    if (!incidentDate) return;

    const startDate = new Date(incidentDate);
    const rule = limitationRules[caseType];
    
    if (rule.periodYears === 999) {
      setCalculated({
        startDate: startDate,
        deadlineDate: null,
        daysRemaining: 999999,
        isExpired: false,
        noLimit: true
      });
      return;
    }

    if (rule.periodYears === 0 && rule.periodMonths === 0 && rule.periodDays === 0) {
      // RERA case (Reasonable time)
      setCalculated({
        startDate: startDate,
        deadlineDate: "Reasonable Time",
        isReasonable: true
      });
      return;
    }

    const deadline = new Date(startDate);
    deadline.setFullYear(deadline.getFullYear() + rule.periodYears);
    deadline.setMonth(deadline.getMonth() + rule.periodMonths);
    deadline.setDate(deadline.getDate() + rule.periodDays);

    const diffTime = deadline.getTime() - TODAY.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    const isExpired = diffDays < 0;

    setCalculated({
      startDate: startDate,
      deadlineDate: deadline,
      daysRemaining: Math.abs(diffDays),
      isExpired: isExpired,
      noLimit: false
    });
  };

  const getStatusDisplay = () => {
    if (!calculated) return null;
    if (calculated.noLimit) {
      return {
        badge: <span className="badge badge-green" style={{ padding: "6px 12px", fontSize: "0.85rem" }}>{language === "Tamil" ? "கால வரம்பு இல்லை" : "No Limitation Limit"}</span>,
        text: language === "Tamil" ? "இந்த வழக்கிற்கு காலாவதி வரம்பு இல்லை. எப்போது வேண்டுமானாலும் தாக்கல் செய்யலாம்." : "This is a major offense. A prosecution can be launched at any time.",
        cardColor: "rgba(46, 204, 113, 0.05)",
        borderColor: "var(--success)"
      };
    }
    if (calculated.isReasonable) {
      return {
        badge: <span className="badge badge-blue" style={{ padding: "6px 12px", fontSize: "0.85rem" }}>{language === "Tamil" ? "நியாயமான காலம்" : "Reasonable Timeline"}</span>,
        text: language === "Tamil" ? "பில்டர் தவறிழைத்ததில் இருந்து நியாயமான காலத்திற்குள் தாக்கல் செய்யப்பட வேண்டும்." : "RERA requires filing within a reasonable timeframe. Prompt action is advised.",
        cardColor: "rgba(52, 152, 219, 0.05)",
        borderColor: "var(--info)"
      };
    }
    if (calculated.isExpired) {
      return {
        badge: <span className="badge badge-red" style={{ padding: "6px 12px", fontSize: "0.85rem" }}>{language === "Tamil" ? "காலாவதியானது (Time-Barred)" : "Expired (Time-Barred)"}</span>,
        text: language === "Tamil" 
          ? `தாக்கல் செய்வதற்கான காலக்கெடு முடிந்துவிட்டது. கால தாமதம் ஆனது: ${calculated.daysRemaining} நாட்கள்.`
          : `The filing window has closed. The case became time-barred ${calculated.daysRemaining} days ago.`,
        cardColor: "rgba(231, 76, 60, 0.05)",
        borderColor: "var(--danger)"
      };
    }
    return {
      badge: <span className="badge badge-green" style={{ padding: "6px 12px", fontSize: "0.85rem" }}>{language === "Tamil" ? "செயலில் உள்ளது (Active)" : "Active (Within Limits)"}</span>,
      text: language === "Tamil"
        ? `உங்களுக்கு இன்னும் கால அவகாசம் உள்ளது. மீதமுள்ள நாட்கள்: ${calculated.daysRemaining} நாட்கள்.`
        : `You are within the filing window. There are ${calculated.daysRemaining} days remaining until the deadline.`,
      cardColor: "rgba(46, 204, 113, 0.05)",
      borderColor: "var(--success)"
    };
  };

  const status = getStatusDisplay();

  return (
    <div>
      <div className="section-header">
        <h2 className="section-title">
          {language === "Tamil" ? "சட்ட காலவரம்பு சரிபார்ப்பு" : "Statute of Limitations Checker"}
        </h2>
        <p className="section-subtitle">
          {language === "Tamil"
            ? "வழக்கு வகை மற்றும் சம்பவம் நடந்த தேதியின் அடிப்படையில் தாக்கல் செய்வதற்கான இறுதி நாளைக் கணக்கிடவும்."
            : "Determine if a civil suit, consumer complaint, or criminal prosecution is time-barred by calculating the filing deadline."}
        </p>
      </div>

      <div className="grid-3" style={{ gap: "25px", alignItems: "start" }}>
        
        {/* Date Selector Form */}
        <div className="card" style={{ gridColumn: "span 1" }}>
          <form onSubmit={calculateDeadline}>
            <h4 style={{ fontFamily: "var(--font-serif)", marginBottom: "20px", color: "var(--accent-gold-light)" }}>
              {language === "Tamil" ? "காலவரம்பு கணக்கீடு" : "Limitation Calculator"}
            </h4>

            {/* Case Type Dropdown */}
            <div className="input-group">
              <label className="input-label">
                {language === "Tamil" ? "தகராறு / குற்றத்தின் வகை" : "Type of Dispute / Offense"}
              </label>
              <select 
                className="input-control" 
                value={caseType} 
                onChange={(e) => {
                  setCaseType(e.target.value);
                  setCalculated(null);
                }}
              >
                {Object.entries(limitationRules).map(([key, val]) => (
                  <option key={key} value={key}>{val.label[language]}</option>
                ))}
              </select>
            </div>

            {/* Incident Date */}
            <div className="input-group" style={{ marginBottom: "25px" }}>
              <label className="input-label">
                {language === "Tamil" ? "சம்பவம் / உரிமை கோரல் நடந்த தேதி" : "Date of Incident / Cause of Action"}
              </label>
              <input
                type="date"
                className="input-control"
                required
                value={incidentDate}
                onChange={(e) => {
                  setIncidentDate(e.target.value);
                  setCalculated(null);
                }}
              />
            </div>

            <button type="submit" className="btn btn-primary" style={{ width: "100%" }} disabled={!incidentDate}>
              {language === "Tamil" ? "காலக்கெடுவைக் கணக்கிடு" : "Calculate Deadline"}
            </button>
          </form>
        </div>

        {/* Results Card */}
        <div style={{ gridColumn: "span 2" }}>
          {calculated ? (
            <div className="card" style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
              
              {/* Header and status badge */}
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid rgba(201,168,76,0.15)", paddingBottom: "15px" }}>
                <div>
                  <h4 style={{ fontFamily: "var(--font-serif)", color: "var(--accent-gold-light)", fontSize: "1.15rem" }}>
                    {limitationRules[caseType].label[language]}
                  </h4>
                  <span style={{ fontSize: "0.78rem", color: "var(--text-secondary)" }}>
                    {language === "Tamil" ? "ஆளும் சட்டம்:" : "Governing Statute:"} <strong>{limitationRules[caseType].act}</strong>
                  </span>
                </div>
                {status.badge}
              </div>

              {/* Deadline calculations */}
              <div className="grid-2" style={{ gap: "20px" }}>
                <div style={{ background: "rgba(255,255,255,0.02)", border: "1px solid var(--border-gold)", borderRadius: "8px", padding: "12px 16px" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "0.78rem", color: "var(--text-secondary)", textTransform: "uppercase", marginBottom: "4px" }}>
                    <FaCalendarAlt style={{ color: "var(--accent-gold)" }} />
                    <span>{language === "Tamil" ? "சம்பவ தேதி" : "Incident Date"}</span>
                  </div>
                  <strong style={{ fontSize: "1.05rem" }}>
                    {calculated.startDate.toLocaleDateString(language === "Tamil" ? "ta-IN" : "en-IN", { day: 'numeric', month: 'long', year: 'numeric' })}
                  </strong>
                </div>

                <div style={{ background: "rgba(255,255,255,0.02)", border: "1px solid var(--border-gold)", borderRadius: "8px", padding: "12px 16px" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "0.78rem", color: "var(--text-secondary)", textTransform: "uppercase", marginBottom: "4px" }}>
                    <FaRegClock style={{ color: "var(--accent-gold)" }} />
                    <span>{language === "Tamil" ? "இறுதி நாள் (Filing Deadline)" : "Filing Deadline"}</span>
                  </div>
                  <strong style={{ fontSize: "1.05rem", color: calculated.isExpired ? "var(--danger)" : "var(--success)" }}>
                    {calculated.noLimit 
                      ? (language === "Tamil" ? "வரம்பற்றது" : "Unlimited")
                      : calculated.isReasonable
                      ? (language === "Tamil" ? "நியாயமான கால அவகாசம்" : "Reasonable Time")
                      : calculated.deadlineDate.toLocaleDateString(language === "Tamil" ? "ta-IN" : "en-IN", { day: 'numeric', month: 'long', year: 'numeric' })}
                  </strong>
                </div>
              </div>

              {/* Status explanation */}
              <div style={{ background: status.cardColor, borderLeft: `4px solid ${status.borderColor}`, padding: "14px 18px", borderRadius: "8px", display: "flex", gap: "10px", alignItems: "flex-start" }}>
                <FaExclamationTriangle style={{ color: status.borderColor, flexShrink: 0, marginTop: "3px" }} />
                <span style={{ fontSize: "0.9rem", lineHeight: "1.4" }}>{status.text}</span>
              </div>

              {/* Legal advisory notes */}
              <div style={{ borderTop: "1px solid rgba(255,255,255,0.06)", paddingTop: "15px" }}>
                <h5 style={{ display: "inline-flex", alignItems: "center", gap: "6px", fontSize: "0.88rem", color: "var(--text-primary)", marginBottom: "6px" }}>
                  <FaBalanceScale style={{ color: "var(--accent-gold)" }} />
                  <span>{language === "Tamil" ? "சட்ட குறிப்பு மற்றும் கால நீட்டிப்பு" : "Limitation Condonation Guidance"}</span>
                </h5>
                <p style={{ fontSize: "0.82rem", color: "var(--text-secondary)", lineHeight: "1.4", paddingLeft: "20px" }}>
                  {limitationRules[caseType].notes[language]}
                </p>
                {calculated.isExpired && !calculated.noLimit && (
                  <div style={{ display: "flex", gap: "8px", alignItems: "flex-start", background: "rgba(241,196,15,0.05)", border: "1px solid rgba(241,196,15,0.15)", borderRadius: "8px", padding: "10px", marginTop: "12px", fontSize: "0.78rem", color: "var(--text-primary)" }}>
                    <FaUndoAlt style={{ color: "var(--warning)", flexShrink: 0, marginTop: "2px" }} />
                    <span>
                      {language === "Tamil"
                        ? "குறிப்பு: காலக்கெடு முடிந்திருந்தாலும், 'பிரிவு 5 கால வரம்புச் சட்டத்தின்' கீழ் தகுந்த மற்றும் போதிய காரணங்களை நீதிமன்றத்தில் நிரூபித்தால் கால தாமதத்தை மன்னித்து வழக்கைத் தாக்கல் செய்ய கோரலாம்."
                        : "Note: Since the deadline has passed, you must file a Condonation of Delay application under Section 5 of the Limitation Act, 1963 alongside your suit, detailing sufficient cause for the delay."}
                    </span>
                  </div>
                )}
              </div>

            </div>
          ) : (
            <div className="card" style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", minHeight: "340px", textAlign: "center", color: "var(--text-secondary)" }}>
              <FaRegClock style={{ fontSize: "3rem", color: "var(--border-gold-hover)", marginBottom: "15px" }} />
              <h4 style={{ fontFamily: "var(--font-serif)", color: "var(--text-primary)", marginBottom: "8px" }}>
                {language === "Tamil" ? "காலக்கெடுவைக் கணக்கிடவும்" : "No Deadline Calculated"}
              </h4>
              <p style={{ maxWidth: "400px", fontSize: "0.88rem" }}>
                {language === "Tamil"
                  ? "இடதுபுறத்தில் வழக்கு வகையைத் தேர்ந்தெடுத்து, சம்பவம் நடந்த தேதியைக் குறிப்பிட்டு கணக்கிடவும்."
                  : "Select a case category and input the incident date to calculate the limitation expiry and view relevant condonation options."}
              </p>
            </div>
          )}
        </div>

      </div>
    </div>
  );
};

export default LimitationsChecker;
