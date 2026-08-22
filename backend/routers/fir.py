import os
import logging
import google.generativeai as genai
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from core.security import check_rate_limit_ai, sanitize_input_dict
from core.gemini import generate_gemini_content
from core.schemas import FIRRequest

logger = logging.getLogger("needhi.routers.fir")

router = APIRouter()

@router.post("/api/generate-fir", dependencies=[Depends(check_rate_limit_ai)])
def generate_fir(req: FIRRequest):
    ps_line = f"Police Station: {req.ps}" if req.ps else "Police Station: ________________________"
    name_line = req.name if req.name else "________________________"
    
    category_instructions = ""
    valid_categories = {"Domestic Violence", "Cyber Fraud", "Property Dispute", "Motor Accident"}
    if req.category in valid_categories:
        # Whitelist fields to prevent prompt injection
        allowed_fields = set()
        if req.category == "Domestic Violence":
            allowed_fields = {"relationship", "abuseType", "frequency", "medicalExam", "dowryDetails"}
        elif req.category == "Cyber Fraud":
            allowed_fields = {"amount", "transactionTime", "txnId", "suspectInfo", "modusOperandi", "cyberCellId"}
        elif req.category == "Property Dispute":
            allowed_fields = {"propertyLocation", "documentNo", "disputeNature", "ownershipDoc", "disputeDate", "damageDetails"}
        elif req.category == "Motor Accident":
            allowed_fields = {"victimVehicle", "accusedVehicle", "injuryNature", "driverDetails", "hospitalName", "negligenceType"}
            
        req.category_fields = sanitize_input_dict(req.category_fields, allowed_fields)
        
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
            
    system_instruction = (
        "You are Needhi AI, an elite Indian legal counsel. "
        "Generate a highly professional, formal, and legally precise written complaint addressed to the "
        "Station House Officer (SHO) to register a First Information Report (FIR) under Section 173 "
        "of the Bharatiya Nagarik Suraksha Sanhita, 2023 (BNSS) (formerly Section 154 of the Code of Criminal Procedure, 1973)."
    )

    prompt = f"""Draft a First Information Report (FIR) complaint based on the following details.
    
    Any details that are not provided or are blank must be represented in the document as a clearly labeled blank underline (e.g., "________________________") so that it can be printed and filled in manually. Do not use generic bracketed placeholders (like '[Your Address]' or similar); always use blank underlines.
    
    Incident Details Provided:
    - Incident Narrative/Issue: {req.issue}
    - State: {req.state or '________________________'}
    - Police Station: {req.ps or '________________________'}
    - Complainant Name: {name_line}
    {category_instructions}
    
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
       State the specific offences committed by the accused. List the relevant legal sections (providing both BNS 2023 and legacy IPC equivalents). Example:
       - Theft: Section 303 BNS (formerly Section 379 IPC)
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
        response, _ = generate_gemini_content(
            prompt,
            generation_config=genai.types.GenerationConfig(max_output_tokens=2048),
            system_instruction=system_instruction
        )
        return {"draft": response.text}
    except Exception as e:
        logger.exception("Error in generate_fir")
        raise HTTPException(status_code=500, detail="An internal error occurred during FIR generation.")
