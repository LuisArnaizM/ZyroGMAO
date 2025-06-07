from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    username: str
    first_name: str
    last_name: str
    email: EmailStr
    password: str
    role: str
    organization_id: Optional[int] = None  # Para super admin que crea usuarios

class UserRead(BaseModel):
    id: int
    username: str
    first_name: str
    last_name: str
    email: str
    role: str
    is_active: int
    organization_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class UserReadWithOrganization(UserRead):
    organization: Optional["OrganizationRead"] = None
    
    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    is_active: Optional[int] = None
    organization_id: Optional[int] = None  # Solo para super admin

class UserLogin(BaseModel):
    login: str
    password: str
    organization_slug: Optional[str] = None  # Para login multi-org

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr
    organization_slug: Optional[str] = None

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class UserProfile(BaseModel):
    id: int
    username: str
    first_name: str
    last_name: str
    email: str
    role: str
    is_active: int
    organization_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    full_name: str
    organization: Optional["OrganizationRead"] = None
    
    class Config:
        from_attributes = True
    
    @classmethod
    def from_user(cls, user):
        return cls(
            id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            role=user.role,
            is_active=user.is_active,
            organization_id=user.organization_id,
            created_at=user.created_at,
            updated_at=user.updated_at,
            full_name=f"{user.first_name} {user.last_name}",
            organization=user.organization
        )

class UserReference(BaseModel):
    id: int
    username: str
    first_name: str
    last_name: str
    full_name: str
    
    class Config:
        from_attributes = True
    
    @classmethod
    def from_user(cls, user):
        return cls(
            id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            full_name=f"{user.first_name} {user.last_name}"
        )

# Importar después para evitar dependencias circulares
from app.schemas.organization import OrganizationRead
UserReadWithOrganization.model_rebuild()
UserProfile.model_rebuild()