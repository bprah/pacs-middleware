# app/api/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas import registration as reg_schema
from app.db.crud import crud_user, crud_pending_registration
from app.api.dependencies import get_db

router = APIRouter()

@router.post("/register", response_model=reg_schema.PendingRegistrationRead, status_code=status.HTTP_201_CREATED)
async def register_user(registration_req: reg_schema.RegistrationRequest, db: AsyncSession = Depends(get_db)):
    # Check if the email already exists in approved users.
    existing_user = await crud_user.get_user_by_email(db, registration_req.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered.")
    
    # Check if there is a pending registration for this email.
    existing_pending = await crud_pending_registration.get_pending_by_email(db, registration_req.email)
    if existing_pending and existing_pending.status == "pending":
        raise HTTPException(status_code=400, detail="Registration already pending.")
    
    # Create a new pending registration.
    pending = await crud_pending_registration.create_pending_registration(db, registration_req)
    return pending

