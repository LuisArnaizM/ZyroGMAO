from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.asset import Asset
from app.schemas.asset import AssetCreate, AssetRead, AssetUpdate

async def create_asset(db: AsyncSession, asset_in: AssetCreate):
    """Create a new asset in the database"""
    new_asset = Asset(**asset_in.dict())
    db.add(new_asset)
    await db.commit()
    await db.refresh(new_asset)
    return new_asset

async def get_asset(db: AsyncSession, asset_id: int):
    """Get an asset by ID"""
    result = await db.execute(select(Asset).where(Asset.id == asset_id))
    return result.scalar_one_or_none()

async def get_assets(db: AsyncSession, skip: int = 0, limit: int = 100):
    """Get all assets with pagination"""
    result = await db.execute(select(Asset).offset(skip).limit(limit))
    return result.scalars().all()

async def update_asset(db: AsyncSession, asset_id: int, asset_in: AssetUpdate):
    """Update an asset by ID"""
    result = await db.execute(select(Asset).where(Asset.id == asset_id))
    asset = result.scalar_one_or_none()
    
    if asset is None:
        return None
    
    # Update only the fields that are provided
    update_data = asset_in.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(asset, key, value)
    
    await db.commit()
    await db.refresh(asset)
    return asset

async def delete_asset(db: AsyncSession, asset_id: int):
    """Delete an asset by ID"""
    result = await db.execute(select(Asset).where(Asset.id == asset_id))
    asset = result.scalar_one_or_none()
    
    if asset is None:
        return False
    
    await db.delete(asset)
    await db.commit()
    return True