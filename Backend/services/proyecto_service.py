from sqlalchemy.orm import Session
from sqlalchemy import func, cast, String
from typing import List, Optional, Tuple
from Backend.models import (
    LineaEstrategica, Programa, Sector, Meta,
    Formulario, Metas, Dependencia, Politica, Categoria, Subcategoria, EstructuraFinanciera,
    VariableSectorial, VariableTecnico,
    VariablesSectorial as VariablesSectorialRel,
    VariablesTecnico as VariablesTecnicoRel,
    Politicas as PoliticasRel,
    Categorias as CategoriasRel,
    Subcategorias as SubcategoriasRel,
    Viabilidad, Viabilidades,
    TipoViabilidad, FuncionarioViabilidad,
    ObservacionEvaluacion,
)
from Backend import schemas

_ACCENTS = "ÁÉÍÓÚáéíóúÑñ"
_ASCII   = "AEIOUaeiouNn"
_TRANS   = str.maketrans(_ACCENTS, _ASCII)

# -------------------------
# Catálogos / Listados base
# -------------------------
def listar_lineas(db: Session) -> List[LineaEstrategica]:
    return db.query(LineaEstrategica).order_by(LineaEstrategica.nombre_linea_estrategica).all()

def listar_sectores(db: Session, linea_id: int) -> List[Sector]:
    return (
        db.query(Sector)
        .filter(Sector.id_linea_estrategica == linea_id)
        .order_by(Sector.nombre_sector)
        .all()
    )

def listar_programas(db: Session, sector_id: int) -> List[Programa]:
    return (
        db.query(Programa)
        .filter(Programa.id_sector == sector_id)
        .order_by(Programa.nombre_programa)
        .all()
    )

def listar_metas(db: Session, programa_id: int) -> List[Meta]:
    return (
        db.query(Meta)
        .filter(Meta.id_programa == programa_id)
        .order_by(Meta.numero_meta)
        .all()
    )

def listar_dependencias(db: Session):
    return db.query(Dependencia).order_by(Dependencia.nombre_dependencia).all()

def listar_variables_sectorial(db):
    return db.query(VariableSectorial).order_by(VariableSectorial.nombre_variable).all()

def listar_variables_tecnico(db):
    return db.query(VariableTecnico).order_by(VariableTecnico.nombre_variable).all()

def leer_respuestas_sectorial(db, form_id:int) -> dict[int,str]:
    rows = db.query(VariablesSectorialRel).filter(VariablesSectorialRel.id_formulario==form_id).all()
    return {r.id_variable_sectorial: (r.respuesta or None) for r in rows}

def leer_respuestas_tecnico(db, form_id:int) -> dict[int,str]:
    rows = db.query(VariablesTecnicoRel).filter(VariablesTecnicoRel.id_formulario==form_id).all()
    return {r.id_variable_tecnico: (r.respuesta or None) for r in rows}

def leer_respuestas_viabilidad(db, form_id:int) -> dict[int,str]:
    rows = db.query(Viabilidades).filter(Viabilidades.id_formulario==form_id).all()
    return {r.id_viabilidad: (r.respuesta or None) for r in rows}

def listar_politicas(db: Session):
    return db.query(Politica).order_by(Politica.nombre_politica).all()

def listar_categorias(db: Session, politica_id: Optional[int] = None):
    q = db.query(Categoria)
    if politica_id is not None:
        q = q.filter(Categoria.id_politica == politica_id)
    return q.order_by(Categoria.nombre_categoria).all()

def listar_subcategorias(db: Session, categoria_id: Optional[int] = None):
    q = db.query(Subcategoria)
    if categoria_id is not None:
        q = q.filter(Subcategoria.id_categoria == categoria_id)
    return q.order_by(Subcategoria.nombre_subcategoria).all()

# -------------------------
# Formulario (CRUD)
# -------------------------

def crear_formulario(db: Session, data: schemas.FormularioCreate) -> Formulario:
    form = Formulario(
        nombre_proyecto=data.nombre_proyecto,
        cod_id_mga=data.cod_id_mga,
        id_dependencia=data.id_dependencia,
        id_linea_estrategica=data.id_linea_estrategica,
        id_programa=data.id_programa,
        id_sector=data.id_sector,
        nombre_secretario=data.nombre_secretario,
        cargo_responsable=data.cargo_responsable,
    )
    db.add(form)
    db.flush()
    db.commit()
    db.refresh(form)
    return form

