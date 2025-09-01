# ...existing code...
import asyncio
from datetime import datetime, timedelta, timezone
import logging
import random
import uuid
import enum as _pyenum
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text

from app.database.postgres import AsyncSessionLocal
from app.auth.security import get_password_hash

from app.models.user import User
from app.models.department import Department
from app.models.asset import Asset
from app.models.component import Component
from app.models.inventory import InventoryItem, TaskUsedComponent
from app.models.failure import Failure
from app.models.workorder import WorkOrder
from app.models.task import Task
from app.models.maintenance import Maintenance
from app.models.maintenancePlan import MaintenancePlan
from app.models.enums import (
    AssetStatus, ComponentStatus, PlanType,
    FailureStatus, FailureSeverity,
    WorkOrderStatus, WorkOrderType, WorkOrderPriority,
    MaintenanceStatus, MaintenanceType,
    TaskStatus, TaskPriority,
)

logger = logging.getLogger(__name__)


def _to_naive(dt: datetime | None) -> datetime | None:
    """Convierte un datetime con tzinfo a naive en UTC si es necesario.

    Muchas columnas en los modelos usan TIMESTAMP WITHOUT TIME ZONE. Cuando el
    seed genera datetimes con tzinfo (timezone.utc) hay incompatibilidades en
    algunos drivers. Este helper normaliza a naive UTC.
    """
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt
    return dt.astimezone(timezone.utc).replace(tzinfo=None)

def _to_db_enum(v):
    """
    Normaliza un Enum o str a la representación que espera la DB (valor en UPPERCASE).
    - Enum -> devuelve .value
    - str -> devuelve .upper()
    - None/otro -> devuelve tal cual
    """
    if isinstance(v, _pyenum.Enum):
        return v.value
    if isinstance(v, str):
        return v.upper()
    return v

STATUS_MAP = {
    "active": AssetStatus.ACTIVE.value,
    "maintenance": AssetStatus.MAINTENANCE.value,
    "inactive": AssetStatus.INACTIVE.value,
    "retired": AssetStatus.RETIRED.value,
}

async def _normalize_asset_component_statuses(session: AsyncSession) -> None:
    """Normaliza los estados de Assets y Components a valores canonizados usando el ORM.

    Lee las filas y asigna los valores exactos definidos en los enums Python, evitando
    SQL crudo y castings dependientes de PostgreSQL UDT.
    """
    # Assets
    assets = (await session.execute(select(Asset))).scalars().all()
    mapped = 0
    for a in assets:
        prev = (a.status or '').lower()
        if prev in ('maintenance'):
            new = AssetStatus.MAINTENANCE.value
        elif prev in ('active'):
            new = AssetStatus.ACTIVE.value
        elif prev in ('inactive'):
            new = AssetStatus.INACTIVE.value
        elif prev in ('retired'):
            new = AssetStatus.RETIRED.value
        else:
            new = (a.status or '').upper()
        if (isinstance(a.status, _pyenum.Enum) and a.status.value != new) or (not isinstance(a.status, _pyenum.Enum) and (a.status or '').upper() != new):
            a.status = new
            mapped += 1

    # Components
    components = (await session.execute(select(Component))).scalars().all()
    for c in components:
        prev = (c.status or '').lower()
        if prev in ('maintenance'):
            new = ComponentStatus.MAINTENANCE.value
        elif prev in ('active'):
            new = ComponentStatus.ACTIVE.value
        elif prev in ('failed'):
            new = ComponentStatus.INACTIVE.value
        elif prev in ('retired'):
            new = ComponentStatus.RETIRED.value
        else:
            new = (c.status or '').upper()
        if (isinstance(c.status, _pyenum.Enum) and c.status.value != new) or (not isinstance(c.status, _pyenum.Enum) and (c.status or '').upper() != new):
            c.status = new

    if mapped:
        await session.flush()
    else:
        # flush anyway to persist any component changes
        await session.flush()

