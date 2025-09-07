from sqlalchemy import Column, Integer, Text, ForeignKey
from Backend.utils.database import Base

class Meta(Base):
    __tablename__ = "meta"
    id = Column(Integer, primary_key=True, index=True)
    id_sector = Column(Integer, ForeignKey("sector.id"), nullable=False)
    numero_meta = Column(Integer, nullable=False)
    nombre_meta = Column(Text, nullable=False)
