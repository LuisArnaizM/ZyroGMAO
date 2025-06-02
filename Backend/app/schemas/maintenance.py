from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class MaintenanceCreate(BaseModel):
    asset_id: int
    user_id: int
    description: str

class MaintenanceRead(BaseModel):
    id: int
    asset_id: int
    user_id: int
    description: str
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class MaintenanceUpdate(BaseModel):
    description: Optional[str] = None
    status: Optional[str] = None
    user_id: Optional[int] = None