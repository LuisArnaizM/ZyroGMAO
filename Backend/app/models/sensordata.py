from datetime import datetime
from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from typing import Optional
from app.database.postgres import Base

class SensorData(Base):
    __tablename__ = "sensor_data"
    
    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(Integer, ForeignKey("sensors.id"), nullable=False, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=True, index=True)  # Opcional
    component_id = Column(Integer, ForeignKey("components.id"), nullable=True, index=True)  # Opcional  
    value = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relaciones
    sensor = relationship("Sensor", back_populates="sensor_data")
    asset = relationship("Asset", back_populates="sensor_data")
    component = relationship("Component", back_populates="sensor_data")