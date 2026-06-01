import os
import io
import json
import base64
import urllib.request
import re as _re
import time
import logging
from collections import defaultdict
from datetime import datetime, timedelta, date
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, Response
from pydantic import BaseModel, EmailStr, Field
import google.generativeai as genai
from PIL import Image
import pypdf
from fpdf import FPDF
from cryptography.fernet import Fernet

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("needhi")

# --- Dynamic TOML Parser ---
try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None

# Root paths
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT_DIR, "backend", "data")

def load_secrets_toml() -> dict:
    secrets_path = os.path.join(ROOT_DIR, ".streamlit", "secrets.toml")
    if not os.path.exists(secrets_path) or tomllib is None:
        return {}
    try:
        with open(secrets_path, "rb") as f:
            return tomllib.load(f)
    except Exception as e:
        logger.exception("Error reading secrets.toml")
        return {}

# --- Atomic File Locking Manager ---
class FileLock:
    def __init__(self, lock_name: str, timeout: int = 5):
        self.lock_path = os.path.join(ROOT_DIR, "backend", f"{lock_name}.lock")
        self.timeout = timeout
        self.locked = False
        
    def __enter__(self):
        start_time = time.time()
        while time.time() - start_time < self.timeout:
            try:
                os.mkdir(self.lock_path)
                self.locked = True
                return self
            except FileExistsError:
                time.sleep(0.1)
        raise RuntimeError(f"Timeout waiting for file lock: {self.lock_path}")
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.locked:
            try:
                os.rmdir(self.lock_path)
            except Exception:
                pass

def safe_json_append(filepath: str, new_record: dict, lock_name: str) -> list:
    """Thread-safe and process-safe read-modify-write for JSON files."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with FileLock(lock_name):
        records = []
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    records = json.loads(content) if content else []
            except Exception:
                records = []
        records.append(new_record)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2, ensure_ascii=False)
        return records

# --- PII Encryption Helpers ---
# Secure default Fernet key for local development fallback
DEV_PII_KEY = b"f1K7kUvT8pX0rY2s3tU4vW5x6y7z8A9b0C1d2E3f4G5=" # Fernet-compliant 32-byte key

def get_fernet():
    key_str = os.environ.get("PII_ENCRYPTION_KEY")
    if not key_str:
        secrets = load_secrets_toml()
        key_str = secrets.get("PII_ENCRYPTION_KEY")
        
    if not key_str:
        logger.warning("PII_ENCRYPTION_KEY environment variable not set. Falling back to development key!")
        return Fernet(DEV_PII_KEY)
    try:
        return Fernet(key_str.encode())
    except Exception as e:
        logger.error(f"Invalid PII_ENCRYPTION_KEY format: {e}. Using development fallback.")
        return Fernet(DEV_PII_KEY)

def encrypt_field(value: str) -> str:
    if not value:
        return value
    try:
        return get_fernet().encrypt(value.encode()).decode()
    except Exception as e:
        logger.error(f"Field encryption failed: {e}")
        return value

def decrypt_field(value: str) -> str:
    if not value:
        return value
    try:
        return get_fernet().decrypt(value.encode()).decode()
    except Exception as e:
        logger.error(f"Field decryption failed: {e}")
        return value

def purge_old_records(filepath: str, days: int = 90):
    """Delete records older than `days` days."""
    if not os.path.exists(filepath):
        return
    cutoff = datetime.now() - timedelta(days=days)
    try:
        lock_name = os.path.basename(filepath).replace(".json", "")
        with FileLock(lock_name):
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read().strip()
                records = json.loads(content) if content else []
            
            fresh = []
            for r in records:
                ts_str = r.get("timestamp")
                if ts_str:
                    try:
                        ts = datetime.fromisoformat(ts_str)
                        if ts > cutoff:
                            fresh.append(r)
                    except ValueError:
                        fresh.append(r)
                else:
                    fresh.append(r)
                    
            if len(fresh) < len(records):
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(fresh, f, indent=2, ensure_ascii=False)
                logger.info(f"Purged {len(records) - len(fresh)} expired records from {filepath}")
    except Exception as e:
        logger.error(f"Failed to purge old records from {filepath}: {e}")

# --- Memory-Based sliding window Rate Limiter ---
class SlidingWindowRateLimiter:
    def __init__(self, limit: int, window: int):
        self.limit = limit
        self.window = window
        self.requests = defaultdict(list)
        
    def is_allowed(self, client_ip: str) -> bool:
        now = time.time()
        self.requests[client_ip] = [t for t in self.requests[client_ip] if now - t < self.window]
        if len(self.requests[client_ip]) >= self.limit:
            return False
        self.requests[client_ip].append(now)
        return True

ai_limiter = SlidingWindowRateLimiter(limit=5, window=60)
data_limiter = SlidingWindowRateLimiter(limit=20, window=60)

def check_rate_limit_ai(request: Request):
    client_ip = request.client.host if request.client else "unknown"
    if not ai_limiter.is_allowed(client_ip):
        raise HTTPException(status_code=429, detail="Too many requests. Please try again in a minute.")

def check_rate_limit_data(request: Request):
    client_ip = request.client.host if request.client else "unknown"
    if not data_limiter.is_allowed(client_ip):
        raise HTTPException(status_code=429, detail="Too many requests. Please try again in a minute.")

app = FastAPI(title="Needhi AI Backend", version="1.0.0")

# Enable CORS for frontend connection (Vite dev server or static build)
ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

# Load API keys from secrets.toml or environment variables
def load_api_keys():
    keys = []
    # Try streamlit secrets via robust tomllib
    secrets = load_secrets_toml()
    for k, v in secrets.items():
        if k.startswith("GEMINI_API_KEY") and v:
            keys.append(v)
            
    # Fallback to environment variables
    for env_var in ["GEMINI_API_KEY", "GEMINI_API_KEY_2", "GEMINI_API_KEY_3", "GEMINI_API_KEY_4", "GEMINI_API_KEY_5", "GEMINI_API_KEY_6"]:
        val = os.environ.get(env_var)
        if val and val not in keys:
            keys.append(val)
            
    # Dynamically scan environment variables for other keys starting with GEMINI_API_KEY
    for k, v in os.environ.items():
        if k.startswith("GEMINI_API_KEY") and v and v not in keys:
            keys.append(v)
            
    return keys if keys else [""]

API_KEYS = load_api_keys()
GOOGLE_API_KEY = API_KEYS[0]
genai.configure(api_key=GOOGLE_API_KEY)

MODEL_FALLBACK_ORDER = [
    "models/gemini-2.5-flash-lite",
    "models/gemini-2.5-flash",
    "models/gemini-2.0-flash",
    "models/gemini-2.0-flash-lite",
]

ACTIVE_MODEL_NAME = "models/gemini-2.5-flash-lite"

# Helper function to query Gemini with Key Rotation and Model Fallbacks
def generate_gemini_content(prompt_or_parts, generation_config=None, stream=False, system_instruction=None):
    global API_KEYS
    models_to_try = [ACTIVE_MODEL_NAME] + [m for m in MODEL_FALLBACK_ORDER if m != ACTIVE_MODEL_NAME]
    
    # Safety settings - use robust block levels for production safety
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    ]
    
    # Try all configured API keys
    for idx, api_key in enumerate(API_KEYS):
        try:
            genai.configure(api_key=api_key)
            for model_name in models_to_try:
                try:
                    model = genai.GenerativeModel(model_name, system_instruction=system_instruction)
                    kwargs = {}
                    if generation_config:
                        kwargs["generation_config"] = generation_config
                    
                    kwargs["safety_settings"] = safety_settings
                    
                    if stream:
                        res = model.generate_content(prompt_or_parts, stream=True, **kwargs)
                    else:
                        res = model.generate_content(prompt_or_parts, **kwargs)
                        
                    # Promote the working key to the front of API_KEYS to make subsequent calls fast
                    if idx > 0:
                        working_key = API_KEYS.pop(idx)
                        API_KEYS.insert(0, working_key)
                        
                    return res, model_name
                except Exception as e:
                    err_str = str(e)
                    # If this key is rate-limited (429) or invalid (400, 401), break to the next key immediately
                    if "429" in err_str or "API_KEY_INVALID" in err_str or "400" in err_str or "401" in err_str:
                        break
                    continue
        except Exception:
            continue
            
    # Ultimate fallback with primary key and primary model
    genai.configure(api_key=API_KEYS[0])
    model = genai.GenerativeModel(models_to_try[0], system_instruction=system_instruction)
    kwargs = {}
    if generation_config:
        kwargs["generation_config"] = generation_config
    kwargs["safety_settings"] = safety_settings
    if stream:
        return model.generate_content(prompt_or_parts, stream=True, **kwargs), models_to_try[0]
    return model.generate_content(prompt_or_parts, **kwargs), models_to_try[0]

# --- Font Loading & PDF Helpers ---
def get_tamil_font(bold=False):
    filename = "NotoSansTamil-Bold.ttf" if bold else "NotoSansTamil-Regular.ttf"
    font_path = os.path.join(ROOT_DIR, filename)
    if not os.path.exists(font_path):
        try:
            url = (
                "https://fonts.gstatic.com/s/notosanstamil/v31/ieVc2YdFI3GCY6SyQy1KfStzYKZgzN1z4LKDbeZce-0429tBManUktuex7shpL0R.ttf"
                if bold else
                "https://fonts.gstatic.com/s/notosanstamil/v31/ieVc2YdFI3GCY6SyQy1KfStzYKZgzN1z4LKDbeZce-0429tBManUktuex7vGo70R.ttf"
            )
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                with open(font_path, 'wb') as out_file:
                    out_file.write(response.read())
        except Exception:
            pass
    return font_path if os.path.exists(font_path) else None

def clean_pdf_text(text, has_custom_font):
    text = _re.sub(r'[*#`]', '', text)
    if has_custom_font:
        cleaned = []
        for char in text:
            code = ord(char)
            if (32 <= code <= 126) or (0x0B80 <= code <= 0x0BFF) or code == 0x20B9 or char in "\n\t\r" or (160 <= code <= 255):
                cleaned.append(char)
            else:
                cleaned.append("")
        return "".join(cleaned)
    else:
        return text.encode('latin-1', 'replace').decode('latin-1')

def send_email_notification(recipients: List[dict], subject: str, body: str) -> tuple:
    """
    Sends email to a list of recipients (each is a dict with 'email' and 'name').
    Returns a tuple (success: bool, status_message: str)
    """
    smtp_host = os.environ.get("SMTP_HOST", "")
    smtp_port = os.environ.get("SMTP_PORT", "")
    smtp_user = os.environ.get("SMTP_USER", "")
    smtp_password = os.environ.get("SMTP_PASSWORD", "")
    resend_key = os.environ.get("RESEND_API_KEY", "")
    brevo_key = os.environ.get("BREVO_API_KEY", "")
    email_from = os.environ.get("EMAIL_FROM", "")
    
    # Check secrets.toml via tomllib
    secrets = load_secrets_toml()
    if secrets:
        if "SMTP_HOST" in secrets: smtp_host = secrets["SMTP_HOST"]
        if "SMTP_PORT" in secrets: smtp_port = str(secrets["SMTP_PORT"])
        if "SMTP_USER" in secrets: smtp_user = secrets["SMTP_USER"]
        if "SMTP_PASSWORD" in secrets: smtp_password = secrets["SMTP_PASSWORD"]
        if "RESEND_API_KEY" in secrets: resend_key = secrets["RESEND_API_KEY"]
        if "BREVO_API_KEY" in secrets: brevo_key = secrets["BREVO_API_KEY"]
        if "EMAIL_FROM" in secrets: email_from = secrets["EMAIL_FROM"]

    to_emails = [r["email"] for r in recipients]
    
    if resend_key:
        try:
            import urllib.request
            url = "https://api.resend.com/emails"
            headers = {
                "Authorization": f"Bearer {resend_key}",
                "Content-Type": "application/json"
            }
            from_addr = email_from if email_from else "onboarding@resend.dev"
            data = {
                "from": f"Needhi AI <{from_addr}>",
                "to": to_emails,
                "subject": subject,
                "text": body
            }
            api_req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers, method="POST")
            with urllib.request.urlopen(api_req, timeout=10) as response:
                resp_data = json.loads(response.read().decode())
                return True, f"Sent successfully via Resend API (ID: {resp_data.get('id')})"
        except Exception as e:
            return False, f"Failed to send via Resend API: {e}"
            
    elif brevo_key:
        try:
            import urllib.request
            url = "https://api.brevo.com/v3/smtp/email"
            headers = {
                "api-key": brevo_key,
                "Content-Type": "application/json"
            }
            from_addr = email_from if email_from else (smtp_user if smtp_user else "noreply@needhi.ai")
            data = {
                "sender": {"name": "Needhi AI", "email": from_addr},
                "to": [{"email": r["email"], "name": r["name"]} for r in recipients],
                "subject": subject,
                "textContent": body
            }
            api_req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers, method="POST")
            with urllib.request.urlopen(api_req, timeout=10) as response:
                resp_data = json.loads(response.read().decode())
                return True, f"Sent successfully via Brevo API (MessageId: {resp_data.get('messageId')})"
        except Exception as e:
            return False, f"Failed to send via Brevo API: {e}"
            
    elif smtp_host and smtp_port and smtp_user and smtp_password:
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            msg = MIMEMultipart()
            msg["From"] = smtp_user
            msg["To"] = ", ".join(to_emails)
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))
            
            port = int(smtp_port)
            if port == 465:
                server = smtplib.SMTP_SSL(smtp_host, port)
                server.login(smtp_user, smtp_password)
                server.sendmail(smtp_user, to_emails, msg.as_string())
                server.close()
            else:
                server = smtplib.SMTP(smtp_host, port)
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.sendmail(smtp_user, to_emails, msg.as_string())
                server.close()
            return True, "Sent successfully via SMTP"
        except Exception as e:
            return False, f"Failed to send via SMTP: {e}"
            
    return False, "Simulated email dispatch (No API keys or SMTP configured)"

# --- Models ---
class ChatMessage(BaseModel):
    role: str = Field(..., max_length=10)
    text: str = Field(..., max_length=8000)

class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    language: str = Field(..., max_length=20)
    history: List[ChatMessage] = Field(default=[], max_length=30)

class PDFGenerateRequest(BaseModel):
    title: str = Field(..., max_length=200)
    text: str = Field(..., max_length=50000)

class FIRRequest(BaseModel):
    issue: str = Field(..., min_length=10, max_length=5000)
    state: str = Field(..., max_length=100)
    ps: str = Field(..., max_length=200)
    name: str = Field(..., max_length=200)
    category: Optional[str] = Field(None, max_length=50)
    category_fields: Optional[dict] = None

class TemplateRequest(BaseModel):
    template_type: str = Field(..., max_length=100)
    fields: dict

class BookLawyerRequest(BaseModel):
    lawyer_id: int
    client_name: str = Field(..., min_length=2, max_length=100)
    client_email: EmailStr = Field(..., max_length=255)
    client_phone: str = Field(..., min_length=10, max_length=15)
    date: str = Field(..., min_length=10, max_length=10)
    slot: str = Field(..., min_length=3, max_length=30)
    details: str = Field(..., max_length=1000)

class BnsCompareRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)

class ChatDocRequest(BaseModel):
    doc_text: str = Field(..., max_length=50000)
    query: str = Field(..., min_length=1, max_length=2000)
    language: str = Field(..., max_length=20)
    history: List[ChatMessage] = Field(default=[], max_length=30)

class PredictOutcomeRequest(BaseModel):
    offense: str = Field(..., max_length=500)
    narrative: str = Field(..., max_length=3000)
    evidence: List[str] = Field(default=[], max_length=20)
    prior_record: str = Field(..., max_length=500)
    jurisdiction: str = Field(..., max_length=100)
    language: str = Field(..., max_length=20)

class SimplifyTextRequest(BaseModel):
    text: str = Field(..., min_length=10, max_length=10000)
    target_language: str = Field(..., max_length=20)

class CaseSubscribeRequest(BaseModel):
    cnr: str = Field(..., min_length=10, max_length=30)
    email: EmailStr = Field(..., max_length=255)
    client_name: str = Field(..., min_length=2, max_length=100)
    language: str = Field("English", max_length=20)

class BnsLookupRequest(BaseModel):
    term: str = Field(default="", max_length=200)
    category: str = Field(default="", max_length=100)

# --- Endpoints ---

@app.get("/api/health")
def health_check():
    return {"status": "ok"}

@app.post("/api/chat", dependencies=[Depends(check_rate_limit_ai)])
async def chat_endpoint(req: ChatRequest):
    query = req.query
    language = req.language
    history = req.history[-10:] if req.history else []
    
    # Prompts
    if language == "Tamil":
        system_instruction = """System: நீங்கள் 'நீதி AI' — இந்திய சட்டத்தில் நிபுணத்துவம் வாய்ந்த AI சட்ட உதவியாளர்.
