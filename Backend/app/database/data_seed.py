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
    # Asignar managers determinísticos a algunos departamentos si vacíos
    dep_map = {d.name: d for d in departments}
    supervisors = [u for u in (await session.execute(select(User))).scalars().all() if u.role == "Supervisor"]
    # Orden estable
    supervisors.sort(key=lambda x: x.id)
    if supervisors:
        if dep_map.get("Maintenance") and not dep_map["Maintenance"].manager_id:
            dep_map["Maintenance"].manager_id = supervisors[0].id
        if len(supervisors) > 1 and dep_map.get("Production") and not dep_map["Production"].manager_id:
            dep_map["Production"].manager_id = supervisors[1].id
        if len(supervisors) > 2 and dep_map.get("IT") and not dep_map["IT"].manager_id:
            dep_map["IT"].manager_id = supervisors[2].id
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

    # Fallos por asset (creamos un histórico temporal consistente para KPIs MTBF/MTTF)
    failures_by_asset: dict[int, list[Failure]] = {}
    horizon_days = 120  # ~4 meses hacia atrás
    base_start = now - timedelta(days=horizon_days)
    for asset in assets:
        failures_for_asset: list[Failure] = []
        # Número de fallos controlado para generar gaps (entre 4 y 8)
        num_failures = random.randint(4, 8)
        failure_times = sorted([
            base_start + timedelta(days=random.uniform(0, horizon_days)) for _ in range(num_failures)
        ])
        prev_resolved: datetime | None = None
        for ft in failure_times:
            comp_candidates = [c for c in components if c.asset_id == asset.id]
            comp = random.choice(comp_candidates) if comp_candidates else None
            reported_date = ft
            # Duración de fallo entre 2h y 48h
            repair_hours = random.uniform(2, 48)
            resolved_date = reported_date + timedelta(hours=repair_hours)
            # Estado final (60% resolved, 30% investigating, 10% pending)
            status_choice = random.choices(
                population=[FailureStatus.RESOLVED.value, FailureStatus.INVESTIGATING.value, FailureStatus.PENDING.value],
                weights=[0.6, 0.3, 0.1],
                k=1
            )[0]
            if status_choice != FailureStatus.RESOLVED.value:
                # Algunas no resueltas aún: quitar resolved_date parcialmente
                if random.random() < 0.5:  # noqa: S311
                    resolved_date = None
            severity_choice = random.choices(
                population=[FailureSeverity.LOW.value, FailureSeverity.MEDIUM.value, FailureSeverity.HIGH.value, FailureSeverity.CRITICAL.value],
                weights=[0.25, 0.4, 0.25, 0.10],
                k=1
            )[0]
            f = Failure(
                description=f"Failure on {asset.name}{' - '+comp.name if comp else ''}",
                status=_to_db_enum(status_choice),
                severity=_to_db_enum(severity_choice),
                asset_id=asset.id,
                component_id=comp.id if comp else None,
                reported_by=(random.choice(supervisors + technicians).id if (supervisors + technicians) else None),
                reported_date=_to_naive(reported_date),
                resolved_date=_to_naive(resolved_date),
            )
            failures_for_asset.append(f)
            session.add(f)
            prev_resolved = resolved_date or prev_resolved
        failures_by_asset[asset.id] = failures_for_asset

    for asset in assets:
        # Espaciamos WO a lo largo del horizonte temporal
        wo_count = 12
        wo_times = sorted([
            now - timedelta(days=random.uniform(0, 110)) for _ in range(wo_count)
        ])
        for k, created_at in enumerate(wo_times, start=1):
            dep = random.choice(departments)
            failure = random.choice(failures_by_asset.get(asset.id, [None]) + [None])
            status_choice = random.choices(
                population=[WorkOrderStatus.OPEN.value, WorkOrderStatus.IN_PROGRESS.value, WorkOrderStatus.COMPLETED.value, WorkOrderStatus.CANCELLED.value],
                weights=[0.25, 0.20, 0.45, 0.10],
                k=1
            )[0]
            scheduled_offset = random.uniform(-5, 15)
            scheduled_date = created_at + timedelta(days=scheduled_offset)
            started_date = None
            completed_date = None
            if status_choice in (WorkOrderStatus.IN_PROGRESS.value, WorkOrderStatus.COMPLETED.value):
                started_date = created_at + timedelta(hours=random.uniform(0.5, 24))
            if status_choice == WorkOrderStatus.COMPLETED.value:
                completed_date = (started_date or created_at) + timedelta(hours=random.uniform(1, 72))
            wo = WorkOrder(
                title=f"WO-{asset.id}-{k}",
                description=f"Maintenance #{k} for {asset.name}",
                work_type=_to_db_enum(random.choice([WorkOrderType.REPAIR.value, WorkOrderType.MAINTENANCE.value, WorkOrderType.INSPECTION.value])),
                status=_to_db_enum(status_choice),
                priority=_to_db_enum(random.choice([WorkOrderPriority.LOW.value, WorkOrderPriority.MEDIUM.value, WorkOrderPriority.HIGH.value])),
                asset_id=asset.id,
                assigned_to=(random.choice(technicians).id if technicians else None),
                created_by=(random.choice(supervisors).id if supervisors else None),
                scheduled_date=_to_naive(scheduled_date),
                department_id=dep.id,
                failure_id=(failure.id if failure else None),
                estimated_hours=round(random.uniform(2.0, 16.0), 1),
                created_at=_to_naive(created_at),
                started_date=_to_naive(started_date),
                completed_date=_to_naive(completed_date),
            )
            session.add(wo)
            await session.flush()

            # 3-6 tareas por WO
            num_tasks = random.randint(3, 6)
            for t in range(num_tasks):
                comp_candidates = [c for c in components if c.asset_id == asset.id]
                comp = random.choice(comp_candidates) if comp_candidates else None
                task_status = random.choices(
                    population=[TaskStatus.PENDING.value, TaskStatus.IN_PROGRESS.value, TaskStatus.COMPLETED.value],
                    weights=[0.3, 0.3, 0.4],
                    k=1
                )[0]
                # Tiempos relativos a created_at del WO
                task_created = created_at + timedelta(hours=random.uniform(0, 48))
                # Simulamos horas reales sólo si completada
                actual_hours = None
                if task_status == TaskStatus.COMPLETED.value:
                    actual_hours = round(random.uniform(0.5, 10.0), 1)
                due = task_created + timedelta(days=random.uniform(1, 30))
                est_hours = round(random.uniform(1.0, 6.0), 1)
                assigned_user_id = (random.choice(technicians).id if technicians else None)
                if assigned_user_id:
                    from app.models.calendar import UserWorkingDay, UserSpecialDay
                    # Cache patrones
                    if not hasattr(session, '_seed_work_pattern'):
                        session._seed_work_pattern = {}
                    if assigned_user_id not in session._seed_work_pattern:
                        rows = (await session.execute(select(UserWorkingDay).where(UserWorkingDay.user_id==assigned_user_id))).scalars().all()
                        if not rows:
                            for wd in range(7):
                                session.add(UserWorkingDay(user_id=assigned_user_id, weekday=wd, hours=(8.0 if wd < 5 else 0.0), is_active=True))
                            await session.flush()
                            rows = (await session.execute(select(UserWorkingDay).where(UserWorkingDay.user_id==assigned_user_id))).scalars().all()
                        session._seed_work_pattern[assigned_user_id] = {r.weekday: (r.hours if r.is_active else 0.0) for r in rows}
                    pattern = session._seed_work_pattern[assigned_user_id]
                    # Cache días especiales
                    if not hasattr(session, '_seed_specials'):
                        specials = (await session.execute(select(UserSpecialDay))).scalars().all()
                        session._seed_specials = {(s.user_id, s.date): s for s in specials}
                    special_map = session._seed_specials
                    attempts = 0
                    while attempts < 20:
                        d_date = due.date()
                        spec = special_map.get((assigned_user_id, d_date))
                        weekday = d_date.weekday()
                        base_hours = pattern.get(weekday, 0.0)
                        # Capacidad día
                        if spec:
                            if not spec.is_working or (spec.is_working and spec.hours is not None and spec.hours <= 0):
                                due = due + timedelta(days=1)
                                attempts += 1
                                continue
                            cap_day = spec.hours if spec.hours is not None else base_hours
                        else:
                            cap_day = base_hours
                        if cap_day <= 0:
                            due = due + timedelta(days=1)
                            attempts += 1
                            continue
                        planned = 0.0
                        for existing in all_tasks:
                            if existing.assigned_to == assigned_user_id and existing.due_date and existing.due_date.date() == d_date:
                                planned += existing.estimated_hours or 0.0
                        if planned + est_hours <= cap_day + 1e-6:
                            break
                        due = due + timedelta(days=1)
                        attempts += 1
                task = Task(
                    title=f"Task {wo.id}-{t+1}{' on '+comp.name if comp else ''}",
                    description=f"Perform action {t+1} on {asset.name}",
                    status=_to_db_enum(task_status),
                    priority=_to_db_enum(random.choice([TaskPriority.LOW.value, TaskPriority.MEDIUM.value, TaskPriority.HIGH.value])),
                    estimated_hours=est_hours,
                    assigned_to=assigned_user_id,
                    created_by_id=(random.choice(supervisors).id if supervisors else None),
                    asset_id=asset.id,
                    component_id=comp.id if comp else None,
                    workorder_id=wo.id,
                    due_date=_to_naive(due),
                    created_at=_to_naive(task_created),
                    actual_hours=actual_hours,
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

    # Consumos de inventario en ~30% de tareas distribuidos últimos 30 días
    from app.models.calendar import UserSpecialDay, UserWorkingDay
    inv_map = {inv.component_id: inv for inv in (await session.execute(select(InventoryItem))).scalars().all()}
    usage_tasks = random.sample(all_tasks, max(1, int(len(all_tasks) * 0.3)))
    today = datetime.now(timezone.utc).date()
    for idx, task in enumerate(usage_tasks):
        day_offset = idx % 30
        usage_date = today - timedelta(days=day_offset)
        usage_dt = datetime.combine(usage_date, datetime.min.time(), tzinfo=timezone.utc)
        comps_same_asset = [c for c in components if c.asset_id == task.asset_id]
        sample_count = min(len(comps_same_asset), random.choice([1, 1, 2]))
        for comp in random.sample(comps_same_asset, k=sample_count):
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
                created_at=_to_naive(usage_dt),
            )
            session.add(tuc)
            inv.quantity = float(inv.quantity) - qty_use

    # NOTA: El ajuste definitivo de due_date evitando días no laborables (patrón + especiales)
    # se realiza fuera (ver _adjust_task_due_dates) para poder reutilizarlo incluso cuando
    # el seed detecta ya muchas tareas y solo queremos corregir fechas.


