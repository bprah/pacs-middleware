# app/schemas/project.py
from pydantic import BaseModel, Field
from typing  import List, Optional
from datetime import datetime

class ProjectCreate(BaseModel):
    name:           str
    description:    Optional[str]     = None
    lead_user_id:   int
    member_ids:     Optional[List[int]] = Field(default=[], max_items=12)

class ProjectUpdate(BaseModel):
    name:           Optional[str]       = None
    description:    Optional[str]       = None
    lead_user_id:   Optional[int]       = None
    member_ids:     Optional[List[int]] = Field(default=None, max_items=12)

class ProjectRead(BaseModel):
    id:             int
    name:           str
    description:    Optional[str]
    lead_user_id:   int
    member_ids:     List[int]
    created_at:     datetime
    updated_at:     Optional[datetime]

    class Config:
        from_attributes = True
