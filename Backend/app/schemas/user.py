from pydantic import BaseModel, EmailStr
from enum import Enum

class UserRole(str, Enum):
    admin = "Admin"
    supervisor = "Supervisor"
    tecnico = "Tecnico"
    consultor = "Consultor"

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: UserRole = UserRole.tecnico

class UserRead(BaseModel):
    email: EmailStr
    role: UserRole

class UserUpdate(BaseModel):
    email: EmailStr
    role: UserRole