async def _ensure_calendar_demo_data(session: AsyncSession, supervisors: list[User], technicians: list[User]):
    """Crea algunos días especiales/vacaciones de ejemplo si aún no existen.

    Se ejecuta siempre (idempotente) antes de generar tareas para que las fechas
    se puedan ajustar adecuadamente.
    """
    from app.models.calendar import UserSpecialDay
    today = datetime.now(timezone.utc).date()
    year_start = today.replace(month=1, day=1)
    try:
        # Vacaciones supervisor principal: semana 30 (aprox fin Julio)
        if supervisors:
            sup = supervisors[0]
            vac_start = year_start + timedelta(days=29*7)  # aprox semana 30 inicio
            for i in range(5):
                d = vac_start + timedelta(days=i)
                if not (await session.execute(select(UserSpecialDay).where(UserSpecialDay.user_id==sup.id, UserSpecialDay.date==d))).scalar_one_or_none():
                    session.add(UserSpecialDay(user_id=sup.id, date=d, is_working=False, hours=0.0, reason="Vacaciones"))
        # Festivo global (1 Mayo) para primeros técnicos
        try:
            may1 = today.replace(month=5, day=1)
        except ValueError:
            # Si hoy es 29/30 Feb (no aplicaría), elegir 1 Junio como fallback
            may1 = today.replace(month=6, day=1)
        for tech in technicians[:5]:
            if not (await session.execute(select(UserSpecialDay).where(UserSpecialDay.user_id==tech.id, UserSpecialDay.date==may1))).scalar_one_or_none():
                session.add(UserSpecialDay(user_id=tech.id, date=may1, is_working=False, hours=0.0, reason="Día del Trabajador"))
        # Media jornada de formación en 3 días para primer técnico
        if technicians:
            d_partial = today + timedelta(days=3)
            t0 = technicians[0]
            if not (await session.execute(select(UserSpecialDay).where(UserSpecialDay.user_id==t0.id, UserSpecialDay.date==d_partial))).scalar_one_or_none():
                session.add(UserSpecialDay(user_id=t0.id, date=d_partial, is_working=True, hours=4.0, reason="Formación"))
        await session.flush()
    except Exception as e:  # noqa: BLE001
        logger.warning(f"Calendario demo parcial omitido: {e}")