FAILURE_STATUS_MAP = {
    "reported": FailureStatus.REPORTED.value,
    "investigating": FailureStatus.INVESTIGATING.value,
    "pending": FailureStatus.PENDING.value,
    "in_progress": FailureStatus.INVESTIGATING.value,
    "resolved": FailureStatus.RESOLVED.value,
    "closed": FailureStatus.CLOSED.value,
}

async def _normalize_failure_statuses(session: AsyncSession) -> None:
    """Normaliza status y severity de failures, workorders, tasks y maintenance usando ORM."""
    # Failures: status & severity
    failures = (await session.execute(select(Failure))).scalars().all()
    for f in failures:
        if f.status:
            f.status = (f.status or '').upper()
        if f.severity:
            f.severity = (f.severity or '').upper()

    # WorkOrders: status, work_type, priority
    workorders = (await session.execute(select(WorkOrder))).scalars().all()
    for wo in workorders:
        st = (wo.status or '').upper()
        if st in ('OPEN','PENDING','SCHEDULED'):
            wo.status = WorkOrderStatus.OPEN.value
        elif st in ('ASSIGNED',):
            wo.status = WorkOrderStatus.ASSIGNED.value
        elif st in ('IN_PROGRESS','INPROGRESS','IN-PROGRESS'):
            wo.status = WorkOrderStatus.IN_PROGRESS.value
        elif st in ('COMPLETED','DONE'):
            wo.status = WorkOrderStatus.COMPLETED.value
        elif st in ('CANCELLED','CANCELED'):
            wo.status = WorkOrderStatus.CANCELLED.value
        else:
            wo.status = st or wo.status

        wt = (wo.work_type or '').upper()
        if wt in ('CORRECTIVE','REPAIR','EMERGENCY'):
            wo.work_type = WorkOrderType.REPAIR.value
        elif wt in ('PREVENTIVE','MAINTENANCE'):
            wo.work_type = WorkOrderType.MAINTENANCE.value
        elif wt in ('INSPECTION',):
            wo.work_type = WorkOrderType.INSPECTION.value
        else:
            wo.work_type = wt or wo.work_type or WorkOrderType.MAINTENANCE.value

        pr = (wo.priority or '').upper()
        if pr in ('LOW',):
            wo.priority = WorkOrderPriority.LOW.value
        elif pr in ('MEDIUM','NORMAL'):
            wo.priority = WorkOrderPriority.MEDIUM.value
        elif pr in ('HIGH','CRITICAL'):
            wo.priority = WorkOrderPriority.HIGH.value
        else:
            wo.priority = pr or wo.priority or WorkOrderPriority.MEDIUM.value

    # Tasks: status & priority
    tasks = (await session.execute(select(Task))).scalars().all()
    for t in tasks:
        ts = (t.status or '').upper()
        if ts in ('PENDING',):
            t.status = TaskStatus.PENDING.value
        elif ts in ('IN_PROGRESS','INPROGRESS'):
            t.status = TaskStatus.IN_PROGRESS.value
        elif ts in ('COMPLETED','DONE'):
            t.status = TaskStatus.COMPLETED.value
        elif ts in ('CANCELLED','CANCELED'):
            t.status = TaskStatus.CANCELLED.value
        else:
            t.status = ts or t.status

        tp = (t.priority or '').upper()
        if tp in ('LOW',):
            t.priority = TaskPriority.LOW.value
        elif tp in ('MEDIUM','NORMAL'):
            t.priority = TaskPriority.MEDIUM.value
        elif tp in ('HIGH','CRITICAL'):
            t.priority = TaskPriority.HIGH.value
        else:
            t.priority = tp or t.priority or TaskPriority.MEDIUM.value

    # Maintenance: status & maintenance_type
    maints = (await session.execute(select(Maintenance))).scalars().all()
    for m in maints:
        ms = (m.status or '').upper()
        if ms in ('SCHEDULED',):
            m.status = MaintenanceStatus.SCHEDULED.value
        elif ms in ('IN_PROGRESS','INPROGRESS'):
            m.status = MaintenanceStatus.IN_PROGRESS.value
        elif ms in ('COMPLETED','DONE'):
            m.status = MaintenanceStatus.COMPLETED.value
        elif ms in ('CANCELLED','CANCELED'):
            m.status = MaintenanceStatus.CANCELLED.value
        else:
            m.status = ms or m.status

        mt = (m.maintenance_type or '').upper()
        if mt in ('PREVENTIVE',):
            m.maintenance_type = MaintenanceType.PREVENTIVE.value
        elif mt in ('CORRECTIVE',):
            m.maintenance_type = MaintenanceType.CORRECTIVE.value
        elif mt in ('PREDICTIVE',):
            m.maintenance_type = MaintenanceType.PREDICTIVE.value
        else:
            m.maintenance_type = mt or m.maintenance_type

    await session.flush()


