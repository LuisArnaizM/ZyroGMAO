from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class FailureCreate(BaseModel):
    asset_id: int
    description: str

class FailureRead(BaseModel):
    id: int
    asset_id: int
    description: str
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class FailureUpdate(BaseModel):
    description: Optional[str] = None
    status: Optional[str] = None

# Para mantener compatibilidad con código existente
MaintenanceRequestCreate = FailureCreate
MaintenanceRequestRead = FailureRead
MaintenanceRequestUpdate = FailureUpdate