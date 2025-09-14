from sqlalchemy import Column, Integer, Text, ForeignKey
from Backend.utils.database import Base

class VariableTecnico(Base):
    __tablename__ = "variable_tecnico"
    id = Column(Integer, primary_key=True, index=True)
    nombre_variable = Column(Text, nullable=False)
