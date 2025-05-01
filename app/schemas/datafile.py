# app/schemas/datafile.py

from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.db.models import (
    ModalityEnum, AccessLevelEnum,
    BodyAreaEnum, FileTypeEnum
)

class DataFileCreate(BaseModel):
    data_name:         str
    project_id:        int
    patient_id:        int
    modality:          ModalityEnum
    access_level:      AccessLevelEnum
    body_area:         Optional[BodyAreaEnum]  = None
    related_report_id: Optional[int]           = None
    comments:          Optional[str]           = None
    file_type:         FileTypeEnum

class DataFileRead(BaseModel):
    id:                int
    data_name:         str
    project_id:        int
    patient_id:        int
    modality:          ModalityEnum
    access_level:      AccessLevelEnum
    body_area:         Optional[BodyAreaEnum]
    related_report_id: Optional[int]
    comments:          Optional[str]
    file_type:         FileTypeEnum
    orthanc_id:        Optional[str]
    storage_path:      Optional[str]
    uploaded_at:       datetime

    class Config:
        from_attributes = True
