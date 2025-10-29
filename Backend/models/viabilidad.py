from sqlalchemy import Column, Integer, Text, Boolean
from Backend.utils.database import Base

class Viabilidad(Base):
    __tablename__ = "viabilidad"

    id = Column(Integer, primary_key=True)
    nombre = Column(Text, nullable=False)
    no_aplica = Column(Boolean, nullable=False, default=False)

    def __repr__(self):
        return f"<Viabilidad id={self.id} no_aplica={self.no_aplica}>"
