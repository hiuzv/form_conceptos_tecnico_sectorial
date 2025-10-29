from sqlalchemy import Column, Integer, Text, Boolean
from Backend.utils.database import Base

class VariableSectorial(Base):
    __tablename__ = "variable_sectorial"
    id = Column(Integer, primary_key=True, index=True)
    nombre_variable = Column(Text, nullable=False)
    no_aplica = Column(Boolean, nullable=False, default=False)

    def __repr__(self):
        return f"<VariableSectorial id={self.id} no_aplica={self.no_aplica}>"
