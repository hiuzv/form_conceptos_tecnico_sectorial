from sqlalchemy import Column, Integer, ForeignKey
from Backend.utils.database import Base

class Categorias(Base):
    __tablename__ = "categorias"
    id = Column(Integer, primary_key=True, index=True)
    id_categoria = Column(Integer, ForeignKey("categoria.id"), nullable=False)
    id_formulario = Column(Integer, ForeignKey("formulario.id", ondelete="CASCADE"), nullable=False)
