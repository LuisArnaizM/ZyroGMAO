from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, or_
from passlib.context import CryptContext

from app.database.postgres import get_db
from app.models.user import User
from app.schemas.user import (
    UserCreate, UserRead, UserProfile, ChangePasswordRequest,
    ForgotPasswordRequest, ResetPasswordRequest, RefreshTokenRequest
)
from app.auth.dependencies import get_current_user, logout_token, oauth2_scheme
from app.auth.auth import (
    login_for_access_token, refresh_access_token, change_password,
    forgot_password, reset_password
)

router = APIRouter(tags=["Auth"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: AsyncSession = Depends(get_db)
):
    """Login con username o email"""
    return await login_for_access_token(form_data, db)

@router.post("/logout")
async def logout(token: str = Depends(oauth2_scheme)):
    """Cerrar sesión invalidando el token"""
    logout_token(token)
    return {"message": "Successfully logged out"}

@router.post("/refresh")
async def refresh_token(
    refresh_request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """Obtener nuevo access token usando refresh token"""
    return await refresh_access_token(refresh_request.refresh_token, db)

@router.post("/register", response_model=UserRead)
async def register_user(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    """Registrar nuevo usuario"""
    # Verificar si username o email ya existen
    result = await db.execute(
        select(User).where(
            or_(User.email == user_in.email, User.username == user_in.username)
        )
    )
    existing_user = result.scalar_one_or_none()

    if existing_user:
        if existing_user.email == user_in.email:
            raise HTTPException(status_code=400, detail="Email already registered")
        else:
            raise HTTPException(status_code=400, detail="Username already taken")

    new_user = User(
        username=user_in.username,
        first_name=user_in.first_name,
        last_name=user_in.last_name,
        email=user_in.email,
        hashed_password=pwd_context.hash(user_in.password),
        role=user_in.role,
        is_active=1
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

@router.get("/me", response_model=UserProfile)
async def get_me(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Obtener información completa del usuario actual"""
    result = await db.execute(select(User).where(User.id == user["id"]))
    db_user = result.scalar_one_or_none()
    
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserProfile.from_user(db_user)

@router.put("/change-password")
async def change_user_password(
    change_request: ChangePasswordRequest,
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Cambiar contraseña del usuario actual"""
    return await change_password(user["id"], change_request, db)

@router.post("/forgot-password")
async def forgot_user_password(
    forgot_request: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db)
):
    """Solicitar reset de contraseña"""
    return await forgot_password(forgot_request.email, db)

@router.post("/reset-password")
async def reset_user_password(
    reset_request: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db)
):
    """Resetear contraseña con token"""
    return await reset_password(reset_request, db)

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
        
        # Obtener un usuario de ejemplo
        result = await db.execute(select(User).where(User.username == "admin"))
        admin_user = result.scalar_one_or_none()
        
        sample_info = "admin con contraseña admin (si usaste los datos de ejemplo)" if admin_user else "No hay usuario admin de ejemplo"
        
        return {
            "status": "ok",
            "message": f"La base de datos contiene {user_count} usuarios.",
            "sample_user": sample_info
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error al conectar con la base de datos: {str(e)}",
            "solution": "Verifica que la base de datos PostgreSQL está en ejecución y que las credenciales son correctas."
        }