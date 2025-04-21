# app/schemas/registration.py
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from typing import List


class RegistrationRequest(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    mobile_phone: Optional[str] = None
    organisation: Optional[str] = None
    # For file uploads, we won’t include them here since files come via UploadFile

class PendingRegistrationRead(BaseModel):
    id: int
    email: EmailStr
    first_name: str
    last_name: str
    mobile_phone: Optional[str] = None
    organisation: Optional[str] = None
    research_id_doc: Optional[str] = None
    ethics_approval_doc: Optional[str] = None
    confidentiality_agreement_doc: Optional[str] = None
    status: str
    submitted_at: datetime

    class Config:
        from_attributes = True 


class RegistrationApprove(BaseModel):
    role_ids: List[int]
