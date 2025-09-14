from typing import List, Optional, Annotated
from decimal import Decimal
from pydantic import BaseModel, Field

ValorMoneda = Annotated[Decimal, Field(max_digits=18, decimal_places=2)]

class OpcionBase(BaseModel):
    id: int
    nombre: str
    class Config:
        from_attributes = True

class LineaRead(BaseModel):
    id: int
    nombre: str
    class Config: from_attributes = True

class ProgramaRead(BaseModel):
    id: int
    codigo_programa: int
    nombre_programa: str
    class Config: from_attributes = True

class SectorRead(BaseModel):
    id: int
    codigo_sector: int
    nombre_sector: str
    class Config: from_attributes = True

class MetaRead(BaseModel):
    id: int
    numero_meta: int
    nombre_meta: str
    class Config: from_attributes = True

class VariableSectorialRead(BaseModel):
    id: int
    nombre_variable: str
    class Config: from_attributes = True

class VariableTecnicoRead(BaseModel):
    id: int
    nombre_variable: str
    class Config: from_attributes = True

class PoliticaRead(BaseModel):
    id: int
    nombre_politica: str
    valor_destinado: Optional[ValorMoneda] = None
    class Config: from_attributes = True

class CategoriaRead(BaseModel):
    id: int
    id_politica: int
    nombre_categoria: str
    class Config: from_attributes = True

class SubcategoriaRead(BaseModel):
    id: int
    id_categoria: int
    nombre_subcategoria: str
    class Config: from_attributes = True

class EstructuraFinancieraIn(BaseModel):
    anio: Optional[int] = None
    entidad: str
    valor: ValorMoneda

class EstructuraFinancieraRow(BaseModel):
    id: int
    anio: Optional[int] = None
    entidad: str
    valor: ValorMoneda
    class Config: from_attributes = True

class EstructuraFinancieraBatchIn(BaseModel):
    form_id: int
    filas: List[EstructuraFinancieraIn] = []

class EstructuraFinancieraRead(BaseModel):
    filas: List[EstructuraFinancieraRow] = []
    total_proyecto: Optional[ValorMoneda] = None

class FormularioCreate(BaseModel):
    nombre_proyecto: str
    cod_id_mga: int
    id_dependencia: int
    id_linea_estrategica: int
    id_programa: int
    id_sector: int
    metas: List[int] = []
    variables_sectorial: List[int] = []
    variables_tecnico: List[int] = []
    estructura_financiera: List[EstructuraFinancieraIn] = []
    politicas: List[int] = []
    valores_politicas: List[ValorMoneda] = []
    categorias: List[int] = []
    subcategorias: List[int] = []

class FormularioRead(BaseModel):
    id: int
    nombre_proyecto: str
    cod_id_mga: int
    id_dependencia: int
    id_linea_estrategica: int
    id_programa: int
    id_sector: int
    metas: List[MetaRead] = []
    variables_sectorial: List[VariableSectorialRead] = []
    variables_tecnico: List[VariableTecnicoRead] = []
    estructura_financiera: List[EstructuraFinancieraRow] = []
    politicas: List[PoliticaRead] = []
    categorias: List[CategoriaRead] = []
    subcategorias: List[SubcategoriaRead] = []
    class Config: from_attributes = True
