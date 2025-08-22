from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.enums import PlanType


class MaintenancePlanBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    plan_type: Optional[PlanType] = Field(None)
    frequency_days: Optional[int] = None
    frequency_weeks: Optional[int] = None
    frequency_months: Optional[int] = None
    estimated_duration: Optional[float] = None
    estimated_cost: Optional[float] = None
    start_date: Optional[datetime] = None
    next_due_date: Optional[datetime] = None
    last_execution_date: Optional[datetime] = None
    active: Optional[bool] = True
    asset_id: Optional[int] = None
    component_id: Optional[int] = None


class MaintenancePlanCreate(MaintenancePlanBase):
    pass


class MaintenancePlanUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    plan_type: Optional[PlanType] = None
    frequency_days: Optional[int] = None
    frequency_weeks: Optional[int] = None
    frequency_months: Optional[int] = None
    estimated_duration: Optional[float] = None
    estimated_cost: Optional[float] = None
    start_date: Optional[datetime] = None
    next_due_date: Optional[datetime] = None
    last_execution_date: Optional[datetime] = None
    active: Optional[bool] = None
    asset_id: Optional[int] = None
    component_id: Optional[int] = None


class MaintenancePlanRead(MaintenancePlanBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
