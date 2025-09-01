from datetime import datetime, timedelta, timezone
from typing import List

from sqlalchemy import func, case, and_, select, cast, String
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workorder import WorkOrder
from app.models.failure import Failure
from app.models.enums import (
    AssetStatus, WorkOrderStatus, FailureStatus, FailureSeverity
)
from app.schemas.kpi import (
    KpiSummary,
    KpiTrendPoint,
    KpiTrends,
    AssetKpi,
    WorkOrderKpi,
    FailureKpi,
    MonthlyResponseSeries,
    MonthlyResponsePoint,
)
from app.models.asset import Asset


async def get_kpi_summary(db: AsyncSession) -> KpiSummary:
    now = datetime.now(timezone.utc)
    month_ago = now - timedelta(days=30)

    # Convert timezone-aware datetimes to naive UTC for DB comparisons
    def _to_db_naive(dt: datetime | None) -> datetime | None:
        if dt is None:
            return None
        if dt.tzinfo is None:
            return dt
        return dt.astimezone(timezone.utc).replace(tzinfo=None)

    naive_now = _to_db_naive(now)
    naive_month_ago = _to_db_naive(month_ago)

    # Totales por estado
    # Helper to compare status robustly (trim + upper)
    status_upper = func.upper(func.trim(cast(WorkOrder.status, String)))

    totals_q = select(
        func.count(WorkOrder.id),
        func.sum(case((status_upper == WorkOrderStatus.OPEN.value, 1), else_=0)),
        func.sum(case((status_upper == WorkOrderStatus.IN_PROGRESS.value, 1), else_=0)),
        func.sum(case((and_(status_upper == WorkOrderStatus.COMPLETED.value, WorkOrder.completed_date >= naive_month_ago), 1), else_=0)),
        func.sum(
            case(
                (
                    and_(
                        cast(WorkOrder.status, String).in_([WorkOrderStatus.OPEN.value, WorkOrderStatus.IN_PROGRESS.value]),
                        WorkOrder.scheduled_date.isnot(None),
                        WorkOrder.scheduled_date < naive_now,
                    ),
                    1,
                ),
                else_=0,
            )
        ),
        func.avg(
            case(
                (
                    and_(
                        WorkOrder.completed_date.isnot(None),
                        WorkOrder.started_date.isnot(None),
                    ),
                    func.extract('epoch', WorkOrder.completed_date - WorkOrder.started_date) / 3600.0,
                ),
                else_=None,
            )
        ),
        # avg completion time from creation to completion: created_at is timestamptz, completed_date is timestamp
        func.avg(
            case(
                (
                    and_(
                        WorkOrder.completed_date.isnot(None),
                        WorkOrder.created_at.isnot(None),
                    ),
                    # Convert created_at (timestamptz) to timestamp (UTC) for safe subtraction
                    func.extract('epoch', WorkOrder.completed_date - func.timezone('UTC', WorkOrder.created_at)) / 3600.0,
                ),
                else_=None,
            )
        ),
        func.count().filter(WorkOrder.scheduled_date.isnot(None)),
    )

    res = await db.execute(totals_q)
    (
        total,
        open_cnt,
        in_progress_cnt,
        completed_30d,
        overdue_cnt,
        mttr_hours,  # avg from start to complete
        avg_completion_time_hours,  # from creation to complete
        planned_count,
    ) = res.one()

    planned_pct = float(planned_count or 0) / float(total or 1) * 100.0

    # MTBF: media entre fechas de resolución consecutivas
    failures_resolved_q = select(Failure.resolved_date).where(Failure.resolved_date.isnot(None)).order_by(Failure.resolved_date.asc())
    res_resolved = await db.execute(failures_resolved_q)
    resolved_dates: List[datetime] = [r[0] for r in res_resolved.all()]
    mtbf_hours = None
    if len(resolved_dates) >= 2:
        mtbf_gaps = [ (resolved_dates[i]-resolved_dates[i-1]).total_seconds()/3600.0 for i in range(1,len(resolved_dates)) ]
        if mtbf_gaps:
            mtbf_hours = sum(mtbf_gaps)/len(mtbf_gaps)

    # MTTF: media entre (resolved_date de fallo i) y (reported_date del fallo i+1) cuando el resuelto ocurre antes del siguiente reporte
    failures_report_q = select(Failure.reported_date, Failure.resolved_date).where(Failure.reported_date.isnot(None)).order_by(Failure.reported_date.asc())
    res_fail = await db.execute(failures_report_q)
    failures_rows = res_fail.all()
    mttf_hours = None
    def _naive(dt: datetime | None) -> datetime | None:
        if dt is None:
            return None
        return dt if dt.tzinfo is None else dt.astimezone(timezone.utc).replace(tzinfo=None)
    if len(failures_rows) >= 2:
        spans = []
        for i in range(len(failures_rows)-1):
            rep_i, res_i = failures_rows[i][0], failures_rows[i][1]
            rep_next, _res_next = failures_rows[i+1][0], failures_rows[i+1][1]
            rep_i_n = _naive(rep_i)
            res_i_n = _naive(res_i)
            rep_next_n = _naive(rep_next)
            if res_i_n and rep_next_n and res_i_n <= rep_next_n:
                spans.append((rep_next_n - res_i_n).total_seconds()/3600.0)
        if spans:
            mttf_hours = sum(spans)/len(spans)

    return KpiSummary(
        total_workorders=int(total or 0),
        open_workorders=int(open_cnt or 0),
        in_progress_workorders=int(in_progress_cnt or 0),
        completed_workorders_30d=int(completed_30d or 0),
        overdue_workorders=int(overdue_cnt or 0),
        planned_pct=round(planned_pct, 2),
        avg_completion_time_hours=(float(avg_completion_time_hours) if avg_completion_time_hours is not None else None),
        mttr_hours=(float(mttr_hours) if mttr_hours is not None else None),
    mtbf_hours=(float(mtbf_hours) if mtbf_hours is not None else None),
    mttf_hours=(float(mttf_hours) if mttf_hours is not None else None),
    )


