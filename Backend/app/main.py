from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, assets, failures, machines, maintenance, sensors, tasks, users, workorders
from app.config import settings

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

@app.get("/")
async def root():
    return {
        "message": f"Bienvenido a {settings.app_name} v{settings.app_version}",
        "docs": "/docs",
        "redoc": "/redoc"
    }