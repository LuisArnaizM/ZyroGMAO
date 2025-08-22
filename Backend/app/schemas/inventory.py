from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from app.schemas.component import ComponentRead


class InventoryItemBase(BaseModel):
    component_id: int = Field(..., description="ID del componente asociado")
    quantity: float = Field(0, ge=0, description="Cantidad en stock")
    unit_cost: Optional[float] = Field(None, ge=0, description="Costo unitario")


class InventoryItemCreate(InventoryItemBase):
    pass


class InventoryItemUpdate(BaseModel):
    quantity: Optional[float] = Field(None, ge=0)
    unit_cost: Optional[float] = Field(None, ge=0)


class InventoryItemRead(InventoryItemBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class InventoryItemReadWithComponent(BaseModel):
    id: int
    quantity: float
    unit_cost: Optional[float] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    component: ComponentRead

    class Config:
        from_attributes = True


class AdjustQuantityRequest(BaseModel):
    delta: float = Field(..., description="Variación de stock, puede ser negativa")
    reason: Optional[str] = Field(None, description="Motivo del ajuste")


class TaskUsedComponentRead(BaseModel):
    id: int
    task_id: int
    component_id: Optional[int]
    quantity: float
    unit_cost_snapshot: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True
