from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime
from typing import Optional, List
from .user import UserReference
from app.models.enums import AssetStatus
from .utils import normalize_enum_value

class AssetCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    asset_type: str = Field(..., min_length=1, max_length=50)
    model: Optional[str] = Field(None, max_length=100)
    serial_number: Optional[str] = Field(None, max_length=100)
    location: Optional[str] = Field(None, max_length=200)
    status: AssetStatus = AssetStatus.ACTIVE
    purchase_cost: Optional[float] = Field(None, ge=0)
    current_value: Optional[float] = Field(None, ge=0)
    responsible_id: Optional[int] = None
    purchase_date: Optional[datetime] = None
    warranty_expiry: Optional[datetime] = None
    
    @field_validator('status', mode='before')
    def _normalize_status_create(cls, v):
        return normalize_enum_value(v, AssetStatus)

class AssetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    description: Optional[str] = None
    asset_type: str
    model: Optional[str] = None
    serial_number: Optional[str] = None
    location: Optional[str] = None
    # 'Active' | 'Inactive' | 'Maintenance' | 'Retired'
    status: AssetStatus
    purchase_cost: Optional[float] = None
    current_value: Optional[float] = None
    responsible_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    purchase_date: Optional[datetime] = None
    warranty_expiry: Optional[datetime] = None
    
    @field_validator('status', mode='before')
    def _normalize_status_read(cls, v):
        return normalize_enum_value(v, AssetStatus)

class AssetReadWithResponsible(AssetRead):
    responsible: Optional[UserReference] = None

class AssetUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    asset_type: Optional[str] = Field(None, min_length=1, max_length=50)
    model: Optional[str] = Field(None, max_length=100)
    serial_number: Optional[str] = Field(None, max_length=100)
    location: Optional[str] = Field(None, max_length=200)
    status: Optional[AssetStatus] = None
    purchase_cost: Optional[float] = Field(None, ge=0)
    current_value: Optional[float] = Field(None, ge=0)
    responsible_id: Optional[int] = None
    purchase_date: Optional[datetime] = None
    warranty_expiry: Optional[datetime] = None

    @field_validator('status', mode='before')
    def _normalize_status_update(cls, v):
        return normalize_enum_value(v, AssetStatus)

# Schema con componentes incluidos
class AssetWithComponents(AssetRead):
    total_components: Optional[int] = 0
    # Lista opcional de componentes (resumen)
    components: Optional[List["ComponentRead"]] = None


# --- Validators to accept legacy strings like 'UNDER_MAINTENANCE' and normalize them
# Nota: normalización centralizada en app/schemas/utils.py


# (validators are defined inside each model class above)


# Evitar errores forward refs en tiempo de tipo
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .component import ComponentRead