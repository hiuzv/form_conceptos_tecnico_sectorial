from sqlalchemy import Column, Integer, ForeignKey
from Backend.utils.database import Base

class VariablesSectorial(Base):
    __tablename__ = "variables_sectorial"
    id = Column(Integer, primary_key=True, index=True)
    id_variable_sectorial = Column(Integer, ForeignKey("variable_sectorial.id"), nullable=False)
    id_formulario = Column(Integer, ForeignKey("formulario.id", ondelete="CASCADE"), nullable=False)
