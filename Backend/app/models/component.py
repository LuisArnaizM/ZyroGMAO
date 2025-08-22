from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.postgres import Base
from sqlalchemy import String
from app.models.enums import ComponentStatus

class Component(Base):
    __tablename__ = "components"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text)
    component_type = Column(String(50), nullable=False)  # motor, bomba, válvula, etc.
    model = Column(String(100))
    serial_number = Column(String(100), unique=True, index=True)
    location = Column(String(200))
    # Persist status as plain string to avoid strict Enum mapping errors with legacy DB values
    status = Column(String(50), default=ComponentStatus.ACTIVE.value, nullable=False)

    # Fechas
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    installed_date = Column(DateTime(timezone=True))
    warranty_expiry = Column(DateTime(timezone=True))
    
    # Información adicional
    purchase_cost = Column(Float)
    current_value = Column(Float)
    maintenance_interval_days = Column(Integer)  # Intervalo de mantenimiento en días
    last_maintenance_date = Column(DateTime(timezone=True))
    
    # Jerarquía - relación con Asset padre
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False, index=True)
    
    # Responsable del componente
    responsible_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    # Relaciones
    asset = relationship("Asset", back_populates="components")
    responsible = relationship("User", back_populates="responsible_components")
    
    # Relaciones con otros modelos que antes dependían de Machine
    sensors = relationship("Sensor", back_populates="component", cascade="all, delete-orphan")
    sensor_data = relationship("SensorData", back_populates="component")
    failures = relationship("Failure", back_populates="component")
    maintenance_records = relationship("Maintenance", back_populates="component")
    tasks = relationship("Task", back_populates="component")
    # Inventario y usos en tareas
    inventory_item = relationship("InventoryItem", uselist=False, back_populates="component")
    used_in_tasks = relationship("TaskUsedComponent", back_populates="component")
    maintenance_plans = relationship("MaintenancePlan", back_populates="component", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Component(id={self.id}, name='{self.name}', type='{self.component_type}')>"
