from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from .user import UserReference
from app.models.enums import MaintenanceType, MaintenanceStatus

class MaintenanceCreate(BaseModel):
    description: str
    asset_id: int
    user_id: int
    maintenance_type: MaintenanceType = MaintenanceType.PREVENTIVE
    scheduled_date: Optional[datetime] = None
    workorder_id: Optional[int] = None

class MaintenanceRead(BaseModel):
    id: int
    description: str
    status: MaintenanceStatus
    maintenance_type: MaintenanceType
    asset_id: int
    user_id: int
    workorder_id: Optional[int] = None
    scheduled_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None
    duration_hours: Optional[float] = None
    cost: Optional[float] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class MaintenanceReadWithUser(MaintenanceRead):
    technician: Optional[UserReference] = None
    
    class Config:
        from_attributes = True

class MaintenanceUpdate(BaseModel):
    description: Optional[str] = None
    status: Optional[str] = None
    maintenance_type: Optional[str] = None
    user_id: Optional[int] = None
    scheduled_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None
    duration_hours: Optional[float] = None
    cost: Optional[float] = None
    notes: Optional[str] = None
    workorder_id: Optional[int] = None