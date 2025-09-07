from sqlalchemy import Column, Integer, Text, ForeignKey
from Backend.utils.database import Base

class Categoria(Base):
    __tablename__ = "categoria"
    id = Column(Integer, primary_key=True, index=True)
    id_politica = Column(Integer, ForeignKey("politica.id"), nullable=False)
    nombre_categoria = Column(Text, nullable=False)