async def _adjust_task_due_dates(session: AsyncSession):
    """Ajusta due_date de tareas que caigan en días no laborables para el usuario asignado.

    Considera:
      - Días especiales (UserSpecialDay) no laborables
      - Patrón de UserWorkingDay (weekday con 0 horas => no laborable)
    Desplaza la fecha al siguiente día laborable hasta 10 intentos (seguridad).
    """
    from app.models.calendar import UserSpecialDay, UserWorkingDay
    tasks = (await session.execute(select(Task).where(Task.assigned_to.isnot(None), Task.due_date.isnot(None)))).scalars().all()
    if not tasks:
        return
    # Cache patrones y especiales por usuario
    # Especiales: map (user_id, date)->is_working,hours
    specials = (await session.execute(select(UserSpecialDay))).scalars().all()
    special_map = {(s.user_id, s.date): s for s in specials}
    # Working pattern por user: weekday->hours
    working_by_user: dict[int, dict[int, float]] = {}
    changed = 0
    for task in tasks:
        if not task.due_date:
            continue
        uid = task.assigned_to
        if uid is None:
            continue
        # Cargar patrón on-demand
        if uid not in working_by_user:
            rows = (await session.execute(select(UserWorkingDay).where(UserWorkingDay.user_id==uid))).scalars().all()
            if not rows:
                # crear por defecto (Mon-Fri 8h)
                for wd in range(7):
                    session.add(UserWorkingDay(user_id=uid, weekday=wd, hours=(8.0 if wd < 5 else 0.0), is_active=True))
                await session.flush()
                rows = (await session.execute(select(UserWorkingDay).where(UserWorkingDay.user_id==uid))).scalars().all()
            working_by_user[uid] = {r.weekday: (r.hours if r.is_active else 0.0) for r in rows}
        # Evaluar la fecha
        attempts = 0
        while attempts < 10:
            due_date_date = task.due_date.date()
            spec = special_map.get((uid, due_date_date))
            if spec:
                if not spec.is_working:  # Día especial no laborable
                    task.due_date = task.due_date + timedelta(days=1)
                    attempts += 1
                    continue
                # Si is_working True y hours None -> usar patrón por defecto; si horas 0 => no laborable
                if spec.is_working and spec.hours is not None and spec.hours <= 0:
                    task.due_date = task.due_date + timedelta(days=1)
                    attempts += 1
                    continue
                break  # es laborable especial
            # No especial: usar patrón weekday
            weekday = due_date_date.weekday()
            hours = working_by_user[uid].get(weekday, 0.0)
            if hours <= 0.0:
                task.due_date = task.due_date + timedelta(days=1)
                attempts += 1
                continue
            break
        if attempts and attempts < 10:
            changed += 1
    if changed:
        logger.info("Ajustadas %s due_date de tareas no laborables", changed)
        await session.flush()


