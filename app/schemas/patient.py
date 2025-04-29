# app/schemas/patient.py
from enum import Enum
from pydantic import BaseModel
from typing  import Optional
from datetime import datetime

class EthnicityEnum(str, Enum):
    asian      = "asian"
    black      = "black"
    white      = "white"
    hispanic   = "hispanic"
    indigenous = "indigenous"
    other      = "other"
    unknown    = "unknown"

class GenderEnum(str, Enum):
    male    = "male"
    female  = "female"
    other   = "other"
    unknown = "unknown"

class PatientCreate(BaseModel):
    first_name:             str
    last_name:              str
    dob:                    str
    ethnicity:              EthnicityEnum
    gender:                 GenderEnum

    past_diagnoses:         Optional[str] = None
    family_medical_history: Optional[str] = None
    current_prescriptions:  Optional[str] = None
    smoking_status:         Optional[bool]  = None
    alcohol_status:         Optional[bool]  = None
    drug_use:               Optional[bool]  = None

class PatientUpdate(BaseModel):
    first_name:             Optional[str] = None
    last_name:              Optional[str] = None
    dob:                    Optional[str] = None
    ethnicity:              Optional[EthnicityEnum] = None
    gender:                 Optional[GenderEnum]    = None

    past_diagnoses:         Optional[str] = None
    family_medical_history: Optional[str] = None
    current_prescriptions:  Optional[str] = None
    smoking_status:         Optional[bool]  = None
    alcohol_status:         Optional[bool]  = None
    drug_use:               Optional[bool]  = None

class PatientRead(BaseModel):
    id:                      int
    first_name:              str
    last_name:               str
    dob:                      str
    ethnicity:               EthnicityEnum
    gender:                  GenderEnum

    past_diagnoses:         Optional[str]
    informed_consent_doc:   Optional[str]
    related_reports_doc:    Optional[str]
    family_medical_history: Optional[str]
    current_prescriptions:  Optional[str]
    smoking_status:         Optional[bool]
    alcohol_status:         Optional[bool]
    drug_use:               Optional[bool]

    added_at:               datetime
    added_by_user_id:       int

    class Config:
        from_attributes = True
