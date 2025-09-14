from sqlalchemy import Column, Integer, Text, ForeignKey
from Backend.utils.database import Base

class VariableSectorial(Base):
    __tablename__ = "variable_sectorial"
    id = Column(Integer, primary_key=True, index=True)
    nombre_variable = Column(Text, nullable=False)