async def get_kpi_trends(db: AsyncSession, weeks: int = 8) -> KpiTrends:
    now = datetime.now(timezone.utc)
    start = now - timedelta(weeks=weeks)

    def _to_db_naive(dt: datetime | None) -> datetime | None:
        if dt is None:
            return None
        if dt.tzinfo is None:
            return dt
        return dt.astimezone(timezone.utc).replace(tzinfo=None)

    naive_start = _to_db_naive(start)

    # Crear buckets semanales [start_of_week]
    # Usamos date_trunc('week', ...) para agrupar
    created_week = func.to_char(func.date_trunc('week', WorkOrder.created_at), 'IYYY-IW')
    created_q = select(
        created_week.label('label'),
        func.count(WorkOrder.id),
    ).where(
        WorkOrder.created_at >= naive_start,
    ).group_by(created_week).order_by(created_week)

    completed_week = func.to_char(func.date_trunc('week', WorkOrder.completed_date), 'IYYY-IW')
    completed_q = select(
        completed_week.label('label'),
        func.count(WorkOrder.id),
    ).where(
        and_(
            WorkOrder.completed_date.isnot(None),
            WorkOrder.completed_date >= naive_start,
        )
    ).group_by(completed_week).order_by(completed_week)

    created_res = await db.execute(created_q)
    completed_res = await db.execute(completed_q)

    created_map = {row[0]: int(row[1]) for row in created_res.all()}
    completed_map = {row[0]: int(row[1]) for row in completed_res.all()}

    # Construir lista de semanas entre start y now en formato IYYY-IW
    points: List[KpiTrendPoint] = []
    week_cursor = start - timedelta(days=start.weekday())  # aprox alineación, no crítico
    for i in range(weeks + 1):
        week_dt = week_cursor + timedelta(weeks=i)
        label = week_dt.strftime('%G-%V')  # ISO Year-Week
        points.append(
            KpiTrendPoint(
                label=label,
                created=created_map.get(label, 0),
                completed=completed_map.get(label, 0),
            )
        )

    return KpiTrends(period='week', window=weeks, points=points)


async def get_assets_kpi(db: AsyncSession) -> AssetKpi:
    # Aggregate counts by status and total value
    q = select(
        func.count(Asset.id),
    func.sum(case((cast(Asset.status, String) == AssetStatus.ACTIVE.value, 1), else_=0)),
    func.sum(case((cast(Asset.status, String) == AssetStatus.MAINTENANCE.value, 1), else_=0)),
    func.sum(case((cast(Asset.status, String) == AssetStatus.INACTIVE.value, 1), else_=0)),
    func.sum(case((cast(Asset.status, String) == AssetStatus.RETIRED.value, 1), else_=0)),
        func.sum(Asset.current_value),
    )
    res = await db.execute(q)
    total, active, maintenance, inactive, retired, total_value = res.one()
    return AssetKpi(
        total=int(total or 0),
        active=int(active or 0),
        maintenance=int(maintenance or 0),
        inactive=int(inactive or 0),
        retired=int(retired or 0),
        total_value=float(total_value) if total_value is not None else None,
    )


