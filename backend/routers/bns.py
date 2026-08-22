import os
import json
import logging
import google.generativeai as genai
from fastapi import APIRouter, HTTPException, Depends
from core.config import STATIC_DATA_DIR
from core.security import check_rate_limit_ai, check_rate_limit_data
from core.gemini import generate_gemini_content
from core.schemas import BnsLookupRequest, BnsCompareRequest

logger = logging.getLogger("needhi.routers.bns")

router = APIRouter()

@router.post("/api/bns-lookup", dependencies=[Depends(check_rate_limit_data)])
def bns_lookup(req: BnsLookupRequest):
    search_term = req.term.lower().strip()
    category = req.category
    
    # Load JSON database
    ipc_bns_path = os.path.join(STATIC_DATA_DIR, "ipc_bns.json")
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

@router.post("/api/bns-compare-ai", dependencies=[Depends(check_rate_limit_ai)])
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
    ipc_bns_path = os.path.join(STATIC_DATA_DIR, "ipc_bns.json")
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
