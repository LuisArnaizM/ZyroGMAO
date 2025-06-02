from pydantic import BaseModel, Field
from datetime import datetime
from typing import Any

class Sensor(BaseModel):
    asset_id: int
    sensor_type: str
    value: Any
    timestamp: datetime = Field(default_factory=datetime.utcnow)
