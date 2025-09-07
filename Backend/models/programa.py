from sqlalchemy import Column, Integer, Text, ForeignKey
from Backend.utils.database import Base

class Programa(Base):
    __tablename__ = "programa"
    id = Column(Integer, primary_key=True, index=True)
    id_linea_estrategica = Column(Integer, ForeignKey("linea_estrategica.id"), nullable=False)
    codigo_programa = Column(Integer, nullable=False)
    nombre_programa = Column(Text, nullable=False)
