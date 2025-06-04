from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, assets, failures, machines, maintenance, sensors, tasks, users, workorders
from app.config import settings
import asyncio
import logging
from app.database.data_seed import db_is_empty, init_db
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestor de ciclo de vida de la aplicación.
    Se ejecuta al arrancar y detener la aplicación.
    """
    # Código que se ejecuta al iniciar la aplicación
    logging.info("🚀 Iniciando aplicación GMAO...")
    
    try:
        # Verificar si la base de datos está vacía
        is_empty = db_is_empty()
        
        if is_empty:
            logging.info("💾 La base de datos está vacía. Inicializando...")
            # Inicializar PostgreSQL de forma síncrona
            init_db()
            logging.info("✅ Base de datos inicializada correctamente")
        else:
            logging.info("✅ Base de datos ya contiene datos. No es necesario inicializar.")
    except Exception as e:
        logging.error(f"❌ Error verificando/inicializando la base de datos: {e}")
    
    yield  # Aquí la aplicación está en ejecución
    
    # Código que se ejecuta al detener la aplicación
    logging.info("👋 Cerrando aplicación GMAO...")

# Crear aplicación FastAPI con metadatos desde la configuración
app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan,
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(auth.router)
app.include_router(assets.router)
app.include_router(failures.router)
app.include_router(machines.router)
app.include_router(maintenance.router)
app.include_router(sensors.router)
app.include_router(tasks.router)
app.include_router(users.router)
app.include_router(workorders.router)
