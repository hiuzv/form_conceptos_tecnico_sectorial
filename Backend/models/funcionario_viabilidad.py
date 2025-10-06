from sqlalchemy import Column, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship, backref
from Backend.utils.database import Base

class FuncionarioViabilidad(Base):
    __tablename__ = "funcionario_viabilidad"

    id = Column(Integer, primary_key=True)
    nombre = Column(Text, nullable=False)
    cargo  = Column(Text, nullable=False)

    id_tipo_viabilidad = Column(Integer,ForeignKey("tipo_viabilidad.id", ondelete="RESTRICT"),nullable=False,)
    id_formulario = Column(Integer,ForeignKey("formulario.id", ondelete="CASCADE"),nullable=False,)

    tipo = relationship("TipoViabilidad")
    formulario = relationship("Formulario",backref=backref("funcionarios_viabilidad", cascade="all, delete-orphan"),)

    def __repr__(self) -> str:
        return f"<FuncionarioViabilidad form={self.id_formulario} tipo={self.id_tipo_viabilidad} nombre={self.nombre!r}>"
