from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.auth.security import decode_token
from app.database.postgres import get_db
from app.models.user import User
from typing import Optional
from typing import Optional
from app.config import settings
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.postgres import get_db
from sqlalchemy.future import select
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login",
    scheme_name="JWT"
)
# Lista para almacenar tokens inválidos (logout)
# En producción, usar Redis o base de datos
blacklisted_tokens = set()

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Verificar si el token está en la lista negra
    if token in blacklisted_tokens:
        raise credentials_exception
    
    try:
        payload = decode_token(token)

        email: str = payload.get("sub")
        username: str = payload.get("username")
        role: str = payload.get("role")
        user_id: int = payload.get("user_id")
        first_name: str = payload.get("first_name")
        last_name: str = payload.get("last_name")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # Verificar que el usuario existe y está activo
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    
    if user is None or user.is_active == 0:
        raise credentials_exception
    
    return {
        "id": user_id,
        "email": email,
        "username": username,
        "first_name": first_name,
        "last_name": last_name,
    "role": role,
        "full_name": f"{first_name} {last_name}"
    }


async def get_optional_user(request: Request, db: AsyncSession = Depends(get_db)):
    """Return user dict if Authorization header present and token valid, else None."""
    auth = request.headers.get("authorization")
    if not auth:
        return None

    parts = auth.split()
    if len(parts) != 2:
        return None
    token = parts[1]

    try:
        payload = decode_token(token)
        email: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        first_name: str = payload.get("first_name")
        last_name: str = payload.get("last_name")
        username: str = payload.get("username")
        role: str = payload.get("role")
        if email is None:
            return None
    except JWTError:
        return None

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None or user.is_active == 0:
        return None
    return {
        "id": user_id,
        "email": email,
        "username": username,
        "first_name": first_name,
        "last_name": last_name,
        "role": role,
        "full_name": f"{first_name} {last_name}",
    }

def require_role(roles: list):
    def dependency(user=Depends(get_current_user)):
        if user["role"] not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return user
    return dependency

def logout_token(token: str):
    """Añadir token a la lista negra"""
    blacklisted_tokens.add(token)

async def get_current_organization():
    # Organización eliminada del modelo. Mantener stub por compatibilidad si hay endpoints que aún la declaran.
    raise HTTPException(status_code=410, detail="Organization scope removed")

async def get_organization_from_domain():
    return None

def require_org_admin():
    """Requerir que el usuario sea administrador de organización o sistema"""
    def dependency(user = Depends(get_current_user)):
        if user["role"] not in ["Admin", "OrgAdmin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Organization admin privileges required"
            )
        return user
    return dependency

def require_same_organization():
    def dependency(user = Depends(get_current_user)):
        raise HTTPException(status_code=410, detail="Organization scope removed")
    return dependency