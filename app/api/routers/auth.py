# app/api/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, status, Form, UploadFile, File
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
import os
import shutil
from datetime import datetime, timedelta, timezone
import pyotp
from app.schemas.login import LoginRequest

from app.db.crud import crud_user, crud_pending_registration
from app.api.dependencies import get_db
from app.core import security

router = APIRouter()

###################################
#         REGISTRATION            #
###################################

@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
async def register_user(
    email: str = Form(...),
    password: str = Form(...),
    first_name: str = Form(...),
    last_name: str = Form(...),
    mobile_phone: Optional[str] = Form(None),
    organisation: Optional[str] = Form(None),
    research_id_doc: Optional[UploadFile] = File(None),
    ethics_approval_doc: Optional[UploadFile] = File(None),
    confidentiality_agreement_doc: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db)
):
    # Check if the email already exists in approved users.
    existing_user = await crud_user.get_user_by_email(db, email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered.")

    # Check if there is a pending registration for this email.
    existing_pending = await crud_pending_registration.get_pending_by_email(db, email)
    if existing_pending and existing_pending.status == "pending":
        raise HTTPException(status_code=400, detail="Registration already pending.")

    # Create uploads folder if it doesn't exist.
    upload_folder = "uploads"
    os.makedirs(upload_folder, exist_ok=True)

    def save_file(file: UploadFile, prefix: str) -> Optional[str]:
        if file:
            file_path = os.path.join(upload_folder, f"{prefix}_{file.filename}")
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            return file_path
        return None

    research_id_path = save_file(research_id_doc, "research_id")
    ethics_approval_path = save_file(ethics_approval_doc, "ethics_approval")
    confidentiality_agreement_path = save_file(confidentiality_agreement_doc, "confidentiality_agreement")

    # Combine all registration data into a dictionary.
    registration_data = {
        "email": email,
        "password": password,
        "first_name": first_name,
        "last_name": last_name,
        "mobile_phone": mobile_phone,
        "organisation": organisation,
        "research_id_doc": research_id_path,
        "ethics_approval_doc": ethics_approval_path,
        "confidentiality_agreement_doc": confidentiality_agreement_path,
    }

    pending = await crud_pending_registration.create_pending_registration(db, registration_data)
    from app.schemas.registration import PendingRegistrationRead
    return PendingRegistrationRead.from_orm(pending).model_dump()


###################################
#            LOGIN                #
###################################

@router.post("/login", response_model=dict)
async def login_user(login_req: LoginRequest, db: AsyncSession = Depends(get_db)):
    # Now we no longer need a local import inside the function
    # Retrieve user by email
    user = await crud_user.get_user_by_email(db, login_req.email)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    now = datetime.now(timezone.utc)
    
    if user.lock_until and user.lock_until > now:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account is locked until {user.lock_until.isoformat()}"
        )
    
    if not security.verify_password(login_req.password, user.hashed_password):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= 5:
            user.lock_until = now + timedelta(minutes=30)
            user.failed_login_attempts = 0
        await db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    if not user.is_totp_verified:
        if not user.totp_secret:
            user.totp_secret = pyotp.random_base32()
            await db.commit()
        totp = pyotp.TOTP(user.totp_secret)
        if not login_req.totp_code:
            qr_url = totp.provisioning_uri(name=user.email, issuer_name="InsightPACS")
            return {
                "totp_setup": True,
                "qr_code_url": qr_url,
                "detail": "Scan the QR code to set up TOTP and then retry login with the TOTP code."
            }
        else:
            if not totp.verify(login_req.totp_code):
                user.failed_login_attempts += 1
                await db.commit()
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid TOTP code")
            user.is_totp_verified = True
    else:
        if not login_req.totp_code:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="TOTP code required")
        totp = pyotp.TOTP(user.totp_secret)
        if not totp.verify(login_req.totp_code):
            user.failed_login_attempts += 1
            await db.commit()
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid TOTP code")
    
    user.failed_login_attempts = 0
    user.lock_until = None
    await db.commit()

    token_data = {
        "sub": user.email,
        "user_id": user.id,
        "roles": [role.name for role in user.roles]
    }
    access_token = security.create_access_token(data=token_data)
    return {"access_token": access_token, "token_type": "bearer"}