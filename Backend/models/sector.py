from sqlalchemy import Column, Integer, Text, ForeignKey
from Backend.utils.database import Base

class Sector(Base):
    __tablename__ = "sector"
    id = Column(Integer, primary_key=True, index=True)
    id_programa = Column(Integer, ForeignKey("programa.id"), nullable=False)
    codigo_sector = Column(Integer, nullable=False)
    nombre_sector = Column(Text, nullable=False)
