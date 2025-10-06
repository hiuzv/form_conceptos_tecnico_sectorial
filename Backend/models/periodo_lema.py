from sqlalchemy import Column, Integer, Text
from Backend.utils.database import Base

class PeriodoLema(Base):
    __tablename__ = "periodo_lema"

    id = Column(Integer, primary_key=True, index=True)
    inicio_periodo = Column(Integer, nullable=False)
    fin_periodo = Column(Integer, nullable=False)
    lema = Column(Text, nullable=False)
