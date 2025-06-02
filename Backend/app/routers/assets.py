from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database.postgres import get_db
from app.schemas.asset import AssetCreate, AssetRead, AssetUpdate
from app.crud.asset import create_asset, get_asset, get_assets, update_asset, delete_asset
from app.auth.dependencies import get_current_user, require_role

router = APIRouter(prefix="/assets", tags=["Assets"])

@router.post("/", response_model=AssetRead)
async def create_new_asset(
    asset_in: AssetCreate, 
    db: AsyncSession = Depends(get_db),
    user = Depends(require_role(["Admin", "Supervisor"]))
):
    return await create_asset(db=db, asset_in=asset_in)

@router.get("/{asset_id}", response_model=AssetRead)
async def read_asset(
    asset_id: int, 
    db: AsyncSession = Depends(get_db)
):
    asset = await get_asset(db=db, asset_id=asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset

@router.get("/", response_model=List[AssetRead])
async def read_assets(
    skip: int = Query(0, ge=0), 
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    return await get_assets(db=db, skip=skip, limit=limit)

@router.put("/{asset_id}", response_model=AssetRead)
async def update_existing_asset(
    asset_id: int, 
    asset_in: AssetUpdate, 
    db: AsyncSession = Depends(get_db),
    user = Depends(require_role(["Admin", "Supervisor"]))
):
    asset = await update_asset(db=db, asset_id=asset_id, asset_in=asset_in)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset

@router.delete("/{asset_id}", response_model=dict)
async def delete_existing_asset(
    asset_id: int, 
    db: AsyncSession = Depends(get_db),
    user = Depends(require_role(["Admin"]))
):
    result = await delete_asset(db=db, asset_id=asset_id)
    if not result:
        raise HTTPException(status_code=404, detail="Asset not found")
    return {"detail": "Asset deleted successfully"}