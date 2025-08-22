from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_
from sqlalchemy.orm import selectinload
from app.models.user import User
from app.schemas.user import UserCreate, UserRead, UserUpdate
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def create_user(db: AsyncSession, user_in: UserCreate):
    """Create a new user"""
    # Check if user already exists (username or email)
    result = await db.execute(
        select(User).where(
            or_(User.email == user_in.email, User.username == user_in.username)
        )
    )
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        return None
    
    new_user = User(
        username=user_in.username,
        first_name=user_in.first_name,
        last_name=user_in.last_name,
        email=user_in.email,
        hashed_password=pwd_context.hash(user_in.password),
        role=user_in.role,
        department_id=user_in.department_id,
        is_active=1  # Activo por defecto
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

async def get_user(db: AsyncSession, user_id: int):
    """Get a user by ID"""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()
async def get_user_by_email(db: AsyncSession, email: str):
    """Get a user by email"""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()

async def get_user_by_username(db: AsyncSession, username: str):
    """Get a user by username"""
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()

async def get_user_by_login(db: AsyncSession, login: str):
    """Get a user by username or email"""
    result = await db.execute(
        select(User).where(
            or_(User.email == login, User.username == login)
        )
    )
    return result.scalar_one_or_none()

async def get_users(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    search: str = None,
    role: str | None = None,
    is_active: bool | None = None,
):
    """
    Get all users with pagination and search capability
    
    Parameters:
    - db: Database session
    - page: Page number (starts from 1)
    - page_size: Number of records per page
    - search: Search string to filter users by email, username, first_name, last_name or role
    """
    # Calculate offset based on page and page_size
    offset = (page - 1) * page_size
    
    # Build the base query
    query = select(User)
    
    # Apply search filter if provided
    if search:
        search_term = f"%{search}%"
        query = query.where(
            (User.email.ilike(search_term)) | 
            (User.username.ilike(search_term)) |
            (User.first_name.ilike(search_term)) |
            (User.last_name.ilike(search_term)) |
            (User.role.ilike(search_term))
        )
    # Apply role filter if provided
    if role:
        query = query.where(User.role == role)
    # Apply is_active filter if provided (0/1)
    if is_active is not None:
        query = query.where(User.is_active.is_(bool(is_active)))
    
    # Apply pagination
    query = query.offset(offset).limit(page_size)
    
    # Execute query
    result = await db.execute(query)
    return result.scalars().all()

async def update_user(db: AsyncSession, user_id: int, user_in: UserUpdate):
    """Update a user by ID"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if user is None:
        return None
    
    # Update fields using model_dump to handle optional fields
    update_data = user_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(user, key, value)
    
    await db.commit()
    await db.refresh(user)
    return user

async def update_password(db: AsyncSession, user_id: int, new_password: str):
    """Update user's password"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if user is None:
        return None
    
    user.hashed_password = pwd_context.hash(new_password)
    await db.commit()
    await db.refresh(user)
    return user

async def deactivate_user(db: AsyncSession, user_id: int):
    """Deactivate a user (soft delete)"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if user is None:
        return None
    
    user.is_active = 0
    await db.commit()
    await db.refresh(user)
    return user

async def activate_user(db: AsyncSession, user_id: int):
    """Activate a user"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if user is None:
        return None
    
    user.is_active = 1
    await db.commit()
    await db.refresh(user)
    return user

async def delete_user(db: AsyncSession, user_id: int):
    """Delete a user by ID (hard delete)"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if user is None:
        return False
    
    await db.delete(user)
    await db.commit()
    return True