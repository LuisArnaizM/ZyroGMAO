from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class WorkOrderCreate(BaseModel):
    task_id: int
    maintenance_id: int  # Ahora hace referencia a failures.id
    description: Optional[str] = None
    status: str = "pending"

class WorkOrderRead(BaseModel):
    id: int
    task_id: int
    maintenance_id: int
    status: str
    description: Optional[str] = None
    created_by: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class WorkOrderUpdate(BaseModel):
    task_id: Optional[int] = None
    maintenance_id: Optional[int] = None
    description: Optional[str] = None
    status: Optional[str] = None