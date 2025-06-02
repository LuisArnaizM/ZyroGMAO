from sqlalchemy import Column, String, Integer, Enum as SqlEnum
from sqlalchemy.ext.declarative import declarative_base
import enum

Base = declarative_base()

class UserRole(str, enum.Enum):
    admin = "Admin"
    supervisor = "Supervisor"
    tecnico = "Tecnico"
    consultor = "Consultor"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(SqlEnum(UserRole), default=UserRole.tecnico)
