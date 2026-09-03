import os
import re
import urllib.request
import json
import logging
from typing import List
from core.config import ROOT_DIR

logger = logging.getLogger("needhi.utils")

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
    text = re.sub(r'[*#`]', '', text)
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
    Returns a tuple (success: bool, status_message: str).
    Reads SMTP_HOST/SMTP_PORT/BREVO_API_KEY from environment variables directly.
    """
    smtp_host = os.environ.get("SMTP_HOST", "")
    smtp_port = os.environ.get("SMTP_PORT", "")
    smtp_user = os.environ.get("SMTP_USER", "")
    smtp_password = os.environ.get("SMTP_PASSWORD", "")
    resend_key = os.environ.get("RESEND_API_KEY", "")
    brevo_key = os.environ.get("BREVO_API_KEY", "")
    email_from = os.environ.get("EMAIL_FROM", "")
    
    to_emails = [r["email"] for r in recipients]
    
    if resend_key:
        try:
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
            
    logger.info(f"Simulated email dispatch: Subject='{subject}' to {to_emails}")
    return False, "Simulated email dispatch (No API keys or SMTP configured)"

def send_otp_email(email: str, name: str, otp_code: str, purpose: str = "login") -> tuple:
    """
    Dispatches a professional OTP verification email to the user's Gmail.
    """
    subject = f"{otp_code} is your Needhi AI Verification Code"
    action_text = "complete your registration" if purpose == "register" else "sign in to your Needhi AI account"
    display_name = name if name else "Citizen"
    
    body = f"""Dear {display_name},

Your Needhi AI one-time verification code (OTP) is:

    {otp_code}

Use this 6-digit code to {action_text}.
This code is confidential and will expire in 10 minutes.

If you did not request this verification code, please ignore this email.

Warm regards,
Needhi AI Legal Assistant
Free AI-Powered Legal Aid for Indian Law
https://needhi-ai.onrender.com
"""
    return send_email_notification([{"email": email, "name": display_name}], subject, body)

