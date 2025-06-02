from pydantic import BaseModel
from datetime import datetime

class MaintenanceCreate(BaseModel):
    asset_id: int
    description: str

class MaintenanceRead(MaintenanceCreate):
    id: int
    status: str
    created_at: datetime

class MaintenanceUpdate(BaseModel):
    description: str
    status: str