def obtener_formulario(db: Session, form_id: int) -> Optional[Formulario]:
    return db.get(Formulario, form_id)

def leer_formulario(db: Session, form_id: int) -> Tuple[Optional[Formulario], List[Meta]]:
    form = db.get(Formulario, form_id)
    if not form:
        return None, []
    metas = (
        db.query(Meta)
        .join(Metas, Metas.id_meta == Meta.id)
        .filter(Metas.id_formulario == form_id)
        .order_by(Meta.numero_meta)
        .all()
    )
    return form, metas

def asignar_metas(db: Session, form_id: int, meta_ids: List[int]) -> None:
    if not meta_ids:
        return
    rows = [Metas(id_meta=m, id_formulario=form_id) for m in meta_ids]
    db.add_all(rows)
    db.commit()

def asignar_variables_sectorial(db, form_id: int, variable_ids: list[int]) -> None:
    if not variable_ids: return
    rows = [VariablesSectorialRel(id_variable_sectorial=v, id_formulario=form_id) for v in variable_ids]
    db.add_all(rows); db.commit()

def asignar_variables_tecnico(db, form_id: int, variable_ids: list[int]) -> None:
    if not variable_ids: return
    rows = [VariablesTecnicoRel(id_variable_tecnico=v, id_formulario=form_id) for v in variable_ids]
    db.add_all(rows); db.commit()

def asignar_politicas(db: Session, form_id: int, politica_ids: List[int], valores: List[float] | None = None) -> None:
    if not politica_ids:
        return
    valores = valores or []
    rows = []
    for i, pid in enumerate(politica_ids):
        val = valores[i] if i < len(valores) else None
        rows.append(PoliticasRel(id_politica=pid, id_formulario=form_id, valor_destinado=val))
    db.add_all(rows)
    db.commit()

def asignar_categorias(db: Session, form_id: int, categoria_ids: List[int]) -> None:
    if not categoria_ids:
        return
    rows = [CategoriasRel(id_categoria=c, id_formulario=form_id) for c in categoria_ids]
    db.add_all(rows)
    db.commit()

def asignar_subcategorias(db: Session, form_id: int, subcategoria_ids: List[int]) -> None:
    if not subcategoria_ids:
        return
    rows = [SubcategoriasRel(id_subcategoria=s, id_formulario=form_id) for s in subcategoria_ids]
    db.add_all(rows)
    db.commit()

def asignar_estructura_financiera(db: Session, form_id: int, filas) -> None:
    db.query(EstructuraFinanciera).filter(EstructuraFinanciera.id_formulario == form_id).delete()
    to_add = []
    by_year = {}

    for f in filas:
        if isinstance(f, dict):
            anio = f.get("anio")
            entidad = (f.get("entidad") or "").strip().upper()
            valor = f.get("valor") or 0
        else:
            anio = getattr(f, "anio", None)
            entidad = (getattr(f, "entidad", None) or "").strip().upper()
            valor = getattr(f, "valor", None) or 0

        if not anio:
            continue

        by_year.setdefault(anio, {})[entidad] = valor

        if entidad != "DEPARTAMENTO":
            to_add.append(EstructuraFinanciera(
                id_formulario=form_id, anio=anio, entidad=entidad, valor=valor
            ))

    for anio, ents in by_year.items():
        val_dep = sum(
            v for k, v in ents.items() if k == "PROPIOS" or k.startswith("SGP_")
        )
        to_add.append(EstructuraFinanciera(
            id_formulario=form_id, anio=anio, entidad="DEPARTAMENTO", valor=val_dep
        ))

    if to_add:
        db.add_all(to_add)
    db.commit()

# -------------------------
# Listar por formulario (JOIN)
# -------------------------

def listar_metas_por_formulario(db: Session, form_id: int) -> List[Meta]:
    return (
        db.query(Meta)
        .join(Metas, Metas.id_meta == Meta.id)
        .filter(Metas.id_formulario == form_id)
        .order_by(Meta.numero_meta)
        .all()
    )

def listar_variables_sectorial_por_formulario(db, form_id: int):
    return (
        db.query(VariableSectorial)
        .join(VariablesSectorialRel, VariablesSectorialRel.id_variable_sectorial == VariableSectorial.id)
        .filter(VariablesSectorialRel.id_formulario == form_id)
        .order_by(VariableSectorial.nombre_variable)
        .all()
    )

