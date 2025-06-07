import os
from datetime import datetime, timedelta
from typing import Optional, Tuple
from jose import JWTError, jwt
from passlib.context import CryptContext
from dotenv import load_dotenv
from app.config import settings

load_dotenv()

# Configurar el contexto de encriptación de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica que una contraseña en texto plano coincida con su hash.
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    Genera un hash de la contraseña proporcionada.
    """
    return pwd_context.hash(password)

def create_token(data: dict, expires_delta: Optional[timedelta] = None) -> Tuple[str, datetime]:
    """
    Crea un token JWT con los datos proporcionados y la fecha de expiración.
    Devuelve el token y la fecha de expiración.
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    return encoded_jwt, expire

def decode_token(token: str) -> dict:
    """
    Decodifica un token JWT y devuelve los datos contenidos.
    Lanza JWTError si el token es inválido.
    """
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

def create_access_token(data: dict) -> Tuple[str, datetime]:
    """
    Crea un token de acceso con los datos proporcionados.
    """
    return create_token(
        data=data,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

def create_refresh_token(data: dict) -> Tuple[str, datetime]:
    """
    Crea un token de actualización con los datos proporcionados.
    """
    return create_token(
        data=data,
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )

def authenticate_user(username: str, password: str, hashed_password: str) -> bool:
    """
    Autentica un usuario verificando su contraseña.
    """
    return verify_password(password, hashed_password)