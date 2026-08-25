import os
import json
import logging
import sqlite3
from datetime import datetime, date
from fastapi import APIRouter, HTTPException, Depends
from core.config import DATABASE_FILE
from core.security import check_rate_limit_data, encrypt_field, decrypt_field, get_current_user
from core.utils import send_email_notification
from core.schemas import BookLawyerRequest

logger = logging.getLogger("needhi.routers.bookings")

router = APIRouter()

@router.get("/api/lawyers")
def get_lawyers(specialization: str = "", city: str = "", search: str = ""):
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    query = "SELECT raw_json FROM lawyers WHERE 1=1"
    params = []
    
    if specialization:
        query += " AND LOWER(specialization) LIKE ?"
        params.append(f"%{specialization.lower()}%")
    if city:
        query += " AND LOWER(city) = ?"
        params.append(city.lower())
        
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    data = [json.loads(row[0]) for row in rows]
    
    if search:
        search_lower = search.lower()
        results = []
        for lawyer in data:
            if (search_lower in lawyer["name"].lower() or
                search_lower in lawyer.get("bio", "").lower() or
                search_lower in lawyer["specialization"].lower()):
                results.append(lawyer)
        return results
        
    return data

@router.post("/api/book-lawyer", dependencies=[Depends(check_rate_limit_data)])
def book_lawyer(req: BookLawyerRequest, user_id: int = Depends(get_current_user)):
    try:
        booking_date = datetime.strptime(req.date, "%Y-%m-%d").date()
        if booking_date < date.today():
            raise HTTPException(status_code=400, detail="Cannot book a consultation slot in the past.")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Expected YYYY-MM-DD.")

    # Load lawyers to validate ID and get details from SQLite
    conn = sqlite3.connect(DATABASE_FILE)
    try:
        cursor = conn.cursor()
        
        # Get active user email and name for security
        cursor.execute("SELECT email, name FROM users WHERE id = ?", (user_id,))
        user_row = cursor.fetchone()
        if not user_row:
            raise HTTPException(status_code=404, detail="User not found")
        user_email, user_name = user_row
        
        # Enforce email identity isolation
        req_email = user_email
        req_name = req.client_name if req.client_name else user_name
        
        cursor.execute("SELECT raw_json FROM lawyers WHERE id = ?", (req.lawyer_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Lawyer not found")
            
        lawyer = json.loads(row[0])
        
        # Generate booking code
        booking_code = "ND-" + os.urandom(3).hex().upper()
        
        # Save booking to SQLite with encrypted PII
        now_str = datetime.now().isoformat()
        cursor.execute("""
        INSERT INTO bookings (lawyer_id, lawyer_name, lawyer_specialty, booking_date, booking_slot, client_name, client_email, client_phone, client_grievance, booking_code, status, created_at, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            req.lawyer_id, lawyer["name"], lawyer["specialization"], req.date, req.slot,
            encrypt_field(req_name), encrypt_field(req_email),
            encrypt_field(req.client_phone), encrypt_field(req.details),
            booking_code, "Confirmed", now_str, now_str
        ))
        conn.commit()
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to save booking to SQLite")
        raise HTTPException(status_code=500, detail="Failed to save booking due to database error.")
    finally:
        conn.close()
    
    # Construct Client Email Content
    client_subject = f"Needhi AI: Legal Consultation Ticket - {booking_code}"
    client_body = f"""Dear {req_name},
 
Your legal consultation with {lawyer['name']} has been successfully scheduled.
 
--- CONSULTATION TICKET ---
Ticket Code: {booking_code}
Lawyer: {lawyer['name']} ({lawyer['specialization']})
Date: {req.date}
Time Slot: {req.slot}
Fee: ₹{lawyer['fee']} (Payable to the lawyer)
 
Client Contact Details:
Name: {req_name}
Phone: {req.client_phone}
Email: {req_email}
 
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
 
A new legal consultation has been scheduled with you by {req_name}.
 
--- CONSULTATION DETAILS ---
Ticket Code: {booking_code}
Date: {req.date}
Time Slot: {req.slot}
Fee: ₹{lawyer['fee']} (Collectable from the client)
 
Client Contact Details:
Name: {req_name}
Phone: {req.client_phone}
Email: {req_email}
 
Advocate Contact Details (Your Info):
Phone: {lawyer['phone']}
Email: {lawyer['email']}
City: {lawyer['city']}
 
Case Summary provided by client:
{req.details}
 
Thank you for using Needhi AI.
"""
    
    # Send email notifications separately
    client_recipients = [{"email": req_email, "name": req_name}]
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

@router.get("/api/bookings/my-bookings")
def get_my_bookings(user_id: int = Depends(get_current_user)):
    conn = sqlite3.connect(DATABASE_FILE)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT email FROM users WHERE id = ?", (user_id,))
        user_row = cursor.fetchone()
        if not user_row:
            raise HTTPException(status_code=404, detail="User not found.")
        user_email = user_row[0].strip().lower()
        
        cursor.execute("SELECT id, lawyer_id, lawyer_name, lawyer_specialty, booking_date, booking_slot, client_name, client_email, client_phone, client_grievance, booking_code, status, created_at FROM bookings")
        rows = cursor.fetchall()
        
        my_bookings = []
        for r in rows:
            decrypted_email = decrypt_field(r[7]).strip().lower()
            if decrypted_email == user_email:
                my_bookings.append({
                    "id": r[0],
                    "lawyer_id": r[1],
                    "lawyer_name": r[2],
                    "lawyer_specialty": r[3],
                    "date": r[4],
                    "slot": r[5],
                    "client_name": decrypt_field(r[6]),
                    "client_email": decrypted_email,
                    "client_phone": decrypt_field(r[8]),
                    "details": decrypt_field(r[9]),
                    "booking_code": r[10],
                    "status": r[11],
                    "created_at": r[12]
                })
        return my_bookings
    finally:
        conn.close()

