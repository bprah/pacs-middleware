# app/schemas/registration.py
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class RegistrationRequest(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str

class PendingRegistrationRead(BaseModel):
    id: int
    email: EmailStr
    first_name: str
    last_name: str
    status: str
    submitted_at: datetime

    class Config:
        orm_mode = True

