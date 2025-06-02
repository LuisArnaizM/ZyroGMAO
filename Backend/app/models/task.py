from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    assigned_to: int  # User ID
    machine_id: int  # Machine ID
    due_date: datetime

class TaskRead(TaskCreate):
    id: int
    created_at: datetime
    updated_at: datetime

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    assigned_to: Optional[int] = None
    machine_id: Optional[int] = None
    due_date: Optional[datetime] = None