from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.postgres import Base

class Sensor(Base):
    __tablename__ = "sensors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    sensor_type = Column(String(50), nullable=False)  # temperature, pressure, vibration, etc.
    description = Column(Text)
    unit = Column(String(20))  # °C, bar, mm/s, etc.
    min_value = Column(Float)
    max_value = Column(Float)
    warning_threshold = Column(Float)
    critical_threshold = Column(Float)
    location = Column(String(100))
    status = Column(String(50), default="active")  # active, inactive, maintenance, error
    last_reading = Column(Float)
    last_reading_time = Column(DateTime)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Foreign Keys - Sensor puede estar en un Asset o en un Component específico
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=True)
    component_id = Column(Integer, ForeignKey("components.id"), nullable=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    
    # Relationships
    asset = relationship("Asset", back_populates="sensors")
    component = relationship("Component", back_populates="sensors")
    organization = relationship("Organization", back_populates="sensors")
    sensor_data = relationship("SensorData", back_populates="sensor")