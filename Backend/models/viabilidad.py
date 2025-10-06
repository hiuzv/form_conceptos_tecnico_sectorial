from sqlalchemy import Column, Integer, Text
from Backend.utils.database import Base

class Viabilidad(Base):
    __tablename__ = "viabilidad"

    id = Column(Integer, primary_key=True)
    nombre = Column(Text, nullable=False)

    def __repr__(self) -> str:
        return f"<Viabilidad id={self.id} nombre={self.nombre!r}>"
