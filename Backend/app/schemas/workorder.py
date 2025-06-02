from pydantic import BaseModel
from datetime import datetime

class WorkOrderCreate(BaseModel):
    task_id: int
    maintenance_id: int
    description: str
    status: str = "pending"

class WorkOrderRead(WorkOrderCreate):
    id: int
    created_at: datetime

class WorkOrderUpdate(BaseModel):
    status: str
    description: str = None