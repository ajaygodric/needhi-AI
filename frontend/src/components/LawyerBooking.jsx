import { useState, useEffect } from "react";
import { searchLawyers, bookLawyer } from "../utils/api";
import { FaCalendarAlt, FaStar, FaCheckCircle, FaUserShield, FaTimes, FaGavel, FaUniversity, FaBriefcase, FaMapMarkerAlt, FaGraduationCap, FaPhone, FaEnvelope, FaExclamationTriangle } from "react-icons/fa";

const LawyerBooking = ({ language }) => {
  const [activeTab, setActiveTab] = useState("directory"); // "directory", "nalsa"
  const [lawyers, setLawyers] = useState([]);
  const [selectedSpecialization, setSelectedSpecialization] = useState("");
  const [selectedCity, setSelectedCity] = useState("");
  const [searchTerm, setSearchTerm] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  // Booking Modal States
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [activeLawyer, setActiveLawyer] = useState(null);
  const [bookingDate, setBookingDate] = useState("");
  const [bookingSlot, setBookingSlot] = useState("");
  const [bookingDetails, setBookingDetails] = useState("");
  const [bookingReceipt, setBookingReceipt] = useState(null);

  const [clientName, setClientName] = useState("");
  const [clientEmail, setClientEmail] = useState("");
  const [clientPhone, setClientPhone] = useState("");
  const [isBookingLoading, setIsBookingLoading] = useState(false);
  const [bookingError, setBookingError] = useState("");

  // NALSA directory state
  const [nalsaState, setNalsaState] = useState("Tamil Nadu");

  const specialties = [
    { id: "", label: { English: "All Specialties", Tamil: "அனைத்து பிரிவுகள்" } },
    { id: "Criminal", label: { English: "Criminal Law", Tamil: "குற்றவியல் சட்டம்" } },
    { id: "Cyber", label: { English: "Cyber Law", Tamil: "சைபர் சட்டம்" } },
    { id: "Property", label: { English: "Property & RERA", Tamil: "சொத்து சட்டம் / RERA" } },
    { id: "Family", label: { English: "Family & Divorce", Tamil: "குடும்ப நல சட்டம்" } },
    { id: "Corporate", label: { English: "Corporate & Contract", Tamil: "நிறுவன சட்டம்" } },
    { id: "Civil", label: { English: "Civil Disputes", Tamil: "சிவில் வழக்குகள்" } }
  ];

  const cities = [
    { id: "", label: { English: "All Cities", Tamil: "அனைத்து நகரங்கள்" } },
    { id: "Chennai", label: { English: "Chennai", Tamil: "சென்னை" } },
    { id: "Delhi", label: { English: "Delhi", Tamil: "டெல்லி" } },
    { id: "Mumbai", label: { English: "Mumbai", Tamil: "மும்பை" } },
    { id: "Bangalore", label: { English: "Bangalore", Tamil: "பெங்களூர்" } }
  ];

  const nalsaData = {
    "Tamil Nadu":    {"authority": "Tamil Nadu State Legal Services Authority", "address": "High Court Buildings, Chennai - 600 104", "phone": "044-25340708", "email": "tnslsa@gmail.com", "helpline": "15100"},
    "Maharashtra":   {"authority": "Maharashtra State Legal Services Authority", "address": "High Court, Mumbai - 400 032", "phone": "022-22630956", "email": "mslsa@nic.in", "helpline": "15100"},
    "Delhi":         {"authority": "Delhi State Legal Services Authority", "address": "Patiala House Courts, New Delhi - 110 001", "phone": "011-23384559", "email": "dslsa@nic.in", "helpline": "15100"},
    "Karnataka":     {"authority": "Karnataka State Legal Services Authority", "address": "High Court of Karnataka, Bengaluru - 560 001", "phone": "080-22868026", "email": "kslsa@nic.in", "helpline": "15100"},
    "Uttar Pradesh": {"authority": "U.P. State Legal Services Authority", "address": "16/99, Civil Lines, Prayagraj - 211 001", "phone": "0532-2440120", "email": "upslsa@nic.in", "helpline": "15100"},
    "West Bengal":   {"authority": "West Bengal State Legal Services Authority", "address": "Calcutta High Court, Kolkata - 700 001", "phone": "033-22371946", "email": "wbslsa@nic.in", "helpline": "15100"},
    "Rajasthan":     {"authority": "Rajasthan State Legal Services Authority", "address": "High Court Premises, Jodhpur - 342 001", "phone": "0291-2434010", "email": "rslsa@nic.in", "helpline": "15100"},
    "Gujarat":       {"authority": "Gujarat State Legal Services Authority", "address": "High Court of Gujarat, Sola, Ahmedabad - 380 060", "phone": "079-27660007", "email": "gslsa@nic.in", "helpline": "15100"},
    "Madhya Pradesh":{"authority": "M.P. State Legal Services Authority", "address": "High Court of M.P., Jabalpur - 482 001", "phone": "0761-2628591", "email": "mpslsa@nic.in", "helpline": "15100"},
    "Kerala":        {"authority": "Kerala State Legal Services Authority", "address": "High Court of Kerala, Ernakulam - 682 031", "phone": "0484-2562266", "email": "kelslsa@nic.in", "helpline": "15100"},
    "Andhra Pradesh":{"authority": "A.P. State Legal Services Authority", "address": "High Court of A.P., Amaravati - 522 020", "phone": "0863-2346919", "email": "apslsa@nic.in", "helpline": "15100"},
    "Telangana":     {"authority": "Telangana State Legal Services Authority", "address": "High Court of Telangana, Hyderabad - 500 001", "phone": "040-23450406", "email": "tslsa@nic.in", "helpline": "15100"},
    "Punjab":        {"authority": "Punjab State Legal Services Authority", "address": "Punjab & Haryana High Court, Chandigarh - 160 001", "phone": "0172-2748513", "email": "pslsa@nic.in", "helpline": "15100"},
    "Haryana":       {"authority": "Haryana State Legal Services Authority", "address": "Punjab & Haryana High Court, Chandigarh - 160 001", "phone": "0172-2748514", "email": "hslsa@nic.in", "helpline": "15100"},
    "Bihar":         {"authority": "Bihar State Legal Services Authority", "address": "Patna High Court, Patna - 800 001", "phone": "0612-2219981", "email": "bslsa@nic.in", "helpline": "15100"}
  };

  useEffect(() => {
    let active = true;
    const fetchLawyers = async () => {
      setIsLoading(true);
      try {
        const data = await searchLawyers(selectedSpecialization, selectedCity, searchTerm);
        if (active) {
          setLawyers(data);
        }
      } catch (err) {
        console.error(err);
      } finally {
        if (active) {
          setIsLoading(false);
        }
      }
    };
    fetchLawyers();
    return () => {
      active = false;
    };
  }, [selectedSpecialization, selectedCity, searchTerm]);

  const openBookingModal = (lawyer) => {
    setActiveLawyer(lawyer);
    setIsModalOpen(true);
    setBookingDate("");
    setBookingSlot("");
    setBookingDetails("");
    setClientName("");
    setClientEmail("");
    setClientPhone("");
    setIsBookingLoading(false);
    setBookingError("");
    setBookingReceipt(null);
  };

  const handleConfirmBooking = async (e) => {
    e.preventDefault();
    if (!bookingDate || !bookingSlot || !clientName || !clientEmail || !clientPhone) return;

    setIsBookingLoading(true);
    setBookingError("");

    try {
      const res = await bookLawyer({
        lawyer_id: activeLawyer.id,
        client_name: clientName,
        client_email: clientEmail,
        client_phone: clientPhone,
        date: bookingDate,
        slot: bookingSlot,
        details: bookingDetails
      });
      setBookingReceipt(res.receipt);
    } catch (err) {
      setBookingError(err.message || "Failed to book lawyer. Please try again.");
    } finally {
      setIsBookingLoading(false);
    }
  };

  return (
    <div>
      <div className="section-header">
        <h2 className="section-title">
          {language === "Tamil" ? "சட்ட ஆலோசனைகள் & முன்பதிவு" : "Legal Counsel & Appointment Booking"}
        </h2>
        <p className="section-subtitle">
          {language === "Tamil"
            ? "வழக்கறிஞர்களிடம் நேரடியாக ஆன்லைன் மூலம் ஆலோசனை பெற முன்பதிவு செய்யுங்கள் அல்லது இலவச சட்ட உதவி மையங்களை அணுகுங்கள்."
            : "Schedule online consultations with verifying legal advocates or look up free legal aid panels (NALSA)."}
        </p>
      </div>

      {/* Tabs */}
      <div className="rights-tab-container">
        <button
          className={`rights-tab ${activeTab === "directory" ? "active" : ""}`}
          onClick={() => setActiveTab("directory")}
          style={{ display: "inline-flex", alignItems: "center", gap: "8px" }}
        >
          <FaGavel />
          <span>{language === "Tamil" ? "வழக்கறிஞர்கள் முன்பதிவு" : "Book Practicing Lawyers"}</span>
        </button>
        <button
          className={`rights-tab ${activeTab === "nalsa" ? "active" : ""}`}
          onClick={() => setActiveTab("nalsa")}
          style={{ display: "inline-flex", alignItems: "center", gap: "8px" }}
        >
          <FaUniversity />
          <span>{language === "Tamil" ? "இலவச சட்ட உதவி மையங்கள் (NALSA)" : "Free Legal Aid Centers (NALSA)"}</span>
        </button>
      </div>

      {/* TAB 1: Lawyer booking directory */}
      {activeTab === "directory" && (
        <div>
          {/* Filters panel */}
          <div className="card" style={{ marginBottom: "25px" }}>
            <div className="grid-3" style={{ gap: "15px" }}>
              <div>
                <label className="input-label">{language === "Tamil" ? "சட்டப்பிரிவு" : "Specialization"}</label>
                <select className="input-control" value={selectedSpecialization} onChange={(e) => setSelectedSpecialization(e.target.value)}>
                  {specialties.map(spec => (
                    <option key={spec.id} value={spec.id}>{spec.label[language]}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="input-label">{language === "Tamil" ? "நகரம்" : "City"}</label>
                <select className="input-control" value={selectedCity} onChange={(e) => setSelectedCity(e.target.value)}>
                  {cities.map(c => (
                    <option key={c.id} value={c.id}>{c.label[language]}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="input-label">{language === "Tamil" ? "தேடுக" : "Text Search"}</label>
                <input
                  type="text"
                  className="input-control"
                  placeholder={language === "Tamil" ? "பெயர் அல்லது சிறப்பு..." : "Search lawyer name or bio..."}
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </div>
            </div>
          </div>

          {/* Directory Listings */}
          {isLoading ? (
            <div className="grid-2">
              {[1, 2, 3].map(n => (
                <div key={n} className="card loading-pulse" style={{ height: "180px" }}></div>
              ))}
            </div>
          ) : lawyers.length === 0 ? (
            <div className="card" style={{ textAlign: "center", padding: "40px" }}>
              <p style={{ color: "var(--text-secondary)" }}>
                {language === "Tamil" ? "வழக்கறிஞர்கள் யாரும் கண்டறியப்படவில்லை." : "No legal advocates found matching your filters."}
              </p>
            </div>
          ) : (
            <div className="grid-2">
              {lawyers.map((lawyer) => (
                <div key={lawyer.id} className="card">
                  <div className="lawyer-card">
                    <div className="lawyer-avatar-container" style={{ display: "flex", alignItems: "center", justifyContent: "center" }}>
                      <FaBriefcase style={{ fontSize: "1.5rem", color: "var(--accent-gold)" }} />
                    </div>
                    <div className="lawyer-details">
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                        <h4 style={{ fontFamily: "var(--font-serif)", fontSize: "1.1rem" }}>{lawyer.name}</h4>
                        <span className="lawyer-rating">
                          <FaStar /> {lawyer.rating} <span className="lawyer-reviews">({lawyer.reviews})</span>
                        </span>
                      </div>
                      <p style={{ color: "var(--accent-gold-light)", fontSize: "0.82rem", fontWeight: "600" }}>{lawyer.specialization}</p>
                      <p style={{ color: "var(--text-secondary)", fontSize: "0.85rem", display: "flex", flexWrap: "wrap", alignItems: "center", gap: "6px" }}>
                        <span style={{ display: "inline-flex", alignItems: "center", gap: "4px" }}><FaMapMarkerAlt style={{ color: "var(--accent-gold-light)" }} /> {lawyer.city}, {lawyer.state}</span>
                        <span>•</span>
                        <span style={{ display: "inline-flex", alignItems: "center", gap: "4px" }}><FaGraduationCap style={{ color: "var(--accent-gold-light)" }} /> {lawyer.experience} Yrs Exp</span>
                      </p>
                      <p style={{ color: "var(--text-secondary)", fontSize: "0.82rem", fontStyle: "italic", margin: "6px 0" }}>
                        "{lawyer.bio}"
                      </p>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "10px", paddingTop: "8px", borderTop: "1px solid rgba(255,255,255,0.06)" }}>
                        <span className="lawyer-fee">₹{lawyer.fee} <small style={{ fontWeight: "400", color: "var(--text-secondary)", fontSize: "0.75rem" }}>/ consult</small></span>
                        <button className="btn btn-primary btn-small" onClick={() => openBookingModal(lawyer)}>
                          <FaCalendarAlt /> {language === "Tamil" ? "முன்பதிவு செய்" : "Book Slot"}
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* TAB 2: NALSA Free Legal Aid */}
      {activeTab === "nalsa" && (
        <div className="card step-card">
          <div className="card-title">
            <span><FaUserShield /></span>
            {language === "Tamil" ? "இலவச சட்ட உதவி திட்டம் (NALSA)" : "National Legal Services Authority (NALSA)"}
          </div>
          <div style={{ background: "rgba(201, 168, 76, 0.08)", border: "1px solid var(--border-gold)", borderRadius: "10px", padding: "16px", marginBottom: "20px", fontSize: "0.85rem" }}>
            {language === "Tamil" 
              ? "சட்டப்பிரிவு 39A-ன் கீழ், ஏழைகள் மற்றும் நலிவடைந்த பிரிவினருக்கு அரசு இலவச சட்ட உதவி வழங்குகிறது. பெண்கள், குழந்தைகள், SC/ST பிரிவினர், மற்றும் ஆண்டு வருமானம் ₹3 லட்சத்திற்கு குறைவானவர்கள் இதற்கு தகுதியானவர்கள்."
              : "Under Article 39A of the Indian Constitution, free legal aid is guaranteed to disadvantaged groups. Eligible citizens include women, children, SC/ST members, industrial workmen, and persons with annual income under ₹3 Lakhs."}
          </div>

          <div className="input-group" style={{ maxWidth: "300px" }}>
            <label className="input-label">{language === "Tamil" ? "உங்கள் மாநிலத்தை தேர்வு செய்க" : "Select Your State Authority"}</label>
            <select className="input-control" value={nalsaState} onChange={(e) => setNalsaState(e.target.value)}>
              {Object.keys(nalsaData).sort().map(st => (
                <option key={st} value={st}>{st}</option>
              ))}
            </select>
          </div>

          {/* Active State Details */}
          {nalsaData[nalsaState] && (
            <div style={{ background: "rgba(255,255,255,0.03)", border: "1px solid var(--border-gold)", borderRadius: "12px", padding: "24px", marginTop: "20px" }}>
              <h3 style={{ fontFamily: "var(--font-serif)", color: "var(--accent-gold-light)", marginBottom: "12px", display: "flex", alignItems: "center", gap: "8px" }}>
                <FaUniversity /> {nalsaData[nalsaState].authority}
              </h3>
              <p style={{ color: "var(--text-primary)", fontSize: "0.93rem", margin: "6px 0", display: "flex", alignItems: "center", gap: "8px" }}>
                <FaMapMarkerAlt style={{ color: "var(--accent-gold)" }} /> <span>Address: <b style={{ fontWeight: "500" }}>{nalsaData[nalsaState].address}</b></span>
              </p>
              <p style={{ color: "var(--text-primary)", fontSize: "0.93rem", margin: "6px 0", display: "flex", alignItems: "center", gap: "8px" }}>
                <FaPhone style={{ color: "var(--accent-gold)" }} /> <span>Telephone: <b style={{ fontWeight: "500" }}>{nalsaData[nalsaState].phone}</b></span>
              </p>
              <p style={{ color: "var(--text-primary)", fontSize: "0.93rem", margin: "6px 0", display: "flex", alignItems: "center", gap: "8px" }}>
                <FaEnvelope style={{ color: "var(--accent-gold)" }} /> <span>Email ID: <b style={{ fontWeight: "500" }}>{nalsaData[nalsaState].email}</b></span>
              </p>
              <p style={{ color: "var(--text-primary)", fontSize: "0.93rem", margin: "6px 0", display: "flex", alignItems: "center", gap: "8px" }}>
                <FaExclamationTriangle style={{ color: "var(--danger)" }} /> <span>NALSA National Helpline: <b style={{ color: "var(--danger)", fontSize: "1.1rem" }}>{nalsaData[nalsaState].helpline}</b> (Toll Free)</span>
              </p>
            </div>
          )}
        </div>
      )}

      {/* Appointment Booking Modal */}
      {isModalOpen && activeLawyer && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h3>{bookingReceipt ? (language === "Tamil" ? "முன்பதிவு விவரம்" : "Booking Confirmed!") : (language === "Tamil" ? "சந்திப்பு முன்பதிவு" : "Schedule Consultation")}</h3>
              <button className="modal-close" onClick={() => setIsModalOpen(false)}>
                <FaTimes />
              </button>
            </div>
            <div className="modal-body">
              {!bookingReceipt ? (
                <form onSubmit={handleConfirmBooking}>
                  <div style={{ marginBottom: "20px", display: "flex", gap: "15px", alignItems: "center" }}>
                    <div style={{ width: "60px", height: "60px", background: "rgba(201,168,76,0.1)", border: "1px solid var(--border-gold)", borderRadius: "8px", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "1.5rem" }}>
                      <FaBriefcase style={{ color: "var(--accent-gold)" }} />
                    </div>
                    <div>
                      <h4 style={{ fontFamily: "var(--font-serif)" }}>{activeLawyer.name}</h4>
                      <p style={{ color: "var(--accent-gold)", fontSize: "0.8rem", fontWeight: "600" }}>{activeLawyer.specialization}</p>
                      <p style={{ color: "var(--text-secondary)", fontSize: "0.8rem" }}>Fee: ₹{activeLawyer.fee} / consultation</p>
                    </div>
                  </div>

                  {/* Client Information */}
                  <div className="input-group">
                    <label className="input-label">{language === "Tamil" ? "உங்கள் பெயர்" : "Your Name"}</label>
                    <input
                      type="text"
                      className="input-control"
                      placeholder="e.g. abcd"
                      required
                      value={clientName}
                      onChange={(e) => setClientName(e.target.value)}
                    />
                  </div>
                  <div className="grid-2">
                    <div className="input-group">
                      <label className="input-label">{language === "Tamil" ? "மின்னஞ்சல்" : "Email Address"}</label>
                      <input
                        type="email"
                        className="input-control"
                        placeholder="e.g. xyz@example.com"
                        required
                        value={clientEmail}
                        onChange={(e) => setClientEmail(e.target.value)}
                      />
                    </div>
                    <div className="input-group">
                      <label className="input-label">{language === "Tamil" ? "கைபேசி எண்" : "Phone Number"}</label>
                      <input
                        type="tel"
                        className="input-control"
                        placeholder="e.g. 1234"
                        required
                        value={clientPhone}
                        onChange={(e) => setClientPhone(e.target.value)}
                      />
                    </div>
                  </div>

                  <div className="grid-2" style={{ marginTop: "15px" }}>
                    <div className="input-group">
                      <label className="input-label">{language === "Tamil" ? "தேதி" : "Select Date"}</label>
                      <input
                        type="date"
                        className="input-control"
                        required
                        value={bookingDate}
                        onChange={(e) => setBookingDate(e.target.value)}
                      />
                    </div>
                    <div className="input-group">
                      <label className="input-label">{language === "Tamil" ? "நேரத்தைத் தேர்ந்தெடு" : "Available Time Slots"}</label>
                      <select
                        className="input-control"
                        required
                        value={bookingSlot}
                        onChange={(e) => setBookingSlot(e.target.value)}
                      >
                        <option value="">-- Choose Slot --</option>
                        {activeLawyer.slots.map(sl => (
                          <option key={sl} value={sl}>{sl}</option>
                        ))}
                      </select>
                    </div>
                  </div>

                  <div className="input-group">
                    <label className="input-label">{language === "Tamil" ? "பிரச்சனை குறித்த சுருக்கம்" : "Brief Description of Case/Grievance"}</label>
                    <textarea
                      rows="3"
                      className="input-control"
                      placeholder="Explain your situation in 2-3 lines..."
                      value={bookingDetails}
                      onChange={(e) => setBookingDetails(e.target.value)}
                    ></textarea>
                  </div>

                  {bookingError && (
                    <div style={{ color: "var(--danger)", fontSize: "0.85rem", marginBottom: "15px", display: "flex", alignItems: "center", gap: "6px" }}>
                      <FaExclamationTriangle /> {bookingError}
                    </div>
                  )}

                  <button type="submit" className="btn btn-primary" style={{ width: "100%" }} disabled={isBookingLoading}>
                    {isBookingLoading ? (language === "Tamil" ? "முன்பதிவு செய்யப்படுகிறது..." : "Booking Appointment...") : (language === "Tamil" ? "முன்பதிவை உறுதி செய்" : "Confirm Appointment")}
                  </button>
                </form>
              ) : (
                <div className="receipt">
                  <div className="receipt-header">
                    <FaCheckCircle className="receipt-success-icon" />
                    <h4 className="receipt-title">{language === "Tamil" ? "முன்பதிவு எண்" : "Consultation Ticket"}</h4>
                    <span style={{ fontSize: "1.1rem", fontFamily: "monospace", color: "var(--accent-gold-light)", fontWeight: "bold" }}>{bookingReceipt.code}</span>
                  </div>
                  
                  <div className="receipt-row">
                    <span className="label">Lawyer:</span>
                    <span className="val">{bookingReceipt.lawyer}</span>
                  </div>
                  <div className="receipt-row">
                    <span className="label">Practice Area:</span>
                    <span className="val" style={{ color: "var(--accent-gold)" }}>{bookingReceipt.specialty}</span>
                  </div>
                  <div className="receipt-row">
                    <span className="label">Scheduled Time:</span>
                    <span className="val" style={{ color: "var(--accent-gold-light)" }}>{bookingReceipt.date} at {bookingReceipt.time}</span>
                  </div>
                  <div className="receipt-row" style={{ borderBottom: "1px dashed var(--border-gold)", paddingBottom: "10px", marginBottom: "10px" }}>
                    <span className="label">Consultation Fee:</span>
                    <span className="val">₹{bookingReceipt.fee} (Payable at clinic)</span>
                  </div>

                  <div style={{ fontSize: "0.82rem", color: "var(--text-secondary)", textAlign: "center" }}>
                    <p style={{ margin: "2px 0", display: "flex", alignItems: "center", justifyContent: "center", gap: "6px" }}><FaPhone /> Call: {bookingReceipt.phone}</p>
                    <p style={{ margin: "2px 0", display: "flex", alignItems: "center", justifyContent: "center", gap: "6px" }}><FaEnvelope /> Email: {bookingReceipt.email}</p>
                    <div style={{ marginTop: "12px", padding: "8px", background: "rgba(46,204,113,0.08)", border: "1px solid rgba(46,204,113,0.2)", borderRadius: "8px", color: "var(--success)", fontWeight: "600", display: "flex", alignItems: "center", justifyContent: "center", gap: "6px" }}>
                      <FaCheckCircle /> {bookingReceipt.email_status && bookingReceipt.email_status.includes("successfully") ? (language === "Tamil" ? "மின்னஞ்சல் அனுப்பப்பட்டது!" : "Ticket Sent to Phone & Email") : (language === "Tamil" ? "முன்பதிவு சேமிக்கப்பட்டது! (வழிகாட்டி பயன்முறை)" : "Ticket Saved! (Simulation Mode)")}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default LawyerBooking;
