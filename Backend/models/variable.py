from sqlalchemy import Column, Integer, Text
from Backend.utils.database import Base

class Variable(Base):
    __tablename__ = "variable"
    id = Column(Integer, primary_key=True, index=True)
    nombre_variable = Column(Text, nullable=False)
