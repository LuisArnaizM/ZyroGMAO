from pydantic import BaseModel, Field
from datetime import datetime
from typing import Any

class SensorDataIn(BaseModel):
    asset_id: int
    sensor_type: str
    value: Any
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class SensorDataOut(SensorDataIn):
    id: int

class SensorUpdate(BaseModel):
    sensor_type: str
    value: Any
    timestamp: datetime = Field(default_factory=datetime.utcnow)