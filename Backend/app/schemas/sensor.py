from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import Any, Optional, Union  # Eliminado 'Float' de aquí

# Esquema para la configuración de sensores en PostgreSQL
class SensorConfigCreate(BaseModel):
    asset_id: int
    name: str
    sensor_type: str
    location: Optional[str] = None
    units: Optional[str] = None
    min_value: Optional[float] = None  
    max_value: Optional[float] = None  

class SensorConfigRead(BaseModel):
    id: int
    asset_id: int
    name: str
    sensor_type: str
    location: Optional[str] = None
    units: Optional[str] = None
    min_value: Optional[float] = None  
    max_value: Optional[float] = None  
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class SensorConfigUpdate(BaseModel):
    name: Optional[str] = None
    sensor_type: Optional[str] = None
    location: Optional[str] = None
    units: Optional[str] = None
    min_value: Optional[float] = None  
    max_value: Optional[float] = None  

# Esquemas para los datos de lecturas de sensores en MongoDB
class SensorReadingCreate(BaseModel):
    sensor_id: int  # Referencia al ID del sensor en PostgreSQL
    asset_id: int   # Referencia al ID del asset
    value: Union[float, int, str]  # Puede ser cualquiera de estos tipos
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SensorReadingRead(SensorReadingCreate):
    id: str  # MongoDB ObjectId como string

# Mantén estos alias para compatibilidad si es necesario
SensorIn = SensorReadingCreate
SensorOut = SensorReadingRead