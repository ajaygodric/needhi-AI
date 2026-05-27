import os
import io
import json
import base64
import streamlit as st
import google.generativeai as genai
from streamlit_option_menu import option_menu
from PIL import Image
import PyPDF2
try:
    import speech_recognition as sr
    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False

try:
    GOOGLE_API_KEY = st.secrets["GEMINI_API_KEY"]
except (KeyError, FileNotFoundError):
    GOOGLE_API_KEY = os.environ.get("GEMINI_API_KEY", "")
CHAT_HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chat_history.json")

def load_chat_history():
    if os.path.exists(CHAT_HISTORY_FILE):
        try:
            with open(CHAT_HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_chat_history(history):
    try:
        with open(CHAT_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

MODEL_FALLBACK_ORDER = [
    "models/gemini-2.0-flash",
    "models/gemini-2.0-flash-lite",
    "models/gemini-2.5-flash-lite",
    "models/gemini-2.5-flash",
]

def get_working_model():
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        all_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        preferred = ["models/gemini-2.0-flash", "models/gemini-2.0-flash-lite", "models/gemini-2.5-flash-lite", "models/gemini-2.5-flash"]
        for p in preferred:
            if p in all_models:
                return p
        flash_models = [m for m in all_models if "flash" in m.lower() and "preview" not in m and "tts" not in m]
        if flash_models:
            return flash_models[0]
        return all_models[0] if all_models else "models/gemini-2.0-flash"
    except:
        return "models/gemini-2.0-flash"

active_model_name = get_working_model()

try:
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel(active_model_name)
except:
    st.error("⚠️ Error initializing model.")

def generate_with_fallback(prompt_or_parts, generation_config=None, safety_settings=None, stream=False):
    import time, re
    models_to_try = [active_model_name] + [m for m in MODEL_FALLBACK_ORDER if m != active_model_name]
    last_err = None
    for model_name in models_to_try:
        try:
            m = genai.GenerativeModel(model_name)
            kwargs = {}
            if generation_config:
                kwargs["generation_config"] = generation_config
            if safety_settings:
                kwargs["safety_settings"] = safety_settings
            if stream:
                kwargs["stream"] = True
            response = m.generate_content(prompt_or_parts, **kwargs)
            return response, model_name
        except Exception as e:
            last_err = e
            err_str = str(e)
            if "429" in err_str:
                # Try to extract retry delay
                delay_match = re.search(r'retry_delay\s*\{\s*seconds:\s*(\d+)', err_str)
                wait = int(delay_match.group(1)) + 2 if delay_match else 5
                # Try same model after wait first, then move to next
                if model_name == models_to_try[0]:
                    time.sleep(min(wait, 20))
                    try:
                        response = m.generate_content(prompt_or_parts, **kwargs)
                        return response, model_name
                    except Exception:
                        pass
                continue
            raise e
    raise last_err

st.set_page_config(page_title="Needhi AI", page_icon="⚖️", layout="wide")

# --- Session State Init ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = load_chat_history()
if "voice_text" not in st.session_state:
    st.session_state.voice_text = ""

# --- Inject faded logo as background watermark ---
_logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "needhi.png")
_logo_b64 = ""
if os.path.exists(_logo_path):
    with open(_logo_path, "rb") as _f:
        _logo_b64 = base64.b64encode(_f.read()).decode()

st.markdown(f"""
<style>
    .stApp {{
        background-color: #0d1117 !important;
    }}
    .stApp::after {{
        content: '';
        position: fixed;
        top: 0; left: 0; right: 0; bottom: 0;
        background-image: url('data:image/png;base64,{_logo_b64}');
        background-repeat: no-repeat;
        background-position: center 45%;
        background-size: 32% auto;
        background-attachment: fixed;
        opacity: 0.06;
        z-index: 0;
        pointer-events: none;
    }}
    [data-testid="stHeader"] {{ background: #0d1117 !important; }}
    section[data-testid="stSidebar"] {{ background: linear-gradient(180deg, #1a1a2e 0%, #16213e 60%, #0f3460 100%) !important; }}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=Inter:wght@300;400;500;600&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    .stApp { color: #e8dcc8; }

    #MainMenu, footer { visibility: hidden; }
    [data-testid="stToolbar"] { display: none; }
    [data-testid="stSidebarCollapsedControl"] { display: none; }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 60%, #0f3460 100%) !important;
        border-right: 1px solid #c9a84c44;
    }
    [data-testid="stSidebar"] * { color: #e8dcc8 !important; }
    [data-testid="stSidebar"] .stRadio label {
        background: rgba(201,168,76,0.08) !important;
        border: 1px solid rgba(201,168,76,0.2) !important;
        border-radius: 8px !important;
        padding: 10px 16px !important;
        margin-bottom: 4px !important;
        transition: all 0.2s !important;
        font-size: 0.9rem !important;
    }
    [data-testid="stSidebar"] .stRadio label:hover {
        background: rgba(201,168,76,0.18) !important;
        border-color: #c9a84c !important;
    }
    .sidebar-brand { text-align: center; padding: 10px 0 20px 0; }
    .sidebar-brand h1 {
        font-family: 'Playfair Display', serif;
        color: #c9a84c !important;
        font-size: 1.6rem;
        margin: 8px 0 2px 0;
        letter-spacing: 3px;
    }
    .sidebar-brand p {
        color: #8a9bb0 !important;
        font-size: 0.75rem;
        letter-spacing: 1px;
        text-transform: uppercase;
        margin: 0;
    }
    .sidebar-label {
        color: #8a9bb0 !important;
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-bottom: 8px;
        display: block;
    }
    .model-badge {
        background: rgba(201,168,76,0.1);
        border: 1px solid rgba(201,168,76,0.3);
        border-radius: 6px;
        padding: 8px 12px;
        font-size: 0.78rem;
        color: #c9a84c !important;
        text-align: center;
        margin-top: 8px;
    }

    /* Hero */
    .hero {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        border-radius: 20px;
        padding: 60px 40px;
        text-align: center;
        margin-bottom: 32px;
        position: relative;
        overflow: hidden;
        box-shadow: 0 20px 60px rgba(0,0,0,0.15);
    }
    .hero::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 4px;
        background: linear-gradient(90deg, transparent, #c9a84c, #f0d080, #c9a84c, transparent);
    }
    .hero-tag {
        display: inline-block;
        background: rgba(201,168,76,0.15);
        border: 1px solid rgba(201,168,76,0.4);
        color: #c9a84c;
        padding: 5px 18px;
        border-radius: 30px;
        font-size: 0.75rem;
        letter-spacing: 2px;
        text-transform: uppercase;
        margin-bottom: 20px;
    }
    .hero-title {
        font-family: 'Playfair Display', serif;
        font-size: 3.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #c9a84c, #f0d080, #e8c96a);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0 0 12px 0;
        letter-spacing: 4px;
    }
    .hero-subtitle {
        color: #8a9bb0;
        font-size: 1.05rem;
        font-weight: 300;
        letter-spacing: 0.5px;
        margin: 0;
    }
    .stats-bar {
        display: flex;
        justify-content: center;
        gap: 40px;
        margin-top: 30px;
        padding-top: 24px;
        border-top: 1px solid rgba(201,168,76,0.15);
    }
    .stat-item { text-align: center; }
    .stat-num {
        font-family: 'Playfair Display', serif;
        font-size: 1.4rem;
        color: #c9a84c;
        font-weight: 700;
        display: block;
    }
    .stat-label { color: #6a7f94; font-size: 0.75rem; letter-spacing: 1px; text-transform: uppercase; }

    /* Search Box */
    .search-box {
        background: rgba(255,255,255,0.04);
        border-radius: 16px;
        padding: 32px 36px;
        margin-bottom: 24px;
        box-shadow: 0 4px 24px rgba(0,0,0,0.3);
        border: 1px solid rgba(201,168,76,0.2);
        backdrop-filter: blur(10px);
    }
    .stTextInput > div > div > input {
        background: rgba(255,255,255,0.06) !important;
        border: 1.5px solid rgba(201,168,76,0.3) !important;
        border-radius: 10px !important;
        color: #e8dcc8 !important;
        padding: 14px 18px !important;
        font-size: 1rem !important;
        transition: all 0.2s !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: #c9a84c !important;
        box-shadow: 0 0 0 3px rgba(201,168,76,0.15) !important;
        background: rgba(255,255,255,0.09) !important;
    }
    .stTextInput > div > div > input::placeholder { color: #4a6080 !important; }
    .stTextInput label { color: #8a9bb0 !important; font-weight: 500 !important; font-size: 0.9rem !important; }

    /* Button */
    .stButton > button {
        background: linear-gradient(135deg, #1a1a2e, #16213e) !important;
        color: #c9a84c !important;
        border: 1.5px solid #c9a84c !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        padding: 14px 24px !important;
        transition: all 0.3s ease !important;
        letter-spacing: 1px !important;
        text-transform: uppercase !important;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #c9a84c, #a8873a) !important;
        color: #1a1a2e !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 24px rgba(201,168,76,0.3) !important;
    }

    /* Result Card */
    .result-card {
        background: rgba(255,255,255,0.04);
        border-radius: 16px;
        padding: 32px 36px;
        margin-top: 24px;
        box-shadow: 0 4px 24px rgba(0,0,0,0.3);
        border: 1px solid rgba(201,168,76,0.2);
        border-top: 4px solid #c9a84c;
        backdrop-filter: blur(10px);
    }
    .result-header {
        font-family: 'Playfair Display', serif;
        color: #e8dcc8;
        font-size: 1.1rem;
        font-weight: 700;
        margin-bottom: 20px;
        padding-bottom: 14px;
        border-bottom: 1px solid rgba(201,168,76,0.15);
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .result-header span { color: #c9a84c; }

    /* Rights Cards */
    .rights-card {
        background: rgba(255,255,255,0.04);
        border-radius: 14px;
        padding: 24px 28px;
        margin-bottom: 16px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.2);
        border: 1px solid rgba(201,168,76,0.15);
        border-left: 4px solid #c9a84c;
        transition: all 0.25s ease;
        backdrop-filter: blur(8px);
    }
    .rights-card:hover {
        transform: translateX(4px);
        box-shadow: 0 6px 24px rgba(0,0,0,0.3);
        border-left-color: #f0d080;
        background: rgba(255,255,255,0.07);
    }
    .rights-card h4 {
        color: #e8dcc8;
        font-family: 'Playfair Display', serif;
        margin-bottom: 10px;
        font-size: 1.05rem;
        font-weight: 600;
    }
    .rights-card p { color: #8a9bb0; font-size: 0.93rem; line-height: 1.75; margin: 0; }

    /* Info Cards */
    .info-card {
        background: rgba(255,255,255,0.04);
        border-radius: 16px;
        padding: 32px 24px;
        text-align: center;
        margin-bottom: 20px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.25);
        border: 1px solid rgba(201,168,76,0.15);
        transition: all 0.3s ease;
        backdrop-filter: blur(8px);
    }
    .info-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 36px rgba(0,0,0,0.4);
        background: rgba(255,255,255,0.07);
        border-color: rgba(201,168,76,0.35);
    }
    .info-card .icon {
        width: 60px; height: 60px;
        background: linear-gradient(135deg, #c9a84c22, #c9a84c44);
        border: 1px solid #c9a84c55;
        border-radius: 14px;
        display: flex; align-items: center; justify-content: center;
        font-size: 1.6rem;
        margin: 0 auto 16px auto;
    }
    .info-card h3 { color: #e8dcc8; font-family: 'Playfair Display', serif; margin-bottom: 8px; font-size: 1.1rem; }
    .info-card p { color: #8a9bb0; font-size: 0.9rem; margin: 0; line-height: 1.6; }

    /* Chat UI */
    .chat-container {
        display: flex;
        flex-direction: column;
        gap: 20px;
        padding: 8px 0 16px 0;
    }
    .chat-row-user {
        display: flex;
        justify-content: flex-end;
        align-items: flex-end;
        gap: 10px;
    }
    .chat-row-ai {
        display: flex;
        justify-content: flex-start;
        align-items: flex-end;
        gap: 10px;
    }
    .chat-avatar {
        width: 36px; height: 36px;
        border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-size: 1rem;
        flex-shrink: 0;
    }
    .chat-avatar-user {
        background: linear-gradient(135deg, #c9a84c, #a8873a);
        color: #1a1a2e;
        font-weight: 700;
    }
    .chat-avatar-ai {
        background: linear-gradient(135deg, #1a1a2e, #0f3460);
        border: 1px solid rgba(201,168,76,0.4);
        color: #c9a84c;
    }
    .chat-bubble-wrap { display: flex; flex-direction: column; max-width: 75%; }
    .chat-bubble-wrap-user { align-items: flex-end; }
    .chat-bubble-wrap-ai { align-items: flex-start; }
    .chat-name {
        font-size: 0.7rem;
        letter-spacing: 1px;
        text-transform: uppercase;
        margin-bottom: 5px;
        font-weight: 600;
    }
    .chat-name-user { color: #c9a84c; }
    .chat-name-ai { color: #6a9bb0; }
    .chat-bubble-user {
        background: linear-gradient(135deg, rgba(201,168,76,0.18), rgba(201,168,76,0.08));
        border: 1px solid rgba(201,168,76,0.35);
        border-radius: 18px 18px 4px 18px;
        padding: 12px 18px;
        color: #f0e6cc;
        font-size: 0.93rem;
        line-height: 1.6;
        box-shadow: 0 2px 12px rgba(201,168,76,0.1);
    }
    .chat-bubble-ai {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(100,140,180,0.2);
        border-radius: 18px 18px 18px 4px;
        padding: 12px 18px;
        color: #c8d8e8;
        font-size: 0.93rem;
        line-height: 1.6;
        box-shadow: 0 2px 12px rgba(0,0,0,0.2);
    }
    .chat-divider {
        display: flex;
        align-items: center;
        gap: 12px;
        margin: 4px 0;
    }
    .chat-divider-line {
        flex: 1;
        height: 1px;
        background: rgba(201,168,76,0.1);
    }
    .chat-divider-text {
        font-size: 0.68rem;
        color: #3a4f64;
        letter-spacing: 1px;
        text-transform: uppercase;
        white-space: nowrap;
    }

    /* Section Title */
    .section-title {
        font-family: 'Playfair Display', serif;
        font-size: 2rem;
        color: #e8dcc8;
        margin-bottom: 6px;
        font-weight: 700;
    }
    .section-subtitle {
        color: #6a7f94;
        font-size: 0.9rem;
        margin-bottom: 28px;
    }

    hr { border-color: #e8e0d0 !important; margin: 20px 0 !important; }

    [data-testid="stDownloadButton"] button {
        background: transparent !important;
        color: #c9a84c !important;
        border: 1.5px solid #c9a84c !important;
        border-radius: 8px !important;
        font-size: 0.85rem !important;
        padding: 10px 20px !important;
    }
    [data-testid="stDownloadButton"] button:hover {
        background: #c9a84c !important;
        color: white !important;
    }

    /* Severity Badge */
    .severity-bar {
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
        margin-top: 20px;
        padding-top: 16px;
        border-top: 1px solid rgba(201,168,76,0.1);
    }
    .badge {
        padding: 6px 16px;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.5px;
        border: 1.5px solid;
    }
    .badge-red    { background: rgba(231,76,60,0.15);   border-color: #e74c3c; color: #e74c3c; }
    .badge-yellow { background: rgba(241,196,15,0.15);  border-color: #f1c40f; color: #f1c40f; }
    .badge-green  { background: rgba(46,204,113,0.15);  border-color: #2ecc71; color: #2ecc71; }
    .badge-blue   { background: rgba(52,152,219,0.15);  border-color: #3498db; color: #3498db; }
    .badge-gray   { background: rgba(149,165,166,0.15); border-color: #95a5a6; color: #95a5a6; }
</style>
""", unsafe_allow_html=True)

# --- TOP NAVBAR + LANGUAGE TOGGLE ---
nav_col, lang_col = st.columns([4, 1])
with nav_col:
    menu = option_menu(
        menu_title=None,
        options=["Home", "Know Your Rights", "About", "Contact Lawyer"],
        icons=["house-fill", "journal-text", "info-circle-fill", "telephone-fill"],
        default_index=0,
        orientation="horizontal",
        styles={
            "container": {"padding": "0", "background-color": "#1a1a2e", "border-bottom": "2px solid #c9a84c33"},
            "icon": {"color": "#c9a84c", "font-size": "14px"},
            "nav-link": {"font-family": "Inter, sans-serif", "color": "#8a9bb0", "font-size": "0.85rem", "font-weight": "500", "padding": "16px 20px", "border-radius": "0", "letter-spacing": "0.5px"},
            "nav-link-selected": {"background-color": "rgba(201,168,76,0.1)", "color": "#c9a84c", "border-bottom": "3px solid #c9a84c", "font-weight": "600"},
        }
    )
with lang_col:
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    language = st.radio("", ["English", "Tamil"], horizontal=True, label_visibility="collapsed")

# --- SIDEBAR (model info only) ---
with st.sidebar:
    logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "needhi.png")
    if os.path.exists(logo_path):
        st.image(logo_path, use_container_width=True)
    st.markdown("""
    <div class="sidebar-brand">
        <h1>NEEDHI</h1>
        <p>AI Legal Assistant</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    display_name = active_model_name.replace("models/", "")
    st.markdown(f'<div class="model-badge">🤖 {display_name}</div>', unsafe_allow_html=True)

    if st.session_state.chat_history:
        st.markdown("---")
        chat_export = "\n\n".join(
            f"{'You' if r == 'user' else 'Needhi AI'}:\n{t}"
            for r, t in st.session_state.chat_history
        )
        st.download_button(
            "💾 Export Chat",
            chat_export,
            file_name="Needhi_Chat_History.txt",
            use_container_width=True,
        )

def detect_severity(text):
    t = text.lower()
    badges = []
    if any(w in t for w in ["non-bailable", "non bailable", "cognizable"]):
        badges.append(('<span class="badge badge-red">🔴 Non-Bailable</span>', 0))
    elif any(w in t for w in ["bailable"]):
        badges.append(('<span class="badge badge-yellow">🟡 Bailable</span>', 1))
    if any(w in t for w in ["civil", "civil suit", "civil dispute", "civil case"]):
        badges.append(('<span class="badge badge-green">🟢 Civil Matter</span>', 2))
    if any(w in t for w in ["criminal", "imprisonment", "jail", "prison", "arrest"]):
        badges.append(('<span class="badge badge-red">⚠️ Criminal Offense</span>', 3))
    if any(w in t for w in ["ipc", "bns", "crpc", "bnss", "section"]):
        badges.append(('<span class="badge badge-blue">📖 IPC/BNS Applicable</span>', 4))
    if not badges:
        badges.append(('<span class="badge badge-gray">ℹ️ General Legal Query</span>', 5))
    badges.sort(key=lambda x: x[1])
    return "".join(b[0] for b in badges)

def run_legal_query(query, language, context_history=None):
    safety = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]
    if language == "Tamil":
        history_block = ""
        if context_history:
            history_block = "\n".join(
                f"{'பயனர்' if r=='user' else 'AI'}: {t}" for r, t in context_history
            )
            history_block = f"\nமுந்தைய உரையாடல்:\n{history_block}\n"
        prompt = f"""System: நீங்கள் 'நீதி AI' — இந்திய சட்டத்தில் நிபுணத்துவம் வாய்ந்த AI சட்ட உதவியாளர்.{history_block}
User Query: '{query}'
TASK:
1. இந்த கேள்வி இந்திய சட்டம், நீதிமன்றம், காவல்துறை, குற்றம் அல்லது உரிமைகள் தொடர்பானதா?
2. இல்லை என்றால் சரியாக பதிலளிக்கவும்: "மன்னிக்கவும். நான் சட்டம் தொடர்பான கேள்விகளுக்கு மட்டுமே பதிலளிப்பேன்."
3. ஆம் என்றால் பின்வரும் format-ல் விரிவான பதில் தரவும்:

**⚖️ சட்ட பிரிவுகள் (Legal Sections)**
- பொருந்தும் BNS/IPC பிரிவுகளை பட்டியலிடவும்

**🔍 குற்றத்தின் விளக்கம் (Offense Explained)**
- எளிய தமிழில் விளக்கவும்

**⚠️ தண்டனை விவரங்கள் (Punishment Details)**
- சிறைத்தண்டனை, அபராதம், பிணை விவரங்கள்

**✅ உங்கள் உரிமைகள் (Your Rights)**
- நீங்கள் என்ன செய்யலாம், எங்கு புகார் செய்யலாம்

**📋 அடுத்த நடவடிக்கைகள் (Next Steps)**
- step-by-step செய்ய வேண்டியவை"""
    else:
        history_block = ""
        if context_history:
            history_block = "\n".join(
                f"{'User' if r=='user' else 'AI'}: {t}" for r, t in context_history
            )
            history_block = f"\nPrevious conversation:\n{history_block}\n"
        prompt = f"""System: You are 'Needhi AI' — an expert AI Legal Assistant specializing in Indian Law.{history_block}
User Query: '{query}'
TASK:
1. Is this related to Indian Law, Court, Police, Crime, or Rights?
2. IF NO: REPLY EXACTLY: "Sorry, I am designed to answer only legal questions."
3. IF YES: Provide a detailed structured response:

**⚖️ Applicable Legal Sections**
- List all relevant BNS/IPC/CrPC sections

**🔍 Offense Explained**
- Clear explanation of the offense

**⚠️ Punishment Details**
- Imprisonment, Fine, Bailable/Non-Bailable, Cognizable/Non-Cognizable

**✅ Your Rights**
- Rights of victim/accused, where to file complaint

**📋 Recommended Next Steps**
- Step-by-step action plan"""

    response, used_model = generate_with_fallback(
        prompt,
        generation_config=genai.types.GenerationConfig(max_output_tokens=4096),
        safety_settings=safety,
        stream=True
    )
    st.markdown('<div class="result-card">', unsafe_allow_html=True)
    st.markdown('<div class="result-header"><span>⚖</span> Needhi AI — Legal Analysis</div>', unsafe_allow_html=True)
    full_text = ""
    result_placeholder = st.empty()
    for chunk in response:
        try:
            if chunk.text:
                full_text += chunk.text
                result_placeholder.markdown(full_text)
        except Exception:
            pass
    if not full_text:
        full_text = "Response was blocked by safety filters. Please rephrase your query."
        result_placeholder.warning(full_text)
    else:
        badges_html = detect_severity(full_text)
        st.markdown(f'<div class="severity-bar">{badges_html}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    return full_text

# --- HOME ---
if menu == "Home":
    if language == "Tamil":
        st.markdown("""
        <div class="hero">
            <div class="hero-tag">AI · Legal · Tamil Nadu</div>
            <p class="hero-title">நீதி AI</p>
            <p class="hero-subtitle">உங்கள் AI சட்ட உதவியாளர் — எளிமையான தமிழில்</p>
            <div class="stats-bar">
                <div class="stat-item"><span class="stat-num">IPC</span><span class="stat-label">Sections</span></div>
                <div class="stat-item"><span class="stat-num">BNS</span><span class="stat-label">Updated Laws</span></div>
                <div class="stat-item"><span class="stat-num">24/7</span><span class="stat-label">Available</span></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="hero">
            <div class="hero-tag">AI · Legal · India</div>
            <p class="hero-title">NEEDHI AI</p>
            <p class="hero-subtitle">Your Intelligent Indian Legal Assistant</p>
            <div class="stats-bar">
                <div class="stat-item"><span class="stat-num">IPC</span><span class="stat-label">Sections</span></div>
                <div class="stat-item"><span class="stat-num">BNS</span><span class="stat-label">Updated Laws</span></div>
                <div class="stat-item"><span class="stat-num">24/7</span><span class="stat-label">Available</span></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    tab_ask, tab_upload, tab_voice = st.tabs(["💬 Ask", "📄 Upload Document", "🎙️ Voice Input"])

    # ── TAB 1: ASK (with chat history) ──────────────────────────────────────
    with tab_ask:
        # Render existing chat history
        if st.session_state.chat_history:
            st.markdown('<div class="chat-container">', unsafe_allow_html=True)
            pairs = list(zip(st.session_state.chat_history[::2], st.session_state.chat_history[1::2]))
            for i, ((_, user_text), (_, ai_text)) in enumerate(pairs):
                # Divider between turns
                if i > 0:
                    st.markdown(f'<div class="chat-divider"><div class="chat-divider-line"></div><div class="chat-divider-text">Turn {i+1}</div><div class="chat-divider-line"></div></div>', unsafe_allow_html=True)
                # User bubble
                st.markdown(f'''
                <div class="chat-row-user">
                    <div class="chat-bubble-wrap chat-bubble-wrap-user">
                        <div class="chat-name chat-name-user">You</div>
                        <div class="chat-bubble-user">{user_text}</div>
                    </div>
                    <div class="chat-avatar chat-avatar-user">👤</div>
                </div>''', unsafe_allow_html=True)
                # AI bubble (summary only — first 300 chars with ellipsis)
                preview = ai_text[:300] + "..." if len(ai_text) > 300 else ai_text
                st.markdown(f'''
                <div class="chat-row-ai">
                    <div class="chat-avatar chat-avatar-ai">⚖️</div>
                    <div class="chat-bubble-wrap chat-bubble-wrap-ai">
                        <div class="chat-name chat-name-ai">Needhi AI</div>
                        <div class="chat-bubble-ai">{preview}</div>
                    </div>
                </div>''', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            if st.button("🗑️ Clear Chat", key="clear_chat"):
                st.session_state.chat_history = []
                save_chat_history([])
                st.rerun()

        st.markdown('<div class="search-box">', unsafe_allow_html=True)
        col1, col2 = st.columns([5, 1])
        with col1:
            input_placeholder = "e.g. My landlord is not returning my deposit..." if language == "English" else "e.g. என் நண்பன் என்னை ஏமாற்றினான்..."
            label = "Describe your legal issue" if language == "English" else "உங்கள் சட்ட பிரச்சனை என்ன?"
            # Pre-fill from voice if available
            default_val = st.session_state.voice_text
            st.session_state.voice_text = ""
            user_query = st.text_input(label, value=default_val, placeholder=input_placeholder, key="ask_input")
        with col2:
            st.write("")
            st.write("")
            btn_text = "Analyze" if language == "English" else "தேடு"
            search_clicked = st.button(btn_text, use_container_width=True, key="ask_btn")
        st.markdown('</div>', unsafe_allow_html=True)

        if search_clicked:
            if not user_query:
                st.warning("⚠️ Please describe your legal issue first.")
            else:
                spin_text = "Analyzing your case..." if language == "English" else "AI சட்ட புத்தகங்களை தேடுகிறது..."
                with st.spinner(spin_text):
                    try:
                        full_text = run_legal_query(user_query, language, st.session_state.chat_history)
                        st.session_state.chat_history.append(("user", user_query))
                        st.session_state.chat_history.append(("ai", full_text))
                        save_chat_history(st.session_state.chat_history)
                        st.write("")
                        st.download_button("↓ Download Legal Report", full_text, file_name="Needhi_Legal_Report.txt", use_container_width=False)
                    except Exception as e:
                        st.error(f"❌ Error: {e}")

    # ── TAB 2: UPLOAD DOCUMENT ───────────────────────────────────────────────
    with tab_upload:
        st.markdown('<p style="color:#8a9bb0;font-size:0.9rem;margin-bottom:16px">Upload a legal document (PDF or image) and Needhi AI will summarize it.</p>', unsafe_allow_html=True)
        uploaded_file = st.file_uploader("Choose a PDF or image", type=["pdf", "png", "jpg", "jpeg"], key="doc_upload")
        doc_question = st.text_input("Ask a specific question about the document (optional)", key="doc_question",
                                     placeholder="e.g. What are my obligations under this agreement?")
        analyze_doc = st.button("📄 Analyze Document", key="analyze_doc_btn")

        if analyze_doc and uploaded_file:
            with st.spinner("Reading document..."):
                try:
                    file_type = uploaded_file.type
                    extra_q = f" Also answer: {doc_question}" if doc_question else ""

                    if file_type == "application/pdf":
                        reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))
                        doc_text = "\n".join(page.extract_text() or "" for page in reader.pages)
                        if not doc_text.strip():
                            st.warning("Could not extract text from this PDF. Try uploading an image instead.")
                        else:
                            prompt = f"""You are Needhi AI, an Indian legal assistant.
Analyze this legal document and provide:
1. Document type and summary
2. Key legal clauses and their implications under Indian law
3. Any rights or obligations of the parties
4. Red flags or concerning clauses
5. Recommended action{extra_q}

Document text:
{doc_text[:12000]}"""
                            response, _ = generate_with_fallback(prompt, generation_config=genai.types.GenerationConfig(max_output_tokens=4096))
                            st.markdown('<div class="result-card">', unsafe_allow_html=True)
                            st.markdown('<div class="result-header"><span>📄</span> Document Analysis</div>', unsafe_allow_html=True)
                            st.markdown(response.text)
                            st.markdown('</div>', unsafe_allow_html=True)
                            st.download_button("↓ Download Analysis", response.text, file_name="Needhi_Doc_Analysis.txt")
                    else:
                        image = Image.open(uploaded_file)
                        prompt = f"""You are Needhi AI, an Indian legal assistant.
Analyze this legal document image and provide:
1. Document type and summary
2. Key legal clauses and their implications under Indian law
3. Any rights or obligations of the parties
4. Red flags or concerning clauses
5. Recommended action{extra_q}"""
                        response, _ = generate_with_fallback([prompt, image])
                        st.markdown('<div class="result-card">', unsafe_allow_html=True)
                        st.markdown('<div class="result-header"><span>📄</span> Document Analysis</div>', unsafe_allow_html=True)
                        st.markdown(response.text)
                        st.markdown('</div>', unsafe_allow_html=True)
                        st.download_button("↓ Download Analysis", response.text, file_name="Needhi_Doc_Analysis.txt")
                except Exception as e:
                    st.error(f"❌ Error analyzing document: {e}")
        elif analyze_doc and not uploaded_file:
            st.warning("⚠️ Please upload a file first.")

    # ── TAB 3: VOICE INPUT ───────────────────────────────────────────────────
    with tab_voice:
        if not VOICE_AVAILABLE:
            st.warning("⚠️ Voice input requires `speechrecognition` and `pyaudio`. Run: `pip install speechrecognition pyaudio`")
        else:
            st.markdown('<p style="color:#8a9bb0;font-size:0.9rem;margin-bottom:16px">Click the button and speak your legal issue. It will be sent to the Ask tab.</p>', unsafe_allow_html=True)
            voice_lang = "ta-IN" if language == "Tamil" else "en-IN"
            if st.button("🎙️ Start Listening", key="voice_btn"):
                recognizer = sr.Recognizer()
                with st.spinner("🎙️ Listening... speak now"):
                    try:
                        with sr.Microphone() as source:
                            recognizer.adjust_for_ambient_noise(source, duration=1)
                            audio = recognizer.listen(source, timeout=8, phrase_time_limit=15)
                        spoken_text = recognizer.recognize_google(audio, language=voice_lang)
                        st.success(f"✅ Heard: {spoken_text}")
                        st.session_state.voice_text = spoken_text
                        st.info("Switch to the 💬 Ask tab — your query has been filled in.")
                    except sr.WaitTimeoutError:
                        st.warning("No speech detected. Please try again.")
                    except sr.UnknownValueError:
                        st.warning("Could not understand the audio. Please speak clearly.")
                    except Exception as e:
                        st.error(f"❌ Voice error: {e}")

