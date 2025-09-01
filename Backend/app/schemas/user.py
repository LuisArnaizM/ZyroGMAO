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
    department_id: Optional[int] = None
    hourly_rate: Optional[float] = 50.0

class UserRead(BaseModel):
    id: int
    username: str
    first_name: str
    last_name: str
    email: str
    role: str
    is_active: int
    department_id: Optional[int] = None
    hourly_rate: Optional[float] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class UserReadWithOrganization(UserRead):
    """Conservado por compatibilidad; ya no incluye organization."""
    pass

class UserUpdate(BaseModel):
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    is_active: Optional[int] = None
    department_id: Optional[int] = None
    hourly_rate: Optional[float] = None

class UserLogin(BaseModel):
    login: str
    password: str
    # Campo legacy eliminado: organization_slug

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

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
    department_id: Optional[int] = None
    hourly_rate: Optional[float] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
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
            email=user.email,
            role=user.role,
            is_active=user.is_active,
            department_id=getattr(user, 'department_id', None),
            hourly_rate=getattr(user, 'hourly_rate', None),
            created_at=user.created_at,
            updated_at=user.updated_at,
            full_name=f"{user.first_name} {user.last_name}",
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

# Limpieza de referencias a organization; clases listas sin dependencias adicionales