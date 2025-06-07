from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import func, and_
from app.models.organization import Organization
from app.models.user import User
from app.models.asset import Asset
from app.models.component import Component
from app.models.task import Task
from app.models.failure import Failure
from app.schemas.organization import OrganizationCreate, OrganizationUpdate, OrganizationStats
from fastapi import HTTPException, status
from typing import List, Optional
import re

async def create_organization(db: AsyncSession, org_data: OrganizationCreate) -> Organization:
    """Crear una nueva organización"""
    
    # Verificar que el slug sea único
    existing_org = await db.execute(
        select(Organization).where(Organization.slug == org_data.slug)
    )
    if existing_org.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization slug already exists"
        )
    
    # Verificar dominio único si se proporciona
    if org_data.domain:
        existing_domain = await db.execute(
            select(Organization).where(Organization.domain == org_data.domain)
        )
        if existing_domain.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Domain already assigned to another organization"
            )
    
    organization = Organization(**org_data.model_dump())
    db.add(organization)
    await db.commit()
    await db.refresh(organization)
    
    return organization

async def get_organization_by_id(db: AsyncSession, org_id: int) -> Optional[Organization]:
    """Obtener organización por ID"""
    result = await db.execute(
        select(Organization).where(Organization.id == org_id)
    )
    return result.scalar_one_or_none()

async def get_organization_by_slug(db: AsyncSession, slug: str) -> Optional[Organization]:
    """Obtener organización por slug"""
    result = await db.execute(
        select(Organization).where(Organization.slug == slug)
    )
    return result.scalar_one_or_none()

async def get_organizations(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    search: Optional[str] = None,
    active_only: bool = True
) -> tuple[List[Organization], int]:
    """Obtener lista de organizaciones con paginación"""
    
    query = select(Organization)
    
    if active_only:
        query = query.where(Organization.is_active == True)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            Organization.name.ilike(search_pattern) |
            Organization.slug.ilike(search_pattern)
        )
    
    # Contar total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Aplicar paginación
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    result = await db.execute(query)
    organizations = result.scalars().all()
    
    return list(organizations), total

async def update_organization(
    db: AsyncSession,
    org_id: int,
    org_update: OrganizationUpdate
) -> Optional[Organization]:
    """Actualizar una organización"""
    
    result = await db.execute(
        select(Organization).where(Organization.id == org_id)
    )
    organization = result.scalar_one_or_none()
    
    if not organization:
        return None
    
    # Verificar dominio único si se actualiza
    if org_update.domain and org_update.domain != organization.domain:
        existing_domain = await db.execute(
            select(Organization).where(
                and_(
                    Organization.domain == org_update.domain,
                    Organization.id != org_id
                )
            )
        )
        if existing_domain.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Domain already assigned to another organization"
            )
    
    # Actualizar campos
    update_data = org_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(organization, field, value)
    
    await db.commit()
    await db.refresh(organization)
    
    return organization

async def delete_organization(db: AsyncSession, org_id: int) -> bool:
    """Eliminar (desactivar) una organización"""
    
    result = await db.execute(
        select(Organization).where(Organization.id == org_id)
    )
    organization = result.scalar_one_or_none()
    
    if not organization:
        return False
    
    # Verificar que no tenga usuarios activos
    users_result = await db.execute(
        select(func.count(User.id)).where(
            and_(
                User.organization_id == org_id,
                User.is_active == 1
            )
        )
    )
    active_users = users_result.scalar()
    
    if active_users > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete organization with {active_users} active users"
        )
    
    # Desactivar en lugar de eliminar
    organization.is_active = False
    await db.commit()
    
    return True

async def get_organization_stats(db: AsyncSession, org_id: int) -> Optional[OrganizationStats]:
    """Obtener estadísticas de una organización"""
    
    result = await db.execute(
        select(Organization).where(Organization.id == org_id)
    )
    organization = result.scalar_one_or_none()
    
    if not organization:
        return None
    
    # Contar usuarios
    user_count_result = await db.execute(
        select(func.count(User.id)).where(User.organization_id == org_id)
    )
    user_count = user_count_result.scalar()
    
    # Contar activos
    asset_count_result = await db.execute(
        select(func.count(Asset.id)).where(Asset.organization_id == org_id)
    )
    asset_count = asset_count_result.scalar()
    
    # Contar componentes
    component_count_result = await db.execute(
        select(func.count(Component.id)).where(Component.organization_id == org_id)
    )
    component_count = component_count_result.scalar()
    
    # Contar tareas activas
    active_tasks_result = await db.execute(
        select(func.count(Task.id)).where(Task.organization_id == org_id)
    )
    active_tasks = active_tasks_result.scalar()
    
    # Contar fallas pendientes
    pending_failures_result = await db.execute(
        select(func.count(Failure.id)).where(
            and_(
                Failure.organization_id == org_id,
                Failure.status == "pending"
            )
        )
    )
    pending_failures = pending_failures_result.scalar()
    
    return OrganizationStats(
        id=organization.id,
        name=organization.name,
        slug=organization.slug,
        user_count=user_count,
        asset_count=asset_count,
        machine_count=component_count,
        active_tasks=active_tasks,
        pending_failures=pending_failures,
        max_users=organization.max_users,
        max_assets=organization.max_assets
    )