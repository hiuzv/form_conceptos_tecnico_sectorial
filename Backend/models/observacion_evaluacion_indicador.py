from sqlalchemy import Column, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship, backref
from Backend.utils.database import Base


class ObservacionEvaluacionIndicador(Base):
    __tablename__ = "observacion_evaluacion_indicador"

    id = Column(Integer, primary_key=True)
    id_observacion_evaluacion = Column(
        Integer,
        ForeignKey("observacion_evaluacion.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    orden = Column(Integer, nullable=False, default=0)
    indicador_objetivo_general = Column(Text, nullable=False, default="")
    unidad_medida = Column(Text, nullable=False, default="")
    meta_resultado = Column(Text, nullable=False, default="")

    observacion_evaluacion = relationship(
        "ObservacionEvaluacion",
        backref=backref(
            "indicadores_objetivo",
            cascade="all, delete-orphan",
            order_by="ObservacionEvaluacionIndicador.orden, ObservacionEvaluacionIndicador.id",
        ),
    )