def listar_variables_tecnico_por_formulario(db, form_id: int):
    return (
        db.query(VariableTecnico)
        .join(VariablesTecnicoRel, VariablesTecnicoRel.id_variable_tecnico == VariableTecnico.id)
        .filter(VariablesTecnicoRel.id_formulario == form_id)
        .order_by(VariableTecnico.nombre_variable)
        .all()
    )


def listar_politicas_por_formulario(db: Session, form_id: int):
    return (
        db.query(Politica, PoliticasRel.valor_destinado)
        .join(PoliticasRel, PoliticasRel.id_politica == Politica.id)
        .filter(PoliticasRel.id_formulario == form_id)
        .order_by(Politica.id)
        .all()
    )

def listar_categorias_por_formulario(db: Session, form_id: int):
    return (
        db.query(Categoria)
        .join(CategoriasRel, CategoriasRel.id_categoria == Categoria.id)
        .filter(CategoriasRel.id_formulario == form_id)
        .order_by(Categoria.nombre_categoria)
        .all()
    )

def listar_subcategorias_por_formulario(db: Session, form_id: int):
    return (
        db.query(Subcategoria)
        .join(SubcategoriasRel, SubcategoriasRel.id_subcategoria == Subcategoria.id)
        .filter(SubcategoriasRel.id_formulario == form_id)
        .order_by(Subcategoria.nombre_subcategoria)
        .all()
    )

def listar_estructura_financiera(db: Session, form_id: int) -> List[EstructuraFinanciera]:
    return (
        db.query(EstructuraFinanciera)
        .filter(EstructuraFinanciera.id_formulario == form_id)
        .order_by(EstructuraFinanciera.anio.nullsfirst(), EstructuraFinanciera.entidad)
        .all()
    )

def listar_proyectos(db: Session) -> List[Formulario]:
    return (
        db.query(Formulario)
        .order_by(Formulario.id.desc())
        .all()
    )

def update_formulario_basicos(db: Session, form_id: int, data: schemas.FormularioUpsertBasicos) -> Formulario:
    form = db.get(Formulario, form_id)
    if not form:
        raise ValueError("Formulario no encontrado")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(form, field, value)
    db.commit()
    db.refresh(form)
    return form


def update_formulario_radicacion(db: Session, form_id: int, data: schemas.FormularioRadicacionUpsert) -> Formulario:
    form = db.get(Formulario, form_id)
    if not form:
        raise ValueError("Formulario no encontrado")

    form.numero_radicacion = (data.numero_radicacion or "").strip() or None
    form.fecha_radicacion = data.fecha_radicacion
    form.bpin = (data.bpin or "").strip() or None
    form.soportes_folios = max(0, int(data.soportes_folios or 0))
    form.soportes_planos = max(0, int(data.soportes_planos or 0))
    form.soportes_cds = max(0, int(data.soportes_cds or 0))
    form.soportes_otros = max(0, int(data.soportes_otros or 0))

    db.commit()
    db.refresh(form)
    return form

def replace_metas(db: Session, form_id: int, meta_ids: List[int]) -> None:
    db.query(Metas).filter(Metas.id_formulario == form_id).delete()
    asignar_metas(db, form_id, meta_ids or [])

def replace_variables_sectorial(db: Session, form_id: int, variable_ids: List[int]) -> None:
    db.query(VariablesSectorialRel).filter(VariablesSectorialRel.id_formulario == form_id).delete()
    asignar_variables_sectorial(db, form_id, variable_ids or [])

def replace_variables_tecnico(db: Session, form_id: int, variable_ids: List[int]) -> None:
    db.query(VariablesTecnicoRel).filter(VariablesTecnicoRel.id_formulario == form_id).delete()
    asignar_variables_tecnico(db, form_id, variable_ids or [])

def replace_politicas(db: Session, form_id: int, politica_ids: List[int], valores: List[float] | None = None) -> None:
    db.query(PoliticasRel).filter(PoliticasRel.id_formulario == form_id).delete()
    asignar_politicas(db, form_id, politica_ids or [], valores or [])

def replace_categorias(db: Session, form_id: int, categoria_ids: List[int]) -> None:
    db.query(CategoriasRel).filter(CategoriasRel.id_formulario == form_id).delete()
    asignar_categorias(db, form_id, categoria_ids or [])

def replace_subcategorias(db: Session, form_id: int, subcategoria_ids: List[int]) -> None:
    db.query(SubcategoriasRel).filter(SubcategoriasRel.id_formulario == form_id).delete()
    asignar_subcategorias(db, form_id, subcategoria_ids or [])

