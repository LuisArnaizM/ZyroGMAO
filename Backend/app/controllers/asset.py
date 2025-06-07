from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.asset import Asset
from app.schemas.asset import AssetCreate, AssetRead, AssetUpdate

async def create_asset(db: AsyncSession, asset_in: AssetCreate, organization_id: int):
    """Create a new asset in the database"""
    
    # Crear asset con organization_id
    asset_data = asset_in.model_dump()
    asset_data['organization_id'] = organization_id
    new_asset = Asset(**asset_data)
    db.add(new_asset)
    await db.commit()
    await db.refresh(new_asset)
    return new_asset

async def get_asset(db: AsyncSession, asset_id: int, organization_id: int):
    """Get an asset by ID within organization"""
    result = await db.execute(
        select(Asset).where(
            Asset.id == asset_id,
            Asset.organization_id == organization_id
        )
    )
    return result.scalar_one_or_none()

async def get_assets(
    db: AsyncSession, 
    organization_id: int,
    page: int = 1,
    page_size: int = 20,
    search: str = None
):
    """Get all assets with pagination and search capability within organization"""
    offset = (page - 1) * page_size

    query = select(Asset).where(Asset.organization_id == organization_id)

    if search:
        search_term = f"%{search}%"
        query = query.where(
            (Asset.name.ilike(search_term)) | 
            (Asset.description.ilike(search_term))
        )
    
    query = query.offset(offset).limit(page_size)
    result = await db.execute(query)
    return result.scalars().all()

async def update_asset(db: AsyncSession, asset_id: int, asset_in: AssetUpdate, organization_id: int):
    """Update an asset by ID within organization"""
    result = await db.execute(
        select(Asset).where(
            Asset.id == asset_id,
            Asset.organization_id == organization_id
        )
    )
    asset = result.scalar_one_or_none()
    
    if asset is None:
        return None
    
    update_data = asset_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(asset, key, value)
    
    await db.commit()
    await db.refresh(asset)
    return asset

async def delete_asset(db: AsyncSession, asset_id: int, organization_id: int):
    """Delete an asset by ID within organization"""
    result = await db.execute(
        select(Asset).where(
            Asset.id == asset_id,
            Asset.organization_id == organization_id
        )
    )
    asset = result.scalar_one_or_none()
    
    if asset is None:
        return False
    
    await db.delete(asset)
    await db.commit()
    return True