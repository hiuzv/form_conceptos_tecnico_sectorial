from sqlalchemy import Column, Integer, ForeignKey
from Backend.utils.database import Base

class VariablesTecnico(Base):
    __tablename__ = "variables_tecnico"
    id = Column(Integer, primary_key=True, index=True)
    id_variable_tecnico = Column(Integer, ForeignKey("variable_tecnico.id"), nullable=False)
    id_formulario = Column(Integer, ForeignKey("formulario.id", ondelete="CASCADE"), nullable=False)
