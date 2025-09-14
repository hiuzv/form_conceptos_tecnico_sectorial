from collections import defaultdict
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from typing import List, Tuple, Optional, Set
from sqlalchemy.orm import Session
from Backend.models import (
    Formulario, Metas, Meta, Sector, Programa, LineaEstrategica, Dependencia,
    VariableSectorial, VariableTecnico, VariablesTecnico as VariablesTecnicoRel,
    VariablesSectorial as VariablesSectorialRel, Politicas as PoliticasRel,
    Categorias as CategoriasRel, Subcategorias as SubcategoriasRel, EstructuraFinanciera, Politica, Categoria, Subcategoria,
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

    data = {
        "nombre_proyecto": form.nombre_proyecto,
        "cod_id_mga": form.cod_id_mga,
        "nombre_dependencia": nombre_dependencia,
        "codigo_sector": cod_sector,
        "nombre_sector": nom_sector,
        "codigo_programa": cod_prog,
        "nombre_programa": nom_prog,
        "nombre_linea_estrategica": nombre_linea,
    }

    # Todas las metas (sin limit)
    metas = (
        db.query(Meta)
        .join(Metas, Metas.id_meta == Meta.id)
        .filter(Metas.id_formulario == form_id)
        .order_by(Meta.numero_meta)
        .all()
    )
    numero_meta = [m.numero_meta for m in metas]
    nombre_meta = [m.nombre_meta for m in metas]

    # === ESTRUCTURA FINANCIERA ===
    ef_rows = (
        db.query(EstructuraFinanciera)
        .filter(EstructuraFinanciera.id_formulario == form_id)
        .all()
    )
    data["estructura_financiera"] = [
        {"anio": r.anio, "entidad": (r.entidad or "").strip().upper(), "valor": r.valor}
        for r in ef_rows
    ]

    # Variables
    ids_sec = [v.id for v in db.query(VariableSectorial).order_by(VariableSectorial.id).all()]
    ids_tec = [v.id for v in db.query(VariableTecnico).order_by(VariableTecnico.id).all()]

    sel_sec_ids = {
    r.id_variable_sectorial
    for r in db.query(VariablesSectorialRel)
               .filter(VariablesSectorialRel.id_formulario == form_id).all()
    }
    sel_tec_ids = {
        r.id_variable_tecnico
        for r in db.query(VariablesTecnicoRel)
                .filter(VariablesTecnicoRel.id_formulario == form_id).all()
    }
    flags_sec = [(vid in sel_sec_ids) for vid in ids_sec]
    flags_tec = [(vid in sel_tec_ids) for vid in ids_tec]

    def pad_or_clip(lst, size):
        return (lst + [False] * (size - len(lst)))[:size] if len(lst) < size else lst[:size]

    flags_sec = pad_or_clip(flags_sec, 9)
    flags_tec = pad_or_clip(flags_tec, 13)

    data["variables_sectorial"] = flags_sec
    data["variables_tecnico"] = flags_tec
    data["variables"] = flags_sec

    # Políticas
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

    # Categorías
    categorias = (
        db.query(Categoria)
        .join(CategoriasRel, CategoriasRel.id_categoria == Categoria.id)
        .filter(CategoriasRel.id_formulario == form_id)
        .order_by(Categoria.id)
        .limit(2)
        .all()
    )
    nombre_categoria = [c.nombre_categoria for c in categorias]

    # Subcategorías
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
        "variables_sectorial": flags_sec,
        "variables_tecnico": flags_tec,
        "nombre_politica": nombre_politica,
        "valor_destinado": valor_destinado,
        "nombre_categoria": nombre_categoria,
        "nombre_focalización": nombre_focalizacion,
        "estructura_financiera": [
            {"anio": r.anio, "entidad": (r.entidad or "").strip().upper(), "valor": r.valor}
            for r in ef_rows
        ],
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
    return bio, out_path.name
