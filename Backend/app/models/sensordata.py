from datetime import datetime
from pydantic import BaseModel

class SensorData(BaseModel):
    sensor_id: int 
    asset_id: int  
    value: float
    timestamp: datetime