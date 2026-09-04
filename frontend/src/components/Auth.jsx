import { useState, useEffect, useRef } from "react";
import { 
  FaUser, 
  FaEnvelope, 
  FaBalanceScale, 
  FaSun, 
  FaMoon, 
  FaLaptop, 
  FaKey, 
  FaPaperPlane, 
  FaCheckCircle, 
  FaEdit, 
  FaShieldAlt 
} from "react-icons/fa";
import { FcGoogle } from "react-icons/fc";

function Auth({ onAuthSuccess, language, themeMode, setThemeMode }) {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [otp, setOtp] = useState("");
  const [otpStep, setOtpStep] = useState("enter_email"); // "enter_email" or "enter_otp"
  const [countdown, setCountdown] = useState(0);
  const [infoMsg, setInfoMsg] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const [googleClientId, setGoogleClientId] = useState("");
  const [gisRendered, setGisRendered] = useState(false);
  const googleBtnRef = useRef(null);

  // Countdown timer for OTP resend
  useEffect(() => {
    let timer = null;
    if (countdown > 0) {
      timer = setTimeout(() => setCountdown((c) => c - 1), 1000);
    }
    return () => clearTimeout(timer);
  }, [countdown]);

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

  const isValidGmail = (mail) => {
    if (!mail) return false;
    const clean = mail.trim().toLowerCase();
    return clean.endsWith("@gmail.com") || clean.endsWith("@googlemail.com");
  };

  const handleGoogleCredentialResponse = async (response) => {
    if (!response || !response.credential) {
      setError("Google authentication was cancelled or failed.");
      return;
    }

    setError("");
    setGoogleLoading(true);

    try {
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
          theme: themeMode === "light" ? "outline" : "filled_black",
          size: "large",
          type: "standard",
          shape: "rectangular",
          text: "continue_with",
          logo_alignment: "left",
          width: 380,
        });
        setGisRendered(true);
      }
    } else {
      const timer = setTimeout(() => {
        if (window.google?.accounts?.id && googleBtnRef.current) {
          window.google.accounts.id.initialize({
            client_id: clientId,
            callback: handleGoogleCredentialResponse,
            auto_select: false,
          });
          googleBtnRef.current.innerHTML = "";
          window.google.accounts.id.renderButton(googleBtnRef.current, {
            theme: themeMode === "light" ? "outline" : "filled_black",
            size: "large",
            type: "standard",
            shape: "rectangular",
            text: "continue_with",
            logo_alignment: "left",
            width: 380,
          });
          setGisRendered(true);
        }
      }, 800);
      return () => clearTimeout(timer);
    }
  };

  const triggerGooglePrompt = () => {
    if (!googleClientId) {
      setError(
        language === "Tamil"
          ? "Google உள்நுழைவுக்கு Google Cloud OAuth Client ID தேவை. கீழே உள்ள Gmail OTP மூலம் உடனடியாக உள்நுழையலாம்."
          : "Google Sign-In setup: Please set your GOOGLE_CLIENT_ID in your environment variables. In the meantime, you can log in or register below using your Gmail OTP."
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

  // Send OTP
  const handleSendOtp = async (e) => {
    if (e) e.preventDefault();
    setError("");
    setInfoMsg("");

    const cleanEmail = email.trim().toLowerCase();
    if (!isValidGmail(cleanEmail)) {
      setError(
        language === "Tamil"
          ? "சரியான @gmail.com மின்னஞ்சலை உள்ளிடவும் (எ.கா. yourname@gmail.com). போலி அல்லது பிற மின்னஞ்சல்கள் அனுமதிக்கப்படாது."
          : "Only valid official @gmail.com addresses are permitted (e.g. yourname@gmail.com)."
      );
      return;
    }

    if (!isLogin && (!name || name.trim().length < 2)) {
      setError(language === "Tamil" ? "தயவுசெய்து உங்கள் பெயரை உள்ளிடவும்." : "Please enter your full name.");
      return;
    }

    setLoading(true);

    try {
      const res = await fetch("/api/auth/send-otp", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: cleanEmail,
          purpose: isLogin ? "login" : "register",
          name: name.trim(),
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        if (res.status === 404 || data.detail?.includes("UNREGISTERED_EMAIL")) {
          // Unregistered email entered on Login -> automatically redirect to Register page!
          setIsLogin(false);
          setOtpStep("enter_email");
          setInfoMsg(
            language === "Tamil"
              ? "இந்த ஜிமெயில் இன்னும் பதிவு செய்யப்படவில்லை. பதிவு செய்ய உங்கள் முழு பெயரை உள்ளிட்டு தொடரவும்."
              : "This Gmail is not registered yet. Please enter your full name below to create your account."
          );
          return;
        }

        if (res.status === 409 || data.detail?.includes("ALREADY_REGISTERED")) {
          // Already registered email entered on Register -> automatically redirect to Login page!
          setIsLogin(true);
          setOtpStep("enter_email");
          setInfoMsg(
            language === "Tamil"
              ? "இந்த ஜிமெயில் ஏற்கனவே பதிவு செய்யப்பட்டுள்ளது. உள்நுழைய OTP பெறவும்."
              : "This Gmail is already registered. Switched to Login. Click below to receive your OTP."
          );
          return;
        }

        throw new Error(data.detail || "Failed to send verification code.");
      }

      setOtpStep("enter_otp");
      setCountdown(45);
      setInfoMsg(data.message || "Verification code sent to your Gmail.");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Verify OTP
  const handleVerifyOtp = async (e) => {
    e.preventDefault();
    setError("");
    setInfoMsg("");

    const cleanEmail = email.trim().toLowerCase();
    const cleanOtp = otp.trim();

    if (!cleanOtp || cleanOtp.length < 4) {
      setError(language === "Tamil" ? "6 இலக்க சரிபார்ப்புக் குறியீட்டை உள்ளிடவும்." : "Please enter the 6-digit verification code.");
      return;
    }

    setLoading(true);

    try {
      const res = await fetch("/api/auth/verify-otp", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: cleanEmail,
          otp: cleanOtp,
          name: name.trim(),
          purpose: isLogin ? "login" : "register",
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Verification failed. Please check the code.");
      }

      onAuthSuccess(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const switchTab = (toLogin) => {
    setIsLogin(toLogin);
    setError("");
    setInfoMsg("");
    setOtp("");
    setOtpStep("enter_email");
  };

  return (
    <div className="auth-page-wrapper">
      {setThemeMode && (
        <div style={{ position: "absolute", top: "20px", right: "20px", zIndex: 10 }}>
          <div className="theme-toggle" style={{ width: "200px" }}>
            <button
              type="button"
              className={`theme-btn ${themeMode === "system" ? "active" : ""}`}
              onClick={() => setThemeMode("system")}
            >
              <FaLaptop /> {language === "Tamil" ? "சிஸ்டம்" : "Auto"}
            </button>
            <button
              type="button"
              className={`theme-btn ${themeMode === "light" ? "active" : ""}`}
              onClick={() => setThemeMode("light")}
            >
              <FaSun /> {language === "Tamil" ? "பகல்" : "Light"}
            </button>
            <button
              type="button"
              className={`theme-btn ${themeMode === "dark" ? "active" : ""}`}
              onClick={() => setThemeMode("dark")}
            >
              <FaMoon /> {language === "Tamil" ? "இரவு" : "Dark"}
            </button>
          </div>
        </div>
      )}

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
          <div 
            ref={googleBtnRef} 
            id="google-signin-btn" 
            className="google-official-btn-container"
            style={{ display: gisRendered ? "flex" : "none", width: "100%", justifyContent: "center" }}
          ></div>
          
          {/* Fallback button if GIS button container is not yet populated */}
          {!gisRendered && (
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
          <span>{language === "Tamil" ? "அல்லது ஜிமெயில் OTP மூலம்" : "or continue with gmail otp"}</span>
        </div>

        {/* Main Tab: Login vs Register */}
        <div className="auth-toggle-buttons">
          <button 
            type="button"
            className={`auth-toggle-btn ${isLogin ? "active" : ""}`}
            onClick={() => switchTab(true)}
          >
            {language === "Tamil" ? "உள்நுழைய (Login)" : "Login"}
          </button>
          <button 
            type="button"
            className={`auth-toggle-btn ${!isLogin ? "active" : ""}`}
            onClick={() => switchTab(false)}
          >
            {language === "Tamil" ? "பதிவு செய்ய (Register)" : "Register"}
          </button>
        </div>

        {/* Alerts */}
        {error && <div className="auth-error-alert">{error}</div>}
        {infoMsg && (
          <div className="auth-success-alert">
            <FaCheckCircle style={{ flexShrink: 0 }} />
            <span>{infoMsg}</span>
          </div>
        )}

        {/* --- PASSWORDLESS GMAIL OTP FLOW --- */}
        <div>
          {otpStep === "enter_email" ? (
            <form onSubmit={handleSendOtp} className="auth-form">
              {!isLogin && (
                <div className="auth-input-group">
                  <FaUser className="input-icon" />
                  <input 
                    type="text" 
                    placeholder={language === "Tamil" ? "உங்கள் முழுப் பெயர்" : "Your Full Name"}
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
                  placeholder="yourname@gmail.com"
                  value={email} 
                  onChange={(e) => {
                    setEmail(e.target.value);
                    if (error) setError("");
                  }} 
                  required 
                />
              </div>

              <div className="auth-gmail-badge">
                <FaShieldAlt style={{ color: "var(--accent-gold)" }} />
                <span>{language === "Tamil" ? "அங்கீகரிக்கப்பட்ட @gmail.com மின்னஞ்சல் மட்டுமே ஏற்கப்படும்" : "Restricted to official @gmail.com accounts only"}</span>
              </div>

              <button type="submit" className="auth-submit-btn" disabled={loading || googleLoading}>
                <FaPaperPlane />
                <span>
                  {loading 
                    ? (language === "Tamil" ? "குறியீடு அனுப்புகிறது..." : "Sending Verification Code...") 
                    : (language === "Tamil" ? "OTP குறியீடு பெறுக" : "Send Verification Code (OTP)")}
                </span>
              </button>
            </form>
          ) : (
            <form onSubmit={handleVerifyOtp} className="auth-form">
              <div className="auth-email-pill">
                <div style={{ display: "flex", alignItems: "center", gap: "8px", minWidth: 0 }}>
                  <FaEnvelope style={{ color: "var(--accent-gold)", flexShrink: 0 }} />
                  <span className="auth-email-text">{email}</span>
                </div>
                <button 
                  type="button" 
                  className="auth-change-email-btn"
                  onClick={() => {
                    setOtpStep("enter_email");
                    setOtp("");
                  }}
                >
                  <FaEdit /> {language === "Tamil" ? "மாற்று" : "Change"}
                </button>
              </div>

              <div className="auth-input-group">
                <FaKey className="input-icon" />
                <input 
                  type="text" 
                  placeholder={language === "Tamil" ? "6-இலக்க OTP குறியீடு" : "Enter 6-digit OTP code"}
                  value={otp} 
                  onChange={(e) => setOtp(e.target.value.replace(/\D/g, "").slice(0, 6))} 
                  maxLength={6}
                  autoFocus
                  required 
                  style={{ letterSpacing: "4px", fontSize: "1.2rem", fontWeight: "700", textAlign: "center" }}
                />
              </div>

              <div className="auth-resend-row">
                {countdown > 0 ? (
                  <span className="auth-countdown-text">
                    {language === "Tamil" ? `மறுபடி அனுப்ப: ${countdown} வினாடிகள்` : `Resend code in ${countdown}s`}
                  </span>
                ) : (
                  <button 
                    type="button" 
                    className="auth-resend-btn"
                    onClick={handleSendOtp}
                    disabled={loading}
                  >
                    {language === "Tamil" ? "புதிய OTP குறியீடு அனுப்பு" : "Resend OTP Code"}
                  </button>
                )}
              </div>

              <button type="submit" className="auth-submit-btn" disabled={loading || otp.length < 4}>
                <FaCheckCircle />
                <span>
                  {loading 
                    ? (language === "Tamil" ? "சரிபார்க்கிறது..." : "Verifying...") 
                    : (isLogin 
                        ? (language === "Tamil" ? "சரிபார்த்து உள்நுழைக" : "Verify & Sign In") 
                        : (language === "Tamil" ? "சரிபார்த்து கணக்கை துவங்கு" : "Verify & Create Account"))}
                </span>
              </button>
            </form>
          )}
        </div>

        {/* Footer Navigation */}
        <p className="auth-footer-note">
          {isLogin 
            ? (language === "Tamil" ? "புதிய கணக்கா? " : "Don't have an account? ") 
            : (language === "Tamil" ? "ஏற்கனவே கணக்கு உள்ளதா? " : "Already have an account? ")}
          <span 
            className="auth-link-text"
            onClick={() => switchTab(!isLogin)}
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
