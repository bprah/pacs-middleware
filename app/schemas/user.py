from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

class UserRead(BaseModel):
    id: int
    email: EmailStr
    first_name: Optional[str]
    last_name: Optional[str]
    mobile_phone: Optional[str]
    organisation: Optional[str]
    roles: List[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class UserMe(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    mobile_phone: Optional[str]
    organisation: Optional[str]
    roles: List[str]
    is_totp_verified: bool

    class Config:
        from_attributes = True
        
class UserSummary(BaseModel):
    id:          int
    first_name:  str
    last_name:   str
    email:       EmailStr

    class Config:
        from_attributes = True