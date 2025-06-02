from pydantic_settings import BaseSettings
from typing import List, Optional
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

class Settings(BaseSettings):
    # Información de la aplicación
    app_name: str = "GMAO System"
    app_version: str = "1.0.0"
    app_description: str = "Sistema GMAO para mantenimiento industrial"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Lista de orígenes permitidos para CORS
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    
    # Configuración de autenticación
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    
    # Configuración de bases de datos - Producción
    postgres_url: str
    mongodb_url: str
    mongodb_db: str
    
    # Configuración de bases de datos - Testing
    test_postgres_url: Optional[str] = None
    test_mongodb_url: Optional[str] = None
    test_mongodb_db: Optional[str] = None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        
        # Definir mapeos de nombres de variables de entorno
        field_aliases = {
            "debug": "APP_DEBUG",
            "host": "APP_HOST",
            "port": "APP_PORT",
            "cors_origins": "APP_CORS_ORIGINS"
        }

settings = Settings()