import io
import re
import logging
import google.generativeai as genai
from typing import Optional
from PIL import Image
import pypdf
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import StreamingResponse
from core.gemini import generate_gemini_content
from core.security import check_rate_limit_ai, get_current_user, get_optional_user
from core.db import search_knowledge_base, DATABASE_FILE
from core.schemas import ChatRequest, ChatDocRequest, SearchHistoryItem
import sqlite3
import time


logger = logging.getLogger("needhi.routers.chat")

router = APIRouter()

@router.post("/api/chat", dependencies=[Depends(check_rate_limit_ai)])
async def chat_endpoint(req: ChatRequest, user_id: Optional[int] = Depends(get_optional_user)):
    query = req.query
    language = req.language
    history = req.history[-10:] if req.history else []
    
    if user_id is not None:
        try:
            conn = sqlite3.connect(DATABASE_FILE)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO search_history (user_id, query, timestamp) VALUES (?, ?, ?)",
                (user_id, query, time.time())
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to save search history: {e}")

    
    # Prevent RAG pollution for simple greetings and short conversational messages
    query_clean = re.sub(r'[^\w\s]', '', query).strip().lower()
    greetings = {
        "hi", "hello", "hey", "hola", "greetings", "good morning", "good afternoon", 
        "good evening", "how are you", "who are you", "what are you", "help", "menu",
        "வணக்கம்", "நலம்", "எப்படி இருக்கிறீர்கள்", "நன்றி"
    }
    
    kb_results = []
    if query_clean not in greetings and len(query_clean) > 2:
        kb_results = search_knowledge_base(query, limit=5)
        
    kb_context = ""
    if kb_results:
        kb_context = "\n".join(
            f"[{i+1}] Source Act: {r['act_name']}, Page: {r['page_number']}\nContent Excerpt:\n{r['content']}\n"
            for i, r in enumerate(kb_results)
        )
        kb_context = f"\n--- OFFICIAL LAW SOURCE CHUNKS ---\n{kb_context}\n--- END OF OFFICIAL SOURCE CHUNKS ---\n"
    
    # Prompts
    if language == "Tamil":
        system_instruction = """System: நீங்கள் 'நீதி AI' — இந்திய சட்டத்தில் நிபுணத்துவம் வாய்ந்த AI சட்ட உதவியாளர்.
அதிகாரப்பூர்வ சட்டங்களின் (BNS, BNSS, BSA, IPC, CrPC) பகுதிகள் 'OFFICIAL LAW SOURCE CHUNKS' என்ற தலைப்பில் வழங்கப்பட்டுள்ளன. உங்கள் பதில்களை இதிலிருந்து பெற முன்னுரிமை கொடுங்கள். நீங்கள் கூறும் ஒவ்வொரு சட்டப்பிரிவு அல்லது தகவலுக்கும் ஆதாரத்தைக் குறிப்பிடவும் (எ.கா. [BNS_2023, Page 12] அல்லது [IPC_1860, Page 5]). வழங்கப்பட்ட பிரிவுகளில் தகவல் இல்லை என்றால், உங்கள் பொதுவான சட்ட அறிவைப் பயன்படுத்தி பதிலளிக்கலாம், ஆனால் எது பொது அறிவு எது அதிகாரப்பூர்வ சட்டப் பகுதி என்பதைத் தெளிவாகக் குறிப்பிடவும்.

TASK:
1. இந்த கேள்வி இந்திய சட்டம், நீதிமன்றம், காவல்துறை, குற்றம், உரிமைகள் அல்லது சட்ட நடைமுறைகள் தொடர்பானதா?
2. இல்லை என்றால் சரியாக பதிலளிக்கவும்: "மன்னிக்கவும். நான் சட்டம் தொடர்பான கேள்விகளுக்கு மட்டுமே பதிலளிப்பேன்."
3. ஆம் என்றால்:
   கேள்வி முந்தைய உரையாடலின் தொடர்ச்சியா (Follow-up), ஒரு புதிய குற்றவியல் குற்றம் பற்றியதா, அல்லது சிவில்/நடைமுறை தலைப்பு பற்றியதா என்று ஆராயுங்கள்.
   
   A. பயனர் கேள்வி ஒரு தொடர் கேள்வி அல்லது உரையாடலின் தொடர்ச்சியாக இருந்தால் (எ.கா. 'இதற்கு எவ்வளவு ஆண்டுகள் சிறை?', 'ஜாமீன் கிடைனகுமா?', 'யார் புகார் செய்ய வேண்டும்?'):
      மேலே உள்ள விரிவான தலைப்புகள் மற்றும் பிரிவுகளை (B அல்லது C) மீண்டும் பயன்படுத்த வேண்டாம்.
      பதிலாக, முந்தைய உரையாடலின் பின்னணியை வைத்துக்கொண்டு, பயனர் கேட்ட குறிப்பிட்ட கேள்விக்கு நேரடியாகவும், உரையாடல் வடிவிலும் 2-4 வாக்கியங்களில் எளிய பதில் தரவும். ஒரு வழக்கறிஞர் உங்களிடம் நேரடியாகப் பேசுவது போன்ற மனித உணர்வுடன் பதில் இருக்க வேண்டும்.
   
   B. கேள்வி ஒரு புதிய குற்றவியல் குற்றம் பற்றியதாக இருந்தால் (எ.கா. திருட்டு, கொலை, ஏமாற்றுதல், தாக்குதல்):
      பின்வரும் தலைப்புகளில் விரிவான பதில் தரவும் (தலைப்புகள் மற்றும் ஈமோஜிகளை அப்படியே பயன்படுத்தவும்):
      **⚖️ சட்ட பிரிவுகள் (Applicable Legal Sections)**
      - பொருந்தும் BNS/IPC/BNSS பிரிவுகள் மற்றும் அவற்றுக்கான ஆதாரங்கள் (எ.கா. [BNS_2023, Page 12])
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
You are provided with actual excerpts from the official laws (BNS, BNSS, BSA, IPC, CrPC) under 'OFFICIAL LAW SOURCE CHUNKS' when available. You must prioritize this context to answer the question. For every legal fact or section number you state, you MUST cite the source in brackets, e.g. [BNS_2023, Page 12] or [IPC_1860, Page 5]. If the context does not contain the answer, you may answer using your general knowledge of Indian Law, but clearly state which parts are from general legal knowledge versus the official source text. Keep citations strictly grounded in the provided sources.

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
      - List relevant BNS/IPC/CrPC/BNSS sections with their sources (e.g. [BNS_2023, Page 12])
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
            
    user_parts = [query]
    if kb_context:
        user_parts.append(kb_context)
        
    messages.append({
        "role": "user",
        "parts": user_parts
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

@router.post("/api/analyze-doc", dependencies=[Depends(check_rate_limit_ai)])
async def analyze_document(
    file: UploadFile = File(...),
    question: Optional[str] = Form(None)
):
    try:
        MAX_FILE_SIZE = 25 * 1024 * 1024
        
        if file.size is not None and file.size > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="File size exceeds the 25MB limit.")
            
        file_bytes = b""
        chunk_size = 1024 * 1024
        while True:
            chunk = await file.read(chunk_size)
            if not chunk:
                break
            file_bytes += chunk
            if len(file_bytes) > MAX_FILE_SIZE:
                raise HTTPException(status_code=413, detail="File size exceeds the 25MB limit.")
                
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
        
        system_instruction = (
            "You are Needhi AI, an Indian legal assistant. "
            "Your task is to analyze legal documents and provide a clear, structured overview. "
            "Identify the document type, key clauses under Indian law, rights/obligations, red flags, and recommended actions. "
            "Base your analysis strictly on the provided document text. Do not assume or hallucinate clauses not present in the document."
        )
        
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
                    f"Document text:\n{doc_text[:150000]}"
                )
                response, _ = generate_gemini_content(
                    prompt, 
                    generation_config=genai.types.GenerationConfig(max_output_tokens=4096),
                    system_instruction=system_instruction
                )
                return {"analysis": response.text, "doc_text": doc_text}
            else:
                pdf_part = {
                    "mime_type": "application/pdf",
                    "data": file_bytes
                }
                
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
            
        elif detected_mime in ["image/png", "image/jpeg"]:
            image = Image.open(io.BytesIO(file_bytes))
            
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

@router.post("/api/chat-doc", dependencies=[Depends(check_rate_limit_ai)])
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
        system_instruction = "நீங்கள் 'நீதி AI' — பயனர் வழங்கிய சட்ட ஆவணங்களில் இருந்து மட்டுமே பதிலளிக்க வேண்டிய ஒரு கண்டிப்பான AI சட்ட உதவியாளர். வழங்கப்பட்ட ஆவணத்தில் உள்ள தகவல்களை மட்டுமே ஆதாரமாகக் கொண்டு பயனரின் கேள்விக்கு எளிய தமிழில் பதிலளிக்கவும்."
        prompt = f"""ஆவணத்தின் உரை (Document Text):
