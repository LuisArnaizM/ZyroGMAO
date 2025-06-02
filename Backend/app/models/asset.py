from sqlalchemy import Column, Integer, String, ForeignKey
from app.database.postgres import Base

class Asset(Base):
    __tablename__ = "assets"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    location = Column(String)
    responsible_id = Column(Integer, ForeignKey("users.id"))
