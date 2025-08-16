from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List, Dict

from app.models.department import Department
from app.models.user import User
from app.schemas.department import DepartmentCreate, DepartmentUpdate


async def create_department(db: AsyncSession, dep_in: DepartmentCreate) -> Department:
    dep = Department(
        name=dep_in.name,
        description=dep_in.description,
        parent_id=dep_in.parent_id,
        manager_id=dep_in.manager_id,
        organization_id=dep_in.organization_id,
        is_active=dep_in.is_active if dep_in.is_active is not None else True,
    )
    db.add(dep)
    await db.commit()
    await db.refresh(dep)
    return dep


async def get_department(db: AsyncSession, dep_id: int) -> Department | None:
    result = await db.execute(select(Department).where(Department.id == dep_id))
    return result.scalar_one_or_none()


async def update_department(db: AsyncSession, dep_id: int, dep_in: DepartmentUpdate) -> Department | None:
    result = await db.execute(select(Department).where(Department.id == dep_id))
    dep = result.scalar_one_or_none()
    if not dep:
        return None
    data = dep_in.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(dep, k, v)
    await db.commit()
    await db.refresh(dep)
    return dep


async def delete_department(db: AsyncSession, dep_id: int) -> bool:
    result = await db.execute(select(Department).where(Department.id == dep_id))
    dep = result.scalar_one_or_none()
    if not dep:
        return False
    await db.delete(dep)
    await db.commit()
    return True


async def list_departments(db: AsyncSession, organization_id: int | None = None) -> List[Department]:
    query = select(Department)
    if organization_id:
        query = query.where(Department.organization_id == organization_id)
    result = await db.execute(query)
    return result.scalars().all()


def build_tree(departments: List[Department]) -> List[Department]:
    by_id: Dict[int, Department] = {d.id: d for d in departments}
    roots: List[Department] = []
    # Reset children to avoid duplicates in-memory
    for d in departments:
        d.children = []
    for d in departments:
        if d.parent_id and d.parent_id in by_id:
            by_id[d.parent_id].children.append(d)
        else:
            roots.append(d)
    return roots


async def get_department_tree(db: AsyncSession, organization_id: int | None = None) -> List[Department]:
    deps = await list_departments(db, organization_id)
    return build_tree(deps)


async def list_users_in_department_subtree(db: AsyncSession, dep_id: int) -> List[User]:
    # Get all departments first
    result = await db.execute(select(Department))
    deps = result.scalars().all()
    # Build adjacency
    by_parent: Dict[int | None, List[int]] = {}
    for d in deps:
        by_parent.setdefault(d.parent_id, []).append(d.id)

    # Collect subtree ids
    to_visit = [dep_id]
    subtree_ids: List[int] = []
    while to_visit:
        cur = to_visit.pop()
        subtree_ids.append(cur)
        to_visit.extend(by_parent.get(cur, []))

    # Query users with department_id in subtree
    result_users = await db.execute(select(User).where(User.department_id.in_(subtree_ids)))
    return result_users.scalars().all()
