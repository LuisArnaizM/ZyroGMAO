# Make app.database a proper package and re-export common helpers
from .postgres import (
    Base,
    engine,
    AsyncSessionLocal,
    get_db,
    create_tables,
    drop_tables,
    apply_simple_migrations,
    check_connection,
)

__all__ = [
    "Base",
    "engine",
    "AsyncSessionLocal",
    "get_db",
    "create_tables",
    "drop_tables",
    "apply_simple_migrations",
    "check_connection",
]
