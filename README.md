# GMAO Zyro

Sistema integral de Gestión de Mantenimiento Asistido por Ordenador (GMAO / CMMS) orientado a la gestión de activos industriales, planificación preventiva/correctiva, trazabilidad de incidencias y soporte para analítica futura con datos IoT.

> Este repositorio contiene el **Backend (FastAPI + PostgreSQL)** y el **Frontend (Next.js + Ant Design + Tailwind)**. Está estructurado para servir como proyecto portfolio demostrando arquitectura full‑stack moderna.

## 🧱 Arquitectura General

```
┌────────────────────┐        ┌──────────────────────────┐
│  Frontend (Next.js)│ <----> │  API REST FastAPI        │
│  React 19 + AntD   │  HTTP  │  Auth JWT + Roles        │
└─────────▲──────────┘        │  Async SQLAlchemy        │
          │                   │  PostgreSQL              │
          │ (fetch/axios)     └─────────┬────────────────┘
          │                              │
          │                              │ (Futuro) Streams / ETL
          │                              ▼
          │                        MongoDB (IoT / Timeseries)
          │
          ▼
   Usuario Final
```

## 🚀 Características Clave

- Gestión de Activos, Componentes y Jerarquías
- Órdenes de Trabajo, Tareas y Mantenimientos
- Registro y seguimiento de Fallos
- Planes de Mantenimiento (preventivo / planificado)
- Calendario de técnicos (días laborales, especiales, vacaciones)
- Control de Inventario básico
- Autenticación JWT + Roles (Admin, Supervisor, Técnico, etc.)
- Script de generación de ERD (PlantUML / Mermaid / dbdiagram)
- Internacionalización inicial (frontend base en inglés)

## 📂 Estructura del Repositorio

```
Backend/
  app/
    auth/            # Seguridad, JWT y dependencias
    controllers/     # Lógica de negocio / servicios
    routers/         # Endpoints FastAPI
    models/          # Modelos SQLAlchemy
    schemas/         # Esquemas Pydantic
    database/        # Conexión y utilidades BD
  migrations/        # (Scripts/migraciones manuales)
  docker-compose.yml
  requirements.txt
  Scripts/generate_erd.py

Frontend/
  zyro-web/
    src/app/         # App Router (Next.js 15)
    public/          # Estáticos
    ...
```

## 🛠️ Tecnologías

| Capa      | Tecnologías |
|-----------|-------------|
| Frontend  | Next.js 15 (App Router), React 19, TypeScript, Ant Design 5, Tailwind 4, i18next |
| Backend   | FastAPI, SQLAlchemy Async, Pydantic, Uvicorn |
| Base Datos| PostgreSQL (principal), (Futuro: MongoDB para sensores) |
| Auth      | JWT (python-jose), passlib bcrypt |
| Infra     | Docker Compose (API + PostgreSQL) |
| Testing   | Pytest + HTTPX |

## 🔐 Roles Principales

| Rol        | Descripción breve |
|------------|-------------------|
| Admin      | Control total del sistema |
| Supervisor | Gestiona órdenes, equipos y planificación |
| Técnico    | Ejecuta tareas y registra mantenimientos |
| Consultor  | Solo lectura / reporting |

## ▶️ Puesta en Marcha Rápida

### 1. Clonar
```bash
git clone <url-del-repo>
cd TFM
```

### 2. Backend con Docker
Asegúrate de tener Docker instalado.

Crea un fichero `.env` dentro de `Backend/` (ejemplo mínimo):
```env
APP_PORT=8000
JWT_SECRET=changeme
JWT_ALGORITHM=HS256
POSTGRES_URL=postgresql+asyncpg://postgres:postgres@db:5432/gmao
```

Levanta servicios:
```bash
cd Backend
docker compose up -d --build
```
La API estará en: http://localhost:8000

Documentación interactiva:
- Swagger: http://localhost:8000/docs
- Redoc: http://localhost:8000/redoc

(Ejecución local sin Docker)
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 3. Frontend
En otra terminal:
```bash
cd Frontend/zyro-web
npm install
npm run dev
```
Abrir: http://localhost:3000

### 4. Credenciales Iniciales
Si tienes un script de seed (`init_database.py` o similar) ejecútalo tras levantar la API para crear usuarios de prueba.
```bash
python Backend/init_database.py  # (si procede)
```

## 🧪 Tests Backend
```bash
cd Backend
pytest -q
```

## 🗃️ Modelo de Datos (Resumen)

Jerarquía básica:
```
Organization → Asset → Component → Sensor
                         ↘ WorkOrder → Task / Maintenance
```

Incluye además: Failures, Inventario, Calendario laboral (user_working_days, user_special_days).

### ERD
Genera diagramas en `erd_output/`:
```bash
python Scripts/generate_erd.py
```
Formatos: PlantUML (`schema.puml`), Mermaid (`schema.mmd`), dbdiagram (`schema.dbdiagram`).

Reflexión directa contra BD (si está corriendo y quieres basarte en el esquema real):
```bash
python Scripts/generate_erd.py --reflect --url postgresql+asyncpg://postgres:postgres@localhost:5432/gmao
```

## 🌐 Internacionalización
El frontend tiene base en inglés y se irá extendiendo la traducción a todas las vistas. Se usa `react-i18next`.

## 📦 Scripts Útiles
| Script | Ubicación | Descripción |
|--------|-----------|-------------|
| `generate_erd.py` | `Backend/Scripts/` | Exporta diagrama ERD (PlantUML, Mermaid, dbdiagram) |
| `reset_db.py` | `Backend/` | Resetea base (si implementado) |
| `init_database.py` | `Backend/` | Población inicial (si procede) |

## 🧩 Decisiones de Diseño
- Separación clara `models` / `schemas` / `routers` / `controllers` para escalabilidad.
- SQLAlchemy Async para soportar más concurrencia.
- Preparado para añadir capa de métricas IoT (MongoDB) sin afectar dominio relacional.
- Generador de ERD para documentación continua.

## 🛡️ Seguridad
- Tokens JWT firmados (HS256).
- Hashing de contraseñas con bcrypt.
- Roles aplicados a endpoints sensibles.

## 📈 Próximas Mejoras (Roadmap)
- Completar traducción i18n en todas las páginas.
- Añadir dashboard de KPIs de mantenimiento.
- Integrar lectura de sensores reales y almacenamiento en MongoDB.
- Alertas y notificaciones (email / websockets).
- CI/CD (GitHub Actions) + despliegue en contenedores.
- Tests de integración ampliados.

## 🤝 Contribución
1. Haz fork
2. Crea rama: `feature/mi-feature`
3. Commit: `feat: descripción` (Convención Conventional Commits)
4. PR descriptivo con capturas / endpoints afectados

## 📄 Licencia
Pending (elige MIT / Apache 2.0 / GPL según tu preferencia).

## 👤 Autor
**Luis Arnaiz**  
Full‑stack Developer | Especializado en mantenimiento industrial digitalizado.

Si usas este proyecto en tu portfolio, puedes acompañarlo con capturas de: Planner, Calendario de Técnicos, Órdenes de Trabajo, y el ERD generado.

---
¿Quieres que genere también un README separado en `Backend/` y otro en `Frontend/` alineados con este? Pídelo y lo preparo.
