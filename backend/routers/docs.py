import logging
from datetime import datetime
import google.generativeai as genai
from fpdf import FPDF
from fastapi import APIRouter, HTTPException, Depends, Response
from core.security import check_rate_limit_ai, sanitize_input_dict
from core.gemini import generate_gemini_content
from core.utils import get_tamil_font, clean_pdf_text
from core.schemas import TemplateRequest, PDFGenerateRequest

logger = logging.getLogger("needhi.routers.docs")

router = APIRouter()

@router.post("/api/generate-template", dependencies=[Depends(check_rate_limit_ai)])
def generate_template(req: TemplateRequest):
    special_guidelines = ""
    tt = req.template_type
    
    # Whitelist template fields to prevent prompt injection
    allowed_fields = set()
    if tt == "Rent Agreement":
        allowed_fields = {"landlord", "tenant", "address", "rent", "deposit", "duration"}
    elif tt == "Legal Notice":
        allowed_fields = {"sender", "receiver", "sender_addr", "receiver_addr", "subject", "details"}
    elif tt == "Affidavit":
        allowed_fields = {"name", "age", "state", "address", "content"}
    elif tt == "Bail Application":
        allowed_fields = {"accused", "court", "case_no", "ps", "grounds"}
    elif tt == "Consumer Complaint":
        allowed_fields = {"complainant", "opposite_party", "complainant_addr", "opposite_addr", "amount", "date", "complaint"}
    elif tt == "Non-Disclosure Agreement (NDA)":
        allowed_fields = {"disclosing_party", "receiving_party", "term_years", "jurisdiction", "purpose"}
    elif tt == "Promissory Note":
        allowed_fields = {"borrower", "lender", "amount", "interest_rate", "due_date", "city_state"}
    elif tt == "Power of Attorney":
        allowed_fields = {"principal", "agent", "principal_addr", "agent_addr", "property_schedule", "powers"}
    elif tt == "Counter-Notice":
        allowed_fields = {"sender", "receiver", "sender_addr", "receiver_addr", "original_notice_date", "original_claims", "counter_details"}
    elif tt == "RTI Application":
        allowed_fields = {"name", "address", "authority", "authority_addr", "information_sought", "period"}
    elif tt == "Police Commissioner Complaint":
        allowed_fields = {"complainant", "complainant_addr", "ps", "complaint_date", "details"}
    elif tt == "Banking Ombudsman Complaint":
        allowed_fields = {"complainant", "complainant_addr", "bank_name", "bank_branch", "account_no", "bank_complaint_date", "details"}
    elif tt == "RERA Complaint":
        allowed_fields = {"complainant", "builder", "project_name", "flat_no", "amount_paid", "details"}
        
    req.fields = sanitize_input_dict(req.fields, allowed_fields)
    
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

@router.post("/api/generate-pdf", dependencies=[Depends(check_rate_limit_ai)])
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
