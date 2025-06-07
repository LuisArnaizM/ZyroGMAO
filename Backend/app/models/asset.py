from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.postgres import Base

class Asset(Base):
    __tablename__ = "assets"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text)
    asset_type = Column(String(50), nullable=False)
    model = Column(String(100))
    serial_number = Column(String(100), unique=True, index=True)
    location = Column(String(200))
    status = Column(String(50), default="operational")
    
    # Fechas
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    purchase_date = Column(DateTime(timezone=True))
    warranty_expiry = Column(DateTime(timezone=True))
    
    # Información adicional
    purchase_cost = Column(Float)
    current_value = Column(Float)
    responsible_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relaciones
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    organization = relationship("Organization", back_populates="assets")
    
    # Usuario responsable
    responsible = relationship("User", back_populates="responsible_assets")
    
    # Componentes hijos - Esta es la nueva estructura jerárquica
    components = relationship("Component", back_populates="asset", cascade="all, delete-orphan")
    
    # Otras relaciones mantenidas para el asset principal
    sensors = relationship("Sensor", back_populates="asset", cascade="all, delete-orphan")
    sensor_data = relationship("SensorData", back_populates="asset")
    failures = relationship("Failure", back_populates="asset")
    maintenance_records = relationship("Maintenance", back_populates="asset")
    workorders = relationship("WorkOrder", back_populates="asset")
    tasks = relationship("Task", back_populates="asset")