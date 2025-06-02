from pydantic import BaseModel
from datetime import datetime

class MachineCreate(BaseModel):
    name: str
    description: str
    location: str
    responsible_id: int

class MachineRead(MachineCreate):
    id: int
    created_at: datetime

class MachineUpdate(BaseModel):
    name: str = None
    description: str = None
    location: str = None
    responsible_id: int = None