async def _rebalance_task_capacity(session: AsyncSession):
    """Redistribuye tareas que exceden la capacidad diaria moviéndolas a días siguientes con hueco.

    Estrategia greedy:
      - Agrupar tareas por (user, fecha) ordenadas por due_date y luego id.
      - Calcular carga acumulada; si se excede capacidad, desplazar tareas excedentes
        al siguiente día laborable con hueco (respetando días no laborables / especiales)
        hasta 30 días hacia adelante para evitar loops infinitos.
    """
    from app.models.calendar import UserSpecialDay, UserWorkingDay
    tasks = (await session.execute(select(Task).where(Task.assigned_to.isnot(None), Task.due_date.isnot(None)))).scalars().all()
    if not tasks:
        return
    # Cache patrones y especiales
    specials = (await session.execute(select(UserSpecialDay))).scalars().all()
    special_map = {(s.user_id, s.date): s for s in specials}
    working_by_user: dict[int, dict[int, float]] = {}
    # Agrupar por usuario y ordenar por fecha
    tasks.sort(key=lambda x: (x.assigned_to, x.due_date, x.id))
    by_user: dict[int, list[Task]] = {}
    for t in tasks:
        by_user.setdefault(t.assigned_to, []).append(t)
    moved = 0
    for uid, user_tasks in by_user.items():
        # patrón
        if uid not in working_by_user:
            rows = (await session.execute(select(UserWorkingDay).where(UserWorkingDay.user_id==uid))).scalars().all()
            if not rows:
                for wd in range(7):
                    session.add(UserWorkingDay(user_id=uid, weekday=wd, hours=(8.0 if wd < 5 else 0.0), is_active=True))
                await session.flush()
                rows = (await session.execute(select(UserWorkingDay).where(UserWorkingDay.user_id==uid))).scalars().all()
            working_by_user[uid] = {r.weekday: (r.hours if r.is_active else 0.0) for r in rows}
        pattern = working_by_user[uid]
        # Recalcular iterativamente hasta que ningún día se exceda (máx 3 pasadas)
        for _pass in range(3):
            overload_found = False
            # Reagrupar por fecha
            day_map: dict[datetime.date, list[Task]] = {}
            for t in user_tasks:
                day_map.setdefault(t.due_date.date(), []).append(t)
            for d, tlist in list(day_map.items()):
                # Obtener capacidad día
                spec = special_map.get((uid, d))
                weekday = d.weekday()
                base_hours = pattern.get(weekday, 0.0)
                if spec:
                    if not spec.is_working or (spec.is_working and spec.hours is not None and spec.hours <= 0):
                        cap = 0.0
                    else:
                        cap = spec.hours if spec.hours is not None else base_hours
                else:
                    cap = base_hours
                if cap <= 0:
                    # mover todas las tareas de este día
                    moving = tlist
                else:
                    # comprobar carga
                    total = sum((t.estimated_hours or 0.0) for t in tlist)
                    if total <= cap + 1e-6:
                        continue
                    overload_found = True
                    # ordenar por id descendente para mover las más recientes primero
                    tlist_sorted = sorted(tlist, key=lambda x: (x.due_date, x.id), reverse=True)
                    moving = []
                    current = total
                    for mt in tlist_sorted:
                        moving.append(mt)
                        current -= (mt.estimated_hours or 0.0)
                        if current <= cap + 1e-6:
                            break
                # Reubicar tareas en moving
                for mt in moving:
                    attempts = 0
                    new_due = mt.due_date + timedelta(days=1)
                    while attempts < 30:
                        nd = new_due.date()
                        spec2 = special_map.get((uid, nd))
                        weekday2 = nd.weekday()
                        base2 = pattern.get(weekday2, 0.0)
                        if spec2:
                            if not spec2.is_working or (spec2.is_working and spec2.hours is not None and spec2.hours <= 0):
                                new_due += timedelta(days=1)
                                attempts += 1
                                continue
                            cap2 = spec2.hours if spec2.hours is not None else base2
                        else:
                            cap2 = base2
                        if cap2 <= 0:
                            new_due += timedelta(days=1)
                            attempts += 1
                            continue
                        # calcular carga ya planificada allí (incluyendo tareas movidas anteriormente en este loop)
                        load2 = 0.0
                        for oth in user_tasks:
                            if oth is mt:
                                continue
                            if oth.due_date.date() == nd:
                                load2 += (oth.estimated_hours or 0.0)
                        if load2 + (mt.estimated_hours or 0.0) <= cap2 + 1e-6:
                            mt.due_date = new_due
                            moved += 1
                            break
                        new_due += timedelta(days=1)
                        attempts += 1
            if not overload_found:
                break
    if moved:
        logger.info("Rebalanceo de capacidad: %s tareas movidas a días posteriores", moved)
        await session.flush()


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

            # 1) Departamentos (siempre asegurar)
            departments = await _ensure_departments(session)

            # 2) Usuarios por rol (siempre asegurar)
            roles = await _ensure_users(session, departments)
            supervisors = roles.get("Supervisor", [])
            technicians = roles.get("Tecnico", [])

            # 3) Calendario demo (ANTES de generar tareas para poder ajustar due_date en creación)
            await _ensure_calendar_demo_data(session, supervisors, technicians)

            if tasks_cnt and tasks_cnt >= 400:
                # Dataset grande ya existe: sólo aseguramos assets/components base y corregimos due_date si hiciera falta
                logger.info("ℹ️ Seed: %s tareas existentes, solo se aplicarán correcciones de calendario", tasks_cnt)
                # Asegurar assets/components (no crea adicionales si ya hay suficientes)
                await _create_assets_components_inventory(session, supervisors, technicians)
                await _adjust_task_due_dates(session)
                await _rebalance_task_capacity(session)
                await session.commit()
                return

            # 4) Activos, componentes e inventario
            assets, components = await _create_assets_components_inventory(session, supervisors, technicians)

            # 5) Fallos + WOs + Tareas + Mantenimientos + Consumos
            await _create_failures_orders_tasks_maintenance(session, assets, components, supervisors, technicians, departments)

            # 6) Ajuste final de due_date evitando días no laborables (patrón + especiales)
            await _adjust_task_due_dates(session)
            await _rebalance_task_capacity(session)

            await session.commit()
            logger.info("✅ Base de datos poblada y due_date ajustadas evitando días no laborables")
        except Exception as e:
            await session.rollback()
            logger.error(f"❌ Error poblando la base de datos: {e}")
            raise

if __name__ == "__main__":
    asyncio.run(seed_database())
# ...existing code...