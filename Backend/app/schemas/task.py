from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from .user import UserReference

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    status: str = "pending"
    priority: str = "medium"
    due_date: Optional[datetime] = None
    assigned_to: Optional[int] = None
    asset_id: Optional[int] = None
    component_id: Optional[int] = None  # Reemplaza machine_id
    workorder_id: Optional[int] = None

class TaskRead(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    status: str
    priority: str
    due_date: Optional[datetime] = None
    assigned_to: Optional[int] = None
    asset_id: Optional[int] = None
    component_id: Optional[int] = None  # Reemplaza machine_id
    workorder_id: Optional[int] = None
    organization_id: int
    created_by_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class TaskReadWithUsers(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    status: str
    priority: str
    due_date: Optional[datetime] = None
    assigned_to: Optional[int] = None
    assignee: Optional[UserReference] = None
    asset_id: Optional[int] = None
    component_id: Optional[int] = None  # Reemplaza machine_id
    workorder_id: Optional[int] = None
    organization_id: int
    created_by_id: int
    creator: Optional[UserReference] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[datetime] = None
    assigned_to: Optional[int] = None
    asset_id: Optional[int] = None
    component_id: Optional[int] = None  # Reemplaza machine_id
    workorder_id: Optional[int] = None