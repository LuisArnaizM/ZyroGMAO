from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.postgres import get_db
from app.auth.dependencies import get_current_user, require_role
from app.auth.dependencies import get_current_organization, require_org_admin
from app.controllers.organization import (
    create_organization,
    get_organization_by_id,
    get_organization_by_slug,
    get_organizations,
    update_organization,
    delete_organization,
    get_organization_stats
)
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationRead,
    OrganizationUpdate,
    OrganizationStats
)
from typing import List, Optional

router = APIRouter(tags=["organizations"])

@router.post("/", response_model=OrganizationRead)
async def create_organization_endpoint(
    org_data: OrganizationCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_role(["Admin"]))  # Solo super admin
):
    """Crear una nueva organización (solo super admin)"""
    return await create_organization(db, org_data)

@router.get("/", response_model=dict)
async def list_organizations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_role(["Admin"]))  # Solo super admin
):
    """Listar organizaciones (solo super admin)"""
    organizations, total = await get_organizations(db, page, page_size, search, active_only)
    
    return {
        "organizations": organizations,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "pages": (total + page_size - 1) // page_size
        }
    }

@router.get("/{org_id}", response_model=OrganizationRead)
async def get_organization_endpoint(
    org_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_role(["Admin"]))
):
    """Obtener organización por ID (solo super admin)"""
    organization = await get_organization_by_id(db, org_id)
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    return organization

@router.put("/{org_id}", response_model=OrganizationRead)
async def update_organization_endpoint(
    org_id: int,
    org_update: OrganizationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_role(["Admin"]))
):
    """Actualizar organización (solo super admin)"""
    organization = await update_organization(db, org_id, org_update)
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    return organization

@router.put("/current", response_model=OrganizationRead)
async def update_current_organization(
    org_update: OrganizationUpdate,
    organization = Depends(get_current_organization),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_org_admin())
):
    """Actualizar la organización actual (org admin)"""
    # Limitar campos que pueden actualizar los org admin
    limited_update = OrganizationUpdate(
        name=org_update.name,
        description=org_update.description,
        domain=org_update.domain
    )
    
    updated_org = await update_organization(db, organization.id, limited_update)
    if not updated_org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return updated_org

@router.get("/{org_id}/stats", response_model=OrganizationStats)
async def get_organization_stats_endpoint(
    org_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_role(["Admin"]))
):
    """Obtener estadísticas de una organización (solo super admin)"""
    stats = await get_organization_stats(db, org_id)
    if not stats:
        raise HTTPException(status_code=404, detail="Organization not found")
    return stats