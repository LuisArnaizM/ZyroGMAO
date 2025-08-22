from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.database.postgres import get_db
from app.auth.dependencies import get_current_user
from app.controllers.component import (
    create_component, get_components, get_component, 
    update_component, delete_component, get_components_by_asset,
    get_component_statistics
)
from app.schemas.component import (
    ComponentCreate, ComponentRead, ComponentUpdate, 
    ComponentDetail, ComponentWithAsset
)
from app.models.user import User

router = APIRouter(tags=["Components"])

@router.post("/", response_model=ComponentRead)
async def create_component_endpoint(
    component_in: ComponentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        component = await create_component(db=db, component_in=component_in)
        return component
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[ComponentRead])
async def get_components_endpoint(
    asset_id: int = Query(None, description="Filter by asset ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    components = await get_components(
        db=db,
        asset_id=asset_id,
        skip=skip, 
        limit=limit
    )
    return components

@router.get("/asset/{asset_id}", response_model=List[ComponentRead])
async def get_components_by_asset_endpoint(
    asset_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        components = await get_components_by_asset(db=db, asset_id=asset_id)
        return components
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{component_id}/statistics")
async def get_component_statistics_endpoint(
    component_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        stats = await get_component_statistics(db=db, component_id=component_id)
        return stats
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{component_id}", response_model=ComponentDetail)
async def get_component_endpoint(
    component_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        component = await get_component(db=db, component_id=component_id)

        # Agregar estadsticas
        stats = await get_component_statistics(db=db, component_id=component_id)

        # Convertir a ComponentDetail
        component_dict = {
            **component.__dict__,
            "total_sensors": stats["total_sensors"],
            "total_failures": stats["total_failures"],
            "total_maintenance_records": stats["total_maintenance_records"],
            "total_tasks": stats["total_tasks"],
            "needs_maintenance": stats["needs_maintenance"],
            "days_since_last_maintenance": stats.get("days_since_last_maintenance")
        }

        if component.responsible:
            component_dict["responsible_name"] = f"{component.responsible.first_name} {component.responsible.last_name}"

        return ComponentDetail(**component_dict)

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.put("/{component_id}", response_model=ComponentRead)
async def update_component_endpoint(
    component_id: int,
    component_in: ComponentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        component = await update_component(
            db=db, 
            component_id=component_id, 
            component_in=component_in,
        )
        return component
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/{component_id}", response_model=dict)
async def delete_component_endpoint(
    component_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        result = await delete_component(db=db, component_id=component_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/asset/{asset_id}", response_model=List[ComponentRead])
async def get_components_by_asset_endpoint(
    asset_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        components = await get_components_by_asset(db=db, asset_id=asset_id)
        return components
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{component_id}/statistics")
async def get_component_statistics_endpoint(
    component_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        stats = await get_component_statistics(db=db, component_id=component_id)
        return stats
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