TASK:
1. இந்த கேள்வி இந்திய சட்டம், நீதிமன்றம், காவல்துறை, குற்றம், உரிமைகள் அல்லது சட்ட நடைமுறைகள் தொடர்பானதா?
2. இல்லை என்றால் சரியாக பதிலளிக்கவும்: "மன்னிக்கவும். நான் சட்டம் தொடர்பான கேள்விகளுக்கு மட்டுமே பதிலளிப்பேன்."
3. ஆம் என்றால்:
   கேள்வி முந்தைய உரையாடலின் தொடர்ச்சியா (Follow-up), ஒரு புதிய குற்றவியல் குற்றம் பற்றியதா, அல்லது சிவில்/நடைமுறை தலைப்பு பற்றியதா என்று ஆராயுங்கள்.
   
   A. பயனர் கேள்வி ஒரு தொடர் கேள்வி அல்லது உரையாடலின் தொடர்ச்சியாக இருந்தால் (எ.கா. 'இதற்கு எவ்வளவு ஆண்டுகள் சிறை?', 'ஜாமீன் கிடைக்குமா?', 'யார் புகார் செய்ய வேண்டும்?'):
      மேலே உள்ள விரிவான தலைப்புகள் மற்றும் பிரிவுகளை (B அல்லது C) மீண்டும் பயன்படுத்த வேண்டாம்.
      பதிலாக, முந்தைய உரையாடலின் பின்னணியை வைத்துக்கொண்டு, பயனர் கேட்ட குறிப்பிட்ட கேள்விக்கு நேரடியாகவும், உரையாடல் வடிவிலும் 2-4 வாக்கியங்களில் எளிய பதில் தரவும். ஒரு வழக்கறிஞர் உங்களிடம் நேரடியாகப் பேசுவது போன்ற மனித உணர்வுடன் பதில் இருக்க வேண்டும்.
   
   B. கேள்வி ஒரு புதிய குற்றவியல் குற்றம் பற்றியதாக இருந்தால் (எ.கா. திருட்டு, கொலை, ஏமாற்றுதல், தாக்குதல்):
      பின்வரும் தலைப்புகளில் விரிவான பதில் தரவும் (தலைப்புகள் மற்றும் ஈமோஜிகளை அப்படியே பயன்படுத்தவும்):
      **⚖️ சட்ட பிரிவுகள் (Applicable Legal Sections)**
      - பொருந்தும் BNS/IPC/BNSS பிரிவுகள்
      **🔍 குற்றத்தின் விளக்கம் (Offense Explained)**
      - குற்றத்தைப் பற்றி எளிய தமிழில் விளக்கவும்
      **⚠️ தண்டனை விவரங்கள் (Punishment Details)**
      - சிறைத்தண்டனை, அபராதம், பிணை (Bailable), காக்னிசபிள் (Cognizable) விவரங்கள்
      **✅ உங்கள் உரிமைகள் (Your Rights)**
      - பாதிக்கப்பட்டவர்/குற்றம் சாட்டப்பட்டவரின் உரிமைகள், எங்கு புகார் செய்யலாம்
      **📋 அடுத்த நடவடிக்கைகள் (Next Steps)**
      - step-by-step செய்ய வேண்டியவை
      
   C. கேள்வி சிவில் சட்டம், சட்ட நடைமுறைகள், குடும்ப சட்டம், வணிக சட்டம் அல்லது உரிமைகள் பற்றியதாக இருந்தால் (எ.கா. நுகர்வோர் புகார், உயில், நிறுவன பதிவு, சொத்து பதிவு):
      "குற்றத்தின் விளக்கம்" அல்லது "தண்டனை விவரங்கள்" போன்ற குற்றவியல் தலைப்புகளை பயன்படுத்த வேண்டாம்.
      பதிலாக, பின்வரும் தலைப்புகளில் விரிவான பதில் தரவும்:
      **⚖️ தொடர்புடைய சட்டங்கள் (Relevant Laws & Acts)**
      - தொடர்புடைய சட்டங்களை பட்டியலிடவும் (எ.கா. நுகர்வோர் பாதுகாப்பு சட்டம் 2019, இந்திய ஒப்பந்த சட்டம் 1872)
      **🔍 நடைமுறை / சட்ட விளக்கம் (Procedure / Topic Explained)**
      - சட்ட நடைமுறை அல்லது தலைப்பைப் பற்றி எளிய தமிழில் விளக்கவும்
      **✅ உங்கள் உரிமைகள் & தீர்வுகள் (Your Rights & Remedies)**
      - உங்களுக்கு உள்ள உரிமைகள், நஷ்டஈடு அல்லது தீர்வுகள்
      **📋 அடுத்த நடவடிக்கைகள் (Next Steps)**
      - எவ்வாறு புகார் செய்ய வேண்டும், காலவரம்பு, தேவையான ஆவணங்கள் போன்ற படிநிலைகள்"""
    else:
        system_instruction = """You are 'Needhi AI' — an expert AI Legal Assistant specializing in Indian Law.
