from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date, datetime, timedelta
from typing import List

from app.database.postgres import get_db
from app.auth.dependencies import get_current_user, require_role
from app.schemas.planner import PlannerWeek, PlannerUserRow, PlannerDay, PlannerTask
from app.controllers.calendar import compute_capacity_week
from app.models.user import User
from app.models.department import Department
from app.models.task import Task
from sqlalchemy.future import select

router = APIRouter(tags=["Planner"])

WORKDAY_HOURS = 8.0


async def _get_subordinate_user_ids(db: AsyncSession, manager_user_id: int) -> List[int]:
    # Obtener departamentos donde el usuario es manager
    result = await db.execute(select(Department).where(Department.manager_id == manager_user_id))
    managed_deps = result.scalars().all()
    if not managed_deps:
        return []
    # Construir árbol para incluir subdepartamentos
    # Obtener todos
    all_res = await db.execute(select(Department))
    all_deps = all_res.scalars().all()
    by_parent = {}
    for d in all_deps:
        by_parent.setdefault(d.parent_id, []).append(d)
    target_dep_ids = set()
    stack = [d.id for d in managed_deps]
    while stack:
        cur = stack.pop()
        if cur in target_dep_ids:
            continue
        target_dep_ids.add(cur)
        children = by_parent.get(cur, [])
        for ch in children:
            stack.append(ch.id)
    # Obtener usuarios en esos departamentos (excluyendo managers quizá?)
    user_res = await db.execute(select(User).where(User.department_id.in_(target_dep_ids)))
    users = user_res.scalars().all()
    return [u.id for u in users]


@router.get("/week", response_model=PlannerWeek)
async def get_planner_week(
    start: date = Query(None, description="Fecha de inicio de la semana (lunes)"),
    days: int = Query(7, ge=1, le=14, description="Número de días a devolver"),
    db: AsyncSession = Depends(get_db),
    current = Depends(require_role(["Admin", "Supervisor"]))
):
    # Calcular lunes de la semana si no viene
    today = date.today()
    if start is None:
        start = today - timedelta(days=today.weekday())
    # Normalizar start a lunes
    start = start - timedelta(days=start.weekday())
    end = start + timedelta(days=days)

    # Obtener ids subordinados
    subordinate_ids = await _get_subordinate_user_ids(db, current["id"]) if current["role"] != "Admin" else None

    user_query = select(User)
    if subordinate_ids is not None:
        if not subordinate_ids:
            return PlannerWeek(start=start, days=days, users=[])
        user_query = user_query.where(User.id.in_(subordinate_ids))
    u_res = await db.execute(user_query)
    users = u_res.scalars().all()

    # Obtener tareas asignadas en rango -> usamos due_date como fecha de planificación (si no due_date, se ignora)
    t_query = select(Task).where(Task.due_date >= datetime.combine(start, datetime.min.time()), Task.due_date < datetime.combine(end, datetime.min.time()))
    if subordinate_ids is not None:
        if subordinate_ids:
            t_query = t_query.where(Task.assigned_to.in_(subordinate_ids))
        else:
            t_query = t_query.where(False)
    t_res = await db.execute(t_query)
    tasks = t_res.scalars().all()
    tasks_by_user_date = {}
    for t in tasks:
        if not t.due_date:
            continue
        d_key = t.due_date.date()
        tasks_by_user_date.setdefault((t.assigned_to, d_key), []).append(t)

    week_users: List[PlannerUserRow] = []
    for u in users:
        capacity_rows = await compute_capacity_week(db, u.id, start, days)
        day_list: List[PlannerDay] = []
        for (d, cap, is_non, reason) in capacity_rows:
            tlist = tasks_by_user_date.get((u.id, d), [])
            planned = sum(filter(None, [t.estimated_hours or 0 for t in tlist]))
            free = max(0.0, cap - planned)
            day_list.append(PlannerDay(
                date=d,
                capacity_hours=cap,
                planned_hours=planned,
                free_hours=free,
                tasks=[PlannerTask.model_validate(t) for t in tlist],
                is_non_working=is_non,
                reason=reason
            ))
        week_users.append(PlannerUserRow(user=u, days=day_list))

    return PlannerWeek(start=start, days=days, users=week_users)
