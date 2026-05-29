import os
import io
import json
import base64
import urllib.request
import re as _re
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, Response
from pydantic import BaseModel
import google.generativeai as genai
from PIL import Image
import pypdf
from fpdf import FPDF

app = FastAPI(title="Needhi AI Backend", version="1.0.0")

# Enable CORS for frontend connection (Vite dev server or static build)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root paths
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT_DIR, "backend", "data")

# Load API keys from secrets.toml or environment variables
def load_api_keys():
    keys = []
    # Try streamlit secrets
    secrets_path = os.path.join(ROOT_DIR, ".streamlit", "secrets.toml")
    if os.path.exists(secrets_path):
        try:
            with open(secrets_path, "r") as f:
                content = f.read()
                # Simple parsing for GEMINI_API_KEY
                for line in content.splitlines():
                    if "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip('"').strip("'")
                        if k.startswith("GEMINI_API_KEY") and v:
                            keys.append(v)
        except Exception as e:
            print(f"Error reading secrets.toml: {e}")
            
    # Fallback to environment variables
    for env_var in ["GEMINI_API_KEY", "GEMINI_API_KEY_2", "GEMINI_API_KEY_3", "GEMINI_API_KEY_4"]:
        val = os.environ.get(env_var)
        if val and val not in keys:
            keys.append(val)
            
    return keys if keys else [""]

API_KEYS = load_api_keys()
GOOGLE_API_KEY = API_KEYS[0]
genai.configure(api_key=GOOGLE_API_KEY)

MODEL_FALLBACK_ORDER = [
    "models/gemini-2.5-flash-lite",
    "models/gemini-3.1-flash-lite",
    "models/gemini-2.5-flash",
    "models/gemini-2.0-flash",
    "models/gemini-2.0-flash-lite",
]

def get_working_model():
    try:
        all_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        preferred = ["models/gemini-2.5-flash-lite", "models/gemini-3.1-flash-lite", "models/gemini-2.5-flash", "models/gemini-2.0-flash", "models/gemini-2.0-flash-lite"]
        for p in preferred:
            if p in all_models:
                return p
        flash_models = [m for m in all_models if "flash" in m.lower() and "preview" not in m and "tts" not in m]
        if flash_models:
            return flash_models[0]
        return all_models[0] if all_models else "models/gemini-2.5-flash-lite"
    except Exception:
        return "models/gemini-2.5-flash-lite"

ACTIVE_MODEL_NAME = get_working_model()

# Helper function to query Gemini with Key Rotation and Model Fallbacks
def generate_gemini_content(prompt_or_parts, generation_config=None, stream=False):
    models_to_try = [ACTIVE_MODEL_NAME] + [m for m in MODEL_FALLBACK_ORDER if m != ACTIVE_MODEL_NAME]
    
    # Try all configured API keys
    for api_key in API_KEYS:
        try:
            genai.configure(api_key=api_key)
            for model_name in models_to_try:
                try:
                    model = genai.GenerativeModel(model_name)
                    kwargs = {}
                    if generation_config:
                        kwargs["generation_config"] = generation_config
                    
                    # Safety settings
                    kwargs["safety_settings"] = [
                        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
                    ]
                    
                    if stream:
                        return model.generate_content(prompt_or_parts, stream=True, **kwargs), model_name
                    else:
                        return model.generate_content(prompt_or_parts, **kwargs), model_name
                except Exception as e:
                    if "429" in str(e):
                        continue # try next model or key
                    raise e
        except Exception:
            continue
            
    # Ultimate fallback with primary key and primary model
    genai.configure(api_key=API_KEYS[0])
    model = genai.GenerativeModel(models_to_try[0])
    kwargs = {}
    if generation_config:
        kwargs["generation_config"] = generation_config
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
            with urllib.request.urlopen(req) as response:
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
    
    # Check secrets.toml
    secrets_path = os.path.join(ROOT_DIR, ".streamlit", "secrets.toml")
    if os.path.exists(secrets_path):
        try:
            with open(secrets_path, "r") as f:
                for line in f.read().splitlines():
                    if "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip('"').strip("'")
                        if k == "SMTP_HOST" and v: smtp_host = v
                        elif k == "SMTP_PORT" and v: smtp_port = v
                        elif k == "SMTP_USER" and v: smtp_user = v
                        elif k == "SMTP_PASSWORD" and v: smtp_password = v
                        elif k == "RESEND_API_KEY" and v: resend_key = v
                        elif k == "BREVO_API_KEY" and v: brevo_key = v
                        elif k == "EMAIL_FROM" and v: email_from = v
        except Exception:
            pass

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
            with urllib.request.urlopen(api_req) as response:
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
            with urllib.request.urlopen(api_req) as response:
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
    role: str
    text: str

