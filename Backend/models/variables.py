from sqlalchemy import Column, Integer, ForeignKey
from Backend.utils.database import Base

class Variables(Base):
    __tablename__ = "variables"
    id = Column(Integer, primary_key=True, index=True)
    id_variable = Column(Integer, ForeignKey("variable.id"), nullable=False)
    id_formulario = Column(Integer, ForeignKey("formulario.id", ondelete="CASCADE"), nullable=False)
