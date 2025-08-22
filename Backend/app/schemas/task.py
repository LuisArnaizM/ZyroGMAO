from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from .user import UserReference
from app.models.enums import TaskStatus, TaskPriority


class TaskUsedComponentIn(BaseModel):
    component_id: int
    quantity: float

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: Optional[datetime] = None
    estimated_hours: Optional[float] = None
    completion_notes: Optional[str] = None
    assigned_to: Optional[int] = None
    asset_id: Optional[int] = None
    component_id: Optional[int] = None  # Reemplaza machine_id
    workorder_id: Optional[int] = None

class TaskRead(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    status: TaskStatus
    priority: TaskPriority
    due_date: Optional[datetime] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    completion_notes: Optional[str] = None
    assigned_to: Optional[int] = None
    asset_id: Optional[int] = None
    component_id: Optional[int] = None  # Reemplaza machine_id
    workorder_id: Optional[int] = None
    created_by_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class TaskReadWithUsers(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    status: TaskStatus
    priority: TaskPriority
    due_date: Optional[datetime] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    completion_notes: Optional[str] = None
    assigned_to: Optional[int] = None
    assignee: Optional[UserReference] = None
    asset_id: Optional[int] = None
    component_id: Optional[int] = None  # Reemplaza machine_id
    workorder_id: Optional[int] = None
    created_by_id: int
    creator: Optional[UserReference] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    due_date: Optional[datetime] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    completion_notes: Optional[str] = None
    assigned_to: Optional[int] = None
    asset_id: Optional[int] = None
    component_id: Optional[int] = None  # Reemplaza machine_id
    workorder_id: Optional[int] = None
    used_components: Optional[List[TaskUsedComponentIn]] = None


class TaskCompleteItemIn(BaseModel):
    component_id: int
    quantity: float


class TaskCompleteRequest(BaseModel):
    notes: Optional[str] = None  # alias para completion_notes
    description: Optional[str] = None
    actual_hours: Optional[float] = None
    used_components: Optional[List[TaskCompleteItemIn]] = None