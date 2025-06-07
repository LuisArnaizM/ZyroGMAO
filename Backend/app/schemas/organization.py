from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class OrganizationCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    slug: str = Field(..., min_length=2, max_length=50, pattern="^[a-z0-9-]+$")
    description: Optional[str] = None
    domain: Optional[str] = None
    max_users: int = Field(default=100, ge=1, le=10000)
    max_assets: int = Field(default=1000, ge=1, le=100000)

class OrganizationRead(BaseModel):
    id: int
    name: str
    slug: str
    description: Optional[str] = None
    domain: Optional[str] = None
    is_active: bool
    max_users: int
    max_assets: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class OrganizationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = None
    domain: Optional[str] = None
    is_active: Optional[bool] = None
    max_users: Optional[int] = Field(None, ge=1, le=10000)
    max_assets: Optional[int] = Field(None, ge=1, le=100000)

class OrganizationStats(BaseModel):
    id: int
    name: str
    slug: str
    user_count: int
    asset_count: int
    machine_count: int  # Ahora representa component_count para compatibilidad
    active_tasks: int
    pending_failures: int
    max_users: int
    max_assets: int
    
    class Config:
        from_attributes = True