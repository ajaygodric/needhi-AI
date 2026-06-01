import { useState } from "react";
import { simplifyLegalText } from "../utils/api";
import { renderMarkdown } from "../utils/renderMarkdown";
import { FaEye, FaLanguage, FaExchangeAlt, FaClipboard, FaRegFileAlt, FaInfoCircle } from "react-icons/fa";

const LegalSimplifier = ({ language }) => {
  const [inputText, setInputText] = useState("");
  const [targetLang, setTargetLang] = useState("English");
  const [isSimplifying, setIsSimplifying] = useState(false);
  const [simplifiedResult, setSimplifiedResult] = useState("");
  const [errorMessage, setErrorMessage] = useState("");

  const handleSimplify = async (e) => {
    e.preventDefault();
    if (!inputText.trim()) return;

    setIsSimplifying(true);
    setSimplifiedResult("");
    setErrorMessage("");

    try {
      const res = await simplifyLegalText(inputText, targetLang);
      setSimplifiedResult(res.simplified);
    } catch (err) {
      console.error(err);
      setErrorMessage(err.message || "Failed to simplify legal text.");
    } finally {
      setIsSimplifying(false);
    }
  };

  const handlePasteDemo = () => {
    const demoText = `
    IN WITNESS WHEREOF, the Parties hereto have executed this Lease Agreement as of the date first written above. PROVIDED ALWAYS and it is hereby agreed that if the Rent hereby reserved or any part thereof shall be unpaid for fifteen (15) days after becoming payable (whether formally demanded or not) or if the Tenant shall fail to observe or perform any of the covenants herein contained, it shall be lawful for the Landlord to re-enter upon the Premises and thereupon this Lease shall absolutely determine.
    `.trim();
    setInputText(demoText);
  };



  return (
    <div>
      <div className="section-header">
        <h2 className="section-title">
          {language === "Tamil" ? "சட்ட மொழியாக்கம் & எளிமையாக்கல்" : "Legal Translation & Simplifier"}
        </h2>
        <p className="section-subtitle">
          {language === "Tamil"
            ? "அறிவிப்புகள், ஷரத்துகள் அல்லது நீதிமன்ற உத்தரவுகளைப் பதிவிட்டு, அவற்றின் எளிய சுருக்கம் மற்றும் விளக்கத்தைப் பெறுங்கள்."
            : "Paste complex legal clauses, notices, or court orders to translate and explain them in plain language (English or Tamil)."}
        </p>
      </div>

      <div className="grid-2" style={{ gap: "25px", alignItems: "start" }}>
        
        {/* Paste Input Card */}
        <div className="card">
          <form onSubmit={handleSimplify}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "15px" }}>
              <h4 style={{ fontFamily: "var(--font-serif)", color: "var(--accent-gold-light)" }}>
                {language === "Tamil" ? "மூல சட்ட உரை" : "Paste Legal Snippet"}
              </h4>
              <button type="button" className="btn btn-small" onClick={handlePasteDemo}>
                {language === "Tamil" ? "உதாரண உரை" : "Try Demo Clause"}
              </button>
            </div>

            <div className="input-group" style={{ marginBottom: "10px" }}>
              <textarea
                rows="10"
                className="input-control"
                style={{ fontFamily: "monospace", fontSize: "0.88rem", borderColor: inputText.length > 4000 ? "var(--danger)" : "" }}
                placeholder={
                  language === "Tamil"
                    ? "சட்ட ஆவணத்தில் உள்ள கடினமான ஆங்கில உரை அல்லது ஷரத்தை இங்கே ஒட்டவும் (Paste)..."
                    : "Paste any complicated contract clause, legal notice, summons, or legal text here..."
                }
                required
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
              ></textarea>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.78rem", marginTop: "5px" }}>
                <span style={{ color: "var(--text-secondary)" }}>
                  {inputText.length > 4000 && (
                    <span style={{ color: "var(--danger)" }}>
                      {language === "Tamil" ? "அதிகபட்ச வரம்பை தாண்டியது (அதிகபட்சம் 4000 எழுத்துக்கள்)" : "Exceeded maximum limit! (Max 4000 characters)"}
                    </span>
                  )}
                </span>
                <span style={{ color: inputText.length > 4000 ? "var(--danger)" : "var(--text-secondary)" }}>
                  {inputText.length} / 4000
                </span>
              </div>
            </div>

            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "20px", marginTop: "20px" }}>
              
              {/* Target Language Toggle */}
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <span style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>
                  <FaLanguage style={{ color: "var(--accent-gold)", fontSize: "1.1rem" }} />
                  <span style={{ marginLeft: "5px" }}>{language === "Tamil" ? "முடிவின் மொழி:" : "Output Language:"}</span>
                </span>
                <div className="lang-toggle" style={{ margin: 0, padding: "2px" }}>
                  <button 
                    type="button"
                    className={`lang-btn ${targetLang === "English" ? "active" : ""}`} 
                    onClick={() => setTargetLang("English")}
                    style={{ padding: "4px 10px", fontSize: "0.75rem" }}
                  >
                    EN
                  </button>
                  <button 
                    type="button"
                    className={`lang-btn ${targetLang === "Tamil" ? "active" : ""}`} 
                    onClick={() => setTargetLang("Tamil")}
                    style={{ padding: "4px 10px", fontSize: "0.75rem" }}
                  >
                    தமிழ்
                  </button>
                </div>
              </div>

              <button type="submit" className="btn btn-primary" disabled={isSimplifying || !inputText.trim() || inputText.length > 4000}>
                {isSimplifying ? (language === "Tamil" ? "எளிமையாக்கப்படுகிறது..." : "Simplifying...") : (language === "Tamil" ? "எளிமைப்படுத்து" : "Simplify Legal Text")}
              </button>

            </div>
          </form>
        </div>

        {/* Simplified Output Card */}
        <div>
          {simplifiedResult ? (
            <div className="card">
              <div className="card-title">
                <span><FaEye /></span>
                {language === "Tamil" ? "எளிமைப்படுத்தப்பட்ட வடிவம்" : "Simplified Plain Language View"}
              </div>

              <div 
                style={{ background: "rgba(255,255,255,0.01)", border: "1px solid var(--border-gold)", borderRadius: "10px", padding: "20px", fontSize: "0.93rem", lineHeight: "1.6" }}
              >
                <div 
                  style={{ whiteSpace: "pre-line" }}
                  dangerouslySetInnerHTML={{ __html: renderMarkdown(simplifiedResult) }}
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
            <div className="card" style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", minHeight: "345px", textAlign: "center", color: "var(--text-secondary)" }}>
              <FaExchangeAlt style={{ fontSize: "3rem", color: "var(--border-gold-hover)", marginBottom: "15px" }} />
              <h4 style={{ fontFamily: "var(--font-serif)", color: "var(--text-primary)", marginBottom: "8px" }}>
                {language === "Tamil" ? "விளக்கம் தயாராக இல்லை" : "Awaiting Legal Snippet"}
              </h4>
              <p style={{ maxWidth: "400px", fontSize: "0.88rem" }}>
                {language === "Tamil"
                  ? "இடதுபுறத்தில் சட்ட உரையைப் பதிவிட்டு, மொழியைத் தேர்வு செய்து, 'எளிமைப்படுத்து' பொத்தானை அழுத்தவும்."
                  : "Paste any complex lease clause or notice text on the left to see it broken down into plain-English/Tamil summary, actions, and deadlines."}
              </p>
            </div>
          )}
        </div>

      </div>
    </div>
  );
};

export default LegalSimplifier;
