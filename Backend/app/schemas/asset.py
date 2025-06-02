from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class AssetCreate(BaseModel):
    name: str
    description: str  # Añadido para coincidir con el modelo
    location: str
    responsible_id: int
    machine_id: Optional[int] = None  # Nuevo: relación con máquina

class AssetRead(BaseModel):
    id: int
    name: str
    description: str  # Añadido para coincidir con el modelo
    location: str
    responsible_id: int
    machine_id: Optional[int] = None  # Nuevo: relación con máquina
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class AssetUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None  # Añadido para coincidir con el modelo
    location: Optional[str] = None
    responsible_id: Optional[int] = None
    machine_id: Optional[int] = None  # Nuevo: relación con máquina