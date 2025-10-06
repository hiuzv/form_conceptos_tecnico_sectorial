from sqlalchemy import Column, Integer, Text, ForeignKey
from Backend.utils.database import Base

class Formulario(Base):
    __tablename__ = "formulario"
    id = Column(Integer, primary_key=True, index=True)
    nombre_proyecto = Column(Text, nullable=False)
    cod_id_mga = Column(Integer, nullable=False)
    id_dependencia = Column(Integer, ForeignKey("dependencia.id"), nullable=True)
    id_linea_estrategica = Column(Integer, ForeignKey("linea_estrategica.id"), nullable=True)
    id_programa = Column(Integer, ForeignKey("programa.id"), nullable=True)
    id_sector = Column(Integer, ForeignKey("sector.id"), nullable=True)
    nombre_secretario = Column(Text, nullable=True)
    oficina_secretario = Column(Text, nullable=True)
    duracion_proyecto = Column(Integer, nullable=True)
    cantidad_beneficiarios = Column(Integer, nullable=True)
