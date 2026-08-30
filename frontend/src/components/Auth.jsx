import { useState, useEffect, useRef } from "react";
import { FaUser, FaLock, FaEnvelope, FaBalanceScale } from "react-icons/fa";
import { FcGoogle } from "react-icons/fc";

function Auth({ onAuthSuccess, language }) {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const [googleClientId, setGoogleClientId] = useState("");
  const googleBtnRef = useRef(null);

  // Fetch Google Client ID and initialize Google Identity Services
  useEffect(() => {
    fetch("/api/auth/config")
      .then((res) => res.json())
      .then((data) => {
        if (data.google_client_id) {
          setGoogleClientId(data.google_client_id);
          initGoogleSignIn(data.google_client_id);
        }
      })
      .catch((err) => console.error("Failed to load auth config:", err));
  }, []);

  const handleGoogleCredentialResponse = async (response) => {
    if (!response || !response.credential) {
      setError("Google authentication was cancelled or failed.");
      return;
    }

    setError("");
    setGoogleLoading(true);

    try {
      // Send the official Google ID Token (JWT) directly to backend for cryptographic verification
      const res = await fetch("/api/auth/google", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          credential: response.credential,
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Official Google authentication failed.");
      }

      onAuthSuccess(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setGoogleLoading(false);
    }
  };

  const initGoogleSignIn = (clientId) => {
    if (window.google?.accounts?.id) {
      window.google.accounts.id.initialize({
        client_id: clientId,
        callback: handleGoogleCredentialResponse,
        auto_select: false,
        cancel_on_tap_outside: true,
      });

      if (googleBtnRef.current) {
        googleBtnRef.current.innerHTML = "";
        window.google.accounts.id.renderButton(googleBtnRef.current, {
          theme: "filled_blue",
          size: "large",
          type: "standard",
          shape: "rectangular",
          text: "continue_with",
          logo_alignment: "left",
          width: 340,
        });
      }
    } else {
      // Retry if Google script is still loading
      const timer = setTimeout(() => {
        if (window.google?.accounts?.id && googleBtnRef.current) {
          window.google.accounts.id.initialize({
            client_id: clientId,
            callback: handleGoogleCredentialResponse,
            auto_select: false,
          });
          googleBtnRef.current.innerHTML = "";
          window.google.accounts.id.renderButton(googleBtnRef.current, {
            theme: "filled_blue",
            size: "large",
            type: "standard",
            shape: "rectangular",
            text: "continue_with",
            logo_alignment: "left",
            width: 340,
          });
        }
      }, 800);
      return () => clearTimeout(timer);
    }
  };

  const triggerGooglePrompt = () => {
    if (!googleClientId) {
      setError(
        language === "Tamil"
          ? "Google உள்நுழைவுக்கு Google Cloud OAuth Client ID (.env அல்லது Render சூழலில் GOOGLE_CLIENT_ID) தேவை. கீழே உள்ள மின்னஞ்சல் மற்றும் கடவுச்சொல் மூலம் உடனடியாக உள்நுழையலாம்."
          : "Google Sign-In setup: Please set your GOOGLE_CLIENT_ID in your .env / Render environment variables. In the meantime, you can log in or register below using your email."
      );
      return;
    }

    if (window.google?.accounts?.id) {
      window.google.accounts.id.prompt((notification) => {
        if (notification.isNotDisplayed() || notification.isSkippedMoment()) {
          console.log("OneTap dismissed or not displayed; rendering standard popup button.");
        }
      });
    } else {
      setError("Google Sign-In SDK is loading. Please click again in a moment.");
    }
  };

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

        {/* Official Google Sign-In Container */}
        <div className="google-auth-wrapper">
          <div ref={googleBtnRef} id="google-signin-btn" className="google-official-btn-container"></div>
          
          {/* Fallback button if GIS button container is not yet populated */}
          {(!googleClientId || !window.google?.accounts?.id) && (
            <button 
              type="button" 
              className="auth-google-btn"
              onClick={triggerGooglePrompt}
              disabled={loading || googleLoading}
            >
              <FcGoogle className="google-icon" />
              <span>
                {googleLoading 
                  ? (language === "Tamil" ? "Google சரிபார்க்கிறது..." : "Verifying with Google...") 
                  : (language === "Tamil" ? "Google உடன் தொடரவும்" : "Continue with Google")}
              </span>
            </button>
          )}
        </div>

        {/* Divider */}
        <div className="auth-divider">
          <span>{language === "Tamil" ? "அல்லது மின்னஞ்சல் மூலம்" : "or continue with email"}</span>
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

          <button type="submit" className="auth-submit-btn" disabled={loading || googleLoading}>
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
