from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.future import select
from typing import List, Optional

from app.models.failure import Failure
from app.schemas.failure import FailureCreate, FailureUpdate

async def create_failure(db: AsyncSession, failure: FailureCreate) -> Failure:
    db_failure = Failure(
        asset_id=failure.asset_id,
        description=failure.description,
        status="open"
    )
    db.add(db_failure)
    await db.commit()
    await db.refresh(db_failure)
    return db_failure

async def get_failure(db: AsyncSession, failure_id: int) -> Optional[Failure]:
    result = await db.execute(select(Failure).filter(Failure.id == failure_id))
    return result.scalar_one_or_none()

async def get_failures(
    db: AsyncSession, 
    page: int = 1,
    page_size: int = 20,
    search: str = None
) -> List[Failure]:
    """
    Get all failures with pagination and search capability
    
    Parameters:
    - db: Database session
    - page: Page number (starts from 1)
    - page_size: Number of records per page
    - search: Search string to filter failures by description or status
    """

    offset = (page - 1) * page_size
    
    query = select(Failure)
    
    if search:
        search_term = f"%{search}%"
        query = query.where(
            (Failure.description.ilike(search_term)) | 
            (Failure.status.ilike(search_term))
        )

    query = query.offset(offset).limit(page_size)

    result = await db.execute(query)
    return result.scalars().all()

async def update_failure(db: AsyncSession, failure_id: int, failure: FailureUpdate) -> Optional[Failure]:
    db_failure = await get_failure(db, failure_id)
    if not db_failure:
        return None
    
    update_data = failure.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_failure, key, value)
    
    await db.commit()
    await db.refresh(db_failure)
    return db_failure

async def delete_failure(db: AsyncSession, failure_id: int) -> bool:
    db_failure = await get_failure(db, failure_id)
    if not db_failure:
        return False
    
    await db.delete(db_failure)
    await db.commit()
    return True