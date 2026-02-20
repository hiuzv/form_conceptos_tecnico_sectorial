from sqlalchemy import Column, Integer, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql import func
from Backend.utils.database import Base


class ObservacionEvaluacion(Base):
    __tablename__ = "observacion_evaluacion"

    id = Column(Integer, primary_key=True)
    id_formulario = Column(Integer, ForeignKey("formulario.id", ondelete="CASCADE"), nullable=False, index=True)
    tipo_documento = Column(Text, nullable=False)  # OBSERVACIONES | VIABILIDAD | VIABILIDAD_AJUSTADA
    contenido_html = Column(Text, nullable=False)
    nombre_evaluador = Column(Text, nullable=False)
    cargo_evaluador = Column(Text, nullable=True)
    concepto_tecnico_favorable_dep = Column(Text, nullable=True)   # SI | NO
    concepto_sectorial_favorable_dep = Column(Text, nullable=True) # SI | NO
    proyecto_viable_dep = Column(Text, nullable=True)              # SI | NO
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    formulario = relationship(
        "Formulario",
        backref=backref("observaciones_evaluacion", cascade="all, delete-orphan"),
    )

    def __repr__(self) -> str:
        return f"<ObservacionEvaluacion id={self.id} form={self.id_formulario} tipo={self.tipo_documento}>"
