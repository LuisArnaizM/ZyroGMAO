from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date, timedelta
from typing import List
from app.database.postgres import get_db
from app.auth.dependencies import get_current_user, require_role
from app.schemas.calendar import WorkingDayPattern, SpecialDay, SpecialDayCreate, UserCalendarWeek, UserCalendarDay, VacationRangeCreate, TeamVacationDay
from app.controllers.calendar import (
    list_pattern, set_pattern, add_special_day, list_special_days, delete_special_day, compute_capacity_week,
    add_vacation_range, list_team_vacations
)
from app.models.department import Department
from app.models.user import User
from sqlalchemy.future import select

router = APIRouter(tags=["Calendar"])


async def _get_subordinate_user_ids(db, manager_user_id: int):
    """Devuelve los ids de usuarios en departamentos hijos (incluyendo raíces gestionadas)."""
    dep_res = await db.execute(select(Department).where(Department.manager_id == manager_user_id))
    managed = dep_res.scalars().all()
    if not managed:
        return []
    all_dep_res = await db.execute(select(Department))
    all_deps = all_dep_res.scalars().all()
    by_parent = {}
    for d in all_deps:
        by_parent.setdefault(d.parent_id, []).append(d)
    target = set()
    stack = [d.id for d in managed]
    while stack:
        cur = stack.pop()
        if cur in target:
            continue
        target.add(cur)
        for ch in by_parent.get(cur, []):
            stack.append(ch.id)
    user_res = await db.execute(select(User).where(User.department_id.in_(target)))
    users = user_res.scalars().all()
    return [u.id for u in users]

def _ensure_access(user_ctx, target_user_id: int, subordinate_ids):
    if user_ctx["role"] == "Admin":
        return
    # Supervisor: usuario objetivo debe estar en la lista
    if target_user_id not in subordinate_ids:
        raise HTTPException(status_code=403, detail="Usuario fuera de su ámbito de gestión")


@router.get("/{user_id}/pattern", response_model=List[WorkingDayPattern])
async def get_pattern(user_id: int, db: AsyncSession = Depends(get_db), current=Depends(require_role(["Admin","Supervisor"]))):
    if current["role"] != "Admin":
        subs = await _get_subordinate_user_ids(db, current["id"])
        _ensure_access(current, user_id, subs)
    rows = await list_pattern(db, user_id)
    return [WorkingDayPattern(weekday=r.weekday, hours=r.hours, is_active=r.is_active) for r in rows]

@router.put("/{user_id}/pattern", response_model=List[WorkingDayPattern])
async def put_pattern(user_id: int, payload: List[WorkingDayPattern], db: AsyncSession = Depends(get_db), current=Depends(require_role(["Admin","Supervisor"]))):
    if current["role"] != "Admin":
        subs = await _get_subordinate_user_ids(db, current["id"])
        _ensure_access(current, user_id, subs)
    rows = await set_pattern(db, user_id, payload)
    return [WorkingDayPattern(weekday=r.weekday, hours=r.hours, is_active=r.is_active) for r in rows]

@router.get("/{user_id}/special", response_model=List[SpecialDay])
async def get_special_days(user_id: int, start: date = Query(...), end: date = Query(...), db: AsyncSession = Depends(get_db), current=Depends(require_role(["Admin","Supervisor"]))):
    if current["role"] != "Admin":
        subs = await _get_subordinate_user_ids(db, current["id"])
        _ensure_access(current, user_id, subs)
    rows = await list_special_days(db, user_id, start, end)
    return rows

@router.post("/{user_id}/special", response_model=SpecialDay)
async def post_special_day(user_id: int, data: SpecialDayCreate, db: AsyncSession = Depends(get_db), current=Depends(require_role(["Admin","Supervisor"]))):
    if current["role"] != "Admin":
        subs = await _get_subordinate_user_ids(db, current["id"])
        _ensure_access(current, user_id, subs)
    row = await add_special_day(db, user_id, data)
    return row

@router.delete("/{user_id}/special/{special_id}")
async def delete_special(user_id: int, special_id: int, db: AsyncSession = Depends(get_db), current=Depends(require_role(["Admin","Supervisor"]))):
    if current["role"] != "Admin":
        subs = await _get_subordinate_user_ids(db, current["id"])
        _ensure_access(current, user_id, subs)
    ok = await delete_special_day(db, user_id, special_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Not found")
    return {"detail": "Deleted"}

@router.get("/{user_id}/week", response_model=UserCalendarWeek)
async def get_calendar_week(user_id: int, start: date = Query(None), days: int = Query(7, ge=1, le=14), db: AsyncSession = Depends(get_db), current=Depends(require_role(["Admin","Supervisor","Tecnico"]))):
    # Default start: current week Monday
    today = date.today()
    if start is None:
        start = today - timedelta(days=today.weekday())
    start = start - timedelta(days=start.weekday())
    if current["role"] == "Supervisor" and current["id"] != user_id:
        subs = await _get_subordinate_user_ids(db, current["id"])
        _ensure_access(current, user_id, subs)
    rows = await compute_capacity_week(db, user_id, start, days)
    return UserCalendarWeek(
        user_id=user_id,
        days=[UserCalendarDay(date=d, capacity_hours=hrs, is_non_working=is_non, reason=reason) for d, hrs, is_non, reason in rows]
    )


@router.post("/{user_id}/vacations", response_model=List[SpecialDay])
async def post_vacation_range(user_id: int, data: VacationRangeCreate, db: AsyncSession = Depends(get_db), current=Depends(require_role(["Admin","Supervisor"]))):
    if current["role"] != "Admin":
        subs = await _get_subordinate_user_ids(db, current["id"])
        _ensure_access(current, user_id, subs)
    rows = await add_vacation_range(db, user_id, data.start_date, data.end_date, data.reason)
    return rows

@router.get("/team/{manager_id}/vacations", response_model=List[TeamVacationDay])
async def get_team_vacations(manager_id: int, start: date = Query(...), end: date = Query(...), db: AsyncSession = Depends(get_db), current=Depends(require_role(["Admin","Supervisor"]))):
    if current["role"] != "Admin" and current["id"] != manager_id:
        raise HTTPException(status_code=403, detail="Solo puede consultar su propio equipo")
    raw = await list_team_vacations(db, manager_id, start, end)
    return [TeamVacationDay(id=i, user_id=uid, first_name=fn, last_name=ln, date=d, reason=r) for i, uid, fn, ln, d, r in raw]
