from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from .user import UserReference
from app.models.enums import FailureSeverity, FailureStatus


class FailureCreate(BaseModel):
    description: str
    asset_id: Optional[int] = None
    component_id: Optional[int] = None
    severity: FailureSeverity = FailureSeverity.MEDIUM


class FailureRead(BaseModel):
    id: int
    description: str
    # 'PENDING' | 'INVESTIGATING' | 'RESOLVED' | ...
    status: FailureStatus
    severity: FailureSeverity
    asset_id: Optional[int] = None
    component_id: Optional[int] = None
    reported_by: int
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
    # Use enum types on input where possible; Pydantic will coerce
    status: Optional[FailureStatus] = None
    severity: Optional[FailureSeverity] = None
    resolved_date: Optional[datetime] = None
    resolution_notes: Optional[str] = None