from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
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

@router.get("/check-db")
async def check_database(db: AsyncSession = Depends(get_db)):
    """Comprueba si la base de datos tiene usuarios"""
    try:
        result = await db.execute(select(func.count()).select_from(User))
        user_count = result.scalar_one()
        
        if user_count == 0:
            return {
                "status": "warning",
                "message": "La base de datos existe pero no hay usuarios. Ejecuta el script de inicialización."
            }
        
        return {
            "status": "ok",
            "message": f"La base de datos contiene {user_count} usuarios.",
            "sample_user": "admin@example.com con contraseña admin123 (si usaste los datos de ejemplo)"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error al conectar con la base de datos: {str(e)}",
            "solution": "Verifica que la base de datos PostgreSQL está en ejecución y que las credenciales son correctas."
        }