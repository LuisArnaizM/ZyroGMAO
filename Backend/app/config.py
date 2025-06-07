import os
from typing import List, Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Información del proyecto - Agregar las variables que faltan
    PROJECT_NAME: str = "Industrial Maintenance Management API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Variables adicionales del .env que estaban faltando
    APP_NAME: str = "GMAO System"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "Sistema GMAO para mantenimiento industrial"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Base de datos
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "gmao")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    
    # Agregar POSTGRES_URL que está en tu .env
    POSTGRES_URL: Optional[str] = None
    
    # MongoDB para datos de sensores
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    MONGODB_DB: str = os.getenv("MONGODB_DB", "sensor_data")
    
    # Seguridad
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-super-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS - Agregar la variable que falta
    CORS_ORIGINS: str = '["http://localhost:3000", "http://localhost:8080", "http://localhost:8000"]'
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080", "http://localhost:8000"]
    
    # Email (para futuras implementaciones)
    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = None
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    
    @property
    def database_url(self) -> str:
        # Usar POSTGRES_URL si está definida, sino construir la URL
        if self.POSTGRES_URL:
            return self.POSTGRES_URL
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    @property
    def mongodb_url(self):
        return self.MONGODB_URL
    
    @property
    def mongodb_db(self):
        return self.MONGODB_DB
    
    @property
    def access_token_expire_minutes(self) -> int:
        return self.ACCESS_TOKEN_EXPIRE_MINUTES
    
    @property
    def refresh_token_expire_days(self) -> int:
        return self.REFRESH_TOKEN_EXPIRE_DAYS
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        # Permitir variables extra para mayor flexibilidad
        extra = "ignore"

settings = Settings()

# Función helper para mantener compatibilidad
def get_database_url() -> str:
    return settings.database_url