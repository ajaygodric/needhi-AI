import logging
import google.generativeai as genai
from fastapi import APIRouter, HTTPException, Depends
from core.security import check_rate_limit_ai
from core.gemini import generate_gemini_content
from core.schemas import PredictOutcomeRequest, SimplifyTextRequest

logger = logging.getLogger("needhi.routers.tools")

router = APIRouter()

@router.post("/api/predict-outcome", dependencies=[Depends(check_rate_limit_ai)])
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

@router.post("/api/simplify-text", dependencies=[Depends(check_rate_limit_ai)])
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