async def _ensure_departments(session: AsyncSession) -> list[Department]:
    cnt = (await session.execute(select(func.count()).select_from(Department))).scalar() or 0
    if cnt >= 5:
        return (await session.execute(select(Department))).scalars().all()

    # Crear arbol de departamentos
    ops = Department(name="Operations", description="Root operations")
    maint = Department(name="Maintenance", description="Maintenance Dept", parent=ops)
    prod = Department(name="Production", description="Production Dept", parent=ops)
    quality = Department(name="Quality", description="Quality Assurance", parent=ops)
    it = Department(name="IT", description="Industrial IT", parent=ops)
    session.add_all([ops, maint, prod, quality, it])
    await session.flush()
    return [ops, maint, prod, quality, it]


def _rand_name(prefix: str, i: int) -> tuple[str, str]:
    first = f"{prefix}{i}"
    last = random.choice(["García", "López", "Martínez", "Sánchez", "Pérez", "González", "Rodríguez"])  # noqa: S311
    return first, last


async def _ensure_users(session: AsyncSession, departments: list[Department]) -> dict[str, list[User]]:
    users = (await session.execute(select(User))).scalars().all()
    # Mapas para idempotencia
    by_username = {u.username: u for u in users}
    by_email = {u.email: u for u in users}

    roles = {"Admin": [], "Supervisor": [], "Tecnico": [], "Consultor": []}
    for u in users:
        roles.setdefault(u.role, []).append(u)

    # Admin base (si no existe)
    if "admin" not in by_username and "admin@example.com" not in by_email:
        admin = User(
            email="admin@example.com",
            username="admin",
            first_name="Admin",
            last_name="User",
            hashed_password=get_password_hash("admin123"),
            role="Admin",
            is_active=True,
            department_id=departments[0].id,
            hourly_rate=80.0,  # Admin rate: $80/hour
        )
        roles["Admin"].append(admin)
        session.add(admin)

    # Supervisores
    for i in range(1, 4):
        username = f"supervisor{i}"
        email = f"supervisor{i}@example.com"
        if username in by_username or email in by_email:
            # ya existe, agregar a roles si aplica
            u = by_username.get(username) or by_email.get(email)
            if u and u not in roles.get(u.role, []):
                roles.setdefault(u.role, []).append(u)
            continue
        fn, ln = _rand_name("Sup", i)
        u = User(
            email=email,
            username=username,
            first_name=fn,
            last_name=ln,
            hashed_password=get_password_hash("manager123"),
            role="Supervisor",
            is_active=True,
            department_id=random.choice(departments).id,
            hourly_rate=60.0,  # Supervisor rate: $60/hour
        )
        roles["Supervisor"].append(u)
        session.add(u)

    # Técnicos
    for i in range(1, 13):
        username = f"tech{i}"
        email = f"tech{i}@example.com"
        if username in by_username or email in by_email:
            u = by_username.get(username) or by_email.get(email)
            if u and u not in roles.get(u.role, []):
                roles.setdefault(u.role, []).append(u)
            continue
        fn, ln = _rand_name("Tech", i)
        u = User(
            email=email,
            username=username,
            first_name=fn,
            last_name=ln,
            hashed_password=get_password_hash("tech123"),
            role="Tecnico",
            is_active=True,
            department_id=random.choice(departments).id,
            hourly_rate=45.0,  # Technician rate: $45/hour
        )
        roles["Tecnico"].append(u)
        session.add(u)

    # Consultores
    for i in range(1, 5):
        username = f"consultor{i}"
        email = f"consultor{i}@example.com"
        if username in by_username or email in by_email:
            u = by_username.get(username) or by_email.get(email)
            if u and u not in roles.get(u.role, []):
                roles.setdefault(u.role, []).append(u)
            continue
        fn, ln = _rand_name("Cons", i)
        u = User(
            email=email,
            username=username,
            first_name=fn,
            last_name=ln,
            hashed_password=get_password_hash("consult123"),
            role="Consultor",
            is_active=True,
            department_id=random.choice(departments).id,
            hourly_rate=70.0,  # Consultant rate: $70/hour
        )
        roles["Consultor"].append(u)
        session.add(u)

    await session.flush()
    return roles


