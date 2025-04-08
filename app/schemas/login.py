# app/schemas/login.py
from pydantic import BaseModel, EmailStr
from typing import Optional

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    totp_code: Optional[str] = None
