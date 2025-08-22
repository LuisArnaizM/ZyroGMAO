from typing import Any, Type
import enum


def normalize_enum_value(v: Any, enum_cls: Type[enum.Enum]) -> Any:
    """Normaliza valores legacy (strings o enums) a miembros del enum donde sea posible.

    - Si v es None lo devuelve.
    - Si v ya es miembro del enum lo devuelve tal cual.
    - Detecta variantes comunes como 'UNDER_MAINTENANCE' y las mapea a 'MAINTENANCE'
      si el enum tiene ese miembro.
    - Si no encuentra coincidencia devuelve el valor original para que Pydantic
      pueda fallar con un error de validación (o aceptarlo si coincide con el Enum).
    """
    if v is None:
        return v
    # Si ya es miembro del enum
    try:
        if isinstance(v, enum_cls):
            return v
    except Exception:
        pass

    sval = str(v).strip().upper()

    # Mapas legacy -- extensible
    legacy_map = {
        "UNDER_MAINTENANCE",
        "UNDER-MAINTENANCE",
        "UNDER MAINTENANCE",
        "UNDERMAINTENANCE",
        "IN_MAINTENANCE",
        "IN-MAINTENANCE",
    }

    if sval in legacy_map:
        # intentar devolver el miembro MAINTENANCE si existe
        for m in enum_cls:
            if m.name == "MAINTENANCE" or str(m.value).upper() == "MAINTENANCE":
                return m

    # Coincidir por name o value exacto
    for m in enum_cls:
        if sval == m.name or sval == str(m.value).upper():
            return m

    # No convertido: devolver el original para que Pydantic decida
    return v
