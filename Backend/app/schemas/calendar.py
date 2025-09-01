from pydantic import BaseModel, Field
from datetime import date
from typing import List, Optional


class WorkingDayPattern(BaseModel):
    weekday: int = Field(ge=0, le=6)
    hours: float = Field(ge=0, le=24)
    is_active: bool = True


class SpecialDay(BaseModel):
    id: Optional[int] = None
    date: date
    is_working: bool
    hours: Optional[float] = Field(default=None, ge=0, le=24)
    reason: Optional[str] = None

    class Config:
        from_attributes = True


class SpecialDayCreate(BaseModel):
    date: date
    is_working: bool
    hours: Optional[float] = Field(default=None, ge=0, le=24)
    reason: Optional[str] = None


class SpecialDayUpdate(BaseModel):
    is_working: Optional[bool] = None
    hours: Optional[float] = Field(default=None, ge=0, le=24)
    reason: Optional[str] = None


class UserCalendarDay(BaseModel):
    date: date
    capacity_hours: float
    is_non_working: bool
    reason: Optional[str] = None


class UserCalendarWeek(BaseModel):
    user_id: int
    days: List[UserCalendarDay]


class VacationRangeCreate(BaseModel):
    start_date: date
    end_date: date
    reason: Optional[str] = None

    def model_post_init(self, __context):  # asegurar orden
        if self.end_date < self.start_date:
            raise ValueError("end_date debe ser >= start_date")


class TeamVacationDay(BaseModel):
    id: int
    user_id: int
    first_name: str
    last_name: str
    date: date
    reason: Optional[str] = None
