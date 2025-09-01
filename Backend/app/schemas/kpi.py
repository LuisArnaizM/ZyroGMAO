from pydantic import BaseModel
from typing import List, Optional


class KpiSummary(BaseModel):
    total_workorders: int
    open_workorders: int
    in_progress_workorders: int
    completed_workorders_30d: int
    overdue_workorders: int
    planned_pct: float
    avg_completion_time_hours: Optional[float] = None
    mttr_hours: Optional[float] = None
    mtbf_hours: Optional[float] = None
    mttf_hours: Optional[float] = None


class KpiTrendPoint(BaseModel):
    label: str
    created: int
    completed: int


class KpiTrends(BaseModel):
    period: str  # week, month
    window: int
    points: List[KpiTrendPoint]


# Per-view KPI response models
class AssetKpi(BaseModel):
    total: int
    active: int
    maintenance: int
    inactive: int
    retired: int
    total_value: Optional[float] = None


class WorkOrderKpi(BaseModel):
    total: int
    draft: int  # mapped from 'open'
    scheduled: int
    in_progress: int
    completed: int
    cancelled: int
    overdue: int


class FailureKpi(BaseModel):
    total: int
    pending: int
    in_progress: int
    resolved: int
    critical: int

class MonthlyResponsePoint(BaseModel):
    month: str  # YYYY-MM
    avg_response_hours: float | None

class MonthlyResponseSeries(BaseModel):
    points: list[MonthlyResponsePoint]
