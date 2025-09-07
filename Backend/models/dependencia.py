from sqlalchemy import Column, Integer, Text
from Backend.utils.database import Base

class Dependencia(Base):
    __tablename__ = "dependencia"
    id = Column(Integer, primary_key=True, index=True)
    nombre_dependencia = Column(Text, nullable=False)