--- ஆவணத்தின் உரை (Document Text) ---
{doc_text[:150000]}
--- முடிவு ---
 
{history_block}
பயனர் கேள்வி: '{query}'
 
பணி (TASK):
வழங்கப்பட்ட ஆவணத்தின் உரையிலிருந்து மட்டுமே பயனரின் கேள்விக்கு எளிய தமிழில் பதிலளிக்கவும். உங்கள் பதிலில் ஆவணத்தின் குறிப்பிட்ட பிரிவுகள் அல்லது ஷரத்துக்களை கண்டிப்பாக ஆதாரமாகக் சுட்டிக்காட்டவும். ஆவணத்தில் இல்லாத தகவலைப் பற்றி கேள்வி இருந்தால், 'கொடுக்கப்பட்ட ஆவணத்தில் இதைப் பற்றிய தகவல்கள் இல்லை' என்று தெளிவாகக் கூறவும். பொதுவான சட்ட விளக்கங்களையோ அல்லது ஊகங்களையோ அளிக்க வேண்டாம்."""
    else:
        system_instruction = "You are 'Needhi AI' — a strict AI Legal Assistant. You must answer the user's question using ONLY the provided document text. Do not make assumptions or use general knowledge."
        prompt = f"""Here is the text of the document:
--- DOCUMENT START ---
{doc_text[:150000]}
--- DOCUMENT END ---
 
{history_block}
User Query: '{query}'
 
TASK:
Answer the user's question using ONLY the context of the uploaded document. You MUST reference specific clauses, page numbers, or sections of the document to support your answer. If the question is not answerable from the document, state clearly: 'I cannot find this information in the uploaded document.' Do not provide general legal info or assumptions."""

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

from typing import List
@router.get("/api/chat/history", response_model=List[SearchHistoryItem])
def get_chat_history(user_id: int = Depends(get_current_user)):
    conn = sqlite3.connect(DATABASE_FILE)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT query, timestamp FROM search_history WHERE user_id = ? ORDER BY id DESC LIMIT 20", (user_id,))
        rows = cursor.fetchall()
        return [SearchHistoryItem(query=row[0], timestamp=row[1]) for row in rows]
    finally:
        conn.close()

@router.delete("/api/chat/history")
def clear_chat_history(user_id: int = Depends(get_current_user)):
    conn = sqlite3.connect(DATABASE_FILE)
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM search_history WHERE user_id = ?", (user_id,))
        conn.commit()
        return {"status": "success", "message": "Search history cleared."}
    finally:
        conn.close()


