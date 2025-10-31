from sqlalchemy import Column, Integer, Text, ForeignKey
from Backend.utils.database import Base

class Meta(Base):
    __tablename__ = "meta"
    id = Column(Integer, primary_key=True, index=True)
    id_programa = Column(Integer, ForeignKey("programa.id"), nullable=False)
    numero_meta = Column(Integer, nullable=False)
    nombre_meta = Column(Text, nullable=False)
    codigo_producto = Column(Integer, nullable=False)
    nombre_producto = Column(Text, nullable=False)
    codigo_indicador_producto = Column(Integer, nullable=False)
    nombre_indicador_producto = Column(Text, nullable=False)
