from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.auth.security import decode_token
from app.database.postgres import get_db
from app.models.user import User
from app.models.organization import Organization
from typing import Optional
from app.config import settings

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
        organization_id: Optional[int] = payload.get("organization_id")
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
        "organization_id": organization_id,
        "full_name": f"{first_name} {last_name}"
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

async def get_current_organization(
    user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Organization:
    """Obtener la organización del usuario actual"""
    if not user.get("organization_id"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not associated with any organization"
        )
    
    result = await db.execute(
        select(Organization).where(
            Organization.id == user["organization_id"],
            Organization.is_active == True
        )
    )
    organization = result.scalar_one_or_none()
    
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found or inactive"
        )
    
    return organization

async def get_organization_from_domain(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Optional[Organization]:
    """Obtener organización basada en el dominio de la request"""
    host = request.headers.get("host", "").split(":")[0]  # Remover puerto si existe
    
    if not host:
        return None
    
    result = await db.execute(
        select(Organization).where(
            Organization.domain == host,
            Organization.is_active == True
        )
    )
    
    return result.scalar_one_or_none()

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
    """Requerir que el usuario pertenezca a la misma organización"""
    def dependency(
        user = Depends(get_current_user),
        organization: Organization = Depends(get_current_organization)
    ):
        if user["organization_id"] != organization.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: different organization"
            )
        return user, organization
    return dependency