TASK:
1. Is this related to Indian Law, Court, Police, Crime, Rights, or Legal Procedures?
2. IF NO: REPLY EXACTLY: "Sorry, I am designed to answer only legal questions."
3. IF YES:
   Analyze whether the query is a conversational follow-up referencing the history, a new Criminal Offense, or a General Legal/Civil/Procedural topic.
   
   A. IF THE QUERY IS A FOLLOW-UP QUESTION OR CONVERSATIONAL CONTINUATION (e.g., 'maximum years of jail for this', 'is it bailable?', 'who files this?', 'what should I do first?'):
      Do NOT output the full structured sections/headings (A or B) again.
      Instead, respond DIRECTLY and CONVERSATIONALLY in a brief, natural paragraph (2-4 sentences) answering the specific follow-up query while referencing the details discussed in the previous conversation history. Keep the tone helpful, direct, and conversational.
   
   B. IF THE QUERY IS A NEW CRIMINAL OFFENSE (e.g., theft, assault, murder, fraud, cheating):
      Provide a detailed structured response with EXACTLY the following headings (use emojis and bolding as shown):
      **⚖️ Applicable Legal Sections**
      - List relevant BNS/IPC/CrPC/BNSS sections
      **🔍 Offense Explained**
      - Clear explanation of the criminal offense
      **⚠️ Punishment Details**
      - Imprisonment, Fine, Bailable/Non-Bailable, Cognizable/Non-Cognizable details
      **✅ Your Rights**
      - Rights of the victim/accused, where to file the complaint
      **📋 Recommended Next Steps**
      - Step-by-step action plan
      
   C. IF THE QUERY IS ABOUT GENERAL LEGAL PROCEDURES, CIVIL LAW, FAMILY LAW, BUSINESS LAW, OR RIGHTS (e.g., consumer complaints, property registry, wills, corporate procedures, civil litigation):
      Do NOT output criminal headings like "Offense Explained" or "Punishment Details" as they are irrelevant for civil matters.
      Instead, provide a detailed, beautifully structured response with headings tailored to the civil/procedural topic:
      **⚖️ Relevant Laws & Acts**
      - Mention relevant acts (e.g., Consumer Protection Act 2019, Indian Contract Act 1872, etc.)
      **🔍 Procedure / Topic Explained**
      - Explain the legal concept, grounds, or eligibility criteria clearly.
      **✅ Your Rights & Remedies**
      - Detail what rights, remedies, compensation, or relief the party is entitled to.
      **📋 Recommended Next Steps**
      - Provide a detailed step-by-step guide on how to file, proceed, or register (including forums, timelines, and required documents)."""

    messages = []
    if history:
        for h in history:
            messages.append({
                "role": "user" if h.role == "user" else "model",
                "parts": [h.text]
            })
    messages.append({
        "role": "user",
        "parts": [query]
    })

    try:
        response, used_model = generate_gemini_content(
            messages,
            generation_config=genai.types.GenerationConfig(max_output_tokens=2048),
            stream=True,
            system_instruction=system_instruction
        )
        
        async def event_generator():
            try:
                for chunk in response:
                    if chunk.candidates and chunk.candidates[0].content.parts:
                        text = chunk.text
                        if text:
                            yield text
            except Exception as e:
                yield f"\n❌ [Stream interrupted: {str(e)}]"
                    
        return StreamingResponse(event_generator(), media_type="text/plain")
    except Exception as e:
        logger.exception("Error in chat_endpoint")
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")

@app.post("/api/analyze-doc", dependencies=[Depends(check_rate_limit_ai)])
async def analyze_document(
    file: UploadFile = File(...),
    question: Optional[str] = Form(None)
):
    try:
        # Enforce 25MB file size limit check (25 * 1024 * 1024 = 26,214,400 bytes)
        MAX_FILE_SIZE = 25 * 1024 * 1024
        
        # Check size if available on the UploadFile object
        if file.size is not None and file.size > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="File size exceeds the 25MB limit.")
            
        # Read in chunks to prevent memory exhaustion if file.size was not set
        file_bytes = b""
        chunk_size = 1024 * 1024  # 1MB chunks
        while True:
            chunk = await file.read(chunk_size)
            if not chunk:
                break
            file_bytes += chunk
            if len(file_bytes) > MAX_FILE_SIZE:
                raise HTTPException(status_code=413, detail="File size exceeds the 25MB limit.")
                
        # Validate magic bytes signature of the file
        detected_mime = None
        if file_bytes.startswith(b"%PDF"):
            detected_mime = "application/pdf"
        elif file_bytes.startswith(b"\x89PNG"):
            detected_mime = "image/png"
        elif file_bytes.startswith(b"\xff\xd8\xff"):
            detected_mime = "image/jpeg"
            
        if not detected_mime:
            raise HTTPException(
                status_code=400,
                detail="Unsupported or invalid file signature detected. Please upload a valid PDF, PNG or JPG."
            )
            
        extra_q = f" Also answer: {question}" if question else ""
        
        # Isolated system instruction for grounding
        system_instruction = (
            "You are Needhi AI, an Indian legal assistant. "
            "Your task is to analyze legal documents and provide a clear, structured overview. "
            "Identify the document type, key clauses under Indian law, rights/obligations, red flags, and recommended actions."
        )
        
        # Analyze PDF text
        if detected_mime == "application/pdf":
            doc_text = ""
            try:
                reader = pypdf.PdfReader(io.BytesIO(file_bytes))
                doc_text = "\n".join(page.extract_text() or "" for page in reader.pages)
            except Exception:
                doc_text = ""
                
            if len(doc_text.strip()) > 100:
                prompt = (
                    f"Analyze this legal document text. Make sure to address the following focus if provided: {extra_q}\n\n"
                    f"Document text:\n{doc_text[:12000]}"
                )
                response, _ = generate_gemini_content(
                    prompt, 
                    generation_config=genai.types.GenerationConfig(max_output_tokens=4096),
                    system_instruction=system_instruction
                )
                return {"analysis": response.text, "doc_text": doc_text}
            else:
                # Scanned PDF or text extraction failed: Fallback to native Gemini PDF analysis (with inline PDF data)
                pdf_part = {
                    "mime_type": "application/pdf",
                    "data": file_bytes
                }
                
                # Perform OCR to get doc_text
                try:
                    ocr_prompt = "Extract and transcribe all the text from this scanned PDF document as-is, without adding any remarks. Return only the extracted text."
                    ocr_response, _ = generate_gemini_content([pdf_part, ocr_prompt], generation_config=genai.types.GenerationConfig(max_output_tokens=2048))
                    doc_text = ocr_response.text
                except Exception:
                    doc_text = "Text extraction failed, but analysis is provided."

                prompt = f"Analyze this scanned legal PDF document. Make sure to address the following focus if provided: {extra_q}"
                response, _ = generate_gemini_content(
                    [pdf_part, prompt], 
                    generation_config=genai.types.GenerationConfig(max_output_tokens=4096),
                    system_instruction=system_instruction
                )
                return {"analysis": response.text, "doc_text": doc_text}
            
        # Analyze Image
        elif detected_mime in ["image/png", "image/jpeg"]:
            image = Image.open(io.BytesIO(file_bytes))
            
            # Perform OCR to get doc_text
            try:
                ocr_prompt = "Extract and transcribe all the text from this image as-is, without adding any remarks. Return only the extracted text."
                ocr_response, _ = generate_gemini_content([ocr_prompt, image], generation_config=genai.types.GenerationConfig(max_output_tokens=2048))
                doc_text = ocr_response.text
            except Exception:
                doc_text = "Text extraction failed, but analysis is provided."

            prompt = f"Analyze this legal document image. Make sure to address the following focus if provided: {extra_q}"
            response, _ = generate_gemini_content([prompt, image], system_instruction=system_instruction)
            return {"analysis": response.text, "doc_text": doc_text}
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format. Please upload PDF, PNG or JPG.")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error in analyze_document")
        raise HTTPException(status_code=500, detail="An internal error occurred during document analysis.")

@app.post("/api/bns-lookup", dependencies=[Depends(check_rate_limit_data)])
def bns_lookup(req: BnsLookupRequest):
    search_term = req.term.lower().strip()
    category = req.category
    
    # Load JSON database
    ipc_bns_path = os.path.join(DATA_DIR, "ipc_bns.json")
    if not os.path.exists(ipc_bns_path):
        return []
        
    try:
        with open(ipc_bns_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        logger.exception("Error reading ipc_bns.json")
        raise HTTPException(status_code=500, detail="Internal database error.")
        
    results = []
    for item in data:
        # Filter by category if specified
        if category and item["category"] != category:
            continue
            
        # Filter by search term
        if search_term:
            in_ipc = search_term in item["ipc"].lower()
            in_bns = search_term in item["bns"].lower()
            in_title = search_term in item["title"].lower()
            in_desc = search_term in item["description"].lower() or search_term in item["tamil_description"].lower()
            
            if in_ipc or in_bns or in_title or in_desc:
                results.append(item)
        else:
            results.append(item)
            
    return results

@app.post("/api/bns-compare-ai", dependencies=[Depends(check_rate_limit_ai)])
def bns_compare_ai(req: BnsCompareRequest):
    query_str = req.query.strip()
    if not query_str:
        return []

    system_instruction = """You are Needhi AI, an expert Indian legal archivist comparing the old Indian Penal Code (IPC) and the new Bharatiya Nyaya Sanhita (BNS) 2023.
Your task is to compare and see transition details for the queried offense.
Analyze the query, find the relevant sections, and provide one or more comparative card entries matching the schema below.

Each object in the returned JSON list must represent a compared section:
- ipc: the old IPC section number(s) (e.g. '144' or '302' or '378, 379')
- bns: the new BNS section number(s) (e.g. '111' or '103(1)' or '303') or 'Repealed'
- title: short title of the offense, combining English and Tamil (e.g. 'Murder (கொலை)' or 'Defamation (அவதூறு)')
- category: 'Body' or 'Property' or 'Women & Children' or 'Public Peace' or 'State Sovereignty' or 'General'
- description: simple description of the offense in English
- tamil_description: simple description of the offense in Tamil
- punishment: punishment details under BNS in English
- tamil_punishment: punishment details under BNS in Tamil
- changes: key transition changes or differences in English
- tamil_changes: key transition changes or differences in Tamil
- bail: 'Bailable' or 'Non-Bailable' or 'Bailable / Non-Bailable' or 'N/A'
- cognizable: 'Cognizable' or 'Non-Cognizable' or 'N/A'

