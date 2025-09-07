from sqlalchemy.orm import Session
from typing import List, Optional, Tuple
from Backend.models import (
    LineaEstrategica, Programa, Sector, Meta,
    Formulario, Metas, Dependencia, Variable, Politica, Categoria, Subcategoria,
    Variables as VariablesRel,
    Politicas as PoliticasRel,
    Categorias as CategoriasRel,
    Subcategorias as SubcategoriasRel,
)
from Backend import schemas

# -------------------------
# Catálogos / Listados base
# -------------------------

def listar_lineas(db: Session) -> List[LineaEstrategica]:
    return db.query(LineaEstrategica).order_by(LineaEstrategica.nombre_linea_estrategica).all()

def listar_programas(db: Session, linea_id: int) -> List[Programa]:
    return (
        db.query(Programa)
        .filter(Programa.id_linea_estrategica == linea_id)
        .order_by(Programa.nombre_programa)
        .all()
    )

def listar_sectores(db: Session, programa_id: int) -> List[Sector]:
    return (
        db.query(Sector)
        .filter(Sector.id_programa == programa_id)
        .order_by(Sector.nombre_sector)
        .all()
    )

def listar_metas(db: Session, sector_id: int) -> List[Meta]:
    return (
        db.query(Meta)
        .filter(Meta.id_sector == sector_id)
        .order_by(Meta.numero_meta)
        .all()
    )

def listar_dependencias(db: Session):
    return db.query(Dependencia).order_by(Dependencia.nombre_dependencia).all()

def listar_variables(db: Session):
    return db.query(Variable).order_by(Variable.nombre_variable).all()

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
    )
    db.add(form)
    db.flush()   # obtenemos form.id
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

def asignar_variables(db: Session, form_id: int, variable_ids: List[int]) -> None:
    if not variable_ids:
        return
    rows = [VariablesRel(id_variable=v, id_formulario=form_id) for v in variable_ids]
    db.add_all(rows)
    db.commit()

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

def listar_variables_por_formulario(db: Session, form_id: int):
    return (
        db.query(Variable)
        .join(VariablesRel, VariablesRel.id_variable == Variable.id)
        .filter(VariablesRel.id_formulario == form_id)
        .order_by(Variable.nombre_variable)
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
