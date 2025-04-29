# app/api/routers/patients.py
import os, shutil
from fastapi import (
    APIRouter, Depends, HTTPException, status,
    UploadFile, File, Form
)
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.schemas.patient import (
    PatientRead, PatientCreate, PatientUpdate,
    EthnicityEnum, GenderEnum,
)
from app.db.crud.crud_patient import (
    get_all_patients, get_patient_by_id,
    create_patient,   update_patient,
)
from app.api.dependencies import (
    get_db, get_current_user_data, check_roles,
)

router = APIRouter(prefix="/patients", tags=["patients"])

# ensure upload dir exists
PATIENT_UPLOAD_DIR = "uploads/patients"
os.makedirs(PATIENT_UPLOAD_DIR, exist_ok=True)

def save_patient_file(
    file: UploadFile,
    first_name: str,
    last_name: str,
    suffix: str
) -> Optional[str]:
    if not file:
        return None
    ext = os.path.splitext(file.filename)[1] or ".pdf"
    filename = f"{first_name}_{last_name}_{suffix}{ext}"
    path = os.path.join(PATIENT_UPLOAD_DIR, filename)
    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return path

# ── LIST ────────────────────────────────────────────────────
@router.get("", response_model=List[PatientRead])
async def list_patients(
    db: AsyncSession = Depends(get_db),
    _=Depends(check_roles(["admin", "researcher", "viewer"]))
):
    patients = await get_all_patients(db)
    return [PatientRead.from_orm(p).model_dump() for p in patients]

# ── CREATE ──────────────────────────────────────────────────
@router.post("", response_model=PatientRead, status_code=status.HTTP_201_CREATED)
async def register_patient(
    first_name:             str             = Form(...),
    last_name:              str             = Form(...),
    dob:                    str             = Form(...),
    ethnicity:              EthnicityEnum   = Form(...),
    gender:                 GenderEnum      = Form(...),

    past_diagnoses:         Optional[str]   = Form(None),
    family_medical_history: Optional[str]   = Form(None),
    current_prescriptions:  Optional[str]   = Form(None),
    smoking_status:         Optional[bool]  = Form(None),
    alcohol_status:         Optional[bool]  = Form(None),
    drug_use:               Optional[bool]  = Form(None),

    informed_consent_doc:   Optional[UploadFile] = File(None),
    related_reports_doc:    Optional[UploadFile] = File(None),

    db: AsyncSession = Depends(get_db),
    user_data=Depends(get_current_user_data),
):
    # save files with <first>_<last>_consent.pdf and _related.pdf
    consent_path = save_patient_file(informed_consent_doc, first_name, last_name, "consent")
    related_path = save_patient_file(related_reports_doc,    first_name, last_name, "related")

    create_data = PatientCreate(
        first_name=first_name,
        last_name=last_name,
        dob=dob,
        ethnicity=ethnicity,
        gender=gender,
        past_diagnoses=past_diagnoses,
        family_medical_history=family_medical_history,
        current_prescriptions=current_prescriptions,
        smoking_status=smoking_status,
        alcohol_status=alcohol_status,
        drug_use=drug_use,
    )
    new_patient = await create_patient(
        db,
        create_data,
        added_by_user_id=user_data["user_id"],
        informed_consent_doc=consent_path,
        related_reports_doc=related_path,
    )
    return PatientRead.from_orm(new_patient).model_dump()

# ── UPDATE ──────────────────────────────────────────────────
@router.put("/{patient_id}", response_model=PatientRead)
async def edit_patient(
    patient_id: int,
    payload: PatientUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(check_roles(["admin", "researcher"]))
):
    updated = await update_patient(db, patient_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Patient not found")
    return PatientRead.from_orm(updated).model_dump()

@router.get("/{patient_id}", response_model=PatientRead)
async def read_patient(
    patient_id: int,
    db: AsyncSession = Depends(get_db),
    _ = Depends(check_roles(["admin", "researcher", "viewer"]))
):
    patient = await get_patient_by_id(db, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return PatientRead.from_orm(patient).model_dump()
