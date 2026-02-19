from typing import List, Optional, Annotated
from decimal import Decimal
from pydantic import BaseModel, Field
from datetime import datetime, date

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
    codigo_producto: int
    nombre_producto: str
    codigo_indicador_producto: int
    nombre_indicador_producto: str
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
    id: Optional[int] = None
    anio: Optional[int] = None
    entidad: str
    valor: ValorMoneda
    class Config: 
        from_attributes = True

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
    nombre_secretario: str
    metas: List[int] = []
    variables_sectorial: List[int] = []
    variables_tecnico: List[int] = []
    estructura_financiera: List[EstructuraFinancieraIn] = []
    politicas: List[int] = []
    valores_politicas: List[ValorMoneda] = []
    categorias: List[int] = []
    subcategorias: List[int] = []
    cargo_responsable: Optional[str] = None

class ViabilidadRead(BaseModel):
    id: int
    nombre: str
    class Config: 
        from_attributes = True

class TipoViabilidadRead(BaseModel):
    id: int
    nombre: str
    class Config:
        from_attributes = True

class FuncionarioViabilidadIn(BaseModel):
    id_tipo_viabilidad: int
    nombre: str
    cargo: str

class FuncionariosViabilidadUpsertIn(BaseModel):
    funcionarios: List[FuncionarioViabilidadIn] = []

class FormularioRead(BaseModel):
    id: int
    nombre_proyecto: str
    cod_id_mga: int
    id_dependencia: int
    id_linea_estrategica: int
    id_programa: int
    id_sector: int
    nombre_secretario: str 
    metas: List[MetaRead] = []
    variables_sectorial: List[VariableSectorialRead] = []
    variables_tecnico: List[VariableTecnicoRead] = []
    estructura_financiera: List[EstructuraFinancieraRow] = []
    politicas: List[PoliticaRead] = []
    categorias: List[CategoriaRead] = []
    subcategorias: List[SubcategoriaRead] = []
    class Config: from_attributes = True
    viabilidades: List[ViabilidadRead] = []
    funcionarios_viabilidad: List[FuncionarioViabilidadIn] = []
    fuentes: Optional[str] = None
    duracion_proyecto: Optional[int] = None
    cantidad_beneficiarios: Optional[int] = None
    cargo_responsable: Optional[str] = None
    numero_radicacion: Optional[str] = None
    fecha_radicacion: Optional[date] = None
    bpin: Optional[str] = None
    soportes_folios: int = 0
    soportes_planos: int = 0
    soportes_cds: int = 0
    soportes_otros: int = 0

class ProyectoListRead(BaseModel):
    nombre: str
    cod_id_mga: int
    id_dependencia: int

class FormularioUpsertBasicos(BaseModel):
    nombre_proyecto: Optional[str] = None
    cod_id_mga: Optional[int] = None
    id_dependencia: Optional[int] = None
    id_linea_estrategica: Optional[int] = None
    id_programa: Optional[int] = None
    id_sector: Optional[int] = None
    nombre_secretario: Optional[str] = None
    fuentes: Optional[str] = None
    duracion_proyecto: Optional[int] = None
    cantidad_beneficiarios: Optional[int] = None
    cargo_responsable: Optional[str] = None

class IdsIn(BaseModel):
    ids: List[int] = []

class PoliticasUpsertIn(BaseModel):
    politicas: List[int] = []
    valores_politicas: List[ValorMoneda] = []

class ProyectoListItem(BaseModel):
    id: int
    nombre: str
    cod_id_mga: int
    id_dependencia: int

class FormularioCreateMinimo(BaseModel):
    nombre_proyecto: str
    cod_id_mga: int
    id_dependencia: int

class FormularioId(BaseModel):
    id: int

class VarCatalogoRead(BaseModel):
    id: int
    nombre: str
    no_aplica: bool

class VarRespuestaRead(BaseModel):
    id: int
    nombre: str
    no_aplica: bool
    respuesta: Optional[str] = None

class VarRespuestaIn(BaseModel):
    id: int
    respuesta: str

class VarsRespuestaUpsertIn(BaseModel):
    respuestas: List[VarRespuestaIn]


class FormularioRadicacionUpsert(BaseModel):
    numero_radicacion: Optional[str] = None
    fecha_radicacion: Optional[date] = None
    bpin: Optional[str] = None
    soportes_folios: int = 0
    soportes_planos: int = 0
    soportes_cds: int = 0
    soportes_otros: int = 0


class ObservacionEvaluacionCreate(BaseModel):
    tipo_documento: str  # OBSERVACIONES | VIABILIDAD
    contenido_html: str
    nombre_evaluador: str
    cargo_evaluador: Optional[str] = None
    concepto_tecnico_favorable_dep: Optional[str] = None
    concepto_sectorial_favorable_dep: Optional[str] = None
    proyecto_viable_dep: Optional[str] = None


class ObservacionEvaluacionRead(BaseModel):
    id: int
    id_formulario: int
    tipo_documento: str
    contenido_html: str
    nombre_evaluador: str
    cargo_evaluador: Optional[str] = None
    concepto_tecnico_favorable_dep: Optional[str] = None
    concepto_sectorial_favorable_dep: Optional[str] = None
    proyecto_viable_dep: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
