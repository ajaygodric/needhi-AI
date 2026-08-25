import { useState, useEffect, useRef } from "react";
import { chatWithNeedhi, analyzeDocument, downloadPdf, chatWithDocument } from "../utils/api";
import { renderMarkdown } from "../utils/renderMarkdown";
import { FaPaperPlane, FaTrash, FaDownload, FaMicrophone, FaFileMedical, FaExclamationTriangle, FaComments, FaFileAlt, FaBalanceScale, FaUser } from "react-icons/fa";

const HomeChat = ({ language, user }) => {
  const [activeTab, setActiveTab] = useState("ask"); // "ask", "upload", "voice"
  
  // Chat state
  const [chatHistory, setChatHistory] = useState([]);
  const [inputMessage, setInputMessage] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamedResponse, setStreamedResponse] = useState("");
  const [searchHistory, setSearchHistory] = useState([]);
  const chatEndRef = useRef(null);

  const fetchSearchHistory = () => {
    if (!user) return;
    fetch("/api/chat/history", {
      headers: {
        "Authorization": `Bearer ${user.token}`
      }
    })
    .then(res => {
      if (res.ok) return res.json();
      return [];
    })
    .then(data => {
      setSearchHistory(data || []);
    })
    .catch(err => console.error(err));
  };

  const handleClearHistory = () => {
    if (!user) return;
    if (!confirm(language === "Tamil" ? "சமீபத்திய தேடல்களை அழிக்க வேண்டுமா?" : "Are you sure you want to clear your search history?")) {
      return;
    }
    fetch("/api/chat/history", {
      method: "DELETE",
      headers: {
        "Authorization": `Bearer ${user.token}`
      }
    })
    .then(res => {
      if (res.ok) {
        setSearchHistory([]);
      }
    })
    .catch(err => console.error(err));
  };

  useEffect(() => {
    fetchSearchHistory();
  }, [user]);


  // Document scan state
  const [selectedFile, setSelectedFile] = useState(null);
  const [extraQuestion, setExtraQuestion] = useState("");
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState("");
  const [docText, setDocText] = useState("");
  const [docChatHistory, setDocChatHistory] = useState([]);
  const [docInputMessage, setDocInputMessage] = useState("");
  const [isDocStreaming, setIsDocStreaming] = useState(false);
  const [docStreamedResponse, setDocStreamedResponse] = useState("");

  // Voice state
  const [isListening, setIsListening] = useState(false);
  const [voiceTranscript, setVoiceTranscript] = useState("");
  const [voiceError, setVoiceError] = useState("");

  // Auto-scroll chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatHistory, streamedResponse]);

  // Suggestions
  const suggestions = {
    English: [
      "What is BNS Section 85 (Cruelty)?",
      "How to file a cyber fraud complaint?",
      "What are tenant rights in case of eviction?",
      "Bail process under new BNSS law?",
      "How do I file a consumer court complaint?"
    ],
    Tamil: [
      "பிரிவு 85 (குடும்ப வன்முறை) என்றால் என்ன?",
      "சைபர் மோசடி புகார் செய்வது எப்படி?",
      "வாடகைதாரர் வெளியேற்றப்பட்டால் என்ன உரிமைகள்?",
      "புதிய BNSS சட்டத்தில் பிணை பெறுவது எப்படி?",
      "நுகர்வோர் நீதிமன்ற புகார் செய்வது எப்படி?"
    ]
  };

  // Run chat query
  const handleSendMessage = (textToSend) => {
    const msg = textToSend || inputMessage;
    if (!msg.trim()) return;

    const userMsg = { role: "user", text: msg };
    const updatedHistory = [...chatHistory, userMsg].slice(-30);
    setChatHistory(updatedHistory);
    setInputMessage("");
    setIsStreaming(true);
    setStreamedResponse("");

    // Call API
    chatWithNeedhi(
      msg,
      language,
      chatHistory.slice(-30),
      (chunk, full) => {
        setStreamedResponse(full);
      },
      (fullText) => {
        setChatHistory([...updatedHistory, { role: "ai", text: fullText }].slice(-30));
        setStreamedResponse("");
        setIsStreaming(false);
        fetchSearchHistory();
      },
      (err) => {
        setChatHistory([...updatedHistory, { role: "ai", text: `❌ Error: ${err.message}. Please try again.` }].slice(-30));
        setStreamedResponse("");
        setIsStreaming(false);
      }
    );
  };

  // Run document analyzer
  const handleAnalyzeDoc = async () => {
    if (!selectedFile) return;
    
    // Check 25MB limit on frontend (25 * 1024 * 1024 = 26,214,400 bytes)
    const MAX_FILE_SIZE = 25 * 1024 * 1024;
    if (selectedFile.size > MAX_FILE_SIZE) {
      setAnalysisResult(
        language === "Tamil"
          ? "❌ பிழை: கோப்பின் அளவு 25MB வரம்பை விட அதிகமாக உள்ளது."
          : "❌ Error: File size exceeds the 25MB limit."
      );
      return;
    }

    setIsAnalyzing(true);
    setAnalysisResult("");
    setDocText("");
    setDocChatHistory([]);

    try {
      const res = await analyzeDocument(selectedFile, extraQuestion);
      setAnalysisResult(res.analysis);
      setDocText(res.doc_text || "");
      setDocChatHistory([
        { role: "ai", text: res.analysis }
      ]);
    } catch (err) {
      setAnalysisResult(`❌ Error: ${err.message}`);
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Send doc follow-up question
  const handleSendDocMessage = () => {
    if (!docInputMessage.trim() || !docText || docText.startsWith("Text extraction failed")) return;

    const userMsg = { role: "user", text: docInputMessage };
    const updatedHistory = [...docChatHistory, userMsg].slice(-30);
    setDocChatHistory(updatedHistory);
    setDocInputMessage("");
    setIsDocStreaming(true);
    setDocStreamedResponse("");

    chatWithDocument(
      docText,
      docInputMessage,
      language,
      docChatHistory.slice(-30),
      (chunk, full) => {
        setDocStreamedResponse(full);
      },
      (fullText) => {
        setDocChatHistory([...updatedHistory, { role: "ai", text: fullText }].slice(-30));
        setDocStreamedResponse("");
        setIsDocStreaming(false);
      },
      (err) => {
        setDocChatHistory([...updatedHistory, { role: "ai", text: `❌ Error: ${err.message}. Please try again.` }].slice(-30));
        setDocStreamedResponse("");
        setIsDocStreaming(false);
      }
    );
  };

  // Native Web Speech API
  const startSpeechRecognition = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setVoiceError("Your browser does not support Speech Recognition. Try Chrome or Edge.");
      return;
    }

    const rec = new SpeechRecognition();
    rec.continuous = false;
    rec.interimResults = false;
    rec.lang = language === "Tamil" ? "ta-IN" : "en-IN";

    rec.onstart = () => {
      setIsListening(true);
      setVoiceError("");
      setVoiceTranscript("");
    };

    rec.onerror = (e) => {
      setVoiceError(`Error: ${e.error}`);
      setIsListening(false);
    };

    rec.onend = () => {
      setIsListening(false);
    };

    rec.onresult = (event) => {
      const result = event.results[0][0].transcript;
      setVoiceTranscript(result);
      setInputMessage(result);
      setActiveTab("ask"); // Switch to chat tab with voice input
    };

    rec.start();
  };

  // Export chat to PDF
  const handleDownloadChatPdf = () => {
    if (chatHistory.length === 0) return;
    
    let formattedText = "";
    chatHistory.forEach((msg, idx) => {
      if (msg.role === "user") {
        formattedText += `\n**Q${Math.floor(idx / 2) + 1}: Complainant Query**\n${msg.text}\n`;
      } else {
        formattedText += `\n**Needhi AI Legal Response**\n${msg.text}\n-----------------------------------\n`;
      }
    });

    downloadPdf("Needhi AI - Legal Consultation", formattedText, "Needhi_Legal_Consultation.pdf");
  };

  // Helper for badges in AI response
  const detectSeverityHtml = (text) => {
    const t = text.toLowerCase();
    const badges = [];
    if (t.includes("non-bailable") || t.includes("non bailable") || t.includes("பிணையில் வர முடியாத") || t.includes("ஜாமீனில் வெளிவர முடியாத")) {
      badges.push(<span key="nb" className="badge badge-red">Non-Bailable</span>);
    } else if (t.includes("bailable") || t.includes("பிணையில் வரக்கூடிய") || t.includes("ஜாமீனில் வரக்கூடிய")) {
      badges.push(<span key="b" className="badge badge-yellow">Bailable</span>);
    }
    if (t.includes("civil") || t.includes("சிவில்") || t.includes("உரிமையியல்")) {
      badges.push(<span key="c" className="badge badge-green">Civil Matter</span>);
    }
    if (t.includes("criminal") || t.includes("imprisonment") || t.includes("jail") || t.includes("குற்றம்") || t.includes("கைது") || t.includes("சிறை")) {
      badges.push(<span key="cr" className="badge badge-red">Criminal Offense</span>);
    }
    if (t.includes("ipc") || t.includes("bns") || t.includes("section") || t.includes("பிரிவு")) {
      badges.push(<span key="sec" className="badge badge-blue">Statutory Provisions</span>);
    }
    return badges.length > 0 ? (
      <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", marginTop: "12px", paddingTop: "8px", borderTop: "1px solid rgba(255,255,255,0.06)" }}>
        {badges}
      </div>
    ) : null;
  };



  return (
    <div>
      <div className="hero">
        <div className="hero-tag">AI · Legal · India</div>
        <h2 className="hero-title">{language === "Tamil" ? "நீதி AI" : "NEEDHI AI"}</h2>
        <p className="hero-subtitle">
          {language === "Tamil" 
            ? "உங்கள் AI சட்ட உதவியாளர் — எளிய தமிழில் சட்ட ஆலோசனைகள்" 
            : "Your Intelligent AI Legal Counsel — Plain English Legal Guidance & Analysis"}
        </p>
        <div className="stats-bar">
          <div className="stat-item"><span className="stat-num">BNS</span><span className="stat-label">Bharatiya Nyaya Sanhita</span></div>
          <div className="stat-item"><span className="stat-num">IPC</span><span className="stat-label">Indian Penal Code</span></div>
          <div className="stat-item"><span className="stat-num">24/7</span><span className="stat-label">Instant Aid</span></div>
        </div>
      </div>

      {/* Tabs */}
      <div className="rights-tab-container">
        <button className={`rights-tab ${activeTab === "ask" ? "active" : ""}`} onClick={() => setActiveTab("ask")} style={{ display: "inline-flex", alignItems: "center", gap: "8px" }}>
          <FaComments /> {language === "Tamil" ? "கேளுங்கள்" : "Ask Legal Question"}
        </button>
        <button className={`rights-tab ${activeTab === "upload" ? "active" : ""}`} onClick={() => setActiveTab("upload")} style={{ display: "inline-flex", alignItems: "center", gap: "8px" }}>
          <FaFileAlt /> {language === "Tamil" ? "கோப்பு பதிவேற்றம்" : "Upload Document"}
        </button>
        <button className={`rights-tab ${activeTab === "voice" ? "active" : ""}`} onClick={() => setActiveTab("voice")} style={{ display: "inline-flex", alignItems: "center", gap: "8px" }}>
          <FaMicrophone /> {language === "Tamil" ? "குரல் வழி கேள்வி" : "Voice Consultation"}
        </button>
      </div>

      {/* TAB 1: Chat Counsel */}
      {activeTab === "ask" && (
        <div>
          <div className="chat-window">
            {chatHistory.length === 0 && !isStreaming ? (
              <div className="chat-empty">
                <div className="chat-empty-icon"><FaBalanceScale /></div>
                <h3>{language === "Tamil" ? "ஆலோசனையைத் தொடங்குங்கள்" : "Start Consultation"}</h3>
                <p>
                  {language === "Tamil"
                    ? "உங்கள் சட்ட சிக்கலை கீழே விரிவாக விவரிக்கவும். உதவ நீதி AI தயாராக உள்ளது."
                    : "Describe your legal issue or ask about specific laws. Needhi AI will analyze applicable legal provisions."}
                </p>
                <div className="chat-suggestions">
                  {suggestions[language].map((s, idx) => (
                    <button key={idx} className="suggestion-chip" onClick={() => handleSendMessage(s)}>
                      {s}
                    </button>
                  ))}
                </div>

                {searchHistory.length > 0 && (
                  <div style={{ marginTop: "25px", width: "100%", borderTop: "1px solid rgba(255,255,255,0.06)", paddingTop: "20px" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
                      <h4 style={{ fontSize: "0.85rem", color: "var(--accent-gold-light)", textTransform: "uppercase", letterSpacing: "1px", margin: 0 }}>
                        {language === "Tamil" ? "சமீபத்திய தேடல்கள்" : "Recent Searches"}
                      </h4>
                      <button 
                        onClick={handleClearHistory}
                        style={{ background: "transparent", border: "none", color: "var(--danger)", fontSize: "0.75rem", fontWeight: "600", cursor: "pointer", display: "inline-flex", alignItems: "center", gap: "4px" }}
                      >
                        <FaTrash style={{ fontSize: "0.68rem" }} /> {language === "Tamil" ? "அழி" : "Clear"}
                      </button>
                    </div>
                    <div className="chat-suggestions" style={{ justifyContent: "center" }}>
                      {searchHistory.map((sh, idx) => (
                        <button 
                          key={idx} 
                          className="suggestion-chip" 
                          onClick={() => handleSendMessage(sh.query)} 
                          style={{ borderColor: "rgba(201,168,76,0.2)", background: "rgba(201,168,76,0.03)", color: "var(--text-secondary)", opacity: 0.9 }}
                        >
                          🔍 {sh.query.length > 40 ? sh.query.slice(0, 40) + "..." : sh.query}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="chat-messages">
                {chatHistory.map((msg, idx) => (
                  <div key={idx} className={`chat-bubble-container ${msg.role}`}>
                    <div className="chat-avatar">
                      {msg.role === "user" ? <FaUser /> : <FaBalanceScale />}
                    </div>
                    <div className="chat-bubble-wrapper">
                      <span className="chat-sender-name">
                        {msg.role === "user" ? (language === "Tamil" ? "நீங்கள்" : "You") : "Needhi AI"}
                      </span>
                      <div className="chat-bubble">
                        <div 
                          style={{ whiteSpace: "pre-line" }}
                          dangerouslySetInnerHTML={{ __html: renderMarkdown(msg.text) }}
                        />
                        {msg.role === "ai" && detectSeverityHtml(msg.text)}
                      </div>
                    </div>
                  </div>
                ))}
                
                {/* Streaming view */}
                {isStreaming && streamedResponse && (
                  <div className="chat-bubble-container ai">
                    <div className="chat-avatar"><FaBalanceScale /></div>
                    <div className="chat-bubble-wrapper">
                      <span className="chat-sender-name">Needhi AI</span>
                      <div className="chat-bubble">
                        <div 
                          style={{ whiteSpace: "pre-line" }}
                          dangerouslySetInnerHTML={{ __html: renderMarkdown(streamedResponse) }}
                        />
                      </div>
                    </div>
                  </div>
                )}

                {/* Loading typing state */}
                {isStreaming && !streamedResponse && (
                  <div className="chat-bubble-container ai">
                    <div className="chat-avatar"><FaBalanceScale /></div>
                    <div className="chat-bubble-wrapper">
                      <span className="chat-sender-name">Needhi AI</span>
                      <div className="chat-bubble">
                        <div className="typing-indicator">
                          <div className="typing-dot"></div>
                          <div className="typing-dot"></div>
                          <div className="typing-dot"></div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
                <div ref={chatEndRef} />
              </div>
            )}

            {/* Input Bar */}
            <div className="chat-input-bar">
              <input
                type="text"
                className="chat-input"
                placeholder={
                  language === "Tamil"
                    ? "எ.கா. என் வீட்டு உரிமையாளர் அட்வான்ஸ் தொகையை தரவில்லை..."
                    : "e.g. My landlord is refusing to return my security deposit..."
                }
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSendMessage()}
                disabled={isStreaming}
              />
              <button className="btn btn-primary" onClick={() => handleSendMessage()} disabled={isStreaming || !inputMessage.trim()}>
                <FaPaperPlane />
              </button>
            </div>
          </div>

          {/* Action Row */}
          {chatHistory.length > 0 && (
            <div style={{ display: "flex", gap: "10px", marginTop: "15px", justifyContent: "flex-end" }}>
              <button className="btn" onClick={handleDownloadChatPdf}>
                <FaDownload /> {language === "Tamil" ? "PDF பதிவிறக்கு" : "Download PDF Report"}
              </button>
              <button className="btn btn-danger" onClick={() => setChatHistory([])}>
                <FaTrash /> {language === "Tamil" ? "அழி" : "Clear Chat"}
              </button>
            </div>
          )}
        </div>
      )}

      {/* TAB 2: Document Scanner */}
      {activeTab === "upload" && (
        <div className="card step-card">
          <div className="card-title" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", width: "100%" }}>
            <span style={{ display: "inline-flex", alignItems: "center", gap: "8px" }}>
              <FaFileMedical />
              {language === "Tamil" ? "சட்ட ஆவண பகுப்பாய்வு & கலந்துரையாடல்" : "Legal Document Q&A & Analysis"}
            </span>
            {analysisResult && (
              <button 
                className="btn btn-small btn-danger" 
                onClick={() => {
                  setSelectedFile(null);
                  setAnalysisResult("");
                  setDocText("");
                  setDocChatHistory([]);
                  setExtraQuestion("");
                }}
              >
                {language === "Tamil" ? "புதிய ஆவணம்" : "Upload Different File"}
              </button>
            )}
          </div>
          
          {!analysisResult ? (
            <div>
              <p style={{ color: "var(--text-secondary)", fontSize: "0.9rem", marginBottom: "20px" }}>
                {language === "Tamil"
                  ? "ஒரு சட்ட ஆவணம் (PDF அல்லது படம்) பதிவேற்றவும். நீதி AI அதன் முக்கிய ஷரத்துக்களை பகுப்பாய்வு செய்யும், பின்னர் உங்களுடன் உரையாடும்."
                  : "Upload any legal agreement, contract, or notice (PDF or Image). Needhi AI will summarize it, identify risks, and chat with you about it."}
              </p>

              <div className="input-group">
                <label className="input-label">{language === "Tamil" ? "கோப்பை தேர்வு செய்யவும் (PDF / PNG / JPG)" : "Choose Document File (PDF / PNG / JPG)"}</label>
                <input
                  type="file"
                  className="input-control"
                  accept=".pdf,.png,.jpg,.jpeg"
                  onChange={(e) => setSelectedFile(e.target.files[0])}
                />
              </div>

              <div className="input-group">
                <label className="input-label">
                  {language === "Tamil" ? "ஆரம்பக் கேள்வி (தேவைப்பட்டால்)" : "Initial Analysis Focus (Optional)"}
                </label>
                <input
                  type="text"
                  className="input-control"
                  placeholder={language === "Tamil" ? "எ.கா. இதில் எனக்கு ஏதேனும் நஷ்டஈடு பொறுப்புகள் உள்ளதா?" : "e.g. Highlight termination clauses and liabilities"}
                  value={extraQuestion}
                  onChange={(e) => setExtraQuestion(e.target.value)}
                />
              </div>

              <button className="btn btn-primary" onClick={handleAnalyzeDoc} disabled={isAnalyzing || !selectedFile} style={{ width: "100%" }}>
                {isAnalyzing ? (language === "Tamil" ? "பகுப்பாய்வு செய்யப்படுகிறது..." : "Analyzing Document...") : (language === "Tamil" ? "ஆவணத்தை ஆராய்" : "Analyze Document")}
              </button>
            </div>
          ) : (
            <div>
              <div style={{ background: "rgba(201,168,76,0.06)", border: "1px solid var(--border-gold)", borderRadius: "10px", padding: "12px 16px", marginBottom: "20px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div style={{ fontSize: "0.9rem", color: "var(--text-primary)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", maxWidth: "70%" }}>
                  <strong>{language === "Tamil" ? "ஆவணம்:" : "Active File:"}</strong> {selectedFile?.name || "Document"}
                </div>
                <button 
                  className="btn btn-small"
                  onClick={() => downloadPdf("Document Scan & Analysis Report", analysisResult, "Document_Analysis.pdf")}
                >
                  <FaDownload /> {language === "Tamil" ? "பதிவிறக்கு" : "Download Summary"}
                </button>
              </div>

              {/* Document Multi-turn Chat Window */}
              <div className="chat-window" style={{ height: "450px", marginBottom: "0px" }}>
                <div className="chat-messages">
                  {docChatHistory.map((msg, idx) => (
                    <div key={idx} className={`chat-bubble-container ${msg.role}`}>
                      <div className="chat-avatar">
                        {msg.role === "user" ? <FaUser /> : <FaBalanceScale />}
                      </div>
                      <div className="chat-bubble-wrapper">
                        <span className="chat-sender-name">
                          {msg.role === "user" ? (language === "Tamil" ? "நீங்கள்" : "You") : "Needhi AI"}
                        </span>
                        <div className="chat-bubble">
                          <div 
                            style={{ whiteSpace: "pre-line" }}
                            dangerouslySetInnerHTML={{ __html: renderMarkdown(msg.text) }}
                          />
                        </div>
                      </div>
                    </div>
                  ))}
                  
                  {/* Streaming doc response */}
                  {isDocStreaming && docStreamedResponse && (
                    <div className="chat-bubble-container ai">
                      <div className="chat-avatar"><FaBalanceScale /></div>
                      <div className="chat-bubble-wrapper">
                        <span className="chat-sender-name">Needhi AI</span>
                        <div className="chat-bubble">
                          <div 
                            style={{ whiteSpace: "pre-line" }}
                            dangerouslySetInnerHTML={{ __html: renderMarkdown(docStreamedResponse) }}
                          />
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Loading typing state */}
                  {isDocStreaming && !docStreamedResponse && (
                    <div className="chat-bubble-container ai">
                      <div className="chat-avatar"><FaBalanceScale /></div>
                      <div className="chat-bubble-wrapper">
                        <span className="chat-sender-name">Needhi AI</span>
                        <div className="chat-bubble">
                          <div className="typing-indicator">
                            <div className="typing-dot"></div>
                            <div className="typing-dot"></div>
                            <div className="typing-dot"></div>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                {/* Doc Input Bar */}
                <div className="chat-input-bar">
                  <input
                    type="text"
                    className="chat-input"
                    placeholder={
                      docText.startsWith("Text extraction failed")
                        ? (language === "Tamil"
                            ? "ஆவண உரை பகுப்பாய்வு தோல்வியடைந்தது. பின்தொடர முடியாது."
                            : "Text extraction failed. Follow-up chat disabled.")
                        : (language === "Tamil"
                            ? "ஆவணம் பற்றி கேளுங்கள் (எ.கா. முறிவு ஷரத்து என்ன சொல்கிறது?)"
                            : "Ask about the document (e.g. Can I terminate this without notice?)")
                    }
                    value={docInputMessage}
                    onChange={(e) => setDocInputMessage(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleSendDocMessage()}
                    disabled={isDocStreaming || docText.startsWith("Text extraction failed")}
                    style={{ opacity: docText.startsWith("Text extraction failed") ? 0.6 : 1 }}
                  />
                  <button 
                    className="btn btn-primary" 
                    onClick={handleSendDocMessage} 
                    disabled={isDocStreaming || !docInputMessage.trim() || docText.startsWith("Text extraction failed")}
                    style={{ opacity: docText.startsWith("Text extraction failed") ? 0.6 : 1 }}
                  >
                    <FaPaperPlane />
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* TAB 3: Voice Input */}
      {activeTab === "voice" && (
        <div className="card step-card" style={{ textAlign: "center", padding: "40px 20px" }}>
          <div className="card-title" style={{ justifyContent: "center" }}>
            <span><FaMicrophone /></span>
            {language === "Tamil" ? "குரல் ஆணை சட்ட ஆலோசனை" : "Speech-to-Text Counsel"}
          </div>
          <p style={{ color: "var(--text-secondary)", fontSize: "0.9rem", maxWidth: "500px", margin: "0 auto 30px auto" }}>
            {language === "Tamil"
              ? "கீழே உள்ள மைக் பொத்தானை அழுத்தி, உங்கள் சட்டச் சிக்கலைத் தெளிவாகப் பேசவும்."
              : "Click the microphone button and describe your case. Needhi AI will transcribe your description and analyze it."}
          </p>

          <div style={{ marginBottom: "30px" }}>
            <button
              className={`btn ${isListening ? "btn-danger" : "btn-primary"}`}
              style={{
                width: "80px",
                height: "80px",
                borderRadius: "50%",
                fontSize: "2rem",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                margin: "0 auto",
                boxShadow: isListening ? "0 0 20px rgba(231,76,60,0.6)" : "none",
                animation: isListening ? "pulseNode 1.2s infinite alternate" : "none"
              }}
              onClick={startSpeechRecognition}
              disabled={isListening}
            >
              <FaMicrophone />
            </button>
            <div style={{ marginTop: "12px", fontWeight: "600", fontSize: "0.9rem", color: isListening ? "var(--danger)" : "var(--text-secondary)" }}>
              {isListening ? (language === "Tamil" ? "கேட்கிறது... பேசவும்" : "Listening... speak now") : (language === "Tamil" ? "தொடங்க கிளிக் செய்க" : "Click to Speak")}
            </div>
          </div>

          {voiceTranscript && (
            <div style={{ background: "rgba(255,255,255,0.03)", border: "1px solid var(--border-gold)", borderRadius: "8px", padding: "16px", maxWidth: "600px", margin: "0 auto 16px auto", textAlign: "left" }}>
              <div style={{ fontSize: "0.75rem", textTransform: "uppercase", color: "var(--accent-gold)", fontWeight: "700" }}>{language === "Tamil" ? "நாங்கள் கேட்டது" : "Transcribed Text"}</div>
              <p style={{ fontSize: "0.95rem", marginTop: "4px" }}>"{voiceTranscript}"</p>
            </div>
          )}

          {voiceError && (
            <div style={{ color: "var(--danger)", display: "flex", alignItems: "center", justifyContent: "center", gap: "8px", fontSize: "0.9rem" }}>
              <FaExclamationTriangle /> {voiceError}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default HomeChat;