async def _create_assets_components_inventory(session: AsyncSession, supervisors: list[User], technicians: list[User]):
    now = datetime.now(timezone.utc)
    existing_assets = (await session.execute(select(Asset))).scalars().all()
    if len(existing_assets) >= 15:
        # Normalizar estados existentes a los usados por el backend (UPPERCASE)
        mapped = 0
        for a in existing_assets:
            prev = (a.status or '').lower()
            if prev == "active":
                new = AssetStatus.ACTIVE.value
            elif prev == "maintenance":
                new = AssetStatus.MAINTENANCE.value
            elif prev in ("inactive", "failed"):
                new = AssetStatus.INACTIVE.value
            elif prev in ("retired", "decommissioned"):
                new = AssetStatus.RETIRED.value
            else:
                new = AssetStatus.ACTIVE.value
            if (isinstance(a.status, _pyenum.Enum) and a.status.value != new) or (not isinstance(a.status, _pyenum.Enum) and (a.status or "").upper() != new):
                a.status = new
                mapped += 1
        if mapped:
            await session.flush()
        components = (await session.execute(select(Component))).scalars().all()
        # Normalizar también estados de componentes para coherencia
        for c in components:
            prev = (c.status or '').lower()
            if prev in ("operational", "active"):
                new = ComponentStatus.ACTIVE.value
            elif prev in ("maintenance", "in_maintenance", "under_maintenance", "under-maintenance", "under maintenance"):
                new = ComponentStatus.MAINTENANCE.value
            elif prev in ("failed", "inactive"):
                new = ComponentStatus.INACTIVE.value
            elif prev in ("retired", "decommissioned"):
                new = ComponentStatus.RETIRED.value
            else:
                new = ComponentStatus.ACTIVE.value
            if (isinstance(c.status, _pyenum.Enum) and c.status.value != new) or (not isinstance(c.status, _pyenum.Enum) and (c.status or "").upper() != new):
                c.status = new
        await session.flush()
        return existing_assets, components

    asset_types = ["machine", "line", "press", "compressor", "robot", "oven", "forklift"]
    status_choices = [
        AssetStatus.ACTIVE.value,
        AssetStatus.MAINTENANCE.value,
        AssetStatus.INACTIVE.value,
        AssetStatus.ACTIVE.value,
        AssetStatus.ACTIVE.value,
        AssetStatus.RETIRED.value,
    ]
    assets: list[Asset] = []
    for i in range(1, 21):  # 20 assets
        atype = random.choice(asset_types)
        sn_suffix = uuid.uuid4().hex[:8]
        a = Asset(
            name=f"{atype.capitalize()} #{i:03d}",
            description=f"{atype.capitalize()} description #{i}",
            asset_type=atype,
            model=f"Model-{100+i}",
            serial_number=f"SN-{now.year}-{i:04d}-{sn_suffix}",
            location=f"Area {random.choice(['A','B','C','D','E'])}",
            status=random.choice(status_choices),
            responsible_id=random.choice(supervisors).id if supervisors else None,
            purchase_cost=round(30000 + random.random()*80000, 2),
            current_value=round(20000 + random.random()*60000, 2),
        )
        assets.append(a)
        session.add(a)
    await session.flush()

    # Componentes e inventario
    component_types = ["motor", "pump", "valve", "spindle", "belt", "bearing", "gear", "filter"]
    components: list[Component] = []
    for asset in assets:
        for j in range(1, 9):  # 8 por asset
            ctype = random.choice(component_types)
            csn_suffix = uuid.uuid4().hex[:8]
            comp = Component(
                name=f"{ctype.capitalize()} {asset.id}-{j}",
                description=f"{ctype} for {asset.name}",
                component_type=ctype,
                model=f"{ctype.upper()}-{1000+asset.id*j}",
                serial_number=f"CMP-{now.year}-{asset.id:03d}-{j:02d}-{csn_suffix}",
                location=f"{asset.location} / Pos {j}",
                status=random.choice(status_choices),
                asset_id=asset.id,
                responsible_id=random.choice(technicians).id if technicians else None,
                maintenance_interval_days=random.choice([30, 60, 90, 120]),
                purchase_cost=round(50 + random.random()*950, 2),
                current_value=round(30 + random.random()*700, 2),
            )
            components.append(comp)
            session.add(comp)
    await session.flush()

    # Inventario por componente
    for comp in components:
        if (await session.execute(select(InventoryItem).where(InventoryItem.component_id == comp.id))).scalar_one_or_none():
            continue
        qty = random.randint(0, 50)
        cost = round(random.uniform(5.0, 500.0), 2)
        inv = InventoryItem(component_id=comp.id, quantity=float(qty), unit_cost=cost)
        session.add(inv)
    await session.flush()

    return assets, components