def listar_proyectos_pag(db: Session, nombre: Optional[str], cod_id_mga: Optional[str], id_dependencia: Optional[int],
                         page:int, page_size:int) -> tuple[list[Formulario], int]:
    q = db.query(Formulario)
    if nombre:
        q = q.filter(_ilike_no_accents(Formulario.nombre_proyecto, nombre))
    if cod_id_mga is not None:
        cod_txt = "".join(ch for ch in cod_id_mga if ch.isdigit())
        if cod_txt:
            q = q.filter(cast(Formulario.cod_id_mga, String).like(f"%{cod_txt}%"))
    if id_dependencia is not None:
        q = q.filter(Formulario.id_dependencia == id_dependencia)
    total = q.count()
    rows = q.order_by(Formulario.id.desc()).offset((page-1)*page_size).limit(page_size).all()
    return rows, total

def crear_formulario_minimo(db: Session, data: schemas.FormularioCreateMinimo) -> Formulario:
    existing = (
        db.query(Formulario)
        .filter(
            Formulario.cod_id_mga == data.cod_id_mga,
            Formulario.id_dependencia == data.id_dependencia,
        )
        .order_by(Formulario.id.desc())
        .first()
    )
    if existing:
        if data.nombre_proyecto and data.nombre_proyecto.strip() and data.nombre_proyecto.strip() != (existing.nombre_proyecto or "").strip():
            existing.nombre_proyecto = data.nombre_proyecto.strip()
            db.commit()
            db.refresh(existing)
        return existing

    form = Formulario(
        nombre_proyecto=data.nombre_proyecto,
        cod_id_mga=data.cod_id_mga,
        id_dependencia=data.id_dependencia,
    )
    db.add(form)
    db.flush()
    db.commit()
    db.refresh(form)
    return form

def listar_viabilidad(db: Session):
    return db.query(Viabilidad).order_by(Viabilidad.id).all()

def listar_tipos_viabilidad(db: Session):
    return db.query(TipoViabilidad).order_by(TipoViabilidad.id).all()

def listar_viabilidades_por_formulario(db: Session, form_id: int):
    return (
        db.query(Viabilidad)
        .join(Viabilidades, Viabilidades.id_viabilidad == Viabilidad.id)
        .filter(Viabilidades.id_formulario == form_id)
        .order_by(Viabilidad.nombre)
        .all()
    )

def listar_funcionarios_viabilidad(db: Session, form_id: int):
    return (
        db.query(FuncionarioViabilidad)
        .filter(FuncionarioViabilidad.id_formulario == form_id)
        .order_by(FuncionarioViabilidad.id_tipo_viabilidad)
        .all()
    )

def replace_viabilidades(db: Session, form_id: int, ids: List[int]):
    db.query(Viabilidades).filter(Viabilidades.id_formulario == form_id).delete()
    rows = [Viabilidades(id_formulario=form_id, id_viabilidad=i) for i in (ids or [])]
    if rows:
        db.add_all(rows)
    db.commit()

def replace_funcionarios_viabilidad(db: Session, form_id: int, filas: List[dict]):
    db.query(FuncionarioViabilidad).filter(FuncionarioViabilidad.id_formulario == form_id).delete()
    to_add = []
    for f in filas or []:
        itv = f.get("id_tipo_viabilidad")
        nombre = (f.get("nombre") or "").strip()
        cargo  = (f.get("cargo") or "").strip()
        if itv and (nombre or cargo):
            to_add.append(FuncionarioViabilidad(
                id_formulario=form_id,
                id_tipo_viabilidad=itv,
                nombre=nombre,
                cargo=cargo
            ))
    if to_add:
        db.add_all(to_add)
    db.commit()

def _ilike_no_accents(column, term: str):
    term_norm = (term or "").translate(_TRANS).lower()
    col_norm  = func.lower(func.translate(column, _ACCENTS, _ASCII))
    return col_norm.like(f"%{term_norm}%")

def listar_cat_variables_sectorial(db): 
    return listar_variables_sectorial(db)

def listar_cat_variables_tecnico(db): 
    return listar_variables_tecnico(db)

def listar_cat_viabilidad(db): 
    return listar_viabilidad(db)

def leer_respuestas_viab(db, form_id:int):
    return leer_respuestas_viabilidad(db, form_id)

