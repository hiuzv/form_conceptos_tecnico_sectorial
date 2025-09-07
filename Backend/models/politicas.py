from sqlalchemy import Column, Integer, ForeignKey, Numeric
from Backend.utils.database import Base

class Politicas(Base):
    __tablename__ = "politicas"
    id = Column(Integer, primary_key=True, index=True)
    id_politica = Column(Integer, ForeignKey("politica.id"), nullable=False)
    id_formulario = Column(Integer, ForeignKey("formulario.id", ondelete="CASCADE"), nullable=False)
    valor_destinado = Column(Numeric(18, 2), nullable=True)