async def _create_maintenance_plans(session: AsyncSession, assets: list[Asset], components: list[Component]):
    """Crear algunos maintenance plans si no existen suficientes (idempotente)."""
    existing = (await session.execute(select(func.count()).select_from(MaintenancePlan))).scalar() or 0
    if existing >= 10:
        return

    samples = []
    plan_types = [PlanType.PREVENTIVE.value, PlanType.PREDICTIVE.value, PlanType.PREVENTIVE.value]
    for i in range(1, 16):
        asset = random.choice(assets) if assets else None
        comp_candidates = [c for c in components if c.asset_id == asset.id] if asset else []
        component = random.choice(comp_candidates) if comp_candidates else None
        p = MaintenancePlan(
            name=f"Plan {i} - {asset.name if asset else 'General'}",
            description=f"Auto-generated maintenance plan {i}",
            plan_type=random.choice(plan_types),
            frequency_days=random.choice([7, 14, 30, 90, None]),
            frequency_weeks=None,
            frequency_months=None,
            estimated_duration=round(random.uniform(1.0, 8.0), 1),
            estimated_cost=round(random.uniform(50.0, 500.0), 2),
            start_date=datetime.now(timezone.utc),
            next_due_date=None,
            last_execution_date=None,
            active=True,
            asset_id=asset.id if asset else None,
            component_id=component.id if component else None,
        )
        samples.append(p)
        session.add(p)
    await session.flush()

    # Mantenimientos creados arriba


