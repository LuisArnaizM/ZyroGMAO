from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import date, timedelta
from typing import List, Dict, Tuple
from app.models.calendar import UserWorkingDay, UserSpecialDay
from app.schemas.calendar import WorkingDayPattern, SpecialDayCreate, SpecialDayUpdate
from app.models.user import User
from app.models.department import Department
from sqlalchemy import and_

async def add_vacation_range(db: AsyncSession, user_id: int, start: date, end: date, reason: str | None = None):
    # Crear días especiales no laborables para cada fecha en rango
    cur = start
    created = []
    while cur <= end:
        res = await db.execute(select(UserSpecialDay).where(UserSpecialDay.user_id == user_id, UserSpecialDay.date == cur))
        row = res.scalar_one_or_none()
        if row:
            row.is_working = False
            row.hours = 0.0
            row.reason = reason or row.reason
        else:
            row = UserSpecialDay(user_id=user_id, date=cur, is_working=False, hours=0.0, reason=reason)
            db.add(row)
        created.append(row)
        cur += timedelta(days=1)
    await db.commit()
    for r in created:
        await db.refresh(r)
    return created

async def list_team_vacations(db: AsyncSession, manager_user_id: int, start: date, end: date):
    # Obtener árbol departamentos
    dep_res = await db.execute(select(Department).where(Department.manager_id == manager_user_id))
    managed = dep_res.scalars().all()
    if not managed:
        return []
    all_dep = (await db.execute(select(Department))).scalars().all()
    by_parent = {}
    for d in all_dep:
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
    # Usuarios
    user_res = await db.execute(select(User).where(User.department_id.in_(target)))
    users = user_res.scalars().all()
    user_ids = [u.id for u in users]
    if not user_ids:
        return []
    vac_res = await db.execute(select(UserSpecialDay).where(
        UserSpecialDay.user_id.in_(user_ids),
        UserSpecialDay.date >= start,
        UserSpecialDay.date <= end,
        UserSpecialDay.is_working == False
    ))
    vacs = vac_res.scalars().all()
    user_map = {u.id: u for u in users}
    result = []
    for v in vacs:
        u = user_map.get(v.user_id)
        if u:
            result.append((v.id, u.id, u.first_name, u.last_name, v.date, v.reason))
    return result


async def get_or_create_default_pattern(db: AsyncSession, user_id: int):
    res = await db.execute(select(UserWorkingDay).where(UserWorkingDay.user_id == user_id))
    rows = res.scalars().all()
    if rows:
        return rows
    # Default: Mon-Fri 8h, Sat/Sun 0h
    defaults = []
    for wd in range(7):
        hours = 8.0 if wd < 5 else 0.0
        defaults.append(UserWorkingDay(user_id=user_id, weekday=wd, hours=hours, is_active=True))
    db.add_all(defaults)
    await db.commit()
    for d in defaults:
        await db.refresh(d)
    return defaults


async def set_pattern(db: AsyncSession, user_id: int, pattern: List[WorkingDayPattern]):
    # Delete existing rows then insert provided (simpler)
    existing = await db.execute(select(UserWorkingDay).where(UserWorkingDay.user_id == user_id))
    for row in existing.scalars().all():
        await db.delete(row)
    await db.flush()
    new_rows = []
    for p in pattern:
        new_rows.append(UserWorkingDay(user_id=user_id, weekday=p.weekday, hours=p.hours, is_active=p.is_active))
    db.add_all(new_rows)
    await db.commit()
    return new_rows


async def list_pattern(db: AsyncSession, user_id: int):
    res = await db.execute(select(UserWorkingDay).where(UserWorkingDay.user_id == user_id))
    rows = res.scalars().all()
    if not rows:
        rows = await get_or_create_default_pattern(db, user_id)
    return rows


async def add_special_day(db: AsyncSession, user_id: int, data: SpecialDayCreate):
    # Upsert: if exists, update
    res = await db.execute(select(UserSpecialDay).where(UserSpecialDay.user_id == user_id, UserSpecialDay.date == data.date))
    existing = res.scalar_one_or_none()
    if existing:
        existing.is_working = data.is_working
        existing.hours = data.hours
        existing.reason = data.reason
        await db.commit()
        await db.refresh(existing)
        return existing
    row = UserSpecialDay(user_id=user_id, date=data.date, is_working=data.is_working, hours=data.hours, reason=data.reason)
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def list_special_days(db: AsyncSession, user_id: int, start: date, end: date):
    res = await db.execute(select(UserSpecialDay).where(UserSpecialDay.user_id == user_id, UserSpecialDay.date >= start, UserSpecialDay.date <= end))
    return res.scalars().all()


async def delete_special_day(db: AsyncSession, user_id: int, special_id: int) -> bool:
    res = await db.execute(select(UserSpecialDay).where(UserSpecialDay.id == special_id, UserSpecialDay.user_id == user_id))
    row = res.scalar_one_or_none()
    if not row:
        return False
    await db.delete(row)
    await db.commit()
    return True


async def compute_capacity_week(db: AsyncSession, user_id: int, start: date, days: int):
    # patterns
    pattern_rows = await list_pattern(db, user_id)
    pattern_map = {r.weekday: (r.hours if r.is_active else 0.0) for r in pattern_rows}
    special_rows = await list_special_days(db, user_id, start, start + timedelta(days=days-1))
    special_map = {r.date: r for r in special_rows}
    result = []
    for i in range(days):
        d = start + timedelta(days=i)
        weekday = d.weekday()
        special = special_map.get(d)
        if special:
            if not special.is_working:
                result.append((d, 0.0, True, special.reason))
            else:
                hrs = special.hours if special.hours is not None else pattern_map.get(weekday, 0.0)
                result.append((d, hrs, False, special.reason))
        else:
            hrs = pattern_map.get(weekday, 0.0)
            is_non = hrs == 0.0
            result.append((d, hrs, is_non, None))
    return result

async def is_non_working(db: AsyncSession, user_id: int, d: date) -> bool:
    rows = await compute_capacity_week(db, user_id, d, 1)
    return rows[0][1] == 0.0