# --- KNOW YOUR RIGHTS ---
elif menu == "Know Your Rights":
    if language == "Tamil":
        st.markdown('<p class="section-title">உங்கள் உரிமைகள்</p><p class="section-subtitle">இந்திய சட்டத்தின் கீழ் உங்களுக்கு உள்ள அடிப்படை உரிமைகள்</p>', unsafe_allow_html=True)
    else:
        st.markdown('<p class="section-title">Know Your Rights</p><p class="section-subtitle">Fundamental rights every Indian citizen must know</p>', unsafe_allow_html=True)

    tab_police, tab_consumer, tab_tenant, tab_cyber = st.tabs(["👮 Police & Arrest", "🛒 Consumer", "🏠 Tenant", "💻 Cyber Crime"])

    with tab_police:
        rights_police = [
            ("📝 Right to FIR" if language=="English" else "📝 FIR உரிமை",
             "Police are legally bound to register an FIR for cognizable offenses. If refused, complain to SP or file in court. (BNSS Section 173)" if language=="English" else "காவல் நிலையத்தில் புகார் அளித்தால் FIR பதிவு செய்ய கடமைப்பட்டுள்ளனர். மறுத்தால் SP-யிடம் புகார் செய்யலாம். (BNSS பிரிவு 173)"),
            ("🔇 Right to Silence" if language=="English" else "🔇 மௌன உரிமை",
             "You have the right to remain silent when arrested. Cannot be forced to testify against yourself. (Article 20(3))" if language=="English" else "கைது செய்யப்பட்டால் மௌனமாக இருக்கலாம். உங்களுக்கு எதிராக சாட்சி சொல்ல வேண்டியதில்லை. (அனுச்சேதம் 20(3))"),
            ("⚖️ Right to Lawyer" if language=="English" else "⚖️ வழக்கறிஞர் உரிமை",
             "Right to consult a lawyer immediately upon arrest. Legal aid is free if you cannot afford one. (Article 22)" if language=="English" else "கைது செய்யப்பட்டவுடன் வழக்கறிஞரை சந்திக்கும் உரிமை உண்டு. இலவச சட்ட உதவி கிடைக்கும். (அனுச்சேதம் 22)"),
            ("🏥 Right to Medical Aid" if language=="English" else "🏥 மருத்துவ உரிமை",
             "Every arrested person has the right to free medical examination and treatment by a government doctor." if language=="English" else "கைதியாக இருந்தாலும் அரசு மருத்துவரிடம் இலவச மருத்துவ பரிசோதனை பெறும் உரிமை உண்டு."),
            ("🌙 No Night Arrest (Women)" if language=="English" else "🌙 இரவு கைது தடை",
             "Women cannot be arrested after sunset and before sunrise except in exceptional circumstances with a female officer." if language=="English" else "பெண்களை சூரிய அஸ்தமனத்திற்கு பிறகு கைது செய்யக்கூடாது. பெண் காவலர் இருக்க வேண்டும்."),
            ("📋 Right to Know Grounds" if language=="English" else "📋 கைது காரணம் அறியும் உரிமை",
             "Police must inform you of the reason for your arrest at the time of arrest. (BNSS Section 47)" if language=="English" else "கைது செய்யும்போது காரணம் சொல்ல வேண்டும். (BNSS பிரிவு 47)"),
            ("👨‍👩‍👧 Right to Inform Family" if language=="English" else "👨‍👩‍👧 குடும்பத்தினருக்கு தகவல்",
             "Police must inform a friend or relative of your arrest within 24 hours. (BNSS Section 50)" if language=="English" else "கைது செய்த 24 மணி நேரத்தில் குடும்பத்தினருக்கு தகவல் தர வேண்டும். (BNSS பிரிவு 50)"),
        ]
        for t, d in rights_police:
            st.markdown(f'<div class="rights-card"><h4>{t}</h4><p>{d}</p></div>', unsafe_allow_html=True)

    with tab_consumer:
        rights_consumer = [
            ("🛡️ Right to Safety" if language=="English" else "🛡️ பாதுகாப்பு உரிமை",
             "Protection against goods and services hazardous to life and property. Consumer Protection Act 2019." if language=="English" else "தீங்கு விளைவிக்கும் பொருட்கள் மற்றும் சேவைகளிலிருந்து பாதுகாப்பு பெறும் உரிமை. நுகர்வோர் பாதுகாப்பு சட்டம் 2019."),
            ("📢 Right to Information" if language=="English" else "📢 தகவல் அறியும் உரிமை",
             "Right to know the quality, quantity, price, and standard of goods/services before purchase." if language=="English" else "பொருளின் தரம், அளவு, விலை அறிந்து வாங்கும் உரிமை உண்டு."),
            ("🔄 Right to Return & Refund" if language=="English" else "🔄 திரும்ப கொடுக்கும் உரிமை",
             "If a product is defective or service is deficient, you can demand replacement, repair, or full refund." if language=="English" else "குறைபாடுள்ள பொருள் அல்லது சேவைக்கு மாற்று, பழுது அல்லது முழு பணம் திரும்ப கேட்கலாம்."),
            ("🏛️ Consumer Forum" if language=="English" else "🏛️ நுகர்வோர் நீதிமன்றம்",
             "District Commission (up to ₹50 lakhs), State Commission (up to ₹2 crore), National Commission (above ₹2 crore)." if language=="English" else "மாவட்ட ஆணையம் (₹50 லட்சம் வரை), மாநில ஆணையம் (₹2 கோடி வரை), தேசிய ஆணையம் (₹2 கோடிக்கு மேல்)."),
            ("📱 E-Commerce Rights" if language=="English" else "📱 ஆன்லைன் வாங்குதல் உரிமை",
             "Online sellers must display all charges upfront. Hidden charges are illegal. Return within stated return policy." if language=="English" else "மறைமுக கட்டணங்கள் சட்டவிரோதம். திரும்ப கொடுக்கும் கொள்கைக்குள் பொருளை திரும்ப கொடுக்கலாம்."),
            ("⚡ Utility Complaints" if language=="English" else "⚡ பயன்பாட்டு சேவை புகார்",
             "Electricity, water, telecom — file with respective ombudsman. TRAI for telecom, CERC for electricity." if language=="English" else "மின்சாரம், தண்ணீர், தொலைத்தொடர்பு — TRAI, CERC ஆம்புட்ஸ்மேனிடம் புகார் செய்யலாம்."),
            ("🏦 Banking Fraud" if language=="English" else "🏦 வங்கி மோசடி",
             "Report unauthorized transactions within 3 days to limit liability. File with Banking Ombudsman (RBI) for free." if language=="English" else "அங்கீகரிக்கப்படாத பரிவர்த்தனையை 3 நாட்களில் வங்கிக்கு தெரிவிக்கவும். RBI ஆம்புட்ஸ்மேனிடம் இலவசமாக புகார் செய்யலாம்."),
        ]
        for t, d in rights_consumer:
            st.markdown(f'<div class="rights-card"><h4>{t}</h4><p>{d}</p></div>', unsafe_allow_html=True)

    with tab_tenant:
        rights_tenant = [
            ("📄 Right to Rent Agreement" if language=="English" else "📄 வாடகை ஒப்பந்த உரிமை",
             "Always insist on a written rent agreement. Register agreements above 11 months." if language=="English" else "எழுத்துப்பூர்வ வாடகை ஒப்பந்தம் கோருங்கள். 11 மாதத்திற்கு மேல் பதிவு செய்வது கட்டாயம்."),
            ("🔑 Right to Possession" if language=="English" else "🔑 வசிக்கும் உரிமை",
             "Landlord cannot forcibly evict you without a court order. Illegal eviction is a criminal offense." if language=="English" else "நீதிமன்ற உத்தரவு இல்லாமல் வீட்டு உரிமையாளர் வலுக்கட்டாயமாக வெளியேற்ற முடியாது. சட்டவிரோதம்."),
            ("💰 Security Deposit" if language=="English" else "💰 வைப்புத்தொகை திரும்ப",
             "Landlord must return security deposit within 30 days of vacating. Deductions must be justified with proof." if language=="English" else "வீடு காலி செய்த 30 நாட்களில் வைப்புத்தொகை திரும்ப தர வேண்டும். கழிவுகளுக்கு ஆதாரம் தேவை."),
            ("🔧 Right to Repairs" if language=="English" else "🔧 பழுது சரிசெய்யும் உரிமை",
             "Landlord is responsible for major structural repairs. Tenant handles minor day-to-day maintenance." if language=="English" else "முக்கிய கட்டமைப்பு பழுதுகளை வீட்டு உரிமையாளர் சரிசெய்ய வேண்டும். சிறிய பழுதுகள் வாடகைதாரர் பொறுப்பு."),
            ("📢 Notice Period" if language=="English" else "📢 நோட்டீஸ் உரிமை",
             "Landlord must give adequate notice (usually 1-3 months) before asking you to vacate." if language=="English" else "வெளியேற சொல்வதற்கு முன் போதுமான நோட்டீஸ் (பொதுவாக 1-3 மாதம்) தர வேண்டும்."),
            ("🚫 No Discrimination" if language=="English" else "🚫 பாகுபாடு தடை",
             "Landlord cannot deny tenancy based on religion, caste, or food habits. This is illegal under Indian law." if language=="English" else "மதம், சாதி, உணவு பழக்கம் காரணமாக வாடகை மறுப்பது சட்டவிரோதம்."),
            ("⚖️ Rent Control Act" if language=="English" else "⚖️ வாடகை கட்டுப்பாட்டு சட்டம்",
             "Most states have Rent Control Acts protecting tenants from arbitrary rent hikes. Check your state's specific act." if language=="English" else "பெரும்பாலான மாநிலங்களில் வாடகை கட்டுப்பாட்டு சட்டம் உள்ளது. தன்னிச்சையான வாடகை உயர்வை தடுக்கலாம்."),
        ]
        for t, d in rights_tenant:
            st.markdown(f'<div class="rights-card"><h4>{t}</h4><p>{d}</p></div>', unsafe_allow_html=True)

    with tab_cyber:
        rights_cyber = [
            ("🚨 Report Cybercrime" if language=="English" else "🚨 சைபர் கிரைம் புகார்",
             "Report at cybercrime.gov.in or call 1930 (National Cyber Crime Helpline). Available 24/7." if language=="English" else "cybercrime.gov.in அல்லது 1930 (தேசிய சைபர் கிரைம் உதவி எண்) அழைக்கவும். 24/7 கிடைக்கும்."),
            ("💳 Online Financial Fraud" if language=="English" else "💳 ஆன்லைன் நிதி மோசடி",
             "Report to your bank immediately and call 1930. Report within 3 days to limit liability. IT Act Section 66C & 66D." if language=="English" else "உடனே வங்கிக்கு தெரிவித்து 1930 அழைக்கவும். 3 நாட்களில் புகார் செய்தால் பொறுப்பு குறையும். IT சட்டம் 66C & 66D."),
            ("📸 Morphing / Fake Photos" if language=="English" else "📸 போலி புகைப்படம்",
             "Creating and sharing morphed images is a crime under IT Act Section 66E and BNS Section 77. Up to 3 years imprisonment." if language=="English" else "மார்பிங் செய்த படங்கள் பகிர்வது IT சட்டம் 66E மற்றும் BNS 77 கீழ் குற்றம். 3 ஆண்டு சிறை தண்டனை."),
            ("😡 Cyberbullying & Harassment" if language=="English" else "😡 சைபர் துன்புறுத்தல்",
             "Online harassment and stalking are punishable under BNS Section 351 and IT Act Section 67. Screenshot and preserve evidence." if language=="English" else "ஆன்லைன் துன்புறுத்தல், தொடர்தல் BNS 351 மற்றும் IT சட்டம் 67 கீழ் தண்டிக்கப்படும். ஆதாரம் சேமிக்கவும்."),
            ("🔐 Data Privacy" if language=="English" else "🔐 தரவு தனியுரிமை",
             "Unauthorized access to your personal data is an offense under IT Act Section 43 & 66." if language=="English" else "உங்கள் தனிப்பட்ட தரவை அங்கீகரிக்கப்படாமல் அணுகுவது IT சட்டம் 43 & 66 கீழ் குற்றம்."),
            ("📧 Phishing & Scams" if language=="English" else "📧 ஃபிஷிங் மோசடி",
             "Phishing impersonating banks or government is punishable under IT Act Section 66D — up to 3 years + ₹1 lakh fine." if language=="English" else "வங்கி அல்லது அரசாங்கமாக நடிக்கும் ஃபிஷிங் IT சட்டம் 66D கீழ் 3 ஆண்டு சிறை + ₹1 லட்சம் அபராதம்."),
            ("👶 Child Safety Online" if language=="English" else "👶 குழந்தை பாதுகாப்பு",
             "Any sexual content involving minors is a serious offense under POCSO Act and IT Act Section 67B. Report immediately." if language=="English" else "சிறுவர்களை உள்ளடக்கிய ஆபாச உள்ளடக்கம் POCSO சட்டம் மற்றும் IT சட்டம் 67B கீழ் கடுமையான குற்றம்."),
        ]
        for t, d in rights_cyber:
            st.markdown(f'<div class="rights-card"><h4>{t}</h4><p>{d}</p></div>', unsafe_allow_html=True)

