from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from passlib.context import CryptContext
from datetime import timedelta

from app.database.postgres import get_db
from app.models.user import User
# Cambia esta línea para importar desde settings en lugar de security directamente
from app.auth.security import create_token
from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def authenticate_user(email: str, password: str, db: AsyncSession):
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    
    if not user:
        return False
    if not pwd_context.verify(password, user.hashed_password):
        return False
    
    return user

async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    user = await authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    access_token, exp_access = create_token(
        {"sub": user.email, "role": user.role},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
    )

    refresh_token, exp_refresh = create_token(
        {"sub": user.email},
        expires_delta=timedelta(days=settings.refresh_token_expire_days)
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": exp_access.isoformat()
    }
