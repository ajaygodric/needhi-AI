from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional

class ChatMessage(BaseModel):
    role: str = Field(..., max_length=10)
    text: str = Field(..., max_length=8000)

class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    language: str = Field(..., max_length=20)
    history: List[ChatMessage] = Field(default=[], max_length=30)

class PDFGenerateRequest(BaseModel):
    title: str = Field(..., max_length=200)
    text: str = Field(..., max_length=50000)

class FIRRequest(BaseModel):
    issue: str = Field(..., min_length=10, max_length=5000)
    state: str = Field(..., max_length=100)
    ps: str = Field(..., max_length=200)
    name: str = Field(..., max_length=200)
    category: Optional[str] = Field(None, max_length=50)
    category_fields: Optional[dict] = None

class TemplateRequest(BaseModel):
    template_type: str = Field(..., max_length=100)
    fields: dict

class BookLawyerRequest(BaseModel):
    lawyer_id: int
    client_name: str = Field(..., min_length=2, max_length=100)
    client_email: EmailStr = Field(..., max_length=255)
    client_phone: str = Field(..., min_length=10, max_length=15)
    date: str = Field(..., min_length=10, max_length=10)
    slot: str = Field(..., min_length=3, max_length=30)
    details: str = Field(..., max_length=1000)

class BnsCompareRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)

class ChatDocRequest(BaseModel):
    doc_text: str = Field(..., max_length=50000)
    query: str = Field(..., min_length=1, max_length=2000)
    language: str = Field(..., max_length=20)
    history: List[ChatMessage] = Field(default=[], max_length=30)

class PredictOutcomeRequest(BaseModel):
    offense: str = Field(..., max_length=500)
    narrative: str = Field(..., max_length=3000)
    evidence: List[str] = Field(default=[], max_length=20)
    prior_record: str = Field(..., max_length=500)
    jurisdiction: str = Field(..., max_length=100)
    language: str = Field(..., max_length=20)

class SimplifyTextRequest(BaseModel):
    text: str = Field(..., min_length=10, max_length=10000)
    target_language: str = Field(..., max_length=20)

class CaseSubscribeRequest(BaseModel):
    cnr: str = Field(..., min_length=10, max_length=30)
    email: EmailStr = Field(..., max_length=255)
    client_name: str = Field(..., min_length=2, max_length=100)
    language: str = Field("English", max_length=20)

class BnsLookupRequest(BaseModel):
    term: str = Field(default="", max_length=200)
    category: str = Field(default="", max_length=100)

class UserRegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr = Field(..., max_length=255)
    password: str = Field(..., min_length=6, max_length=100)

class UserLoginRequest(BaseModel):
    email: EmailStr = Field(..., max_length=255)
    password: str = Field(..., min_length=6, max_length=100)

class AuthResponse(BaseModel):
    token: str
    name: str
    email: EmailStr

class UserMeResponse(BaseModel):
    name: str
    email: EmailStr

class SearchHistoryItem(BaseModel):
    query: str
    timestamp: float

