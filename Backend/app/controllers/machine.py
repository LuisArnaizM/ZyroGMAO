from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.machine import Machine
from app.schemas.machine import MachineCreate, MachineRead, MachineUpdate
from datetime import datetime

async def create_machine(db: AsyncSession, machine_in: MachineCreate):
    """Create a new machine"""
    new_machine = Machine(
        name=machine_in.name,
        description=machine_in.description,
        location=machine_in.location,
        responsible_id=machine_in.responsible_id,
        created_at=datetime.now()
    )
    db.add(new_machine)
    await db.commit()
    await db.refresh(new_machine)
    return new_machine

async def get_machine(db: AsyncSession, machine_id: int):
    """Get a machine by ID"""
    result = await db.execute(select(Machine).where(Machine.id == machine_id))
    return result.scalar_one_or_none()

async def get_machines(
    db: AsyncSession, 
    page: int = 1,
    page_size: int = 20,
    search: str = None
):
    """
    Get all machines with pagination and search capability
    
    Parameters:
    - db: Database session
    - page: Page number (starts from 1)
    - page_size: Number of records per page
    - search: Search string to filter machines by name, description or location
    """
    # Calculate offset based on page and page_size
    offset = (page - 1) * page_size
    
    # Build the base query
    query = select(Machine)
    
    # Apply search filter if provided
    if search:
        search_term = f"%{search}%"
        query = query.where(
            (Machine.name.ilike(search_term)) | 
            (Machine.description.ilike(search_term)) |
            (Machine.location.ilike(search_term))
        )
    
    # Apply pagination
    query = query.offset(offset).limit(page_size)
    
    # Execute query
    result = await db.execute(query)
    return result.scalars().all()
async def update_machine(db: AsyncSession, machine_id: int, machine_in: MachineUpdate):
    """Update a machine by ID"""
    result = await db.execute(select(Machine).where(Machine.id == machine_id))
    machine = result.scalar_one_or_none()
    
    if machine is None:
        return None
    
    # Update only the fields that are provided
    update_data = machine_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(machine, key, value)
    
    await db.commit()
    await db.refresh(machine)
    return machine

async def delete_machine(db: AsyncSession, machine_id: int):
    """Delete a machine by ID"""
    result = await db.execute(select(Machine).where(Machine.id == machine_id))
    machine = result.scalar_one_or_none()
    
    if machine is None:
        return False
    
    await db.delete(machine)
    await db.commit()
    return True