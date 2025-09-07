from sqlalchemy import Column, Integer, Text, ForeignKey
from Backend.utils.database import Base

class Subcategoria(Base):
    __tablename__ = "subcategoria"
    id = Column(Integer, primary_key=True, index=True)
    id_categoria = Column(Integer, ForeignKey("categoria.id"), nullable=False)
    nombre_subcategoria = Column(Text, nullable=False)
