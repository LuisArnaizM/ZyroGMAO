from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class MachineCreate(BaseModel):
    name: str
    description: str
    location: str
    responsible_id: int

class MachineRead(BaseModel):
    id: int
    name: str
    description: str
    location: str
    responsible_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class MachineUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    responsible_id: Optional[int] = None