async def _create_failures_orders_tasks_maintenance(
    session: AsyncSession,
    assets: list[Asset],
    components: list[Component],
    supervisors: list[User],
    technicians: list[User],
    departments: list[Department],
):
    now = datetime.now(timezone.utc)
    # Evitar duplicar masivo
    existing_tasks = (await session.execute(select(func.count()).select_from(Task))).scalar() or 0
    if existing_tasks >= 400:
        return

    all_tasks: list[Task] = []

    # Fallos por asset
    failures_by_asset: dict[int, list[Failure]] = {}
    for asset in assets:
        failures_for_asset: list[Failure] = []
        for _ in range(random.randint(1, 3)):
            comp_candidates = [c for c in components if c.asset_id == asset.id]
            comp = random.choice(comp_candidates) if comp_candidates else None
            f = Failure(
                description=f"Failure on {asset.name}{' - '+comp.name if comp else ''}",
                status=_to_db_enum(random.choice([FailureStatus.PENDING.value, FailureStatus.INVESTIGATING.value, FailureStatus.RESOLVED.value])),
                severity=_to_db_enum(random.choice([FailureSeverity.LOW.value, FailureSeverity.MEDIUM.value, FailureSeverity.HIGH.value, FailureSeverity.CRITICAL.value])),
                asset_id=asset.id,
                component_id=comp.id if comp else None,
                reported_by=(random.choice(supervisors + technicians).id if (supervisors + technicians) else None),
            )
            failures_for_asset.append(f)
            session.add(f)
        failures_by_asset[asset.id] = failures_for_asset

    for asset in assets:
        for k in range(1, 11):  # 10 WO por asset
            dep = random.choice(departments)
            failure = random.choice(failures_by_asset.get(asset.id, [None]) + [None])
            wo = WorkOrder(
                title=f"WO-{asset.id}-{k}",
                description=f"Maintenance #{k} for {asset.name}",
                work_type=_to_db_enum(random.choice([WorkOrderType.REPAIR.value, WorkOrderType.MAINTENANCE.value, WorkOrderType.INSPECTION.value])),
                status=_to_db_enum(random.choice([WorkOrderStatus.OPEN.value, WorkOrderStatus.IN_PROGRESS.value, WorkOrderStatus.COMPLETED.value, WorkOrderStatus.CANCELLED.value])),
                priority=_to_db_enum(random.choice([WorkOrderPriority.LOW.value, WorkOrderPriority.MEDIUM.value, WorkOrderPriority.HIGH.value])),
                asset_id=asset.id,
                assigned_to=(random.choice(technicians).id if technicians else None),
                created_by=(random.choice(supervisors).id if supervisors else None),
                scheduled_date=_to_naive(now - timedelta(days=random.randint(0, 120)) + timedelta(days=random.randint(-5, 20))),
                department_id=dep.id,
                failure_id=(failure.id if failure else None),
                estimated_hours=round(random.uniform(2.0, 16.0), 1),
            )
            session.add(wo)
            await session.flush()

            # 3-6 tareas por WO
            num_tasks = random.randint(3, 6)
            for t in range(num_tasks):
                comp_candidates = [c for c in components if c.asset_id == asset.id]
                comp = random.choice(comp_candidates) if comp_candidates else None
                status = _to_db_enum(random.choice([TaskStatus.PENDING.value, TaskStatus.IN_PROGRESS.value, TaskStatus.COMPLETED.value]))
                due = _to_naive(now + timedelta(days=random.randint(-30, 45)))
                task = Task(
                    title=f"Task {wo.id}-{t+1}{' on '+comp.name if comp else ''}",
                    description=f"Perform action {t+1} on {asset.name}",
                    status=status,
                    priority=_to_db_enum(random.choice([TaskPriority.LOW.value, TaskPriority.MEDIUM.value, TaskPriority.HIGH.value])),
                    estimated_hours=round(random.uniform(1.0, 8.0), 1),
                    assigned_to=(random.choice(technicians).id if technicians else None),
                    created_by_id=(random.choice(supervisors).id if supervisors else None),
                    asset_id=asset.id,
                    component_id=comp.id if comp else None,
                    workorder_id=wo.id,
                    due_date=due,
                )
                session.add(task)
                all_tasks.append(task)
    await session.flush()

    # Mantenimientos
    for task in random.sample(all_tasks, max(1, int(len(all_tasks) * 0.25))):
        maint = Maintenance(
            description=f"Maintenance for {task.title}",
            status=_to_db_enum(random.choice([MaintenanceStatus.SCHEDULED.value, MaintenanceStatus.IN_PROGRESS.value, MaintenanceStatus.COMPLETED.value, MaintenanceStatus.CANCELLED.value])),
            maintenance_type=_to_db_enum(random.choice([MaintenanceType.PREVENTIVE.value, MaintenanceType.CORRECTIVE.value, MaintenanceType.PREDICTIVE.value])),
            scheduled_date=_to_naive(datetime.now(timezone.utc) + timedelta(days=random.randint(-20, 30))),
            completed_date=None,
            duration_hours=round(random.uniform(0.5, 12.0), 1),
            cost=round(random.uniform(20.0, 400.0), 2),
            notes="Auto generated",
            asset_id=task.asset_id,
            component_id=task.component_id,
            user_id=task.assigned_to,
            workorder_id=task.workorder_id,
        )
        session.add(maint)
    await session.flush()

    # Consumos de inventario en ~30% de tareas
    inv_map = {inv.component_id: inv for inv in (await session.execute(select(InventoryItem))).scalars().all()}
    for task in random.sample(all_tasks, max(1, int(len(all_tasks) * 0.3))):
        comps_same_asset = [c for c in components if c.asset_id == task.asset_id]
        for comp in random.sample(comps_same_asset, k=min(len(comps_same_asset), random.choice([1, 1, 2]))):
            inv = inv_map.get(comp.id)
            if not inv or (inv.quantity or 0) <= 0:
                continue
            qty_use = min(round(random.uniform(0.5, 3.0), 1), float(inv.quantity))
            if qty_use <= 0:
                continue
            tuc = TaskUsedComponent(
                task_id=task.id,
                component_id=comp.id,
                quantity=qty_use,
                unit_cost_snapshot=inv.unit_cost,
            )
            session.add(tuc)
            inv.quantity = float(inv.quantity) - qty_use


