from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from .user import UserReference

class FailureCreate(BaseModel):
    description: str
    asset_id: int
    severity: str = "medium"

class FailureRead(BaseModel):
    id: int
    description: str
    status: str
    severity: str
    asset_id: int
    reported_by: int
    organization_id: int
    reported_date: datetime
    resolved_date: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class FailureReadWithUser(FailureRead):
    reported_by_user: Optional[UserReference] = None
    
    class Config:
        from_attributes = True

class FailureUpdate(BaseModel):
    description: Optional[str] = None
    status: Optional[str] = None
    severity: Optional[str] = None
    resolved_date: Optional[datetime] = None
    resolution_notes: Optional[str] = None