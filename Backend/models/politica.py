from sqlalchemy import Column, Integer, Text
from Backend.utils.database import Base

class Politica(Base):
    __tablename__ = "politica"
    id = Column(Integer, primary_key=True, index=True)
    nombre_politica = Column(Text, nullable=False)
