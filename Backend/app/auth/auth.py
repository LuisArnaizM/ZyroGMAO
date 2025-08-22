from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_
from passlib.context import CryptContext
from datetime import timedelta, datetime
import secrets
import uuid

from app.database.postgres import get_db
from app.models.user import User
from app.auth.security import create_token, decode_token
from app.config import settings
from app.schemas.user import ChangePasswordRequest, ForgotPasswordRequest, ResetPasswordRequest

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def authenticate_user(login: str, password: str, db: AsyncSession):
    """Autentica usuario por username o email"""
    result = await db.execute(
        select(User).where(
            or_(User.email == login, User.username == login)
        )
    )
    user = result.scalar_one_or_none()
    
    if not user or user.is_active == 0:  # 0 = inactivo
        return False
    if not pwd_context.verify(password, user.hashed_password):
        return False
    
    return user

async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm,
    db: AsyncSession
):
    user = await authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    access_token, exp_access = create_token(
        {
            "sub": user.email,
            "username": user.username,
            "role": user.role,
            "user_id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name
        },
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
    )

    refresh_token, exp_refresh = create_token(
        {"sub": user.email, "type": "refresh"},
        expires_delta=timedelta(days=settings.refresh_token_expire_days)
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": exp_access.isoformat(),
        "user": {
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "role": user.role,
            "full_name": f"{user.first_name} {user.last_name}"
        }
    }

async def refresh_access_token(refresh_token: str, db: AsyncSession):
    """Genera un nuevo access token usando el refresh token"""
    try:
        payload = decode_token(refresh_token)
        email = payload.get("sub")
        token_type = payload.get("type")

        if not email or token_type != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        # Buscar el usuario
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if not user or user.is_active == 0:
            raise HTTPException(status_code=401, detail="User not found or inactive")

        # Crear nuevo access token
        access_token, exp_access = create_token(
            {
                "sub": user.email,
                "username": user.username,
                "role": user.role,
                "user_id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name,
            },
            expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": exp_access.isoformat(),
        }

    except Exception:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

async def change_password(user_id: int, change_request: ChangePasswordRequest, db: AsyncSession):
    """Cambiar contraseña del usuario"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verificar contraseña actual
    if not pwd_context.verify(change_request.current_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    # Actualizar contraseña
    user.hashed_password = pwd_context.hash(change_request.new_password)
    
    await db.commit()
    return {"message": "Password changed successfully"}

async def forgot_password(email: str, db: AsyncSession):
    """Generar token para resetear contraseña"""
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    
    if not user:
        # No revelar si el email existe o no por seguridad
        return {"message": "If the email exists, you will receive a password reset link"}
    
    # Generar token único
    reset_token = str(uuid.uuid4())
    return {
        "message": "If the email exists, you will receive a password reset link",
        "reset_token": reset_token,
        "email": email
    }

async def reset_password(reset_request: ResetPasswordRequest, db: AsyncSession):
    """Resetear contraseña usando el token"""

    return {"message": "Password reset functionality not fully implemented yet"}