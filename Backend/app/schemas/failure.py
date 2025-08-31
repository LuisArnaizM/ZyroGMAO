from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from .user import UserReference


class FailureCreate(BaseModel):
    description: str
    asset_id: Optional[int] = None
    component_id: Optional[int] = None
    severity: str = "MEDIUM"


class FailureRead(BaseModel):
    id: int
    description: str
    status: str
    severity: str
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
    # Use string types for consistency
    status: Optional[str] = None
    severity: Optional[str] = None
    resolved_date: Optional[datetime] = None
    resolution_notes: Optional[str] = None


class FailureWithWorkOrder(BaseModel):
    id: int
    description: str
    severity: str
    status: str
    reported_by: int
    reported_date: datetime
    resolved_date: Optional[datetime] = None
    asset_id: Optional[int] = None
    component_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    workorder_id: Optional[int] = None

    class Config:
        from_attributes = True