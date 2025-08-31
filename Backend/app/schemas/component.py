from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional
from datetime import datetime
from app.models.enums import ComponentStatus
from .utils import normalize_enum_value

# Schema base
class ComponentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    component_type: str = Field(..., min_length=1, max_length=50)  # motor, bomba, válvula, etc.
    model: Optional[str] = Field(None, max_length=100)
    serial_number: Optional[str] = Field(None, max_length=100)
    location: Optional[str] = Field(None, max_length=200)
    # Align with frontend statuses: 'Active' | 'Inactive' | 'Maintenance' | 'Retired'
    status: ComponentStatus = ComponentStatus.ACTIVE
    purchase_cost: Optional[float] = Field(None, ge=0)
    current_value: Optional[float] = Field(None, ge=0)
    maintenance_interval_days: Optional[int] = Field(None, ge=1)
    responsible_id: Optional[int] = None

# Schema para crear componente
class ComponentCreate(ComponentBase):
    asset_id: int = Field(..., description="ID del asset padre")
    installed_date: Optional[datetime] = None
    warranty_expiry: Optional[datetime] = None

    @field_validator('status', mode='before')
    def _normalize_status_create(cls, v):
        return normalize_enum_value(v, ComponentStatus)

# Schema para actualizar componente
class ComponentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    component_type: Optional[str] = Field(None, min_length=1, max_length=50)
    model: Optional[str] = Field(None, max_length=100)
    serial_number: Optional[str] = Field(None, max_length=100)
    location: Optional[str] = Field(None, max_length=200)
    status: Optional[ComponentStatus] = None
    purchase_cost: Optional[float] = Field(None, ge=0)
    current_value: Optional[float] = Field(None, ge=0)
    maintenance_interval_days: Optional[int] = Field(None, ge=1)
    responsible_id: Optional[int] = None
    installed_date: Optional[datetime] = None
    warranty_expiry: Optional[datetime] = None
    last_maintenance_date: Optional[datetime] = None

    @field_validator('status', mode='before')
    def _normalize_status_update(cls, v):
        return normalize_enum_value(v, ComponentStatus)

# Schema para respuesta (lectura)
class ComponentRead(ComponentBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    asset_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    installed_date: Optional[datetime] = None
    warranty_expiry: Optional[datetime] = None
    last_maintenance_date: Optional[datetime] = None

    @field_validator('status', mode='before')
    def _normalize_status_read(cls, v):
        return normalize_enum_value(v, ComponentStatus)

# Schema con información básica del asset padre
class ComponentWithAsset(ComponentRead):
    asset_name: Optional[str] = None
    asset_type: Optional[str] = None

# Schema para respuesta completa con relaciones
class ComponentDetail(ComponentRead):
    # Información del responsable
    responsible_name: Optional[str] = None
    
    # Estadísticas del componente
    total_failures: Optional[int] = 0
    total_maintenance_records: Optional[int] = 0
    total_tasks: Optional[int] = 0
    
    # Estado de mantenimiento
    needs_maintenance: Optional[bool] = False
    days_since_last_maintenance: Optional[int] = None