Ensure the Tamil translations for titles, descriptions, punishments, and changes are accurate, formal, and natural.
If the queried section is repealed or de-criminalized, set 'bns' to 'Repealed'.
Return only a valid JSON array of objects. Do not wrap in markdown or backticks."""

    prompt = f"transition details for: '{query_str}'"

    try:
        response, _ = generate_gemini_content(
            prompt, 
            generation_config=genai.types.GenerationConfig(
                response_mime_type="application/json",
                max_output_tokens=2048
            ),
            system_instruction=system_instruction
        )
        
        resp_text = response.text.strip()
        if resp_text.startswith("```"):
            lines = resp_text.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines[-1].strip() == "```":
                lines = lines[:-1]
            resp_text = "\n".join(lines).strip()
            
        cards = json.loads(resp_text)
        if isinstance(cards, list) and len(cards) > 0:
            return cards
    except Exception as e:
        logger.exception("BNS AI comparison failed, falling back to local search")
        
    # Local fallback
    ipc_bns_path = os.path.join(DATA_DIR, "ipc_bns.json")
    if os.path.exists(ipc_bns_path):
        try:
            with open(ipc_bns_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            fallback_results = []
            search_lower = query_str.lower()
            for item in data:
                in_ipc = search_lower in item["ipc"].lower()
                in_bns = search_lower in item["bns"].lower()
                in_title = search_lower in item["title"].lower()
                in_desc = search_lower in item["description"].lower() or search_lower in item["tamil_description"].lower()
                
                if in_ipc or in_bns or in_title or in_desc:
                    fallback_results.append(item)
            return fallback_results
        except Exception:
            pass
            
    return []

@app.post("/api/cases/subscribe", dependencies=[Depends(check_rate_limit_data)])
def subscribe_to_case(req: CaseSubscribeRequest, request: Request):
    cnr = req.cnr.strip()
    email = req.email.strip().lower()
    client_name = req.client_name.strip()
    language = req.language
    
    if not cnr or not email or not client_name:
        raise HTTPException(status_code=400, detail="Missing required subscription fields")
        
    # Check if case exists to get the details
    cases_path = os.path.join(DATA_DIR, "cases.json")
    case_details = None
    if os.path.exists(cases_path):
        try:
            with open(cases_path, "r", encoding="utf-8") as f:
                cases = json.load(f)
            for c in cases:
                if c["cnr"].lower() == cnr.lower():
                    case_details = c
                    break
        except Exception as e:
            logger.exception("Failed to read cases database")
            raise HTTPException(status_code=500, detail="Internal database error.")
            
    if not case_details:
        raise HTTPException(status_code=404, detail="Case with this CNR number not found")
        
    # Save subscription (pending verification)
    subscriptions_path = os.path.join(DATA_DIR, "subscriptions.json")
    verification_token = os.urandom(16).hex()
    
    with FileLock("subscriptions"):
        subscriptions = []
        if os.path.exists(subscriptions_path):
            try:
                with open(subscriptions_path, "r", encoding="utf-8") as f:
                    subscriptions = json.load(f)
            except Exception:
                subscriptions = []
                
        # Check if already subscribed and verified
        already_subscribed = False
        for sub in subscriptions:
            dec_email = decrypt_field(sub.get("email", ""))
            if sub.get("cnr", "").lower() == cnr.lower() and dec_email.lower() == email:
                if sub.get("verified", True):
                    already_subscribed = True
                break
                
        if already_subscribed:
            return {
                "status": "already_subscribed",
                "message": "You are already subscribed to this case."
            }
            
        # Add or update subscription as pending
        subscriptions = [
            sub for sub in subscriptions
            if not (sub.get("cnr", "").lower() == cnr.lower() and decrypt_field(sub.get("email", "")).lower() == email)
        ]
        
        subscriptions.append({
            "cnr": cnr,
            "email": encrypt_field(email),
            "client_name": encrypt_field(client_name),
            "language": language,
            "verification_token": verification_token,
            "verified": False,
            "subscribed_at": datetime.now().isoformat(),
            "timestamp": datetime.now().isoformat()
        })
        
        try:
            with open(subscriptions_path, "w", encoding="utf-8") as f:
                json.dump(subscriptions, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.exception("Failed to save subscription")
            raise HTTPException(status_code=500, detail="Failed to save subscription due to database error.")
            
    # Send verification email containing verification link
    confirm_url = f"{request.base_url}api/cases/confirm-subscription?token={verification_token}"
    
    if language == "Tamil":
        subject = f"நீதி AI: வழக்கு கண்காணிப்பு சந்தா சரிபார்ப்பு - {cnr}"
        body = f"""அன்புள்ள {client_name},
  
{cnr} ({case_details.get('tamil_title', case_details.get('title'))}) வழக்குகான மின்னஞ்சல் விழிப்பூட்டல்களை சரிபார்க்க கீழே உள்ள இணைப்பை கிளிக் செய்யவும்:
{confirm_url}
  
இந்த கோரிக்கையை நீங்கள் செய்யவில்லை என்றால், இந்த மின்னஞ்சலை புறக்கணிக்கலாம்.
  
நன்றி,
நீதி AI சட்ட குழு.
"""
    else:
        subject = f"Needhi AI: Verify your Case Tracker Subscription - {cnr}"
        body = f"""Dear {client_name},
  
Please verify your subscription to email alerts for CNR: {cnr} ({case_details.get('title')}) by clicking the link below:
{confirm_url}
  
If you did not request this, you can ignore this email.
  