async def seed_database():
    """Puebla la base de datos con un conjunto amplio de datos (idempotente por umbrales)."""
    async with AsyncSessionLocal() as session:
        try:
            # Normalizar estados existentes siempre
            await _normalize_asset_component_statuses(session)
            await _normalize_failure_statuses(session)
            await session.commit()
            # Si ya hay suficientes tareas, asumir que está poblado amplio
            tasks_cnt = (await session.execute(select(func.count()).select_from(Task))).scalar() or 0
            if tasks_cnt and tasks_cnt >= 400:
                logger.info("ℹ️ Seed: ya existen %s+ tareas, se omite repoblado", tasks_cnt)
                return

            # 1) Departamentos
            departments = await _ensure_departments(session)

            # 2) Usuarios por rol
            roles = await _ensure_users(session, departments)
            admins = roles.get("Admin", [])
            supervisors = roles.get("Supervisor", [])
            technicians = roles.get("Tecnico", [])

            # 3) Activos, componentes e inventario
            assets, components = await _create_assets_components_inventory(session, supervisors, technicians)

            # 4) Fallos + WOs + Tareas + Mantenimientos + Consumos
            await _create_failures_orders_tasks_maintenance(session, assets, components, supervisors, technicians, departments)

            await session.commit()
            logger.info("✅ Base de datos poblada con dataset amplio (departments, users, assets, components, inventory, failures, WOs, tasks, maintenance)")
        except Exception as e:
            await session.rollback()
            logger.error(f"❌ Error poblando la base de datos: {e}")
            raise

if __name__ == "__main__":
    asyncio.run(seed_database())
# ...existing code...