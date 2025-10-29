from sqlalchemy import Column, Integer, ForeignKey, Text
from Backend.utils.database import Base

class VariablesSectorial(Base):
    __tablename__ = "variables_sectorial"
    id = Column(Integer, primary_key=True, index=True)
    id_variable_sectorial = Column(Integer, ForeignKey("variable_sectorial.id"), nullable=False)
    id_formulario = Column(Integer, ForeignKey("formulario.id", ondelete="CASCADE"), nullable=False)
    respuesta = Column(Text, nullable=False)

    def __repr__(self):
        return f"<VariablesSectorial form={self.id_formulario} var={self.id_variable_sectorial} resp={self.respuesta}>"
