from pydantic import BaseModel
from typing import List, Optional
from datetime import date, datetime
from app.schemas.user import UserRead
from app.schemas.task import TaskRead


class PlannerTask(BaseModel):
    id: int
    title: str
    estimated_hours: Optional[float] = 0.0
    status: str
    priority: Optional[str] = None
    due_date: Optional[datetime] = None

    class Config:
        from_attributes = True


class PlannerDay(BaseModel):
    date: date
    capacity_hours: float
    planned_hours: float
    free_hours: float
    tasks: List[PlannerTask]


class PlannerUserRow(BaseModel):
    user: UserRead
    days: List[PlannerDay]


class PlannerWeek(BaseModel):
    start: date
    days: int
    users: List[PlannerUserRow]
