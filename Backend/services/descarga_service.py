from io import BytesIO
from pathlib import Path
from typing import List, Tuple, Optional, Set

from sqlalchemy.orm import Session

from Backend.models import (
    Formulario, Metas, Meta, Sector, Programa, LineaEstrategica, Dependencia,
    Variables as VariablesRel, Politicas as PoliticasRel,
    Categorias as CategoriasRel, Subcategorias as SubcategoriasRel,
    Variable, Politica, Categoria, Subcategoria,
)
from Backend.services.excel_fill import fill_from_template


def _armar_data_para_template(db: Session, form_id: int) -> dict:
    row = (
        db.query(
            Formulario,
            Dependencia.nombre_dependencia,
            LineaEstrategica.nombre_linea_estrategica,
            Programa.codigo_programa,
            Programa.nombre_programa,
            Sector.codigo_sector,
            Sector.nombre_sector,
        )
        .join(Dependencia, Dependencia.id == Formulario.id_dependencia)
        .join(LineaEstrategica, LineaEstrategica.id == Formulario.id_linea_estrategica)
        .join(Sector, Sector.id == Formulario.id_sector)
        .join(Programa, Programa.id == Formulario.id_programa)
        .filter(Formulario.id == form_id)
        .one_or_none()
    )
    if not row:
        raise ValueError("Formulario no encontrado")

    form, nombre_dependencia, nombre_linea, cod_prog, nom_prog, cod_sector, nom_sector = row
    metas = (
        db.query(Meta)
        .join(Metas, Metas.id_meta == Meta.id)
        .filter(Metas.id_formulario == form_id)
        .order_by(Meta.numero_meta)
        .limit(3)
        .all()
    )
    numero_meta = [m.numero_meta for m in metas]
    nombre_meta = [m.nombre_meta for m in metas]
    todas_vars = db.query(Variable).order_by(Variable.id).limit(9).all()
    vars_presentes: Set[int] = {
        r.id_variable for r in db.query(VariablesRel).filter(VariablesRel.id_formulario == form_id).all()
    }
    variables_flags: List[bool] = [(v.id in vars_presentes) for v in todas_vars]
    while len(variables_flags) < 9:
        variables_flags.append(False) 
    politicas = (
        db.query(Politica.nombre_politica, PoliticasRel.valor_destinado)
        .join(PoliticasRel, PoliticasRel.id_politica == Politica.id)
        .filter(PoliticasRel.id_formulario == form_id)
        .order_by(Politica.id)
        .limit(2)
        .all()
    )
    nombre_politica = [r[0] for r in politicas]
    valor_destinado = [r[1] for r in politicas]  
    categorias = (
        db.query(Categoria)
        .join(CategoriasRel, CategoriasRel.id_categoria == Categoria.id)
        .filter(CategoriasRel.id_formulario == form_id)
        .order_by(Categoria.id)
        .limit(2)
        .all()
    )
    nombre_categoria = [c.nombre_categoria for c in categorias]
    subcats = (
        db.query(Subcategoria)
        .join(SubcategoriasRel, SubcategoriasRel.id_subcategoria == Subcategoria.id)
        .filter(SubcategoriasRel.id_formulario == form_id)
        .order_by(Subcategoria.id)
        .limit(2)
        .all()
    )
    nombre_focalizacion = [s.nombre_subcategoria for s in subcats]

    data = {
        "nombre_proyecto": form.nombre_proyecto,
        "cod_id_mga": form.cod_id_mga,
        "nombre_dependencia": nombre_dependencia,
        "codigo_sector": cod_sector,
        "nombre_sector": nom_sector,
        "codigo_programa": cod_prog,
        "nombre_programa": nom_prog,
        "nombre_linea_estrategica": nombre_linea,
        "numero_meta": numero_meta,
        "nombre_meta": nombre_meta,
        "variables": variables_flags,
        "nombre_politica": nombre_politica,
        "valor_destinado": valor_destinado, 
        "nombre_categoria": nombre_categoria,
        "nombre_focalización": nombre_focalizacion,
    }
    return data


def excel_formulario(db: Session, form_id: int) -> Tuple[BytesIO, str]:
    data = _armar_data_para_template(db, form_id)
    base_dir = Path(__file__).resolve().parents[2]
    out_path = fill_from_template(base_dir=base_dir, data=data)
    bio = BytesIO()
    with open(out_path, "rb") as f:
        bio.write(f.read())
    bio.seek(0)

    suggested_name = out_path.name
    return bio, suggested_name
