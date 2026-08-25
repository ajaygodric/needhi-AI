import { useState } from "react";
import { FaUser, FaLock, FaEnvelope, FaBalanceScale } from "react-icons/fa";

function Auth({ onAuthSuccess, language }) {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    const endpoint = isLogin ? "/api/auth/login" : "/api/auth/register";
    const payload = isLogin 
      ? { email, password } 
      : { name, email, password };

    try {
      const response = await fetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Authentication failed. Please try again.");
      }

      onAuthSuccess(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page-wrapper">
      <div className="auth-card-container">
        <div className="auth-brand-header">
          <div className="auth-brand-logo">
            <FaBalanceScale />
          </div>
          <h1>NEEDHI AI</h1>
          <p className="subtitle">
            {language === "Tamil" 
              ? "நீதிமன்ற உதவி மற்றும் வழிகாட்டி" 
              : "AI-Powered Legal Assistant for Indian Law"}
          </p>
        </div>

        <div className="auth-toggle-buttons">
          <button 
            type="button"
            className={`auth-toggle-btn ${isLogin ? "active" : ""}`}
            onClick={() => { setIsLogin(true); setError(""); }}
          >
            {language === "Tamil" ? "உள்நுழைய" : "Login"}
          </button>
          <button 
            type="button"
            className={`auth-toggle-btn ${!isLogin ? "active" : ""}`}
            onClick={() => { setIsLogin(false); setError(""); }}
          >
            {language === "Tamil" ? "பதிவு செய்ய" : "Register"}
          </button>
        </div>

        {error && <div className="auth-error-alert">{error}</div>}

        <form onSubmit={handleSubmit} className="auth-form">
          {!isLogin && (
            <div className="auth-input-group">
              <FaUser className="input-icon" />
              <input 
                type="text" 
                placeholder={language === "Tamil" ? "உங்கள் பெயர்" : "Your Name"}
                value={name} 
                onChange={(e) => setName(e.target.value)} 
                required 
              />
            </div>
          )}

          <div className="auth-input-group">
            <FaEnvelope className="input-icon" />
            <input 
              type="email" 
              placeholder={language === "Tamil" ? "மின்னஞ்சல் முகவரி" : "Email Address"}
              value={email} 
              onChange={(e) => setEmail(e.target.value)} 
              required 
            />
          </div>

          <div className="auth-input-group">
            <FaLock className="input-icon" />
            <input 
              type="password" 
              placeholder={language === "Tamil" ? "கடவுச்சொல்" : "Password"}
              value={password} 
              onChange={(e) => setPassword(e.target.value)} 
              required 
            />
          </div>

          <button type="submit" className="auth-submit-btn" disabled={loading}>
            {loading 
              ? (language === "Tamil" ? "செயலாக்குகிறது..." : "Processing...") 
              : (isLogin 
                  ? (language === "Tamil" ? "உள்நுழைய" : "Sign In") 
                  : (language === "Tamil" ? "கணக்கை உருவாக்கு" : "Create Account"))}
          </button>
        </form>

        <p className="auth-footer-note">
          {isLogin 
            ? (language === "Tamil" ? "புதிய கணக்கா? " : "Don't have an account? ") 
            : (language === "Tamil" ? "ஏற்கனவே கணக்கு உள்ளதா? " : "Already have an account? ")}
          <span 
            className="auth-link-text"
            onClick={() => { setIsLogin(!isLogin); setError(""); }}
          >
            {isLogin 
              ? (language === "Tamil" ? "இங்கே பதிவு செய்யவும்" : "Register here") 
              : (language === "Tamil" ? "இங்கே உள்நுழையவும்" : "Login here")}
          </span>
        </p>
      </div>
    </div>
  );
}

export default Auth;
