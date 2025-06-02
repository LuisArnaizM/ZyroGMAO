from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, assets, failures, machines, maintenance, sensors, tasks, users, workorders
from app.config import settings
import asyncio
import logging
from app.database.data_seed import db_is_empty, init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Código que se ejecuta al iniciar
    try:
        # Verificar si la base de datos está vacía usando run_in_executor para Python 3.8
        loop = asyncio.get_event_loop()
        is_empty = await loop.run_in_executor(None, db_is_empty)
        
        if is_empty:
            logging.info("Base de datos vacía, inicializando...")
            await loop.run_in_executor(None, init_db)
            logging.info("✅ Base de datos inicializada correctamente")
        else:
            logging.info("La base de datos ya contiene datos, omitiendo inicialización")
    except Exception as e:
        logging.error(f"❌ Error verificando/inicializando la base de datos: {e}")
    
    yield  # Aquí la aplicación se está ejecutando
    
    # Código que se ejecuta al cerrar
    logging.info("Cerrando la aplicación...")

# Pasar el gestor de lifespan al crear la app
app = FastAPI(title="GMAO API", lifespan=lifespan)

# Crear aplicación FastAPI con metadatos desde la configuración
app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
    debug=settings.debug
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