def upsert_respuestas_sectorial(db, form_id:int, pares:list[tuple[int,str]]):
    cat = {v.id: v.no_aplica for v in listar_variables_sectorial(db)}
    db.query(VariablesSectorialRel).filter(VariablesSectorialRel.id_formulario==form_id).delete()
    to_add=[]
    for vid, resp in pares or []:
        if vid not in cat: continue
        no_apl = bool(cat[vid])
        resp = (resp or "").upper().strip()
        if resp not in ("SI","NO","N/A"): continue
        if resp=="N/A" and not no_apl:
            continue
        to_add.append(VariablesSectorialRel(id_formulario=form_id, id_variable_sectorial=vid, respuesta=resp))
    if to_add: db.add_all(to_add)
    db.commit()

def upsert_respuestas_tecnico(db, form_id:int, pares:list[tuple[int,str]]):
    cat = {v.id: v.no_aplica for v in listar_variables_tecnico(db)}
    db.query(VariablesTecnicoRel).filter(VariablesTecnicoRel.id_formulario==form_id).delete()
    to_add=[]
    for vid, resp in pares or []:
        if vid not in cat: continue
        no_apl = bool(cat[vid])
        resp = (resp or "").upper().strip()
        if resp not in ("SI","NO","N/A"): continue
        if resp=="N/A" and not no_apl:
            continue
        to_add.append(VariablesTecnicoRel(id_formulario=form_id, id_variable_tecnico=vid, respuesta=resp))
    if to_add: db.add_all(to_add)
    db.commit()

def upsert_respuestas_viab(db, form_id:int, pares:list[tuple[int,str]]):
    cat = {v.id: v.no_aplica for v in listar_viabilidad(db)}
    db.query(Viabilidades).filter(Viabilidades.id_formulario==form_id).delete()
    to_add=[]
    for vid, resp in pares or []:
        if vid not in cat: continue
        no_apl = bool(cat[vid])
        resp = (resp or "").upper().strip()
        if resp not in ("SI","NO","N/A"): continue
        if resp=="N/A" and not no_apl:
            continue
        to_add.append(Viabilidades(id_formulario=form_id, id_viabilidad=vid, respuesta=resp))
    if to_add: db.add_all(to_add)
    db.commit()


def crear_observacion_evaluacion(
    db: Session,
    form_id: int,
    tipo_documento: str,
    contenido_html: str,
    nombre_evaluador: str,
    cargo_evaluador: str | None = None,
    concepto_tecnico_favorable_dep: str | None = None,
    concepto_sectorial_favorable_dep: str | None = None,
    proyecto_viable_dep: str | None = None,
) -> ObservacionEvaluacion:
    form = db.get(Formulario, form_id)
    if not form:
        raise ValueError("Formulario no encontrado")

    tipo = (tipo_documento or "").strip().upper()
    if tipo not in ("OBSERVACIONES", "VIABILIDAD"):
        raise ValueError("tipo_documento invalido. Usa OBSERVACIONES o VIABILIDAD")

    contenido = (contenido_html or "").strip()
    evaluador = (nombre_evaluador or "").strip()
    cargo_eval = (cargo_evaluador or "").strip()
    if not contenido:
        raise ValueError("contenido_html es requerido")
    if not evaluador:
        raise ValueError("nombre_evaluador es requerido")
    if not cargo_eval:
        raise ValueError("cargo_evaluador es requerido")

    def _norm_check(v: str | None) -> str | None:
        if v is None:
            return None
        vv = (v or "").strip().upper()
        return vv if vv in ("SI", "NO") else None

    chk_tec = _norm_check(concepto_tecnico_favorable_dep)
    chk_sec = _norm_check(concepto_sectorial_favorable_dep)
    chk_via = _norm_check(proyecto_viable_dep)

    row = ObservacionEvaluacion(
        id_formulario=form_id,
        tipo_documento=tipo,
        contenido_html=contenido,
        nombre_evaluador=evaluador,
        cargo_evaluador=cargo_eval,
        concepto_tecnico_favorable_dep=chk_tec,
        concepto_sectorial_favorable_dep=chk_sec,
        proyecto_viable_dep=chk_via,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def listar_observaciones_evaluacion(db: Session, form_id: int) -> list[ObservacionEvaluacion]:
    return (
        db.query(ObservacionEvaluacion)
        .filter(ObservacionEvaluacion.id_formulario == form_id)
        .order_by(ObservacionEvaluacion.created_at.desc(), ObservacionEvaluacion.id.desc())
        .all()
    )
