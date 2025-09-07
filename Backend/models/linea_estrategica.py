from sqlalchemy import Column, Integer, Text
from Backend.utils.database import Base

class LineaEstrategica(Base):
    __tablename__ = "linea_estrategica"
    id = Column(Integer, primary_key=True, index=True)
    nombre_linea_estrategica = Column(Text, nullable=False)
