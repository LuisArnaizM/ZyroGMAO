import os
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from dotenv import load_dotenv
from typing import Tuple
from app.config import settings

load_dotenv()



def create_token(data: dict, expires_delta: Optional[timedelta] = None) -> Tuple[str, datetime]:
    """
    Crea un token JWT con los datos proporcionados y la fecha de expiración.
    Devuelve el token y la fecha de expiración.
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    
    return encoded_jwt, expire

def decode_token(token: str) -> dict:
    """
    Decodifica un token JWT y devuelve los datos contenidos.
    Lanza JWTError si el token es inválido.
    """
    return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])

def create_access_token(data: dict) -> Tuple[str, datetime]:
    """
    Crea un token de acceso con los datos proporcionados.
    """
    return create_token(
        data=data,
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
    )

def create_refresh_token(data: dict) -> Tuple[str, datetime]:
    """
    Crea un token de actualización con los datos proporcionados.
    """
    return create_token(
        data=data,
        expires_delta=timedelta(days=settings.refresh_token_expire_days)
    )