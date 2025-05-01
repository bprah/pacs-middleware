# app/api/routers/datafiles.py

from fastapi import (
    APIRouter, Depends, HTTPException,
    UploadFile, File, Form, status
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
import httpx, pydicom, io, os, shutil

from app.api.dependencies import get_db, check_roles
from app.db.crud.crud_datafile import (
    create_datafile,
    list_datafiles,
    get_datafile_by_orthanc_id,
)
from app.schemas.datafile import DataFileCreate, DataFileRead
from app.db.models import FileTypeEnum

router = APIRouter(
    prefix="/files",
    tags=["files"],
    dependencies=[Depends(check_roles(["admin", "researcher"]))],
)

ORTHANC_URL  = "http://localhost:8042/instances"
ORTHANC_AUTH = ("orthanc", "orthanc")

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.get("", response_model=list[DataFileRead])
async def get_all_files(db: AsyncSession = Depends(get_db)):
    """List all file‐metadata entries."""
    return await list_datafiles(db)


@router.post("", response_model=DataFileRead, status_code=status.HTTP_201_CREATED)
async def upload_file(
    data_name:         str            = Form(...),
    project_id:        int            = Form(...),
    patient_id:        int            = Form(...),
    modality:          str            = Form(...),
    access_level:      str            = Form(...),
    file_type:         FileTypeEnum   = Form(...),
    body_area:         str | None     = Form(None),
    related_report_id: int | None     = Form(None),
    comments:          str | None     = Form(None),
    upload:            UploadFile     = File(...),
    db:                AsyncSession   = Depends(get_db),
):
    """
    Dispatch based on file_type:
      - DICOM → validate + forward to Orthanc, guard against duplicates
      - else  → save locally
    """

    # Build our Pydantic‐validated input
    df_in = DataFileCreate(
      data_name=data_name,
      project_id=project_id,
      patient_id=patient_id,
      modality=modality,         # coerced to ModalityEnum
      access_level=access_level, # coerced to AccessLevelEnum
      body_area=body_area,       # coerced to BodyAreaEnum
      related_report_id=related_report_id,
      comments=comments,
      file_type=file_type,
    )

    # Read the entire upload into memory once
    contents = await upload.read()

    if file_type is FileTypeEnum.DICOM:
        # ─── 1) Validate as DICOM ────────────────────────────────────────────
        try:
            pydicom.dcmread(io.BytesIO(contents))
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Not a valid DICOM file"
            )

        # ─── 2) Send to Orthanc ─────────────────────────────────────────────
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                ORTHANC_URL,
                content=contents,
                auth=ORTHANC_AUTH,
                headers={"Content-Type": "application/dicom"},
                timeout=30.0,
            )

        # Catch an Orthanc‐side conflict
        if resp.status_code == status.HTTP_409_CONFLICT:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This DICOM instance already exists in Orthanc"
            )
        if resp.status_code != status.HTTP_200_OK:
            detail = await resp.text()
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Orthanc error {resp.status_code}: {detail}"
            )

        orthanc_id = resp.json().get("ID")
        if not orthanc_id:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Orthanc did not return an instance ID"
            )

        # ─── 3) App-level guard against duplicate orthanc_id in our DB ──────
        existing = await get_datafile_by_orthanc_id(db, orthanc_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This DICOM instance has already been recorded locally"
            )

        # ─── 4) Persist to our DB, translating any race-condition errors ────
        try:
            df = await create_datafile(
                db,
                df_in,
                orthanc_id=orthanc_id,
                storage_path=None
            )
        except IntegrityError:
            # in case a race slipped through
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Duplicate datafile record"
            )

        return df

    # ─── Generic file (PDF, JPG, etc.) ────────────────────────────────────
    safe_name = data_name.replace(" ", "_")
    filename  = f"{file_type.value}_{safe_name}_{upload.filename}"
    path      = os.path.join(UPLOAD_DIR, filename)
    with open(path, "wb") as buf:
        shutil.copyfileobj(upload.file, buf)

    # No Orthanc step—just record `storage_path`
    df = await create_datafile(
        db,
        df_in,
        orthanc_id=None,
        storage_path=path
    )
    return df