class ChatRequest(BaseModel):
    query: str
    language: str
    history: List[ChatMessage]

class PDFGenerateRequest(BaseModel):
    title: str
    text: str

class FIRRequest(BaseModel):
    issue: str
    state: str
    ps: str
    name: str

class TemplateRequest(BaseModel):
    template_type: str
    fields: dict

class BookLawyerRequest(BaseModel):
    lawyer_id: int
    client_name: str
    client_email: str
    client_phone: str
    date: str
    slot: str
    details: str

class BnsCompareRequest(BaseModel):
    query: str

class CaseSubscribeRequest(BaseModel):
    cnr: str
    email: str
    client_name: str
    language: str = "English"

# --- Endpoints ---

@app.get("/api/health")
def health_check():
    brevo_key = os.environ.get("BREVO_API_KEY", "")
    brevo_prefix = brevo_key[:12] if brevo_key else "Not Set"
    
    secrets_path = os.path.join(ROOT_DIR, ".streamlit", "secrets.toml")
    secrets_brevo = "Not Set"
    if os.path.exists(secrets_path):
        try:
            with open(secrets_path, "r") as f:
                for line in f.read().splitlines():
                    if "=" in line:
                        k, v = line.split("=", 1)
                        if k.strip() == "BREVO_API_KEY":
                            secrets_brevo = v.strip().strip('"').strip("'")[:12]
        except Exception:
            pass
            
    return {
        "status": "ok",
        "model": ACTIVE_MODEL_NAME,
        "keys_loaded": len(API_KEYS),
        "brevo_env_prefix": brevo_prefix,
        "brevo_secrets_prefix": secrets_brevo
    }

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    query = req.query
    language = req.language
    history = req.history
    
    # Format chat history for prompt
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
            history_block = f"\nPrevious conversation:\n{history_block}\n"

    # Prompts
    if language == "Tamil":
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

    try:
        response, used_model = generate_gemini_content(
            prompt,
            generation_config=genai.types.GenerationConfig(max_output_tokens=2048),
            stream=True
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
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze-doc")
async def analyze_document(
    file: UploadFile = File(...),
    question: Optional[str] = Form(None)
):
    try:
        file_bytes = await file.read()
        file_type = file.content_type
        extra_q = f" Also answer: {question}" if question else ""
        
        # Analyze PDF text
        if file_type == "application/pdf":
            doc_text = ""
            try:
                reader = pypdf.PdfReader(io.BytesIO(file_bytes))
                doc_text = "\n".join(page.extract_text() or "" for page in reader.pages)
            except Exception:
                doc_text = ""
                
            if len(doc_text.strip()) > 100:
                prompt = f"""You are Needhi AI, an Indian legal assistant.
Analyze this legal document and provide:
1. Document type and summary
2. Key legal clauses and their implications under Indian law
3. Any rights or obligations of the parties
4. Red flags or concerning clauses
5. Recommended action{extra_q}

Document text:
{doc_text[:12000]}"""
                response, _ = generate_gemini_content(prompt, generation_config=genai.types.GenerationConfig(max_output_tokens=4096))
                return {"analysis": response.text}
            else:
                # Scanned PDF or text extraction failed: Fallback to native Gemini PDF analysis (with inline PDF data)
                prompt = f"""You are Needhi AI, an Indian legal assistant.
Analyze this scanned legal PDF document and provide:
1. Document type and summary
2. Key legal clauses and their implications under Indian law
3. Any rights or obligations of the parties
4. Red flags or concerning clauses
5. Recommended action{extra_q}"""
                pdf_part = {
                    "mime_type": "application/pdf",
                    "data": file_bytes
                }
                response, _ = generate_gemini_content([pdf_part, prompt], generation_config=genai.types.GenerationConfig(max_output_tokens=4096))
                return {"analysis": response.text}
            
        # Analyze Image
        elif file_type in ["image/png", "image/jpeg", "image/jpg"]:
            image = Image.open(io.BytesIO(file_bytes))
            prompt = f"""You are Needhi AI, an Indian legal assistant.
Analyze this legal document image and provide:
1. Document type and summary
2. Key legal clauses and their implications under Indian law
3. Any rights or obligations of the parties
4. Red flags or concerning clauses
5. Recommended action{extra_q}"""
            response, _ = generate_gemini_content([prompt, image])
            return {"analysis": response.text}
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format. Please upload PDF, PNG or JPG.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/bns-lookup")
def bns_lookup(query: dict):
    search_term = query.get("term", "").lower().strip()
    category = query.get("category", "")
    
    # Load JSON database
    ipc_bns_path = os.path.join(DATA_DIR, "ipc_bns.json")
    if not os.path.exists(ipc_bns_path):
        return []
        
    with open(ipc_bns_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
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

@app.post("/api/bns-compare-ai")
def bns_compare_ai(req: BnsCompareRequest):
    query_str = req.query.strip()
    if not query_str:
        return []

    prompt = f"""
    You are an expert Indian legal archivist comparing the old Indian Penal Code (IPC) and the new Bharatiya Nyaya Sanhita (BNS) 2023.
    The user wants to compare and see transition details for: '{query_str}'.
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
    Return only a valid JSON array of objects. Do not wrap in markdown or backticks.
    """

    try:
        response, _ = generate_gemini_content(prompt, generation_config=genai.types.GenerationConfig(
            response_mime_type="application/json",
            max_output_tokens=2048
        ))
        
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
        print("BNS AI comparison failed, falling back to local search:", e)
        
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

@app.post("/api/cases/subscribe")
def subscribe_to_case(req: CaseSubscribeRequest):
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
            raise HTTPException(status_code=500, detail=f"Failed to read cases database: {e}")
            
    if not case_details:
        raise HTTPException(status_code=404, detail="Case with this CNR number not found")
        
    # Save subscription
    subscriptions_path = os.path.join(DATA_DIR, "subscriptions.json")
    subscriptions = []
    if os.path.exists(subscriptions_path):
        try:
            with open(subscriptions_path, "r", encoding="utf-8") as f:
                subscriptions = json.load(f)
        except Exception:
            pass
            
    # Check if already subscribed
    already_subscribed = False
    for sub in subscriptions:
        if sub.get("cnr", "").lower() == cnr.lower() and sub.get("email", "").lower() == email:
            already_subscribed = True
            break
            
    if not already_subscribed:
        subscriptions.append({
            "cnr": cnr,
            "email": email,
            "client_name": client_name,
            "language": language,
            "subscribed_at": datetime.now().isoformat()
        })
        try:
            with open(subscriptions_path, "w", encoding="utf-8") as f:
                json.dump(subscriptions, f, indent=2, ensure_ascii=False)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save subscription: {e}")
            
    # Construct Email Content
    case_title = case_details.get("title", cnr)
    case_title_tamil = case_details.get("tamil_title", case_title)
    
    if language == "Tamil":
        subject = f"நீதி AI: வழக்கு கண்காணிப்பு சந்தா உறுதிசெய்யப்பட்டது - {cnr}"
        body = f"""அன்புள்ள {client_name},
  
நீங்கள் {cnr} ({case_title_tamil}) வழக்குகான மின்னஞ்சல் விழிப்பூட்டல்களுக்கு வெற்றிகரமாக குழுசேர்ந்துள்ளீர்கள்.
  
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

    recipients = [{"email": email, "name": client_name}]
    email_sent, email_status = send_email_notification(recipients, subject, body)
    
    return {
        "status": "success",
        "message": "Subscription registered successfully",
        "email_sent": email_sent,
        "email_status": email_status
    }

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

@app.post("/api/book-lawyer")
def book_lawyer(req: BookLawyerRequest):
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
    import os as _os
    booking_code = "ND-" + str(_os.urandom(3).hex().upper())
    
    # Save booking to bookings.json
    bookings_path = os.path.join(DATA_DIR, "bookings.json")
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
        "client_name": req.client_name,
        "client_email": req.client_email,
        "client_phone": req.client_phone,
        "date": req.date,
        "slot": req.slot,
        "details": req.details,
        "timestamp": datetime.now().isoformat()
    }
    
    bookings.append(new_booking)
    
    try:
        with open(bookings_path, "w", encoding="utf-8") as f:
            json.dump(bookings, f, indent=2, ensure_ascii=False)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save booking: {e}")
        
    # Construct Email Content
    subject = f"Needhi AI: Legal Consultation Ticket - {booking_code}"
    body = f"""Dear {req.client_name},
 
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
    
    # Send email notification
    recipients = [
        {"email": req.client_email, "name": req.client_name},
        {"email": lawyer["email"], "name": lawyer["name"]}
    ]
    email_sent, email_status = send_email_notification(recipients, subject, body)
        
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

@app.post("/api/generate-fir")
def generate_fir(req: FIRRequest):
    ps_line = f"Police Station: {req.ps}" if req.ps else "Police Station: ________________________"
    name_line = req.name if req.name else "________________________"
    
    prompt = f"""You are Needhi AI, an elite Indian legal counsel. Generate a highly professional, formal, and legally precise written complaint addressed to the Station House Officer (SHO) to register a First Information Report (FIR) under Section 173 of the Bharatiya Nagarik Suraksha Sanhita, 2023 (BNSS) (formerly Section 154 of the Code of Criminal Procedure, 1973).
    
    Any details that are not provided or are blank must be represented in the document as a clearly labeled blank underline (e.g., "________________________") so that it can be printed and filled in manually. Do not use generic bracketed placeholders (like '[Your Address]' or similar); always use blank underlines.
    
    Incident Details Provided:
    - Incident Narrative/Issue: {req.issue}
    - State: {req.state or '________________________'}
    - Police Station: {req.ps or '________________________'}
    - Complainant Name: {name_line}
    
    Structure the document as a standard Indian Police complaint with the following sections, formatted using clean, professional markdown:
    
    1. **OFFICIAL ADDRESS HEADER**:
       To,
       The Station House Officer,
       {ps_line},
       District: ________________________,
       {req.state or 'State: ________________________'}
       
    2. **SUBJECT LINE**: 
       Must be highly formal, stating: "SUBJECT: Written Complaint for registration of FIR under Section 173 of the BNSS, 2023, regarding the offences committed against the Complainant on [Date/Time placeholder]."
       
    3. **COMPLAINANT DETAILS**:
       State the Complainant's name, parentage/husband's name (father's/husband's name: ________________________), age (________________________ years), residential address (________________________), contact number (________________________), and nationality (________________________).
       
    4. **ACCUSED DETAILS**:
       Provide details of the accused. If known, list their names, descriptions, or addresses. If unknown, state "Unidentified/Unknown persons (to be identified during investigation)".
       
    5. **CHRONOLOGICAL NARRATIVE OF THE INCIDENT**:
       Draft a detailed, factual, and legally precise narration of the incident based on the user's issue. Use formal legal vocabulary. Ensure the chronological chain of events is clear (Date, Time, and Specific Location placeholders included).
       
    6. **SPECIFIC OFFENCES & LEGAL SECTIONS**:
       Explicitly state which offences have been committed. For each offence, provide a brief paragraph explaining how the acts constitute the offence, citing both the **new Bharatiya Nyaya Sanhita, 2023 (BNS)** section and the **corresponding old Indian Penal Code, 1860 (IPC)** section in parentheses for full legal compatibility. E.g.:
       - Voluntarily causing hurt: Section 115(2) BNS (formerly Section 323 IPC)
       - Cheating: Section 318 BNS (formerly Section 420 IPC)
       - Theft: Section 303 BNS (formerly Section 379 IPC)
       - Criminal Intimidation: Section 351 BNS (formerly Section 506 IPC)
       - Criminal Conspiracy: Section 61 BNS (formerly Section 120B IPC)
       - Criminal Trespass: Section 329 BNS (formerly Section 447 IPC)
       Ensure the sections cited are 100% accurate based on the legal definitions.
       
    7. **RELIEF SOUGHT / ACTION REQUESTED**:
       A formal prayer requesting the SHO to:
       a) Register a First Information Report (FIR) under Section 173 of the BNSS, 2023, against the accused persons.
       b) Conduct a thorough investigation and secure the arrest of the accused.
       c) Recovery of any stolen property or securing of material evidence.
       
    8. **DECLARATION & SIGNATURE BLOCKS**:
       - Place: ________________________
       - Date: ________________________
       - Complainant Signature block (Signature: ________________________, Name: {name_line})
       
    Tone: Extremely formal, authoritative, and structured according to standard legal practice in Indian police stations. Output only the drafted complaint. Do not add any conversational remarks or notes outside the draft."""

    try:
        response, _ = generate_gemini_content(prompt, generation_config=genai.types.GenerationConfig(max_output_tokens=2048))
        return {"draft": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate-template")
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

# Serve React static files in production if dist exists
dist_path = os.path.join(ROOT_DIR, "frontend", "dist")
if os.path.exists(dist_path):
    from fastapi.staticfiles import StaticFiles
    app.mount("/", StaticFiles(directory=dist_path, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
