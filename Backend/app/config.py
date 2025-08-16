import os
from typing import List, Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Información del proyecto - Agregar las variables que faltan
    PROJECT_NAME: str = "Industrial Maintenance Management API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/v1"
    
    # Variables adicionales del .env que estaban faltando
    APP_NAME: str = "GMAO System"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "Sistema GMAO para mantenimiento industrial"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Base de datos
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "db")  # Cambiado de localhost a db
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "gmao")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    
    # URLs para Docker y local
    POSTGRES_URL: Optional[str] = None
    POSTGRES_URL_DOCKER: Optional[str] = None
    
    # MongoDB para datos de sensores
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://mongo:27017")  # Cambiado de localhost a mongo
    MONGODB_URL_DOCKER: str = os.getenv("MONGODB_URL_DOCKER", "mongodb://mongo:27017")
    MONGODB_DB: str = os.getenv("MONGODB_DB", "gmao_sensors")
    
    # Seguridad
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-super-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS - Configuración mejorada para desarrollo
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", '["http://localhost:3000", "http://localhost:3001", "http://localhost:3002", "http://localhost:8080", "http://localhost:8000"]')
    
    # Lista de orígenes permitidos - construida dinámicamente
    @property
    def cors_origins_list(self) -> List[str]:
        """Convierte la string de CORS_ORIGINS a lista"""
        import json
        try:
            return json.loads(self.CORS_ORIGINS)
        except:
            # Fallback con orígenes de desarrollo comunes
            return [
                "http://localhost:3000",
                "http://localhost:3001", 
                "http://localhost:3002",
                "http://localhost:8080",
                "http://localhost:8000",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:3001",
                "http://127.0.0.1:3002"
            ]
    
    BACKEND_CORS_ORIGINS: List[str] = []  # Se inicializa en __post_init__
    
    # Email (para futuras implementaciones)
    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = None
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    
    def model_post_init(self, __context) -> None:
        """Inicializa BACKEND_CORS_ORIGINS después de la creación del objeto"""
        self.BACKEND_CORS_ORIGINS = self.cors_origins_list
    
    @property
    def database_url(self) -> str:
        # Priorizar POSTGRES_URL_DOCKER si está definida (para Docker)
        if self.POSTGRES_URL_DOCKER:
            return self.POSTGRES_URL_DOCKER
        # Usar POSTGRES_URL si está definida
        elif self.POSTGRES_URL:
            return self.POSTGRES_URL
        # Sino construir la URL usando POSTGRES_SERVER (que será 'db' en Docker)
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    @property
    def mongodb_url(self):
        # Usar MONGODB_URL_DOCKER si está disponible, sino usar MONGODB_URL
        if self.MONGODB_URL_DOCKER:
            return self.MONGODB_URL_DOCKER
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