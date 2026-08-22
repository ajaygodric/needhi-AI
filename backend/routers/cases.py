import os
import json
import logging
import sqlite3
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Request, Depends, Response
from core.config import DATABASE_FILE
from core.security import check_rate_limit_data, encrypt_field, decrypt_field
from core.utils import send_email_notification
from core.schemas import CaseSubscribeRequest

logger = logging.getLogger("needhi.routers.cases")

router = APIRouter()

@router.get("/api/cases")
def get_cases(search: str = "", search_type: str = "CNR Number"):
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    search_clean = search.strip().lower()
    if not search_clean:
        cursor.execute("SELECT raw_json FROM cases")
        rows = cursor.fetchall()
        conn.close()
        return [json.loads(row[0]) for row in rows]
        
    # Query database using SQL filters
    if search_type == "CNR Number":
        cursor.execute("SELECT raw_json FROM cases WHERE LOWER(cnr) LIKE ?", (f"%{search_clean}%",))
    elif search_type == "Party Name":
        cursor.execute("SELECT raw_json FROM cases WHERE LOWER(petitioner) LIKE ? OR LOWER(respondent) LIKE ?", (f"%{search_clean}%", f"%{search_clean}%"))
    elif search_type == "FIR Number":
        cursor.execute("SELECT raw_json FROM cases WHERE LOWER(case_no) LIKE ?", (f"%{search_clean}%",))
    elif search_type == "Advocate Name":
        cursor.execute("SELECT raw_json FROM cases WHERE LOWER(petitioner_adv) LIKE ? OR LOWER(respondent_adv) LIKE ?", (f"%{search_clean}%", f"%{search_clean}%"))
    else:
        cursor.execute("SELECT raw_json FROM cases")
        
    rows = cursor.fetchall()
    conn.close()
    
    return [json.loads(row[0]) for row in rows]

@router.post("/api/cases/subscribe", dependencies=[Depends(check_rate_limit_data)])
def subscribe_to_case(req: CaseSubscribeRequest, request: Request):
    cnr = req.cnr.strip()
    email = req.email.strip().lower()
    client_name = req.client_name.strip()
    language = req.language
    
    if not cnr or not email or not client_name:
        raise HTTPException(status_code=400, detail="Missing required subscription fields")
        
    # Check if case exists to get the details from SQLite
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT raw_json FROM cases WHERE LOWER(cnr) = ?", (cnr.lower(),))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Case with this CNR number not found")
        
    case_details = json.loads(row[0])
    
    # Check if already subscribed and verified in SQLite
    cursor.execute("SELECT email, verified FROM subscriptions WHERE LOWER(cnr) = ?", (cnr.lower(),))
    rows = cursor.fetchall()
    already_subscribed = False
    for enc_email, verified in rows:
        dec_email = decrypt_field(enc_email)
        if dec_email.lower() == email and verified == 1:
            already_subscribed = True
            break
            
    if already_subscribed:
        conn.close()
        return {
            "status": "already_subscribed",
            "message": "You are already subscribed to this case."
        }
        
    # Delete any pending subscriptions for this cnr + email to avoid duplicate rows
    cursor.execute("SELECT id, email FROM subscriptions WHERE LOWER(cnr) = ?", (cnr.lower(),))
    all_subs = cursor.fetchall()
    for sub_id, enc_email in all_subs:
        if decrypt_field(enc_email).lower() == email:
            cursor.execute("DELETE FROM subscriptions WHERE id = ?", (sub_id,))
            
    verification_token = os.urandom(16).hex()
    now_str = datetime.now().isoformat()
    
    cursor.execute("""
    INSERT INTO subscriptions (cnr, email, client_name, language, verification_token, verified, subscribed_at, timestamp)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        cnr, encrypt_field(email), encrypt_field(client_name), language,
        verification_token, 0, now_str, now_str
    ))
    
    conn.commit()
    conn.close()
    
    # Send verification email containing verification link
    confirm_url = f"{request.base_url}api/cases/confirm-subscription?token={verification_token}"
    
    if language == "Tamil":
        subject = f"நீதி AI: வழக்கு கண்காணிப்பு சந்தா சரிபார்ப்பு - {cnr}"
        body = f"""அன்புள்ள {client_name},
  
{cnr} ({case_details.get('tamil_title', case_details.get('title'))}) வழக்குகான மின்னஞ்சல் விழிப்பூட்டல்களை சரிபார்க்க கீழே உள்ள இணைப்பை கிளிக் செய்யவும்:
{confirm_url}
  
இந்த கோரிக்கையை நீங்கள் செய்யவில்லை என்றால், இந்த மின்னஞ்சலை புறக்கணிக்கலாம்.
  
நன்றி,
மின்னஞ்சல் நீதி AI சட்ட குழு.
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

@router.get("/api/cases/confirm-subscription")
def confirm_subscription(token: str):
    if not token:
        raise HTTPException(status_code=400, detail="Token is missing.")
        
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    # Find pending subscription with this token
    cursor.execute("SELECT id, cnr, email, client_name, language FROM subscriptions WHERE verification_token = ? AND verified = 0", (token,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
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
        
    sub_id, cnr, enc_email, enc_client_name, language = row
    
    # Update subscription to verified
    cursor.execute("UPDATE subscriptions SET verified = 1, verification_token = NULL WHERE id = ?", (sub_id,))
    conn.commit()
    
    # Get case details
    cursor.execute("SELECT raw_json FROM cases WHERE LOWER(cnr) = ?", (cnr.lower(),))
    case_row = cursor.fetchone()
    case_details = json.loads(case_row[0]) if case_row else None
    
    conn.close()
    
    email = decrypt_field(enc_email)
    client_name = decrypt_field(enc_client_name)
    
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
மின்னஞ்சல் நீதி AI சட்ட குழு.
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
