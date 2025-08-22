from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from .user import UserReference
from app.models.enums import WorkOrderType, WorkOrderStatus, WorkOrderPriority

class WorkOrderCreate(BaseModel):
    title: str
    description: Optional[str] = None
    work_type: WorkOrderType  # preventive, corrective, emergency
    status: WorkOrderStatus = WorkOrderStatus.OPEN
    priority: WorkOrderPriority = WorkOrderPriority.MEDIUM
    estimated_hours: Optional[float] = None
    estimated_cost: Optional[float] = None
    scheduled_date: Optional[datetime] = None
    asset_id: int
    assigned_to: Optional[int] = None
    failure_id: Optional[int] = None
    department_id: Optional[int] = None

class WorkOrderRead(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    work_type: WorkOrderType
    status: WorkOrderStatus
    priority: WorkOrderPriority
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    estimated_cost: Optional[float] = None
    actual_cost: Optional[float] = None
    scheduled_date: Optional[datetime] = None
    started_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None
    asset_id: int
    assigned_to: Optional[int] = None
    created_by: int
    failure_id: Optional[int] = None
    department_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class WorkOrderReadWithUsers(WorkOrderRead):
    assigned_user: Optional[UserReference] = None
    created_by_user: Optional[UserReference] = None
    
    class Config:
        from_attributes = True

class WorkOrderUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    work_type: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    estimated_cost: Optional[float] = None
    actual_cost: Optional[float] = None
    scheduled_date: Optional[datetime] = None
    started_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None
    assigned_to: Optional[int] = None
    failure_id: Optional[int] = None
    department_id: Optional[int] = None