async def get_workorders_kpi(db: AsyncSession) -> WorkOrderKpi:
    now = datetime.now(timezone.utc)
    def _to_db_naive(dt: datetime | None) -> datetime | None:
        if dt is None:
            return None
        if dt.tzinfo is None:
            return dt
        return dt.astimezone(timezone.utc).replace(tzinfo=None)

    naive_now = _to_db_naive(now)
    status_upper = func.upper(func.trim(cast(WorkOrder.status, String)))
    q = select(
        func.count(WorkOrder.id),
    func.sum(case((status_upper == WorkOrderStatus.OPEN.value, 1), else_=0)),
    func.sum(case((status_upper == WorkOrderStatus.ASSIGNED.value, 1), else_=0)),
    func.sum(case((status_upper == WorkOrderStatus.IN_PROGRESS.value, 1), else_=0)),
    func.sum(case((status_upper == WorkOrderStatus.COMPLETED.value, 1), else_=0)),
    func.sum(case((status_upper == WorkOrderStatus.CANCELLED.value, 1), else_=0)),
        func.sum(
            case(
                (
                    and_(
                        cast(WorkOrder.status, String).in_([
                            WorkOrderStatus.OPEN.value,
                            WorkOrderStatus.IN_PROGRESS.value,
                        ]),
                        WorkOrder.scheduled_date.isnot(None),
                        WorkOrder.scheduled_date < naive_now,
                    ),
                    1,
                ),
                else_=0,
            )
        ),
    )
    res = await db.execute(q)
    total, draft, scheduled, in_progress, completed, cancelled, overdue = res.one()
    return WorkOrderKpi(
        total=int(total or 0),
        draft=int(draft or 0),
        scheduled=int(scheduled or 0),
        in_progress=int(in_progress or 0),
        completed=int(completed or 0),
        cancelled=int(cancelled or 0),
        overdue=int(overdue or 0),
    )


async def get_failures_kpi(db: AsyncSession) -> FailureKpi:
    q = select(
        func.count(Failure.id),
    func.sum(case((cast(Failure.status, String) == FailureStatus.PENDING.value, 1), else_=0)),
    func.sum(case((cast(Failure.status, String) == FailureStatus.INVESTIGATING.value, 1), else_=0)),
    func.sum(case((cast(Failure.status, String) == FailureStatus.RESOLVED.value, 1), else_=0)),
    func.sum(case((cast(Failure.severity, String) == FailureSeverity.CRITICAL.value, 1), else_=0)),
    )
    res = await db.execute(q)
    total, pending, in_progress, resolved, critical = res.one()
    return FailureKpi(
        total=int(total or 0),
        pending=int(pending or 0),
        in_progress=int(in_progress or 0),
        resolved=int(resolved or 0),
        critical=int(critical or 0),
    )


async def get_monthly_response_times(db: AsyncSession, months: int = 6) -> MonthlyResponseSeries:
    """Media de tiempo de respuesta (started->completed si ambos existen, si no created->completed) agrupado por mes."""
    now = datetime.now(timezone.utc)
    start = (now.replace(day=1) - timedelta(days=months*31)).replace(day=1)
    def _naive(dt: datetime | None) -> datetime | None:
        if dt is None:
            return None
        return dt if dt.tzinfo is None else dt.astimezone(timezone.utc).replace(tzinfo=None)
    naive_start = _naive(start)
    # Construir expresión de mes YYYY-MM
    month_label = func.to_char(func.date_trunc('month', WorkOrder.completed_date), 'YYYY-MM')
    duration_expr = case(
        (
            and_(WorkOrder.started_date.isnot(None), WorkOrder.completed_date.isnot(None)),
            func.extract('epoch', WorkOrder.completed_date - WorkOrder.started_date)/3600.0
        ),
        else_=case(
            (
                and_(WorkOrder.created_at.isnot(None), WorkOrder.completed_date.isnot(None)),
                func.extract('epoch', WorkOrder.completed_date - func.timezone('UTC', WorkOrder.created_at))/3600.0
            ),
            else_=None
        )
    )
    q = select(
        month_label.label('m'),
        func.avg(duration_expr)
    ).where(
        and_(
            WorkOrder.completed_date.isnot(None),
            WorkOrder.completed_date >= naive_start,
        )
    ).group_by(month_label).order_by(month_label)
    res = await db.execute(q)
    rows = res.all()
    # Crear mapa
    avg_map = {r[0]: float(r[1]) if r[1] is not None else None for r in rows}
    # Generar meses continuos hasta actual
    points: list[MonthlyResponsePoint] = []
    cursor = start.replace(day=1)
    end_month = now.replace(day=1)
    while cursor <= end_month:
        key = cursor.strftime('%Y-%m')
        points.append(MonthlyResponsePoint(month=key, avg_response_hours=avg_map.get(key)))
        # avanzar un mes
        if cursor.month == 12:
            cursor = cursor.replace(year=cursor.year+1, month=1)
        else:
            cursor = cursor.replace(month=cursor.month+1)
    # recortar a últimos 'months' + mes actual
    if len(points) > months+1:
        points = points[-(months+1):]
    return MonthlyResponseSeries(points=points)
