from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from passlib.context import CryptContext

from app.database.postgres import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserRead
from app.auth.dependencies import get_current_user
from app.auth.auth import login_for_access_token

router = APIRouter(prefix="/auth", tags=["Auth"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    return await login_for_access_token(form_data, db)

@router.post("/register", response_model=UserRead)
async def register_user(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == user_in.email))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User(
        email=user_in.email,
        hashed_password=pwd_context.hash(user_in.password),
        role=user_in.role
    )
    db.add(new_user)
    await db.commit()
    return UserRead(email=new_user.email, role=new_user.role)

@router.get("/me", response_model=UserRead)
async def get_me(user=Depends(get_current_user)):
    return UserRead(email=user["email"], role=user["role"])