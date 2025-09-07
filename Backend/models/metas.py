from sqlalchemy import Column, Integer, ForeignKey
from Backend.utils.database import Base

class Metas(Base):
    __tablename__ = "metas"
    id = Column(Integer, primary_key=True, index=True)
    id_meta = Column(Integer, ForeignKey("meta.id"), nullable=False)
    id_formulario = Column(Integer, ForeignKey("formulario.id", ondelete="CASCADE"), nullable=False)
