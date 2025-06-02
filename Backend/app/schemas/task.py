from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class TaskCreate(BaseModel):
    name: str
    description: Optional[str] = None
    assigned_to: Optional[int] = None  # User ID
    machine_id: Optional[int] = None  # Machine ID
    due_date: Optional[datetime] = None

class TaskRead(TaskCreate):
    id: int
    created_at: datetime
    updated_at: datetime

class TaskUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    assigned_to: Optional[int] = None  # User ID
    machine_id: Optional[int] = None  # Machine ID
    due_date: Optional[datetime] = None