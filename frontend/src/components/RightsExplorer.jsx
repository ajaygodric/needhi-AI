import { useState } from "react";
import {
  FaUserShield,
  FaShoppingCart,
  FaHome,
  FaLaptop,
  FaFileSignature,
  FaVolumeMute,
  FaBalanceScale,
  FaMoon,
  FaClipboardList,
  FaShieldAlt,
  FaBullhorn,
  FaRedo,
  FaUniversity,
  FaFileAlt,
  FaKey,
  FaMoneyBillWave,
  FaWrench,
  FaExclamationTriangle,
  FaCreditCard,
  FaCamera
} from "react-icons/fa";

const RightsExplorer = ({ language }) => {
  const [activeTab, setActiveTab] = useState("police");

  const tabs = [
    { id: "police", label: { English: "Police & Arrest", Tamil: "காவல் & கைது" }, icon: FaUserShield },
    { id: "consumer", label: { English: "Consumer Rights", Tamil: "நுகர்வோர் உரிமை" }, icon: FaShoppingCart },
    { id: "tenant", label: { English: "Tenant Rights", Tamil: "வாடகைதாரர்" }, icon: FaHome },
    { id: "cyber", label: { English: "Cyber Security", Tamil: "இணையப் பாதுகாப்பு" }, icon: FaLaptop }
  ];

  const rightsData = {
    police: [
      {
        icon: FaFileSignature,
        title: { English: "Right to Register FIR", Tamil: "எஃப்.ஐ.ஆர் (FIR) பதிவு செய்யும் உரிமை" },
        desc: { 
          English: "Police are legally bound to register an FIR for cognizable offenses under BNSS Section 173. If refused, complain to the SP or file in court.", 
          Tamil: "கைது செய்யக்கூடிய குற்றங்களுக்கு எஃப்.ஐ.ஆர் பதிவு செய்ய வேண்டியது காவல்துறையின் கடமை (BNSS பிரிவு 173). மறுக்கப்பட்டால் எஸ்.பி.யிடம் புகார் செய்யலாம்."
        }
      },
      {
        icon: FaVolumeMute,
        title: { English: "Right to Silence", Tamil: "மௌன விரத உரிமை" },
        desc: {
          English: "Under Article 20(3) of the Constitution, you have the right to remain silent when arrested and cannot be forced to testify against yourself.",
          Tamil: "அரசியலமைப்புச் சட்டப் பிரிவு 20(3)-ன் படி, கைது செய்யப்படும்போது மௌனமாக இருக்க உங்களுக்கு உரிமை உண்டு. உங்களுக்கு எதிராக வாக்குமூலம் அளிக்க கட்டாயப்படுத்த முடியாது."
        }
      },
      {
        icon: FaBalanceScale,
        title: { English: "Right to Consult a Lawyer", Tamil: "வழக்கறிஞர் ஆலோசனை உரிமை" },
        desc: {
          English: "You have the right to consult a lawyer immediately upon arrest. Legal aid is free if you cannot afford one (Article 22).",
          Tamil: "கைது செய்யப்பட்டவுடன் ஒரு வழக்கறிஞரை அணுக உரிமை உண்டு. ஏழைகளுக்கு இலவச சட்ட உதவி வழங்க அரசு கடமைப்பட்டுள்ளது (பிரிவு 22)."
        }
      },
      {
        icon: FaMoon,
        title: { English: "Night Arrest Limitation (Women)", Tamil: "இரவு நேர கைது தடை (பெண்கள்)" },
        desc: {
          English: "Women cannot be arrested after sunset and before sunrise, except in extraordinary circumstances under permission of a judicial magistrate and with a female officer.",
          Tamil: "அசாதாரண சூழ்நிலைகளைத் தவிர்த்து, சூரிய அஸ்தமனத்திற்குப் பிறகு மற்றும் சூரிய உதயத்திற்கு முன்பு பெண்களைக் கைது செய்யக்கூடாது. பெண் காவலர் உடன் இருக்க வேண்டும்."
        }
      },
      {
        icon: FaClipboardList,
        title: { English: "Right to Know Grounds of Arrest", Tamil: "கைது காரணத்தை அறியும் உரிமை" },
        desc: {
          English: "Police must immediately inform you of the exact reason and grounds for your arrest at the time of detention (BNSS Section 47).",
          Tamil: "கைது செய்யப்படும் போதே, அதற்கான காரணத்தை உடனடியாகக் காவல் துறையினர் உங்களிடம் தெரிவிக்க வேண்டும் (BNSS பிரிவு 47)."
        }
      }
    ],
    consumer: [
      {
        icon: FaShieldAlt,
        title: { English: "Right to Safety", Tamil: "பாதுகாப்பு உரிமை" },
        desc: {
          English: "Protection against goods, production processes, and services that are hazardous to health or life under Consumer Protection Act 2019.",
          Tamil: "ஆரோக்கியம் அல்லது உயிருக்கு ஆபத்தை விளைவிக்கும் பொருட்கள் மற்றும் சேவைகளுக்கு எதிரான பாதுகாப்பு பெறும் உரிமை (நுகர்வோர் பாதுகாப்பு சட்டம் 2019)."
        }
      },
      {
        icon: FaBullhorn,
        title: { English: "Right to Information", Tamil: "தகவல் அறியும் உரிமை" },
        desc: {
          English: "Right to be informed about the quality, quantity, potency, purity, standard, and price of goods or services before purchase.",
          Tamil: "பொருட்களின் தரம், அளவு, தூய்மை மற்றும் விலை விவரங்களை நுகர்வோர் வாங்குவதற்கு முன் தெரிந்து கொள்ளும் உரிமை."
        }
      },
      {
        icon: FaRedo,
        title: { English: "Right to Refund & Replacement", Tamil: "பணத்தைத் திரும்பப் பெறும் உரிமை" },
        desc: {
          English: "If a product is defective or a service is deficient, you have the right to request a repair, replacement, or complete refund.",
          Tamil: "வாங்கிய பொருள் அல்லது சேவையில் குறைபாடு இருந்தால், அதனை பழுதுபார்க்க, மாற்ற அல்லது பணத்தைத் திரும்பப் பெற உரிமை உண்டு."
        }
      },
      {
        icon: FaUniversity,
        title: { English: "Right to file complaint in Consumer Commission", Tamil: "நுகர்வோர் நீதிமன்ற உரிமை" },
        desc: {
          English: "Three-tier dispute resolution system: District Commission (up to ₹50 Lakhs), State Commission (up to ₹2 Crores), and National Commission (above ₹2 Crores).",
          Tamil: "மாவட்ட நுகர்வோர் நீதிமன்றம் (₹50 லட்சம் வரை), மாநில நுகர்வோர் நீதிமன்றம் (₹2 கோடி வரை) மற்றும் தேசிய நுகர்வோர் நீதிமன்றம் (₹2 கோடிக்கு மேல்) மூலம் தீர்வு காணலாம்."
        }
      }
    ],
    tenant: [
      {
        icon: FaFileAlt,
        title: { English: "Right to a Written Rent Agreement", Tamil: "வாடகை ஒப்பந்த உரிமை" },
        desc: {
          English: "Tenants should insist on a signed, written rent agreement. Registration is legally required if the lease exceeds 11 months.",
          Tamil: "எழுதுபூர்வமான வாடகை ஒப்பந்தம் கோர உரிமை உண்டு. 11 மாதங்களுக்கு மேல் வாடகைக்கு இருந்தால் ஒப்பந்தத்தைப் பதிவு செய்வது கட்டாயம்."
        }
      },
      {
        icon: FaKey,
        title: { English: "Protection from Illegal Eviction", Tamil: "சட்டவிரோத வெளியேற்றத் தடை" },
        desc: {
          English: "Landlords cannot forcibly evict you or cut off utilities (water, electricity) without a formal civil court eviction order.",
          Tamil: "சிவில் நீதிமன்ற உத்தரவின்றி வீட்டு உரிமையாளர் உங்களை வலுக்கட்டாயமாக வெளியேற்றவோ அல்லது குடிநீர், மின்சார இணைப்புகளைத் துண்டிக்கவோ முடியாது."
        }
      },
      {
        icon: FaMoneyBillWave,
        title: { English: "Security Deposit Refund", Tamil: "வைப்புத்தொகை திரும்பப் பெறுதல்" },
        desc: {
          English: "Security deposits must be refunded within 30 days of vacating the property. Deductions must be itemized with proof of damage.",
          Tamil: "வீட்டை காலி செய்த 30 நாட்களுக்குள் வைப்புத்தொகை திரும்ப வழங்கப்பட வேண்டும். சேதங்களுக்கு மட்டுமே பிடித்தம் செய்ய முடியும்."
        }
      },
      {
        icon: FaWrench,
        title: { English: "Essential Repairs", Tamil: "பழுதுபார்ப்புப் பொறுப்பு" },
        desc: {
          English: "The landlord is responsible for major structural repairs (leaks, plumbing, rewiring), while minor maintenance is managed by the tenant.",
          Tamil: "கட்டமைப்பு சார்ந்த பழுதுகளை சரிசெய்ய வேண்டியது வீட்டு உரிமையாளரின் கடமை. சிறிய அளவிலான பராமரிப்புகள் வாடகைதாரர் பொறுப்பு."
        }
      }
    ],
    cyber: [
      {
        icon: FaExclamationTriangle,
        title: { English: "24/7 Helpline & Portal", Tamil: "24/7 இணைய குற்ற உதவி எண்" },
        desc: {
          English: "Report financial cyber scams immediately to the national helpline 1930 or file complaints online at cybercrime.gov.in.",
          Tamil: "ஆன்லைன் நிதி மோசடிகளை 1930 என்ற உதவி எண்ணிற்கு உடனடியாகத் தெரிவிக்கலாம் அல்லது cybercrime.gov.in என்ற இணையதளத்தில் புகார் அளிக்கலாம்."
        }
      },
      {
        icon: FaCreditCard,
        title: { English: "Bank Liability Limits", Tamil: "வங்கி மோசடிப் பொறுப்பு" },
        desc: {
          English: "Report unauthorized bank transactions within 3 days. Under RBI rules, your liability becomes zero for bank/phishing lapses if reported promptly.",
          Tamil: "அங்கீகரிக்கப்படாத வங்கிப் பரிவர்த்தனைகளை 3 நாட்களுக்குள் தெரிவிக்கவும். உடனடியாகத் தெரிவித்தால் முழுத் தொகையையும் பெற முடியும்."
        }
      },
      {
        icon: FaCamera,
        title: { English: "Morphing & Morph Images Protection", Tamil: "போலி புகைப்பட மார்பிங் பாதுகாப்பு" },
        desc: {
          English: "Creating or sharing morphed images of women is a severe criminal offense under BNS Section 77 and IT Act Section 66E.",
          Tamil: "பெண்களின் புகைப்படங்களை மார்பிங் செய்வது BNS பிரிவு 77 மற்றும் IT சட்டம் 66E பிரிவுகளின் கீழ் கடுமையான குற்றமாகும்."
        }
      }
    ]
  };

  return (
    <div>
      <div className="section-header">
        <h2 className="section-title">
          {language === "Tamil" ? "சட்ட அடிப்படை உரிமைகள்" : "Know Your Rights"}
        </h2>
        <p className="section-subtitle">
          {language === "Tamil"
            ? "இந்திய குடிமக்களுக்கான அடிப்படை உரிமைகள், காவல், நுகர்வோர் மற்றும் வாடகைதாரர் சட்டங்கள் குறித்த விரிவான வழிகாட்டி."
            : "A structured guide outlining critical civil liberties, consumer protections, tenant privileges, and cyber safety regulations in India."}
        </p>
      </div>

      {/* Tabs */}
      <div className="rights-tab-container">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              className={`rights-tab ${activeTab === tab.id ? "active" : ""}`}
              onClick={() => setActiveTab(tab.id)}
              style={{ display: "inline-flex", alignItems: "center", gap: "8px" }}
            >
              <Icon style={{ flexShrink: 0 }} />
              <span>{tab.label[language]}</span>
            </button>
          );
        })}
      </div>

      {/* Accordion list */}
      <div className="rights-list">
        {rightsData[activeTab].map((right, idx) => {
          const CardIcon = right.icon;
          return (
            <div key={idx} className="rights-card-item">
              <h4 style={{ display: "inline-flex", alignItems: "center", gap: "8px" }}>
                <CardIcon style={{ color: "var(--accent-gold)", flexShrink: 0 }} />
                <span>{right.title[language]}</span>
              </h4>
              <p>{right.desc[language]}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default RightsExplorer;
