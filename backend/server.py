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

# --- Endpoints ---

@app.get("/api/health")
def health_check():
    return {"status": "ok", "model": ACTIVE_MODEL_NAME, "keys_loaded": len(API_KEYS)}

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
    booking_code = "ND-" + str(os.urandom(3).hex().upper())
    
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
        
    # Send email notification or simulate
    smtp_host = os.environ.get("SMTP_HOST", "")
    smtp_port = os.environ.get("SMTP_PORT", "")
    smtp_user = os.environ.get("SMTP_USER", "")
    smtp_password = os.environ.get("SMTP_PASSWORD", "")
    resend_key = os.environ.get("RESEND_API_KEY", "")
    brevo_key = os.environ.get("BREVO_API_KEY", "")
    
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
        except Exception:
            pass
            
    email_status = "Simulated email dispatch"
    email_sent = False
    
    # Construct Email Content
    subject = f"Needhi AI: Legal Consultation Ticket - {booking_code}"
    body = f"""Dear {req.client_name},
 
Your legal consultation with {lawyer['name']} has been successfully scheduled.
 
--- CONSULTATION TICKET ---
Ticket Code: {booking_code}
Lawyer: {lawyer['name']} ({lawyer['specialization']})
Date: {req.date}
Time Slot: {req.slot}
Fee: \u20b9{lawyer['fee']} (Payable to the lawyer)
 
Advocate Contact Details:
Phone: {lawyer['phone']}
Email: {lawyer['email']}
City: {lawyer['city']}
 
Case Summary provided:
{req.details}
 
Thank you for choosing Needhi AI.
"""
    
    if resend_key:
        try:
            import urllib.request
            url = "https://api.resend.com/emails"
            headers = {
                "Authorization": f"Bearer {resend_key}",
                "Content-Type": "application/json"
            }
            # Resend requires a verified domain unless using onboarding@resend.dev
            from_email = os.environ.get("EMAIL_FROM", "onboarding@resend.dev")
            data = {
                "from": f"Needhi AI <{from_email}>",
                "to": [req.client_email, lawyer["email"]],
                "subject": subject,
                "text": body
            }
            api_req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers, method="POST")
            with urllib.request.urlopen(api_req) as response:
                resp_data = json.loads(response.read().decode())
                email_sent = True
                email_status = f"Sent successfully via Resend API (ID: {resp_data.get('id')})"
        except Exception as e:
            email_status = f"Failed to send via Resend API: {e}"
            
    elif brevo_key:
        try:
            import urllib.request
            url = "https://api.brevo.com/v3/smtp/email"
            headers = {
                "api-key": brevo_key,
                "Content-Type": "application/json"
            }
            from_email = os.environ.get("EMAIL_FROM", "noreply@needhi.ai")
            data = {
                "sender": {"name": "Needhi AI", "email": from_email},
                "to": [
                    {"email": req.client_email, "name": req.client_name},
                    {"email": lawyer["email"], "name": lawyer["name"]}
                ],
                "subject": subject,
                "textContent": body
            }
            api_req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers, method="POST")
            with urllib.request.urlopen(api_req) as response:
                resp_data = json.loads(response.read().decode())
                email_sent = True
                email_status = f"Sent successfully via Brevo API (MessageId: {resp_data.get('messageId')})"
        except Exception as e:
            email_status = f"Failed to send via Brevo API: {e}"
            
    elif smtp_host and smtp_port and smtp_user and smtp_password:
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            # Send to Client and CC Lawyer
            msg = MIMEMultipart()
            msg["From"] = smtp_user
            msg["To"] = f"{req.client_email}, {lawyer['email']}"
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))
            
            port = int(smtp_port)
            if port == 465:
                server = smtplib.SMTP_SSL(smtp_host, port)
                server.login(smtp_user, smtp_password)
                server.sendmail(smtp_user, [req.client_email, lawyer["email"]], msg.as_string())
                server.close()
            else:
                server = smtplib.SMTP(smtp_host, port)
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.sendmail(smtp_user, [req.client_email, lawyer["email"]], msg.as_string())
                server.close()
                
            email_sent = True
            email_status = "Emailed to client and lawyer successfully"
        except Exception as e:
            email_status = f"Failed to send email via SMTP: {e}"
    else:
        # Print simulated dispatch details
        print(f"\n=== NEEDHI AI SMTP SIMULATOR ===")
        print(f"To: {req.client_email}")
        print(f"From: {smtp_user or 'noreply@needhi.ai'}")
        print(f"Subject: {subject}")
        print(f"Body:\n{body}")
        print(f"=================================\n")
        
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
    
    prompt = f"""You are Needhi AI, an Indian legal assistant. Generate a formal FIR (First Information Report) draft in English based on the following incident. Use proper legal FIR format used in India.
Any details that are not provided or are blank must be represented in the document as a clearly labeled blank underline (e.g., "________________________") so that it can be printed and filled in manually. Do not use generic bracketed placeholders (like '[Your Address]' or similar); always use blank underlines '________________________'.

Incident: {req.issue}
State: {req.state or 'India'}
{ps_line}
Complainant: {name_line}

Format the FIR with these sections:
1. TO: The Station House Officer, {ps_line}
2. Subject line
3. Complainant details (name, address placeholder)
4. Date, time and place of incident
5. Detailed description of the incident
6. Names/description of accused (if known)
7. Witnesses (if any)
8. Relief sought
9. Declaration
10. Signature line

Make it formal, legally precise, and ready to submit. Include relevant BNS/IPC sections at the end."""

    try:
        response, _ = generate_gemini_content(prompt, generation_config=genai.types.GenerationConfig(max_output_tokens=2048))
        return {"draft": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate-template")
def generate_template(req: TemplateRequest):
    prompt = f"""You are Needhi AI, an expert Indian legal assistant.
Generate a formal, legally valid {req.template_type} document for India.

Here are the specific details to include in the document:
{req.fields}

Instructions:
1. For any detail in the above list that is provided, insert it directly into its respective position in the document.
2. For any detail/field that is empty, blank, or not provided (e.g., empty string ""), represent it in the document as a clearly labeled blank fillable underline (e.g., "________________________") so that it can be printed and filled in manually.
3. Do NOT use brackets or text placeholders like "[Landlord Name]", "[Insert Date]", or "<Tenant Name>" for missing info; use actual underlines like "________________________" with a clear label preceding it (e.g., "Landlord Name: ________________________").
4. Ensure the document has all standard legally binding clauses, a proper header, sections, covenants, witness signatures, deponent signatures, or verification sections as appropriate for a {req.template_type}.
5. Use formal, professional legal language."""

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
