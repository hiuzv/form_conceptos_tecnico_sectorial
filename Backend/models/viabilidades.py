from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint, Text
from sqlalchemy.orm import relationship, backref
from Backend.utils.database import Base

class Viabilidades(Base):
    __tablename__ = "viabilidades"

    id = Column(Integer, primary_key=True)
    id_viabilidad = Column(Integer,ForeignKey("viabilidad.id", ondelete="CASCADE"),nullable=False,)
    id_formulario = Column(Integer,ForeignKey("formulario.id", ondelete="CASCADE"),nullable=False,)
    respuesta = Column(Text, nullable=False)

    __table_args__ = (UniqueConstraint("id_formulario", "id_viabilidad", name="ux_viab_form_viab"),)

    viabilidad = relationship("Viabilidad")
    formulario = relationship("Formulario",backref=backref("viabilidades_rel", cascade="all, delete-orphan"),)

    def __repr__(self) -> str:
        return f"<Viabilidades form={self.id_formulario} viab={self.id_viabilidad}>"
