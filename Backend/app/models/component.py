from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.postgres import Base

class Component(Base):
    __tablename__ = "components"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text)
    component_type = Column(String(50), nullable=False)  # motor, bomba, válvula, etc.
    model = Column(String(100))
    serial_number = Column(String(100), unique=True, index=True)
    location = Column(String(200))  # Ubicación específica dentro del asset
    status = Column(String(50), default="operational")  # operational, maintenance, failed, etc.
    
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
    
    # Organización (heredada del asset, pero duplicada para facilitar consultas)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    
    # Relaciones
    asset = relationship("Asset", back_populates="components")
    responsible = relationship("User", back_populates="responsible_components")
    organization = relationship("Organization", back_populates="components")
    
    # Relaciones con otros modelos que antes dependían de Machine
    sensors = relationship("Sensor", back_populates="component", cascade="all, delete-orphan")
    sensor_data = relationship("SensorData", back_populates="component")
    failures = relationship("Failure", back_populates="component")
    maintenance_records = relationship("Maintenance", back_populates="component")
    tasks = relationship("Task", back_populates="component")
    
    def __repr__(self):
        return f"<Component(id={self.id}, name='{self.name}', type='{self.component_type}')>"
