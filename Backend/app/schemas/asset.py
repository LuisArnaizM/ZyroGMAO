from pydantic import BaseModel

class AssetCreate(BaseModel):
    name: str
    location: str
    responsible_id: int

class AssetRead(AssetCreate):
    id: int

class AssetUpdate(BaseModel):
    name: str = None
    location: str = None
    responsible_id: int = None