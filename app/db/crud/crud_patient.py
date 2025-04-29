# app/db/crud/crud_patient.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
from app.db.models import Patient
from app.schemas.patient import PatientCreate, PatientUpdate

async def get_all_patients(db: AsyncSession) -> List[Patient]:
    result = await db.execute(select(Patient))
    return result.scalars().all()

async def get_patient_by_id(db: AsyncSession, patient_id: int) -> Optional[Patient]:
    result = await db.execute(select(Patient).where(Patient.id == patient_id))
    return result.scalars().first()

async def create_patient(
    db: AsyncSession,
    data: PatientCreate,
    added_by_user_id: int,
    informed_consent_doc: Optional[str] = None,
    related_reports_doc:  Optional[str] = None,
) -> Patient:
    patient = Patient(
        **data.model_dump(),
        informed_consent_doc=informed_consent_doc,
        related_reports_doc=related_reports_doc,
        added_by_user_id=added_by_user_id,
    )
    db.add(patient)
    await db.commit()
    await db.refresh(patient)
    return patient

async def update_patient(
    db: AsyncSession,
    patient_id: int,
    data: PatientUpdate,
) -> Optional[Patient]:
    patient = await get_patient_by_id(db, patient_id)
    if not patient:
        return None
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(patient, field, value)
    await db.commit()
    await db.refresh(patient)
    return patient
