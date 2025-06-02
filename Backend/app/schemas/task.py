from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class TaskCreate(BaseModel):
    name: str
    description: Optional[str] = None
    assigned_to: int  # Usuario asignado
    machine_id: int
    due_date: datetime

class TaskRead(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    assigned_to: int
    machine_id: int
    due_date: datetime
    created_by_id: int  # Cambiado de string a int para coincidir con el modelo
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class TaskUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    assigned_to: Optional[int] = None
    machine_id: Optional[int] = None
    due_date: Optional[datetime] = None