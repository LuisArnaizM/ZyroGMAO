from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import logging

from app.config import settings
from app.database.postgres import check_connection, create_tables
from app.database.data_seed import seed_database
from app.routers import (
    auth, users, organization, assets, sensors, 
    failures, maintenance, tasks, workorders, components, department
)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestiona el ciclo de vida de la aplicación.
    """
    # Startup
    logger.info("🚀 Iniciando aplicación...")
    
    # Verificar conexión a la base de datos
    if await check_connection():
        logger.info("✅ Conexión a base de datos establecida")
        
        try:
            # Crear tablas si no existen
            logger.info("📝 Verificando/creando tablas...")
            await create_tables()
            logger.info("✅ Tablas verificadas/creadas exitosamente")
            
            # Poblar con datos iniciales si es necesario
            logger.info("🌱 Verificando datos iniciales...")
            await seed_database()
            logger.info("✅ Datos iniciales verificados")
            
        except Exception as e:
            logger.warning(f"⚠️ Error durante la inicialización de datos: {e}")
            # No fallar el startup por esto, las tablas podrían ya existir
    else:
        logger.error("❌ No se pudo conectar a la base de datos")
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    logger.info("✅ Aplicación iniciada correctamente")
    
    yield
    
    # Shutdown
    logger.info("🛑 Cerrando aplicación...")

# Crear aplicación FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="API para gestión de mantenimiento industrial con IoT",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware de hosts confiables (deshabilitado en desarrollo)
# TODO: Habilitar en producción con configuración correcta
# if not settings.DEBUG and settings.BACKEND_CORS_ORIGINS:
#     allowed_hosts = []
#     for origin in settings.BACKEND_CORS_ORIGINS:
#         if "://" in origin:
#             host = origin.split("://")[1]
#             allowed_hosts.append(host)
#         else:
#             allowed_hosts.append(origin)
#     
#     app.add_middleware(
#         TrustedHostMiddleware,
#         allowed_hosts=allowed_hosts
#     )

# Incluir routers
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth")
app.include_router(users.router, prefix=f"{settings.API_V1_STR}/users")
app.include_router(organization.router, prefix=f"{settings.API_V1_STR}/organization")
app.include_router(assets.router, prefix=f"{settings.API_V1_STR}/assets")
app.include_router(components.router, prefix=f"{settings.API_V1_STR}/components")
app.include_router(department.router, prefix=f"{settings.API_V1_STR}/department")
app.include_router(sensors.router, prefix=f"{settings.API_V1_STR}/sensors")
app.include_router(failures.router, prefix=f"{settings.API_V1_STR}/failures")
app.include_router(maintenance.router, prefix=f"{settings.API_V1_STR}/maintenance")
app.include_router(tasks.router, prefix=f"{settings.API_V1_STR}/tasks")
app.include_router(workorders.router, prefix=f"{settings.API_V1_STR}/workorders")

@app.get("/")
async def root():
    """
    Endpoint raíz que proporciona información básica de la API.
    """
    return {
        "message": "Industrial Maintenance Management API",
        "version": settings.VERSION,
        "docs_url": "/docs",
        "health_check": "/health"
    }

@app.get("/health")
async def health_check():
    """
    Endpoint de verificación de salud de la aplicación.
    """
    db_status = await check_connection()
    
    return {
        "status": "healthy" if db_status else "unhealthy",
        "database": "connected" if db_status else "disconnected",
        "version": settings.VERSION
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )