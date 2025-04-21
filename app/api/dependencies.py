# app/api/dependencies.py
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import async_session

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from typing import List
from app.core.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user_data(token: str = Depends(oauth2_scheme)) -> dict:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        # payload should contain 'sub', 'user_id', 'roles', 'exp'
        return payload
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

def check_roles(required_roles: List[str]):
    def role_checker(user_data: dict = Depends(get_current_user_data)):
        if not any(r in user_data.get("roles", []) for r in required_roles):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return user_data
    return role_checker


async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session