# --- ABOUT ---
elif menu == "About":
    st.markdown('<p class="section-title">About Needhi AI</p><p class="section-subtitle">Built to make Indian law accessible to everyone</p>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class="info-card">
            <div class="icon">👨💻</div>
            <h3>Developer</h3>
            <p>Ajay Godric<br><small style="color:#b0bec5;">Creator & Lead Developer</small></p>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="info-card">
            <div class="icon">🛠️</div>
            <h3>Tech Stack</h3>
            <p>Python & Streamlit<br><small style="color:#b0bec5;"></small></p>
        </div>""", unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="info-card">
            <div class="icon">⚖️</div>
            <h3>Purpose</h3>
            <p>Free Legal Aid<br><small style="color:#b0bec5;">For Every Indian Citizen</small></p>
        </div>""", unsafe_allow_html=True)

    st.markdown("""
    <div class="rights-card" style="margin-top:10px; border-left-color:#e67e22;">
        <h4>⚠️ Disclaimer</h4>
        <p>Needhi AI provides general legal information only. It is not a substitute for professional legal advice.
        Always consult a qualified lawyer for your specific legal matters.</p>
    </div>
    """, unsafe_allow_html=True)

# --- CONTACT ---
elif menu == "Contact Lawyer":
    st.markdown('<p class="section-title">Get Legal Help</p><p class="section-subtitle">Reach out through any of the channels below</p>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div class="info-card">
            <div class="icon">📧</div>
            <h3>Email Us</h3>
            <p>help@needhi.ai<br><small style="color:#b0bec5;">Response within 24 hours</small></p>
        </div>""", unsafe_allow_html=True)
        st.markdown("""
        <div class="info-card">
            <div class="icon">🏛️</div>
            <h3>District Legal Aid</h3>
            <p>Visit your nearest<br><small style="color:#b0bec5;">District Legal Services Authority</small></p>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="info-card">
            <div class="icon">📱</div>
            <h3>Helpline</h3>
            <p>1800-LEGAL-HELP<br><small style="color:#b0bec5;">Toll Free · 24/7</small></p>
        </div>""", unsafe_allow_html=True)
        st.markdown("""
        <div class="info-card">
            <div class="icon">🆘</div>
            <h3>Emergency</h3>
            <p>Police: 100 · Women: 1091<br><small style="color:#b0bec5;">Legal Aid: 15100</small></p>
        </div>""", unsafe_allow_html=True)