Thank you,
Needhi AI Legal Suite.
"""

    recipients = [{"email": email, "name": client_name}]
    try:
        email_sent, email_status = send_email_notification(recipients, subject, body)
    except Exception as e:
        logger.exception("Failed to send verification email")
        email_sent, email_status = False, "Failed to send email"
        
    return {
        "status": "success",
        "message": "Verification email sent successfully. Please confirm your subscription.",
        "email_sent": email_sent,
        "email_status": email_status
    }

@app.get("/api/cases/confirm-subscription")
def confirm_subscription(token: str):
    if not token:
        raise HTTPException(status_code=400, detail="Token is missing.")
        
    subscriptions_path = os.path.join(DATA_DIR, "subscriptions.json")
    if not os.path.exists(subscriptions_path):
        raise HTTPException(status_code=404, detail="No subscriptions found.")
        
    found_sub = None
    with FileLock("subscriptions"):
        try:
            with open(subscriptions_path, "r", encoding="utf-8") as f:
                subscriptions = json.load(f)
        except Exception:
            subscriptions = []
            
        for sub in subscriptions:
            if sub.get("verification_token") == token:
                sub["verified"] = True
                sub["verification_token"] = None
                found_sub = sub
                break
                
        if found_sub:
            try:
                with open(subscriptions_path, "w", encoding="utf-8") as f:
                    json.dump(subscriptions, f, indent=2, ensure_ascii=False)
            except Exception as e:
                logger.exception("Failed to update subscription status")
                raise HTTPException(status_code=500, detail="Internal server error.")
                
    if not found_sub:
        return Response(content="""
        <html>
        <head>
            <style>
                body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #0f172a; color: #f8fafc; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }
                .card { background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(10px); padding: 2.5rem; border-radius: 1rem; border: 1px solid rgba(255,255,255,0.1); max-width: 400px; text-align: center; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }
                h1 { color: #f43f5e; margin-bottom: 1rem; font-size: 1.75rem; }
                p { color: #cbd5e1; line-height: 1.5; font-size: 1rem; }
            </style>
        </head>
        <body>
            <div class="card">
                <h1>Verification Link Invalid</h1>
                <p>This verification link is invalid, expired, or has already been used.</p>
            </div>
        </body>
        </html>
        """, media_type="text/html")
        
    cnr = found_sub.get("cnr")
    email = decrypt_field(found_sub.get("email"))
    client_name = decrypt_field(found_sub.get("client_name"))
    language = found_sub.get("language")
    
    # Load case details
    cases_path = os.path.join(DATA_DIR, "cases.json")
    case_details = None
    if os.path.exists(cases_path):
        try:
            with open(cases_path, "r", encoding="utf-8") as f:
                cases = json.load(f)
            for c in cases:
                if c["cnr"].lower() == cnr.lower():
                    case_details = c
                    break
        except Exception:
            pass
            
    if case_details:
        case_title = case_details.get("title", cnr)
        case_title_tamil = case_details.get("tamil_title", case_title)
        
        if language == "Tamil":
            subject = f"நீதி AI: வழக்கு கண்காணிப்பு சந்தா உறுதிசெய்யப்பட்டது - {cnr}"
            body = f"""அன்புள்ள {client_name},
      
உங்கள் {cnr} ({case_title_tamil}) வழக்குகான மின்னஞ்சல் விழிப்பூட்டல்களுக்கு வெற்றிகரமாக குழுசேர்ந்துள்ளீர்கள்.
      
--- வழக்கு கண்காணிப்பு விவரங்கள் ---
வழக்கு தலைப்பு: {case_title_tamil}
நீதிமன்றம்: {case_details.get('tamil_court', case_details.get('court'))}
தற்போதைய நிலை: {case_details.get('current_stage_tamil', case_details.get('current_stage'))}
அடுத்த விசாரணை தேதி: {case_details.get('next_hearing')} (அறை: {case_details.get('courtroom')})
      
இந்த வழக்கில் புதிய தகவல்கள் அல்லது விசாரணை தேதிகள் புதுப்பிக்கப்படும்போது, {email} என்ற முகவரிக்கு மின்னஞ்சல் அனுப்பப்படும்.
      
நன்றி,
நீதி AI சட்ட குழு.
"""
        else:
            subject = f"Needhi AI: Case Tracker Subscription Confirmed - {cnr}"
            body = f"""Dear {client_name},
      
You have successfully subscribed to email alerts for CNR: {cnr} ({case_title}).
      
--- CASE TRACKER SUBSCRIPTION INFO ---
Case Title: {case_title}
Court: {case_details.get('court')}
Current Stage: {case_details.get('current_stage')}
Next Hearing Date: {case_details.get('next_hearing')} (Courtroom: {case_details.get('courtroom')})
      
You will receive automated notifications at {email} when the court logs new hearing stages or updates.
      
Thank you,
Needhi AI Legal Suite.
"""
        try:
            send_email_notification([{"email": email, "name": client_name}], subject, body)
        except Exception as e:
            logger.exception("Failed to send confirmation email after verification")
            
    return Response(content=f"""
    <html>
    <head>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #0f172a; color: #f8fafc; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }}
            .card {{ background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(10px); padding: 2.5rem; border-radius: 1rem; border: 1px solid rgba(255,255,255,0.1); max-width: 400px; text-align: center; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }}
            h1 {{ color: #10b981; margin-bottom: 1rem; font-size: 1.75rem; }}
            p {{ color: #cbd5e1; line-height: 1.5; font-size: 1rem; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h1>Subscription Confirmed!</h1>
            <p>Thank you, {client_name}. Your email alerts for case {cnr} have been successfully activated.</p>
        </div>
    </body>
    </html>
    """, media_type="text/html")

@app.get("/api/cases")
def get_cases(search: str = "", search_type: str = "CNR Number"):
    cases_path = os.path.join(DATA_DIR, "cases.json")
    if not os.path.exists(cases_path):
        return []
        
    with open(cases_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    search = search.strip().lower()
    if not search:
        return data
        
    results = []
    for case in data:
        if search_type == "CNR Number" and search in case["cnr"].lower():
            results.append(case)
        elif search_type == "Party Name" and (search in case["petitioner"].lower() or search in case["respondent"].lower()):
            results.append(case)
        elif search_type == "FIR Number" and search in case["case_no"].lower():
            results.append(case)
        elif search_type == "Advocate Name" and (search in case["petitioner_adv"].lower() or search in case["respondent_adv"].lower()):
            results.append(case)
            
    return results

@app.get("/api/lawyers")
def get_lawyers(specialization: str = "", city: str = "", search: str = ""):
    lawyers_path = os.path.join(DATA_DIR, "lawyers.json")
    if not os.path.exists(lawyers_path):
        return []
        
    with open(lawyers_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    results = []
    for lawyer in data:
        # Specialization filter
        if specialization and specialization.lower() not in lawyer["specialization"].lower():
            continue
            
        # City filter
        if city and city.lower() != lawyer["city"].lower():
            continue
            
        # Text search
        if search:
            search = search.lower()
            match = (
                search in lawyer["name"].lower() or
                search in lawyer["bio"].lower() or
                search in lawyer["specialization"].lower()
            )
            if not match:
                continue
                
        results.append(lawyer)
        
    return results

@app.post("/api/book-lawyer", dependencies=[Depends(check_rate_limit_data)])
def book_lawyer(req: BookLawyerRequest):
    # Validate date: must be today or in the future
    try:
        booking_date = datetime.strptime(req.date, "%Y-%m-%d").date()
        if booking_date < date.today():
            raise HTTPException(status_code=400, detail="Cannot book a consultation slot in the past.")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Expected YYYY-MM-DD.")

    # Load lawyers to validate ID and get details
    lawyers_path = os.path.join(DATA_DIR, "lawyers.json")
    if not os.path.exists(lawyers_path):
        raise HTTPException(status_code=500, detail="Lawyers database not found")
        
    with open(lawyers_path, "r", encoding="utf-8") as f:
        lawyers = json.load(f)
        
    lawyer = None
    for l in lawyers:
        if l["id"] == req.lawyer_id:
            lawyer = l
            break
            
    if not lawyer:
        raise HTTPException(status_code=404, detail="Lawyer not found")
        
    # Generate booking code
    booking_code = "ND-" + os.urandom(3).hex().upper()
    
    # Save booking to bookings.json under thread-safe lock with encrypted PII
    bookings_path = os.path.join(DATA_DIR, "bookings.json")
    with FileLock("bookings"):
        bookings = []
        if os.path.exists(bookings_path):
            try:
                with open(bookings_path, "r", encoding="utf-8") as f:
                    bookings = json.load(f)
            except Exception:
                bookings = []
                
        new_booking = {
            "code": booking_code,
            "lawyer_id": req.lawyer_id,
            "lawyer_name": lawyer["name"],
            "specialization": lawyer["specialization"],
            "client_name": encrypt_field(req.client_name),
            "client_email": encrypt_field(req.client_email),
            "client_phone": encrypt_field(req.client_phone),
            "date": req.date,
            "slot": req.slot,
            "details": encrypt_field(req.details),
            "timestamp": datetime.now().isoformat()
        }
        
        bookings.append(new_booking)
        
        try:
            with open(bookings_path, "w", encoding="utf-8") as f:
                json.dump(bookings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.exception("Failed to save booking")
            raise HTTPException(status_code=500, detail="Failed to save booking due to database error.")
        
    # Construct Client Email Content
    client_subject = f"Needhi AI: Legal Consultation Ticket - {booking_code}"
    client_body = f"""Dear {req.client_name},
 
Your legal consultation with {lawyer['name']} has been successfully scheduled.
 
--- CONSULTATION TICKET ---
Ticket Code: {booking_code}
Lawyer: {lawyer['name']} ({lawyer['specialization']})
Date: {req.date}
Time Slot: {req.slot}
Fee: ₹{lawyer['fee']} (Payable to the lawyer)
 
Client Contact Details:
Name: {req.client_name}
Phone: {req.client_phone}
Email: {req.client_email}
 
Advocate Contact Details:
Phone: {lawyer['phone']}
Email: {lawyer['email']}
City: {lawyer['city']}
 
Case Summary provided:
{req.details}
 
Thank you for choosing Needhi AI.
"""
    
    # Construct Advocate Email Content
    advocate_subject = f"Needhi AI: New Consultation Booking - {booking_code}"
    advocate_body = f"""Dear {lawyer['name']},
 
A new legal consultation has been scheduled with you by {req.client_name}.
 
--- CONSULTATION DETAILS ---
Ticket Code: {booking_code}
Date: {req.date}
Time Slot: {req.slot}
Fee: ₹{lawyer['fee']} (Collectable from the client)
 
Client Contact Details:
Name: {req.client_name}
Phone: {req.client_phone}
Email: {req.client_email}
 
Advocate Contact Details (Your Info):
Phone: {lawyer['phone']}
Email: {lawyer['email']}
City: {lawyer['city']}
 
Case Summary provided by client:
{req.details}
 
Thank you for using Needhi AI.
"""
    
    # Send email notifications separately
    client_recipients = [{"email": req.client_email, "name": req.client_name}]
    advocate_recipients = [{"email": lawyer["email"], "name": lawyer["name"]}]
    
    try:
        email_sent, email_status = send_email_notification(client_recipients, client_subject, client_body)
    except Exception:
        logger.exception("Failed to send client email notification")
        email_sent, email_status = False, "Failed to send email"
        
    try:
        send_email_notification(advocate_recipients, advocate_subject, advocate_body)
    except Exception:
        logger.exception("Failed to send advocate email notification")
        
    return {
        "status": "success",
        "booking_code": booking_code,
        "email_sent": email_sent,
        "email_status": email_status,
        "receipt": {
            "code": booking_code,
            "lawyer": lawyer["name"],
            "specialty": lawyer["specialization"],
            "date": req.date,
            "time": req.slot,
            "fee": lawyer["fee"],
            "phone": lawyer["phone"],
            "email": lawyer["email"],
            "email_status": email_status
        }
    }

@app.post("/api/generate-fir", dependencies=[Depends(check_rate_limit_ai)])
def generate_fir(req: FIRRequest):
    ps_line = f"Police Station: {req.ps}" if req.ps else "Police Station: ________________________"
    name_line = req.name if req.name else "________________________"
    
    category_instructions = ""
    valid_categories = {"Domestic Violence", "Cyber Fraud", "Property Dispute", "Motor Accident"}
    if req.category in valid_categories:
        fields_desc = ""
        if req.category_fields:
            fields_desc = "\n".join([f"- {k}: {v}" for k, v in req.category_fields.items() if v])
        
        category_instructions = f"\nINCIDENT CATEGORY: {req.category}\n"
        if fields_desc:
            category_instructions += f"Category-specific structured fields provided by user:\n{fields_desc}\n"
            
        category_instructions += "\nCRITICAL: Since this is a " + req.category + " case, you MUST explicitly cite the following sections in your draft under 'SPECIFIC OFFENCES & LEGAL SECTIONS':\n"
        
        if req.category == "Domestic Violence":
            category_instructions += (
                "- Cruelty by Husband or Relatives: Section 85 of BNS (formerly Section 498A of IPC)\n"
                "- Voluntarily causing hurt: Section 115(2) of BNS (formerly Section 323 of IPC)\n"
                "- Criminal Intimidation: Section 351 of BNS (formerly Section 506 of IPC)\n"
            )
        elif req.category == "Cyber Fraud":
            category_instructions += (
                "- Cheating: Section 318 of BNS (formerly Section 420 of IPC)\n"
                "- Cheating by personation: Section 319 of BNS (formerly Section 419 of IPC)\n"
                "- Cheating by personation using computer resource: Section 66D of the Information Technology Act, 2000 (IT Act)\n"
            )
        elif req.category == "Property Dispute":
            category_instructions += (
                "- Criminal Trespass: Section 329 of BNS (formerly Section 447 of IPC)\n"
                "- Mischief causing damage: Section 324(4) of BNS (formerly Section 427 of IPC)\n"
                "- Criminal Conspiracy: Section 61 of BNS (formerly Section 120B of IPC)\n"
            )
        elif req.category == "Motor Accident":
            category_instructions += (
                "- Rash driving on a public way: Section 281 of BNS (formerly Section 279 of IPC)\n"
                "- Causing hurt or grievous hurt by rash/negligent act: Section 125A or 125B of BNS (formerly Section 337/338 of IPC)\n"
                "- Causing death by negligence: Section 106(1) of BNS (formerly Section 304A of IPC) [Only include if there is a fatality/death mentioned in the narrative]\n"
            )
            
    system_instr@app.post("/api/generate-template", dependencies=[Depends(check_rate_limit_ai)])
def generate_template(req: TemplateRequest):
    special_guidelines = ""
    tt = req.template_type
    
    if tt == "Rent Agreement":
        special_guidelines = (
            "- The document MUST follow the standard structure of a Rent Agreement/Lease Deed in India.\n"
            "- Explicitly state at the top: 'THIS DEED OF RENT AGREEMENT is executed on this [Day] day of [Month], [Year] on a Non-Judicial Stamp Paper of Rs. 100/-' or 'Rs. 200/-'.\n"
            "- Structure clearly into sections:\n"
            "  1. PARTIES: Describe Landlord (First Party) and Tenant (Second Party), including full names, ages, parent's names, and addresses.\n"
            "  2. DEMISED PREMISES: Full physical description of the leased property.\n"
            "  3. DURATION AND LEASE TERM: State the period (e.g. 11 months) and the commencement date.\n"
            "  4. RENT AND PAYMENTS: Clear monthly rent amount (in figures and words), due date, mode of payment, and utility/maintenance responsibilities.\n"
            "  5. SECURITY DEPOSIT: Interest-free security deposit amount, terms of refund, and deductions.\n"
            "  6. TENANT'S COVENANTS: Proper maintenance of premises, no illegal activities, no structural alterations, and permitting landlord visits for inspection.\n"
            "  7. TERMINATION AND NOTICE PERIOD: Notice period required by either party (usually 1 or 2 months) to vacate the premises before expiry.\n"
            "  8. RENEWAL TERMS: Conditions under which the agreement can be renewed, specifying standard escalation percentage (usually 5% to 10%).\n"
            "  9. DISPUTE RESOLUTION (ARBITRATION): Explicitly state: 'Any dispute arising out of or in connection with this agreement shall be referred to arbitration in accordance with the provisions of the Arbitration and Conciliation Act, 1996. The seat and venue of arbitration shall be Chennai, Tamil Nadu, and proceedings shall be in English.'\n"
            "  10. JURISDICTION: Govern under local laws of the State (e.g., Tamil Nadu Regulation of Rights and Responsibilities of Landlords and Tenants Act, 2017) and designate local civil courts.\n"
            "- SIGNATURE BLOCKS: Include signature spaces for 'LANDLORD (First Party)', 'TENANT (Second Party)', 'WITNESS 1 (Name, Signature, Address)', and 'WITNESS 2 (Name, Signature, Address)'.\n"
        )
    elif tt == "Legal Notice":
        special_guidelines = (
            "- The document must represent a formal legal notice sent by an advocate or individual.\n"
            "- Header must include: 'REGISTERED POST WITH ACKNOWLEDGEMENT DUE / SPEED POST' and the date.\n"
            "- Addressed formally: 'To, [Receiver Name], residing at [Receiver Address]'.\n"
            "- Subject Line: Formally phrase the subject to clearly state the cause of action, e.g., 'SUBJECT: Legal Notice under Section 138 of the Negotiable Instruments Act, 1881 / for breach of contract / recovery of dues'.\n"
            "- INSTRUCTIONS / PREAMBLE: 'Under instructions from and on behalf of my client [Sender Name], residing at [Sender Address], I hereby serve you with the following Legal Notice:'\n"
            "- CHRONOLOGICAL NARRATIVE: Outline the facts of the dispute or transaction chronologically.\n"
            "- BREACH & DEFAULT DETAILS: Clearly state the breach of contract, non-payment, or offense committed by the receiver. Cite relevant acts where applicable (e.g., Indian Contract Act 1872, or Negotiable Instruments Act 1881).\n"
            "- DEMAND FOR COMPLIANCE: Direct the receiver to pay the outstanding amount or perform the requested action within 15 days (standard Indian timeline) or 30 days of receiving this notice.\n"
            "- LEGAL ACTION WARNING: State clearly that if the receiver fails to comply within the specified time, my client will initiate appropriate civil and/or criminal proceedings in the competent courts of jurisdiction at the receiver's sole cost, risk, and responsibility.\n"
            "- SIGNATURE BLOCKS: 'Sincerely, [Sender/Advocate Name], Advocate / Sender'.\n"
        )
    elif tt == "Affidavit":
        special_guidelines = (
            "- The document must represent a formal Affidavit for declaration/affirmation.\n"
            "- Header: 'BEFORE THE OATH COMMISSIONER / NOTARY PUBLIC AT [City/State]'\n"
            "- Preamble/Deponent Details: 'I, [Name], [Son/Daughter/Wife] of [Parent/Husband Name], aged about [Age] years, residing at [Address], do hereby solemnly affirm and state on oath as under:'\n"
            "- NUMBERED PARAGRAPHS: Number each declaration paragraph (1, 2, 3...) detailing the specific facts/statements being attested.\n"
            "- VERIFICATION CLAUSE: The verification must be absolute and precise:\n"
            "  'VERIFICATION: Verified at [Place] on this [Date] day of [Month], [Year], that the contents of paragraphs 1 to [N] of the above affidavit are true and correct to the best of my knowledge and belief, and nothing material has been concealed therefrom.'\n"
            "- SIGNATURE & ATTESTATION:\n"
            "  - Signature of the Deponent: 'DEPONENT: ________________________'\n"
            "  - Attestation block for Oath Commissioner / Notary Public: 'Solemnly affirmed and signed before me on this ____ day of ________, 20__ at _______. Notary Public / Oath Commissioner.'\n"
        )
    elif tt == "Bail Application":
        special_guidelines = (
            "- The document must represent a formal bail petition filed in court.\n"
            "- Court Header: 'IN THE COURT OF THE SESSIONS JUDGE / CHIEF METROPOLITAN MAGISTRATE AT [Location]'\n"
            "- Case Details Block:\n"
            "  'In the Matter of:\n"
            "   State vs. [Accused Name]\n"
            "   FIR No: [Case Number/FIR No]\n"
            "   Under Section(s): [BNS/IPC Sections]\n"
            "   Police Station: [Police Station]'\n"
            "- Application Title: 'APPLICATION FOR BAIL UNDER SECTION 480/482 OF THE BHARATIYA NAGARIK SURAKSHA SANHITA, 2023 (BNSS) (formerly Section 437/439 of the Code of Criminal Procedure, 1973)'\n"
            "- PETITIONER DETAILS: 'The humble petition of the Accused/Petitioner above named most respectfully showeth:'\n"
            "- DETAILED GROUNDS FOR BAIL:\n"
            "  1. Provide a list of legal grounds (e.g. innocence, false implication, lack of criminal history, ready to abide by bail conditions, ready to submit sureties, deep roots in society, no flight risk, no risk of tampering with prosecution witnesses/evidence).\n"
            "  2. Structure each ground in a separate, numbered paragraph.\n"
            "- PRAYER: Formal prayer requesting: 'Wherefore, it is most respectfully prayed that this Hon'ble Court may be pleased to release the Accused/Petitioner on bail on such terms and conditions as this Court may deem fit in the interest of justice.'\n"
            "- SIGNATURE BLOCKS: 'Co-signed by Accused/Petitioner' and 'Through: [Advocate/Counsel Signature]'.\n"
            "- VERIFICATION AFFIDAVIT: Include a short verification affidavit of the deponent/relative who is signing on behalf of the accused.\n"
        )
    elif tt == "Consumer Complaint":
        special_guidelines = (
            "- The document must follow the structure of a formal consumer complaint filed under the Consumer Protection Act, 2019.\n"
            "- Court Header: 'BEFORE THE DISTRICT CONSUMER DISPUTES REDRESSAL COMMISSION AT [City]'\n"
            "- Parties description:\n"
            "  '[Complainant Name], residing at [Complainant Address] ... COMPLAINANT\n"
            "   VERSUS\n"
            "   [Opposite Party Name], located at [Opposite Party Address] ... OPPOSITE PARTY'\n"
            "- Complaint Title: 'COMPLAINT UNDER SECTION 35 OF THE CONSUMER PROTECTION ACT, 2019'\n"
            "- SECTIONS & FACTS OF THE COMPLAINT:\n"
            "  1. Transaction Details: Purchase/booking details, amount paid, transaction date.\n"
            "  2. DEFICIENCY IN SERVICE/DEFECT IN GOODS: Explicitly describe the defects, deficiency, failure of warranty, or unfair trade practice.\n"
            "  3. Correspondence/Notice: Summary of communications and notices sent prior to filing the complaint.\n"
            "  4. Cause of Action: When the cause of action arose.\n"
            "  5. Jurisdiction: Explaining why the Commission has territorial and pecuniary jurisdiction.\n"
            "- PRAYER/RELIEF SOUGHT: State clearly the specific reliefs prayed for:\n"
            "  a) Refund of the principal amount with interest.\n"
            "  b) Compensation for mental agony, harassment, and business loss.\n"
            "  c) Litigation and filing expenses.\n"
            "  d) Any other relief this Hon'ble Commission deems fit.\n"
            "- VERIFICATION CLAUSE:\n"
            "  'VERIFICATION: I, [Complainant Name], do hereby verify that the contents of paragraphs 1 to [N] are true and correct to my knowledge and belief.'\n"
            "- SIGNATURE BLOCKS: 'COMPLAINANT: ________________________' and 'Through Counsel: ________________________'.\n"
            "- INDEX OF DOCUMENTS: List placeholders for documents annexed (Invoice, warranty card, notices, postal receipts, etc.).\n"
        )
    elif tt == "Non-Disclosure Agreement (NDA)":
        special_guidelines = (
            "- The document must represent a formal Mutual/One-Way Non-Disclosure Agreement (NDA) under the Indian Contract Act, 1872.\n"
            "- Title: 'MUTUAL NON-DISCLOSURE AGREEMENT'\n"
            "- Preamble: Executed on [Date] between Disclosing Party [Disclosing Party Name] and Receiving Party [Receiving Party Name].\n"
            "- Core clauses:\n"
            "  1. DEFINITION OF CONFIDENTIAL INFORMATION: Technical, financial, and proprietary information.\n"
            "  2. NON-DISCLOSURE OBLIGATIONS: Use of confidential information solely for the Purpose. Duty to protect with standard of care.\n"
            "  3. EXCLUSIONS FROM CONFIDENTIALITY: Information already public, independent development, or legal order.\n"
            "  4. TERM AND DURATION: Confidentiality obligations persist for [Duration] years from disclosure or agreement termination.\n"
            "  5. REMEDIES: Injunctions, damages, and specific performance.\n"
            "  6. GOVERNING LAW & JURISDICTION: Governance under the Indian Contract Act, 1872, with exclusive jurisdiction of courts in [Jurisdiction/City].\n"
            "- SIGNATURES: Signature blocks for both parties, including witness signature areas.\n"
        )
    elif tt == "Promissory Note":
        special_guidelines = (
            "- The document must represent a legally binding Promissory Note under the Negotiable Instruments Act, 1881.\n"
            "- Title: 'PROMISSORY NOTE'\n"
            "- Stamp duty note: Include a designated box or placeholder representing the 'REVENUE STAMP' of appropriate value.\n"
            "- Core Promise: 'ON DEMAND / On [Due Date], I, [Borrower Name], son/daughter of ________________, residing at [Borrower Address], hereby unconditionally promise to pay to [Lender Name], son/daughter of ________________, residing at [Lender Address], or to order, the sum of Rs. [Principal Amount] (Rupees ________________________ only) with interest at the rate of [Interest Rate]% per annum from the date hereof until repayment.'\n"
            "- Witness areas: Include witness 1 and witness 2 signature fields.\n"
            "- Signature of the Borrower: Place it directly across the revenue stamp placeholder.\n"
        )
    elif tt == "Power of Attorney":
        special_guidelines = (
            "- The document must represent a General/Special Power of Attorney (GPA/SPA) under the Powers of Attorney Act, 1882.\n"
            "- Title: 'GENERAL POWER OF ATTORNEY / SPECIAL POWER OF ATTORNEY'\n"
            "- Executed on a non-judicial stamp paper of appropriate value.\n"
            "- Preamble: 'KNOW ALL MEN BY THESE PRESENTS that I, [Principal Name], residing at [Principal Address], do hereby nominate, constitute, and appoint [Attorney Name], residing at [Attorney Address], as my true and lawful Attorney in my name and on my behalf to perform all or any of the following acts...'\n"
            "- SCOPE OF POWERS: Specific list of powers (e.g. sale, lease, mortgage, court filings, signing deeds).\n"
            "- SCHEDULE OF PROPERTY: A section describing the boundaries and details of the property under power.\n"
            "- REVOCATION AND INDEMNITY: Clauses governing the validity and indemnity of acts done by the Attorney.\n"
            "- SIGNATURES: Signed by the Principal, accepted by the Attorney, and attested by two witnesses.\n"
        )
    elif tt == "Counter-Notice":
        special_guidelines = (
            "- The document must represent a formal reply/counter-notice responding to a legal notice received.\n"
            "- Header must include: 'REGISTERED POST WITH ACKNOWLEDGEMENT DUE / SPEED POST' and the date.\n"
            "- Addressed formally to the sender's advocate or the sender: 'To, [Opposite Party / Advocate Name], at [Opposite Party Address]'.\n"
            "- Reference line: 'SUBJECT: Reply to the Legal Notice dated [Original Notice Date] regarding [Original Notice Subject]'.\n"
            "- Preamble: 'Under instructions from and on behalf of my client [Sender Name], residing at [Sender Address], I hereby reply to your legal notice as follows:'\n"
            "- Numbered Paragraphs of Denials: Chronologically deny the allegations in the original notice (deny breach of contract, deny outstanding liability, etc.). State clearly that the claims are false, frivolous, and vexatious.\n"
            "- Specific Defenses: Describe the client's version of facts, details of payments made, compliance with agreements, or other legal defenses.\n"
            "- Legal Warning: Demand that the opposite party withdraw the notice unconditionally within 15 days of receipt, failing which my client will initiate legal action for harassment, damages, and litigation expenses under civil and criminal laws at your cost.\n"
            "- SIGNATURE BLOCK: 'Sincerely, [Sender/Advocate Name], Advocate / Reply Sender'.\n"
        )
    elif tt == "RTI Application":
        special_guidelines = (
            "- The document must represent a formal application under Section 6(1) of the Right to Information Act, 2005.\n"
            "- Addressed to: 'To, The Public Information Officer (PIO), [Public Authority Name], [Public Authority Address]'.\n"
            "- Title: 'APPLICATION UNDER SECTION 6(1) OF THE RIGHT TO INFORMATION ACT, 2005'\n"
            "- Particulars of the applicant: Name, address, contact details.\n"
            "- Particulars of information sought: Clearly list the details/documents required in numbered queries (1, 2, 3...).\n"
            "- Specify the period of information required (e.g., Financial Year 2024-25).\n"
            "- Citizenship declaration: 'I hereby declare that I am a citizen of India.'\n"
            "- Application Fee: Mention payment details of the ₹10 fee (e.g. IPO No. / Demand Draft No. / Cash Receipt No.: ________________________, or state if applicant belongs to BPL category and is exempt).\n"
            "- SIGNATURE BLOCK: 'Signature of Applicant: ________________________, Place: ________________________, Date: ________________________'.\n"
        )
    elif tt == "Police Commissioner Complaint":
        special_guidelines = (
            "- The document must represent a formal complaint addressed to the Commissioner of Police for escalation.\n"
            "- Reference Section 173(4) of the Bharatiya Nagarik Suraksha Sanhita, 2023 (BNSS) (formerly Section 154(3) of the CrPC) for reporting police inaction at the local station level.\n"
            "- Addressed to: 'To, The Commissioner of Police, [Office Address / City]'.\n"
            "- Subject: 'SUBJECT: Escalation Complaint under Section 173(4) of the BNSS, 2023, regarding refusal/failure of local Police Station [Local PS Name] to register an FIR for [Offense Subject].'\n"
            "- Preamble: Detail the complainant's identity (Name, age, parentage, address).\n"
            "- Chronology: Details of the original offence committed, the subsequent complaint submitted to the local Police Station on [Local Complaint Date], and the failure/inaction of the local officers to register an FIR.\n"
            "- Relief: Pray/request the Commissioner to look into the matter, direct the registration of an FIR, and initiate a fair investigation.\n"
            "- SIGNATURE BLOCK: 'Place: ________________________, Date: ________________________, Complainant Signature: ________________________'.\n"
        )
    elif tt == "Banking Ombudsman Complaint":
        special_guidelines = (
            "- The document must follow the format of a complaint under the Reserve Bank of India (Integrated Ombudsman Scheme), 2021.\n"
            "- Addressed to: 'To, The Banking Ombudsman, Reserve Bank of India, [Ombudsman City/Address]'.\n"
            "- Subject: 'SUBJECT: Complaint under RBI Integrated Ombudsman Scheme, 2021 against [Bank Name] Branch [Bank Branch] for deficiency in service regarding [Grievance Issue].'\n"
            "- Details of complainant: Name, Address, Account Number.\n"
            "- Ground of Complaint: Details of bank's failure (e.g. unauthorized transactions, debit card fraud, failed ATM transaction not refunded, delay in loan/pension processing).\n"
            "- Pre-requisite condition: State that a written representation was submitted to the bank on [Complaint to Bank Date] (which is at least 30 days prior, or reply was unsatisfactory).\n"
            "- Declaration: 'I hereby declare that this matter has not been filed/decided before any other court, Consumer Commission, or forum.'\n"
            "- Relief sought: Refund of amount (₹[Amount]), compensation for mental agony, and interest.\n"
            "- SIGNATURE BLOCK: 'Signature of Complainant: ________________________, Date: ________________________'.\n"
        )
    elif tt == "RERA Complaint":
        special_guidelines = (
            "- The document must follow the structure of a formal complaint filed under Section 31 of the Real Estate (Regulation and Development) Act, 2016 (RERA).\n"
            "- Addressed to: 'BEFORE THE REAL ESTATE REGULATORY AUTHORITY AT [State/City]'.\n"
            "- Parties: '[Complainant Name] ... COMPLAINANT versus [Builder/Promoter Name] ... RESPONDENT'.\n"
            "- Subject: 'COMPLAINT UNDER SECTION 31 OF THE REAL ESTATE (REGULATION & DEVELOPMENT) ACT, 2016'.\n"
            "- Core details: RERA registration number of project [RERA Project Reg No], Unit/Flat number [Unit Number], total cost [Total Flat Cost], amount paid till date [Amount Paid].\n"
            "- Nature of grievance: Describe details of violation by promoter (e.g. delay in handing over possession, lack of amenities, structural defects, failure to execute builder-buyer agreement).\n"
            "- Relief claimed: Refund of payment with interest, delay interest compensation, or immediate possession.\n"
            "- Verification: A standard verification statement signed by the complainant.\n"
            "- SIGNATURE BLOCK: 'Signature of Complainant: ________________________, Date: ________________________'.\n"
        )


    prompt = f"""You are Needhi AI, an expert Indian legal assistant.
Generate a formal, highly accurate, and legally valid {tt} document for India.

Here are the specific details to include in the document:
{req.fields}

Template-Specific Drafting Instructions:
{special_guidelines}

General Instructions:
1. For any detail in the details list that is provided, insert it directly into its respective position in the document.
2. For any detail/field that is empty, blank, or not provided (e.g., empty string ""), represent it in the document as a clearly labeled blank fillable underline (e.g., "________________________") so that it can be printed and filled in manually.
3. Do NOT use brackets or text placeholders like "[Landlord Name]", "[Insert Date]", or "<Tenant Name>" for missing info; use actual underlines like "________________________" with a clear label preceding it (e.g., "Landlord Name: ________________________").
4. Ensure the document has all standard legally binding clauses, a proper header, sections, covenants, witness signatures, deponent signatures, or verification sections as appropriate.
5. Use formal, professional, and precise legal language. Do not output any conversational text or metadata outside of the draft itself.
"""

    try:
        response, _ = generate_gemini_content(prompt, generation_config=genai.types.GenerationConfig(max_output_tokens=2048))
        return {"draft": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate-pdf")
def generate_pdf(req: PDFGenerateRequest):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_margins(15, 15, 15)
        
        reg_font = get_tamil_font(bold=False)
        bold_font = get_tamil_font(bold=True)
        has_custom_font = reg_font is not None and bold_font is not None
        
        if has_custom_font:
            pdf.add_font("NotoSansTamil", "", reg_font)
            pdf.add_font("NotoSansTamil", "B", bold_font)
            font_family = "NotoSansTamil"
        else:
            font_family = "Helvetica"
            
        pdf.set_font(font_family, "B", 14 if has_custom_font else 16)
        pdf.set_text_color(30, 30, 60)
        
        # Clean title & write
        clean_title = clean_pdf_text(req.title, has_custom_font)
        pdf.cell(0, 10, clean_title, align="C")
        pdf.ln(10)
        pdf.set_font(font_family, "", 9)
        pdf.set_text_color(120, 120, 140)
        pdf.cell(0, 6, f"Generated: {datetime.now().strftime('%d %b %Y, %I:%M %p')} | Needhi AI Legal Suite", align="C")
        pdf.ln(6)
        pdf.set_draw_color(201, 168, 76)
        pdf.set_line_width(0.5)
        pdf.line(15, pdf.get_y(), 195, pdf.get_y())
        pdf.ln(6)
        
        pdf.set_font(font_family, "", 10)
        pdf.set_text_color(30, 30, 30)
        
        # Clean text lines & write
        lines = req.text.split("\n")
        for line in lines:
            if not line.strip():
                pdf.ln(4)
                continue
            
            # Format markdown headers in text
            if line.strip().startswith("**") and line.strip().endswith("**"):
                pdf.set_font(font_family, "B", 10)
                clean_line = clean_pdf_text(line.replace("**", ""), has_custom_font)
                pdf.multi_cell(0, 6, clean_line, new_x="LMARGIN", new_y="NEXT")
                pdf.set_font(font_family, "", 10)
            elif line.strip().startswith("###"):
                pdf.set_font(font_family, "B", 11)
                clean_line = clean_pdf_text(line.replace("###", ""), has_custom_font)
                pdf.multi_cell(0, 6, clean_line, new_x="LMARGIN", new_y="NEXT")
                pdf.set_font(font_family, "", 10)
            else:
                clean_line = clean_pdf_text(line, has_custom_font)
                pdf.multi_cell(0, 5.5, clean_line, new_x="LMARGIN", new_y="NEXT")
                
        pdf_bytes = pdf.output()
        return Response(content=bytes(pdf_bytes), media_type="application/pdf", headers={
            "Content-Disposition": "attachment; filename=Needhi_Document.pdf"
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat-doc", dependencies=[Depends(check_rate_limit_ai)])
async def chat_doc_endpoint(req: ChatDocRequest):
    doc_text = req.doc_text
    query = req.query
    language = req.language
    history = req.history[-10:] if req.history else []
    
    history_block = ""
    if history:
        if language == "Tamil":
            history_block = "\n".join(
                f"{'பயனர்' if h.role=='user' else 'AI'}: {h.text}" for h in history
            )
            history_block = f"\nமுந்தைய உரையாடல்:\n{history_block}\n"
        else:
            history_block = "\n".join(
                f"{'User' if h.role=='user' else 'AI'}: {h.text}" for h in history
            )
            history_block = f"\nPrevious conversation history:\n{history_block}\n"

    if language == "Tamil":
        system_instruction = "நீங்கள் 'நீதி AI' — இந்திய சட்டத்தில் நிபுணத்துவம் வாய்ந்த AI சட்ட உதவியாளர். பயனர் வழங்கிய சட்ட ஆவணத்தின் பின்னணியில் இருந்து பயனரின் கேள்விக்கு நேரடியாகவும், தெளிவாகவும் எளிய தமிழில் பதிலளிக்கவும்."
        prompt = f"""ஆவணத்தின் உரை (Document Text):
--- ஆவணத்தின் உரை (Document Text) ---
{doc_text[:12000]}
--- முடிவு ---

{history_block}
பயனர் கேள்வி: '{query}'

பணி (TASK):
ஆவணத்தின் பின்னணியில் இருந்து பயனரின் கேள்விக்கு எளிய தமிழில் பதிலளிக்கவும். தேவைப்பட்டால் ஆவணத்தின் குறிப்பிட்ட பிரிவுகள் அல்லது ஷரத்துக்களை சுட்டிக்காட்டவும். ஆவணத்தில் இல்லாத தகவலைப் பற்றி கேள்வி இருந்தால், 'கொடுக்கப்பட்ட ஆவணத்தில் இதைப் பற்றிய தகவல்கள் இல்லை' என்று கூறிவிட்டு பொதுவான சட்ட பின்னணியை விளக்கவும்."""
    else:
        system_instruction = "You are 'Needhi AI' — an expert AI Legal Assistant specializing in Indian Law. Answer the user's question directly, clearly, and concisely in English, using the context of the uploaded document."
        prompt = f"""Here is the text of the document:
--- DOCUMENT START ---
{doc_text[:12000]}
--- DOCUMENT END ---

{history_block}
User Query: '{query}'

TASK:
Answer the user's question using the context of the uploaded document. Reference specific clauses or sections of the document where relevant. If the question is not answerable from the document, state that clearly, but provide general legal information if applicable."""

    try:
        response, used_model = generate_gemini_content(
            prompt,
            generation_config=genai.types.GenerationConfig(max_output_tokens=2048),
            stream=True,
            system_instruction=system_instruction
        )
        
        async def event_generator():
            try:
                for chunk in response:
                    if chunk.candidates and chunk.candidates[0].content.parts:
                        text = chunk.text
                        if text:
                            yield text
            except Exception as e:
                yield f"\n❌ [Stream interrupted: {str(e)}]"
                    
        return StreamingResponse(event_generator(), media_type="text/plain")
    except Exception as e:
        logger.exception("Error in chat_doc_endpoint")
        raise HTTPException(status_code=500, detail="An internal error occurred during document chat.")

@app.post("/api/predict-outcome", dependencies=[Depends(check_rate_limit_ai)])
def predict_outcome(req: PredictOutcomeRequest):
    evidence_list = ", ".join(req.evidence) if req.evidence else "No direct evidence specified"
    
    if req.language == "Tamil":
        system_instruction = "நீங்கள் ஒரு இந்திய சட்ட நிபுணர் மற்றும் வழக்கறிஞர். பயனர் வழங்கிய வழக்குகளின் விவரங்களின் அடிப்படையில் அதன் சட்டபூர்வ விளைவுகளை துல்லியமாக கணிக்கவும்."
        prompt = f"""வழக்கின் விவரங்கள்:
- குற்றம்/சட்ட பிரிவு: {req.offense}
- நடந்த சம்பவம்: {req.narrative}
- ஆதாரங்கள்: {evidence_list}
- முந்தைய குற்ற பின்னணி: {req.prior_record}
- அதிகார வரம்பு (மாநிலம்): {req.jurisdiction}

பணி:
கீழ்க்கண்ட விவரங்களுடன் ஒரு விரிவான சட்டபூர்வ கணிப்பு அறிக்கையை எளிய தமிழில் தயார் செய்க:
1. **ஜாமீன் பெறுவதற்கான வாய்ப்பு (Bail Probability)**: (உயர் / நடுத்தர / குறைந்த - அதற்கான காரணங்களுடன்)
2. **தண்டனை அல்லது அபராதம் (Likely Sentencing / Penalties)**: (BNS/IPC பிரிவுகளின்படி தண்டனை விவரம் மற்றும் அபராதம்)
3. **வழக்கின் பலம் (Case Strength)**: (பலமான வழக்கு / நடுத்தரம் / பலவீனமானது - ஆதாரங்களின் அடிப்படையில் பகுப்பாய்வு)
4. **முக்கிய சாதக/பாதக காரணிகள் (Key Factors & Risks)**
5. **சட்டபூர்வ மறுப்புரை (Disclaimer)**: "மறுப்புரை: இது AI தொழில்நுட்பத்தால் உருவாக்கப்பட்ட ஒரு தற்காலிக கணிப்பு மட்டுமே. இது முறையான சட்ட ஆலோசனையாக கருதப்படக் கூடாது. உங்கள் வழக்கிற்கு தகுதியான வழக்கறிஞரை அணுகவும்."
"""
    else:
        system_instruction = "You are an expert Indian legal archivist and counsel. Predict the likely legal outcomes based on the provided case details."
        prompt = f"""Case Parameters:
- Offense/Dispute: {req.offense}
- Factual Narrative: {req.narrative}
- Evidence Available: {evidence_list}
- Prior Criminal Record: {req.prior_record}
- Jurisdiction (State): {req.jurisdiction}

TASK:
Generate a detailed, objective, and structured case outcome prediction report containing:
1. **Bail Probability**: (High / Medium / Low with detailed reasons)
2. **Likely Sentencing / Penalties**: (Sentencing ranges, fines, or damages under BNS/IPC and other relevant laws)
3. **Case Strength Assessment**: (Strong / Moderate / Weak with analysis of the available evidence)
4. **Key Strengths & Risk Factors**: (Factors supporting or weakening the case)
5. **Legal Disclaimer**: "DISCLAIMER: This is an AI-generated outcome estimation based on the facts provided and does not constitute formal legal advice. Please consult a qualified advocate for actual legal representation."
"""

    try:
        response, _ = generate_gemini_content(
            prompt,
            generation_config=genai.types.GenerationConfig(max_output_tokens=3076),
            system_instruction=system_instruction
        )
        return {"prediction": response.text}
    except Exception as e:
        logger.exception("Error in predict_outcome")
        raise HTTPException(status_code=500, detail="An internal error occurred during outcome prediction.")

@app.post("/api/simplify-text", dependencies=[Depends(check_rate_limit_ai)])
def simplify_text(req: SimplifyTextRequest):
    if req.target_language == "Tamil":
        system_instruction = "நீங்கள் ஒரு தமிழ் சட்ட மொழிபெயர்ப்பாளர் மற்றும் எளிமைப்படுத்துபவர். பயனர் வழங்கும் சட்ட உரையை எளிய தமிழில் சுருக்கி விளக்கவும்."
        prompt = f"""சட்ட உரை snippet:
---
{req.text}
---

பணி:
பின்வரும் தலைப்புகளில் எளிய தமிழில் பதில் தரவும்:
1. **எளிய சுருக்கம் (Plain Language Summary)**: (இந்த உரை என்ன சொல்கிறது என்பதை 2-3 வரிகளில் எளிமையாக விளக்கவும்)
2. **முக்கிய உரிமைகள் & கடமைகள் (Key Rights & Obligations)**: (பயனர் செய்ய வேண்டியவை அல்லது அவர்களுக்கு உள்ள உரிமைகள்)
3. **காலக்கெடு / முக்கிய தேதிகள் (Deadlines & Key Dates)**: (ஏதேனும் காலக்கெடு குறிப்பிடப்பட்டிருந்தால்)
4. **கடினமான சட்ட சொற்களின் பொருள் (Legal Terms Explained)**: (உரையில் உள்ள கடினமான ஆங்கில/சட்ட சொற்களுக்கு எளிய தமிழ் விளக்கம்)
"""
    else:
        system_instruction = "You are an expert legal simplifier. Translate and simplify the complex legal text snippet into plain, simple English that a layperson can easily understand."
        prompt = f"""Legal text snippet:
---
{req.text}
---

TASK:
Provide a clear, beautiful, and structured plain-language translation under the following headings:
1. **Plain Language Summary**: (A simple 2-3 sentence overview of what this text actually means)
2. **Key Rights & Obligations**: (What the reader is required to do or what they are entitled to under this text)
3. **Deadlines & Timelines**: (Any deadlines or key action dates mentioned)
4. **Key Legal Terms Simplified**: (Brief explanations of any jargon or complex legal terms used in the text)
"""

    try:
        response, _ = generate_gemini_content(
            prompt,
            generation_config=genai.types.GenerationConfig(max_output_tokens=3076),
            system_instruction=system_instruction
        )
        return {"simplified": response.text}
    except Exception as e:
        logger.exception("Error in simplify_text")
        raise HTTPException(status_code=500, detail="An internal error occurred during text simplification.")

@app.on_event("startup")
def startup_event():
    bookings_path = os.path.join(DATA_DIR, "bookings.json")
    subscriptions_path = os.path.join(DATA_DIR, "subscriptions.json")
    purge_old_records(bookings_path, days=90)
    purge_old_records(subscriptions_path, days=90)

# Serve React static files in production if dist exists
dist_path = os.path.join(ROOT_DIR, "frontend", "dist")
if os.path.exists(dist_path):
    from fastapi.staticfiles import StaticFiles
    app.mount("/", StaticFiles(directory=dist_path, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
