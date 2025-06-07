from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List
from .user import UserReference

class AssetCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    asset_type: str = Field(..., min_length=1, max_length=50)
    model: Optional[str] = Field(None, max_length=100)
    serial_number: Optional[str] = Field(None, max_length=100)
    location: Optional[str] = Field(None, max_length=200)
    status: str = Field(default="operational", max_length=50)
    purchase_cost: Optional[float] = Field(None, ge=0)
    current_value: Optional[float] = Field(None, ge=0)
    responsible_id: Optional[int] = None
    purchase_date: Optional[datetime] = None
    warranty_expiry: Optional[datetime] = None

class AssetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    description: Optional[str] = None
    asset_type: str
    model: Optional[str] = None
    serial_number: Optional[str] = None
    location: Optional[str] = None
    status: str
    purchase_cost: Optional[float] = None
    current_value: Optional[float] = None
    responsible_id: Optional[int] = None
    organization_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    purchase_date: Optional[datetime] = None
    warranty_expiry: Optional[datetime] = None

class AssetReadWithResponsible(AssetRead):
    responsible: Optional[UserReference] = None

class AssetUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    asset_type: Optional[str] = Field(None, min_length=1, max_length=50)
    model: Optional[str] = Field(None, max_length=100)
    serial_number: Optional[str] = Field(None, max_length=100)
    location: Optional[str] = Field(None, max_length=200)
    status: Optional[str] = Field(None, max_length=50)
    purchase_cost: Optional[float] = Field(None, ge=0)
    current_value: Optional[float] = Field(None, ge=0)
    responsible_id: Optional[int] = None
    purchase_date: Optional[datetime] = None
    warranty_expiry: Optional[datetime] = None

# Schema con componentes incluidos
class AssetWithComponents(AssetRead):
    total_components: Optional[int] = 0