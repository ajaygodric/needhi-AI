import { useState, useMemo } from "react";
import { useNavigate } from "react-router-dom";
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
  FaCamera,
  FaSearch,
  FaLightbulb,
  FaComments,
  FaCheck,
  FaCopy,
  FaPhoneAlt
} from "react-icons/fa";

const RightsExplorer = ({ language }) => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState("police");
  const [searchTerm, setSearchTerm] = useState("");
  const [copiedId, setCopiedId] = useState(null);

  const categories = [
    { 
      id: "police", 
      label: { English: "Police & Arrest", Tamil: "காவல் & கைது" }, 
      mobileLabel: { English: "Police & Bail", Tamil: "காவல்" },
      icon: FaUserShield,
      helpline: "100 / 112",
      authority: { English: "BNSS 2024 & Constitution", Tamil: "BNSS 2024 & அரசியலமைப்பு" }
    },
    { 
      id: "consumer", 
      label: { English: "Consumer Rights", Tamil: "நுகர்வோர் உரிமை" }, 
      mobileLabel: { English: "Consumer", Tamil: "நுகர்வோர்" },
      icon: FaShoppingCart,
      helpline: "1915",
      authority: { English: "Consumer Protection Act 2019", Tamil: "நுகர்வோர் பாதுகாப்பு சட்டம் 2019" }
    },
    { 
      id: "tenant", 
      label: { English: "Tenant Rights", Tamil: "வாடகைதாரர் சட்டம்" }, 
      mobileLabel: { English: "Tenant Rights", Tamil: "வாடகைதாரர்" },
      icon: FaHome,
      helpline: "Rent Court / Civil",
      authority: { English: "Model Tenancy Act & State Rent Laws", Tamil: "மாதிரி வாடகை சட்டம் & மாநில விதிகள்" }
    },
    { 
      id: "cyber", 
      label: { English: "Cyber & Digital Safety", Tamil: "இணையப் பாதுகாப்பு" }, 
      mobileLabel: { English: "Cyber Safety", Tamil: "இணையம்" },
      icon: FaLaptop,
      helpline: "1930 (Cyber Helpline)",
      authority: { English: "IT Act 2000 & BNS 2024", Tamil: "IT சட்டம் 2000 & BNS 2024" }
    }
  ];

  const rightsData = {
    police: [
      {
        id: "p1",
        icon: FaFileSignature,
        section: "BNSS Sec. 173(1)",
        title: { English: "Mandatory FIR Registration", Tamil: "எஃப்.ஐ.ஆர் (FIR) கட்டாய பதிவு உரிமை" },
        desc: { 
          English: "Police officers are legally mandated to register an FIR upon receiving information disclosing a cognizable offense (e.g. theft, assault, fraud). Zero FIR can be filed at ANY police station regardless of jurisdiction.", 
          Tamil: "கைது செய்யக்கூடிய குற்றங்களுக்கு எஃப்.ஐ.ஆர் பதிவு செய்ய வேண்டியது காவல்துறையின் சட்டப்பூர்வ கடமை. எந்தவொரு காவல் நிலையத்திலும் 'ஜீரோ எஃப்.ஐ.ஆர்' (Zero FIR) பதிவு செய்யலாம்."
        },
        actionTip: {
          English: "If an officer refuses to register an FIR, you can send the substance of information in writing by post to the Superintendent of Police (SP) under BNSS Sec 173(3) or petition the Judicial Magistrate under Sec 175(3).",
          Tamil: "FIR பதிவு செய்ய மறுக்கப்பட்டால், மாவட்ட எஸ்.பி. (SP) அல்லது மாஜிஸ்திரேட்டிடம் எழுத்துப்பூர்வமாக புகார் அளிக்கலாம்."
        }
      },
      {
        id: "p2",
        icon: FaVolumeMute,
        section: "Constitution Art. 20(3)",
        title: { English: "Right to Silence & Protection from Self-Incrimination", Tamil: "மௌனமாக இருக்கும் & தற்காப்பு உரிமை" },
        desc: { 
          English: "No person accused of an offense can be compelled to be a witness against themselves. You cannot be forced to sign blank papers, confess, or provide self-incriminating oral statements under police coercion.", 
          Tamil: "கைது செய்யப்படும்போது மௌனமாக இருக்க உரிமை உண்டு. உங்களுக்கு எதிராக நீங்களே சாட்சியம் அளிக்கவோ, வெற்றுத் தாளில் கையொப்பமிடவோ கட்டாயப்படுத்த முடியாது."
        },
        actionTip: {
          English: "Any confession made to a police officer is inadmissible in court under Indian Evidence / Bharatiya Sakshya Adhiniyam Sec 23. Only statements before a Magistrate hold legal weight.",
          Tamil: "காவல்துறையிடம் அளிக்கும் வாக்குமூலம் நீதிமன்றத்தில் ஆதாரமாக ஏற்றுக்கொள்ளப்படாது."
        }
      },
      {
        id: "p3",
        icon: FaBalanceScale,
        section: "Constitution Art. 22(1) & BNSS Sec. 47",
        title: { English: "Right to Legal Representation & Free Legal Aid", Tamil: "வழக்கறிஞர் ஆலோசனை & இலவச சட்ட உதவி உரிமை" },
        desc: { 
          English: "Every arrested individual has an absolute constitutional right to consult and be defended by a legal practitioner of their choice from the moment of arrest and during police interrogation.", 
          Tamil: "கைது செய்யப்பட்ட உடனேயே தனது விருப்பப்படி வழக்கறிஞரை அணுகவும் ஆலோசிக்கவும் உரிமை உண்டு. கட்டணம் செலுத்த முடியாதவர்களுக்கு அரசு இலவச வழக்கறிஞரை வழங்க வேண்டும்."
        },
        actionTip: {
          English: "If you cannot afford an advocate, the Magistrate is legally bound to provide a free legal aid counsel through the District Legal Services Authority (DLSA). Dial 15100 for NALSA free aid.",
          Tamil: "வழக்கறிஞர் கட்டணம் செலுத்த முடியாவிட்டால் 15100 அல்லது DLSA மூலம் இலவச வழக்கறிஞர் பெறலாம்."
        }
      },
      {
        id: "p4",
        icon: FaMoon,
        section: "BNSS Sec. 43(5)",
        title: { English: "Night Arrest Protections for Women", Tamil: "பெண்களுக்கான இரவு நேர கைது பாதுகாப்பு" },
        desc: { 
          English: "No woman can be arrested after sunset and before sunrise except in extraordinary circumstances, and only with the prior written permission of a Judicial Magistrate of First Class and in the presence of a female police officer.", 
          Tamil: "சூரிய அஸ்தமனத்திற்குப் பிறகு மற்றும் சூரிய உதயத்திற்கு முன்பு பெண்களைக் கைது செய்யக்கூடாது. பெண் காவலர் உடன் இருப்பது கட்டாயம்."
        },
        actionTip: {
          English: "Women must be interrogated only at their residence in the presence of family members or in a recognized shelter home, not detained overnight in police stations.",
          Tamil: "பெண்களை அவர்களின் இல்லத்தில் வைத்தே குடும்பத்தினர் முன்னிலையில் விசாரிக்க வேண்டும்."
        }
      },
      {
        id: "p5",
        icon: FaClipboardList,
        section: "BNSS Sec. 47 & 50",
        title: { English: "Right to Know Grounds of Arrest & Production in 24 Hours", Tamil: "கைது காரணம் அறிதல் & 24 மணி நேர ஆஜர்" },
        desc: { 
          English: "Police must immediately communicate the exact grounds of arrest and whether the offense is bailable. The arrestee must be produced before the nearest Magistrate within 24 hours excluding travel time.", 
          Tamil: "கைதுக்கான காரணத்தையும், அது ஜாமீனில் வரக்கூடியதா என்பதையும் உடனடியாகத் தெரிவிக்க வேண்டும். 24 மணி நேரத்திற்குள் மாஜிஸ்திரேட் முன் ஆஜர்படுத்த வேண்டும்."
        },
        actionTip: {
          English: "Police must immediately prepare an Arrest Memo signed by a witness (family/neighbor) and inform one designated friend or family member of the arrest.",
          Tamil: "கைது செய்த விவரத்தை குடும்பத்தினருக்கு உடனடியாகத் தெரிவிக்க வேண்டும் மற்றும் கைது குறிப்பாணை (Arrest Memo) அளிக்க வேண்டும்."
        }
      }
    ],
    consumer: [
      {
        id: "c1",
        icon: FaShieldAlt,
        section: "CPA 2019 Sec. 2(9)(i)",
        title: { English: "Right to Safety Against Hazardous Goods & Services", Tamil: "பாதுகாப்பற்ற பொருட்களுக்கு எதிரான பாதுகாப்பு" },
        desc: { 
          English: "Consumers are protected against products, manufacturing defects, adulterated food, and deficient services that pose risks to health, life, or property.", 
          Tamil: "ஆரோக்கியம், உயிர் அல்லது உடமைகளுக்கு ஆபத்து விளைவிக்கும் தரமற்ற பொருட்கள் மற்றும் சேவைகளுக்கு எதிராக பாதுகாப்பு பெறும் உரிமை."
        },
        actionTip: {
          English: "Manufacturers and service providers are subject to strict product liability claims for injuries or losses caused by defective products.",
          Tamil: "குறைபாடுள்ள பொருட்களால் பாதிப்பு ஏற்பட்டால் உற்பத்தியாளர் மீது நஷ்டஈடு கோரி வழக்கு தொடரலாம்."
        }
      },
      {
        id: "c2",
        icon: FaBullhorn,
        section: "CPA 2019 Sec. 2(9)(ii)",
        title: { English: "Right to Complete Information & Fair Pricing", Tamil: "முழு தகவல் & நியாயமான விலை பெறும் உரிமை" },
        desc: { 
          English: "Right to be informed about the purity, standard, date of expiry, ingredients, MRP, and safety warnings before purchase. No seller can charge above the Maximum Retail Price (MRP).", 
          Tamil: "பொருளின் தரம், அளவு, காலாவதி தேதி, MRP விலை போன்ற அனைத்து விவரங்களையும் வாங்குவதற்கு முன் தெரிந்து கொள்ளும் உரிமை. MRP-க்கு மேல் விற்கக்கூடாது."
        },
        actionTip: {
          English: "Charging over MRP or not providing a valid GST receipt is a punishable unfair trade practice. Complain via the National Consumer Helpline app or portal.",
          Tamil: "MRP-ஐ விட கூடுதல் விலை வசூலிப்பது தண்டனைக்குரிய குற்றம். தேசிய நுகர்வோர் போர்ட்டலில் புகார் செய்யலாம்."
        }
      },
      {
        id: "c3",
        icon: FaRedo,
        section: "CPA 2019 Sec. 39",
        title: { English: "Right to Refund, Repair & Replacement", Tamil: "பணத்தைத் திரும்பப் பெறுதல் & மாற்றித் தரும் உரிமை" },
        desc: { 
          English: "If a purchased product is defective, non-functional, or service is deficient, the consumer is entitled to have defects repaired, replaced with a new item, or receive a 100% refund.", 
          Tamil: "பொருளில் குறைபாடு இருந்தால், பழுதுபார்க்க, புதிய பொருள் பெற அல்லது பணத்தைத் திரும்பப் பெற நுகர்வோருக்கு முழு உரிமை உண்டு."
        },
        actionTip: {
          English: "Clauses like 'Goods once sold will not be taken back' are legally invalid and void under the Consumer Protection Act.",
          Tamil: "'விற்ற பொருட்கள் திரும்பப் பெறப்படமாட்டாது' என்ற வாசகம் நுகர்வோர் சட்டப்படி செல்லாது."
        }
      },
      {
        id: "c4",
        icon: FaUniversity,
        section: "CPA 2019 Sec. 34-58",
        title: { English: "Right to Redressal in Consumer Commissions (e-Daakhil)", Tamil: "நுகர்வோர் நீதிமன்றத்தில் நீதி பெறும் உரிமை" },
        desc: { 
          English: "Three-tier judicial redressal system: District Commission (claims up to ₹50 Lakhs), State Commission (up to ₹2 Crores), and National Commission (above ₹2 Crores).", 
          Tamil: "மாவட்ட நுகர்வோர் ஆணையம் (₹50 லட்சம் வரை), மாநில ஆணையம் (₹2 கோடி வரை), தேசிய ஆணையம் (₹2 கோடிக்கு மேல்) மூலம் நஷ்டஈடு பெறலாம்."
        },
        actionTip: {
          English: "You can file consumer cases online from home using the official e-Daakhil portal (edaakhil.nic.in) without hiring a lawyer.",
          Tamil: "வழக்கறிஞர் இன்றியே edaakhil.nic.in இணையதளம் மூலம் வீட்டிலிருந்தே நேரடியாக புகார் தாக்கல் செய்யலாம்."
        }
      }
    ],
    tenant: [
      {
        id: "t1",
        icon: FaFileAlt,
        section: "Model Tenancy Act 2021",
        title: { English: "Right to a Written Agreement & Rent Receipt", Tamil: "எழுத்துப்பூர்வ வாடகை ஒப்பந்தம் & ரசீது உரிமை" },
        desc: { 
          English: "Every tenancy must be backed by a written, signed agreement specifying rent, tenure, and maintenance terms. Tenants have the right to receive an official rent receipt upon payment.", 
          Tamil: "வாடகை காலம், தொகை மற்றும் விதிமுறைகள் அடங்கிய எழுத்துப்பூர்வ ஒப்பந்தம் பெற உரிமை உண்டு. வாடகை செலுத்தியவுடன் ரசீது பெறுவதும் சட்டப்பூர்வ உரிமை."
        },
        actionTip: {
          English: "Rent agreements exceeding 11 months must be registered under the Registration Act to be admissible in legal disputes.",
          Tamil: "11 மாதங்களுக்கு மேற்பட்ட வாடகை ஒப்பந்தங்களை சார்பதிவாளர் அலுவலகத்தில் பதிவு செய்வது கட்டாயம்."
        }
      },
      {
        id: "t2",
        icon: FaKey,
        section: "Transfer of Property Act Sec. 108",
        title: { English: "Protection Against Illegal & Forcible Eviction", Tamil: "சட்டவிரோத வெளியேற்றத்திற்கு எதிரான பாதுகாப்பு" },
        desc: { 
          English: "Landlords cannot arbitrarily evict tenants, lock premises, disconnect water, power, or utility connections without a formal decree from a competent Rent Court.", 
          Tamil: "நீதிமன்ற உத்தரவின்றி வீட்டு உரிமையாளர் வாடகைதாரரை வலுக்கட்டாயமாக வெளியேற்றவோ அல்லது குடிநீர், மின்சாரத்தைத் துண்டிக்கவோ முடியாது."
        },
        actionTip: {
          English: "If utilities are cut off unlawfully, you can file an urgent restoration petition before the Rent Authority or local civil magistrate.",
          Tamil: "மின்சாரம்/குடிநீர் துண்டிக்கப்பட்டால் காவல் நிலையம் மற்றும் வாடகை நீதிமன்றத்தில் உடனடி மனு தாக்கல் செய்யலாம்."
        }
      },
      {
        id: "t3",
        icon: FaMoneyBillWave,
        section: "Model Tenancy Act Sec. 11",
        title: { English: "Security Deposit Cap & Mandatory 30-Day Refund", Tamil: "வைப்புத்தொகை உச்சவரம்பு & 30 நாள் திரும்பப் பெறுதல்" },
        desc: { 
          English: "Security deposits for residential properties are capped at a maximum of 2 months' rent under the Model Tenancy Act. Deposits must be refunded within 30 days of vacating after reasonable deductions.", 
          Tamil: "வீடு காலி செய்த 30 நாட்களுக்குள் வைப்புத்தொகை திரும்பத் தரப்பட வேண்டும். சேதங்களுக்கான முறையான ரசீது இன்றி தொகையைப் பிடித்தம் செய்ய முடியாது."
        },
        actionTip: {
          English: "Always conduct a joint move-out inspection and record photo/video evidence of property condition when handing over keys.",
          Tamil: "வீட்டை காலி செய்யும்போது புகைப்பட ஆதாரங்களை எடுத்து வைப்பது தேவையற்ற பிடித்தங்களைத் தடுக்கும்."
        }
      },
      {
        id: "t4",
        icon: FaWrench,
        section: "Model Tenancy Act Sec. 15",
        title: { English: "Right to Habitable Premises & Structural Maintenance", Tamil: "பராமரிப்பு & கட்டமைப்பு பழுதுநீக்கும் உரிமை" },
        desc: { 
          English: "Landlords are legally responsible for structural repairs, whitewashing, plumbing leaks, and wiring. If the landlord fails to repair within reasonable notice, the tenant can deduct repair costs from rent.", 
          Tamil: "கட்டமைப்பு சேதங்கள், கசிவுகள் மற்றும் வயரிங் பழுதுகளை சரிசெய்ய வேண்டியது உரிமையாளர் கடமை. செய்யத் தவறினால் வாடகையிலிருந்து கழித்துக் கொள்ளலாம்."
        },
        actionTip: {
          English: "Landlords must give at least 24 hours prior written notice before entering the rental property for inspection.",
          Tamil: "வீட்டை ஆய்வு செய்ய வரும்போது உரிமையாளர் 24 மணி நேரத்திற்கு முன்பே தெரிவிக்க வேண்டும்."
        }
      }
    ],
    cyber: [
      {
        id: "cy1",
        icon: FaExclamationTriangle,
        section: "IT Act Sec. 66D & Helpline 1930",
        title: { English: "Right to Immediate Freeze on Financial Cyber Fraud", Tamil: "ஆன்லைன் வங்கி மோசடி கணக்கு முடக்கும் உரிமை" },
        desc: { 
          English: "Victims of financial cyber fraud, OTP phishing, or UPI scams have the right to get the stolen money frozen immediately across intermediary bank accounts by calling national helpline 1930 within the 'Golden Hour'.", 
          Tamil: "ஆன்லைன் பண மோசடி நடந்த 1-2 மணி நேரத்திற்குள் 1930 எண்ணிற்கு அழைத்தால், குற்றவாளியின் வங்கிக் கணக்கை உடனடியாக முடக்கி பணத்தை மீட்க முடியும்."
        },
        actionTip: {
          English: "Dial 1930 or submit details on cybercrime.gov.in immediately. You will receive an acknowledgment SMS and Citizen Financial Cyber Fraud Reporting System (CFCFRMS) ticket.",
          Tamil: "1930 என்ற எண்ணிற்கு அழைத்து அல்லது cybercrime.gov.in தளத்தில் புகார் பதிவு செய்யலாம்."
        }
      },
      {
        id: "cy2",
        icon: FaCreditCard,
        section: "RBI Circular DBR.No.Leg.BC.78/2017",
        title: { English: "Zero Customer Liability for Unauthorized Bank Debits", Tamil: "வங்கி மோசடியில் வாடிக்கையாளருக்கு பூஜ்ஜிய பொறுப்பு" },
        desc: { 
          English: "Under Reserve Bank of India (RBI) mandates, if you notify your bank of an unauthorized electronic transaction within 3 working days, your financial liability is exactly ZERO.", 
          Tamil: "அங்கீகரிக்கப்படாத வங்கிப் பரிவர்த்தனையை 3 நாட்களுக்குள் வங்கிக்குத் தெரிவித்தால், இழப்பிற்கு நீங்கள் பொறுப்பல்ல — வங்கி முழுத் தொகையையும் திருப்பித் தர வேண்டும்."
        },
        actionTip: {
          English: "Notify your bank via official customer care email/phone and block debit cards immediately. The bank must reverse the amount within 10 working days.",
          Tamil: "உடனடியாக கார்டை பிளாக் செய்து வங்கிக்கு மின்னஞ்சல் அனுப்பவும். 10 நாட்களுக்குள் வங்கி பணத்தை வரவு வைக்க வேண்டும்."
        }
      },
      {
        id: "cy3",
        icon: FaCamera,
        section: "BNS Sec. 77 & IT Act Sec. 66E / 67A",
        title: { English: "Strict Protection Against Image Morphing & Voyeurism", Tamil: "போலி புகைப்பட மார்பிங் & அந்தரங்க பாதுகாப்பு" },
        desc: { 
          English: "Capturing, publishing, transmitting, or creating AI/deepfake morphed images or videos of a person without consent is a non-bailable criminal offense punishable by up to 5 years imprisonment.", 
          Tamil: "அனுமதியின்றி பெண்களின் புகைப்படங்களை மார்பிங் செய்வது, பகிர்வது அல்லது அச்சுறுத்துவது 5 ஆண்டுகள் வரை சிறைத்தண்டனைக்குரிய கடுமையான குற்றமாகும்."
        },
        actionTip: {
          English: "You can report non-consensual intimate imagery directly to the National Commission for Women (NCW) or file a takedown request under IT Rules 2021.",
          Tamil: "சமூக வலைதளங்களில் இருந்து 24 மணி நேரத்திற்குள் ஆபாச உள்ளடக்கங்களை நீக்க கோரிக்கை வைக்கலாம்."
        }
      },
      {
        id: "cy4",
        icon: FaShieldAlt,
        section: "DPDP Act 2023 & IT Act Sec. 43A",
        title: { English: "Right to Digital Privacy & Personal Data Erasure", Tamil: "தனிநபர் தகவல் பாதுகாப்பு & நீக்கும் உரிமை" },
        desc: { 
          English: "Under the Digital Personal Data Protection (DPDP) Act, citizens have the right to know how their data is processed, withdraw consent, and demand complete erasure of personal records from online platforms.", 
          Tamil: "நிறுவனங்களிடம் உள்ள உங்கள் தனிநபர் தகவல்களைத் திருத்தவும், பயன்பாட்டை நிறுத்தவும், முழுமையாக நீக்கவும் சட்டப்படி கோர உரிமை உண்டு."
        },
        actionTip: {
          English: "Companies failing to protect consumer data against data breaches face penalties of up to ₹250 Crores under the DPDP Act.",
          Tamil: "தனிநபர் தகவல்களை பாதுகாப்பதில் அலட்சியம் காட்டும் நிறுவனங்கள் மீது கடுமையான அபராதம் விதிக்கப்படும்."
        }
      }
    ]
  };

  // Filter rights based on active tab and search query
  const filteredRights = useMemo(() => {
    const list = rightsData[activeTab] || [];
    if (!searchTerm.trim()) return list;
    const query = searchTerm.toLowerCase();
    return list.filter(r => 
      r.title.English.toLowerCase().includes(query) ||
      r.title.Tamil.toLowerCase().includes(query) ||
      r.desc.English.toLowerCase().includes(query) ||
      r.desc.Tamil.toLowerCase().includes(query) ||
      r.section.toLowerCase().includes(query)
    );
  }, [activeTab, searchTerm]);

  const activeCategory = categories.find(c => c.id === activeTab) || categories[0];
  const CategoryIcon = activeCategory.icon;

  const handleCopyRight = (right) => {
    const text = `⚖️ ${right.title[language]} (${right.section})\n\n📖 ${right.desc[language]}\n\n💡 Practical Step: ${right.actionTip[language]}\n\n— Verified via Needhi AI`;
    navigator.clipboard.writeText(text);
    setCopiedId(right.id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleAskAiAboutRight = (right) => {
    const query = `Explain my legal rights regarding "${right.title.English}" under ${right.section}. How can I enforce this legally in India?`;
    navigate("/", { state: { initialPrompt: query } });
  };

  return (
    <div className="rights-explorer-page">
      {/* Header Banner */}
      <div className="rights-hero-banner">
        <div className="rights-hero-badge">
          <FaBalanceScale />
          <span>{language === "Tamil" ? "இந்திய சட்ட & அரசியலமைப்பு உரிமைகள்" : "Constitutional & Statutory Legal Rights"}</span>
        </div>
        <h2 className="rights-hero-title">
          {language === "Tamil" ? "அடிப்படை சட்ட உரிமைகள் களஞ்சியம்" : "Know Your Legal Rights"}
        </h2>
        <p className="rights-hero-subtitle">
          {language === "Tamil"
            ? "இந்திய குடிமக்களுக்கான அடிப்படை சிவில் உரிமைகள், காவல் துறை வழிகாட்டுதல்கள், நுகர்வோர் மற்றும் வாடகைதாரர் பாதுகாப்பு சட்டங்களின் முழுமையான கையேடு."
            : "A structured legal library outlining essential civil liberties, police safeguards, consumer protections, tenant privileges, and cyber safety regulations."}
        </p>

        {/* Search Bar */}
        <div className="rights-search-container">
          <FaSearch className="rights-search-icon" />
          <input
            type="text"
            className="rights-search-input"
            placeholder={
              language === "Tamil"
                ? "உரிமைகள், சட்டப்பிரிவு அல்லது சொற்களைத் தேடுங்கள் (எ.கா. FIR, ஜாமீன், MRP, வைப்புத்தொகை)..."
                : "Search rights, legal sections, or keywords (e.g., FIR, Bail, Refund, Security Deposit, 1930)..."
            }
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          {searchTerm && (
            <button className="rights-search-clear" onClick={() => setSearchTerm("")}>
              ✕
            </button>
          )}
        </div>
      </div>

      {/* Category Tabs */}
      <div className="rights-category-grid">
        {categories.map((cat) => {
          const Icon = cat.icon;
          const isActive = activeTab === cat.id;
          const count = rightsData[cat.id]?.length || 0;
          return (
            <button
              key={cat.id}
              className={`rights-cat-card ${isActive ? "active" : ""}`}
              onClick={() => {
                setActiveTab(cat.id);
                setSearchTerm("");
              }}
            >
              <div className="rights-cat-icon-wrapper">
                <Icon className="rights-cat-icon" />
              </div>
              <div className="rights-cat-info">
                <span className="rights-cat-title-full">{cat.label[language]}</span>
                <span className="rights-cat-title-mobile">{cat.mobileLabel[language]}</span>
                <span className="rights-cat-count">{count} {language === "Tamil" ? "உரிமைகள்" : "Rights"}</span>
              </div>
            </button>
          );
        })}
      </div>

      {/* Active Category Info Banner */}
      <div className="rights-active-header">
        <div className="rights-active-title-group">
          <div className="rights-active-icon-badge">
            <CategoryIcon />
          </div>
          <div>
            <h3 className="rights-active-name">{activeCategory.label[language]}</h3>
            <span className="rights-active-law-badge">{activeCategory.authority[language]}</span>
          </div>
        </div>
        <div className="rights-active-helpline-pill">
          <FaPhoneAlt className="helpline-pulse-icon" />
          <span>{language === "Tamil" ? "உதவி எண்:" : "Helpline:"} <b>{activeCategory.helpline}</b></span>
        </div>
      </div>

      {/* Rights Grid */}
      {filteredRights.length === 0 ? (
        <div className="card rights-empty-card">
          <FaBalanceScale style={{ fontSize: "2.5rem", color: "var(--accent-gold)", marginBottom: "12px" }} />
          <h4>{language === "Tamil" ? "உரிமைகள் எதுவும் பொருந்தவில்லை" : "No Matching Legal Rights Found"}</h4>
          <p style={{ color: "var(--text-secondary)", fontSize: "0.9rem" }}>
            {language === "Tamil"
              ? "உங்கள் தேடல் சொல்லிற்கு ஏற்ற உரிமைகள் இல்லை. வேறு சொற்களைப் பயன்படுத்திப் பார்க்கவும்."
              : "Try adjusting your search terms or browse across the category tabs above."}
          </p>
        </div>
      ) : (
        <div className="rights-cards-grid">
          {filteredRights.map((right) => {
            const CardIcon = right.icon;
            const isCopied = copiedId === right.id;

            return (
              <div key={right.id} className="rights-premium-card">
                {/* Card Top Section */}
                <div className="rights-card-header">
                  <div className="rights-card-icon-box">
                    <CardIcon />
                  </div>
                  <div className="rights-card-title-box">
                    <span className="rights-section-tag">{right.section}</span>
                    <h4 className="rights-card-title">{right.title[language]}</h4>
                  </div>
                </div>

                {/* Card Description */}
                <p className="rights-card-desc">{right.desc[language]}</p>

                {/* Practical Action Box */}
                {right.actionTip && (
                  <div className="rights-action-box">
                    <div className="rights-action-title">
                      <FaLightbulb style={{ color: "var(--accent-gold-light)" }} />
                      <span>{language === "Tamil" ? "நடைமுறை வழிகாட்டல்:" : "Practical Legal Step:"}</span>
                    </div>
                    <p className="rights-action-text">{right.actionTip[language]}</p>
                  </div>
                )}

                {/* Card Footer Actions */}
                <div className="rights-card-footer">
                  <button 
                    className="rights-action-btn copy-btn"
                    onClick={() => handleCopyRight(right)}
                    title={language === "Tamil" ? "விவரங்களை நகலெடு" : "Copy Legal Right Summary"}
                  >
                    {isCopied ? <FaCheck style={{ color: "var(--success)" }} /> : <FaCopy />}
                    <span>{isCopied ? (language === "Tamil" ? "நகலெடுக்கப்பட்டது!" : "Copied!") : (language === "Tamil" ? "நகலெடு" : "Copy")}</span>
                  </button>

                  <button 
                    className="rights-action-btn ask-ai-btn"
                    onClick={() => handleAskAiAboutRight(right)}
                    title={language === "Tamil" ? "நீதி AI-யிடம் கேளுங்கள்" : "Ask Needhi AI about this right"}
                  >
                    <FaComments />
                    <span>{language === "Tamil" ? "AI-யிடம் கேளுங்கள்" : "Ask Needhi AI"}</span>
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default RightsExplorer;
