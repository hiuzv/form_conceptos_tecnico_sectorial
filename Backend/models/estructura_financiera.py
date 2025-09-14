from sqlalchemy import Column, Integer, Text, Numeric, ForeignKey
from Backend.utils.database import Base

class EstructuraFinanciera(Base):
    __tablename__ = "estructura_financiera"
    id = Column(Integer, primary_key=True, index=True)
    id_formulario = Column(Integer, ForeignKey("formulario.id", ondelete="CASCADE"), nullable=False)
    anio = Column(Integer, nullable=True)
    entidad = Column(Text, nullable=False)
    valor = Column(Numeric(18, 2), nullable=False)
