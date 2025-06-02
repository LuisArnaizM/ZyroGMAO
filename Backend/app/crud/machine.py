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
        created_at=datetime.utcnow()
    )
    db.add(new_machine)
    await db.commit()
    await db.refresh(new_machine)
    return new_machine

async def get_machine(db: AsyncSession, machine_id: int):
    """Get a machine by ID"""
    result = await db.execute(select(Machine).where(Machine.id == machine_id))
    return result.scalar_one_or_none()

async def get_machines(db: AsyncSession, skip: int = 0, limit: int = 100):
    """Get all machines with pagination"""
    result = await db.execute(select(Machine).offset(skip).limit(limit))
    return result.scalars().all()

async def update_machine(db: AsyncSession, machine_id: int, machine_in: MachineUpdate):
    """Update a machine by ID"""
    result = await db.execute(select(Machine).where(Machine.id == machine_id))
    machine = result.scalar_one_or_none()
    
    if machine is None:
        return None
    
    # Update only the fields that are provided
    update_data = machine_in.dict(exclude_unset=True)
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