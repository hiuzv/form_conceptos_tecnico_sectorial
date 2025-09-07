from sqlalchemy import Column, Integer, ForeignKey
from Backend.utils.database import Base

class Subcategorias(Base):
    __tablename__ = "subcategorias"
    id = Column(Integer, primary_key=True, index=True)
    id_subcategoria = Column(Integer, ForeignKey("subcategoria.id"), nullable=False)
    id_formulario = Column(Integer, ForeignKey("formulario.id", ondelete="CASCADE"), nullable=False)
