from __future__ import annotations
from collections import defaultdict
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from datetime import datetime
from zoneinfo import ZoneInfo
from Backend.models import (
    Formulario, Metas, Meta, Sector, Programa, LineaEstrategica, Dependencia,
    VariableSectorial, VariableTecnico,
    VariablesTecnico as VariablesTecnicoRel,
    VariablesSectorial as VariablesSectorialRel,
    Politicas as PoliticasRel,
    Categorias as CategoriasRel,
    Subcategorias as SubcategoriasRel,
    EstructuraFinanciera, Politica, Categoria, Subcategoria,
)
from Backend.services.excel_fill import fill_from_template
from Backend.services.word_fill import fill_docx


# =========================
# Utilidades de fecha/mes
# =========================
def _spanish_month(m: int) -> str:
    names = [
        "", "enero", "febrero", "marzo", "abril", "mayo", "junio",
        "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
    ]
    return names[m] if 1 <= m <= 12 else ""

_DAY_WORDS = {
    1: "uno", 2: "dos", 3: "tres", 4: "cuatro", 5: "cinco",
    6: "seis", 7: "siete", 8: "ocho", 9: "nueve", 10: "diez",
    11: "once", 12: "doce", 13: "trece", 14: "catorce", 15: "quince",
    16: "dieciséis", 17: "diecisiete", 18: "dieciocho", 19: "diecinueve",
    20: "veinte", 21: "veintiuno", 22: "veintidós", 23: "veintitrés",
    24: "veinticuatro", 25: "veinticinco", 26: "veintiséis", 27: "veintisiete",
    28: "veintiocho", 29: "veintinueve", 30: "treinta", 31: "treinta y uno"
}

def _to_day_words(d: int) -> str:
    return _DAY_WORDS.get(int(d), "")

def _now_bogota() -> datetime:
    try:
        return datetime.now(ZoneInfo("America/Bogota"))
    except Exception:
        return datetime.now()


# =========================
# Carga base (común) desde BD
# =========================
def _fetch_base_context(db: Session, form_id: int) -> dict:
    row = (
        db.query(
            Formulario,
            Dependencia.nombre_dependencia,
            LineaEstrategica.nombre_linea_estrategica,
            Programa.codigo_programa, Programa.nombre_programa,
            Sector.codigo_sector, Sector.nombre_sector,
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

    form, dep_nom, linea_nom, prog_cod, prog_nom, sec_cod, sec_nom = row

    base = {
        "form_id": form.id,
        "nombre_proyecto": form.nombre_proyecto,
        "cod_id_mga": form.cod_id_mga,
        "id_dependencia": form.id_dependencia,
        "nombre_dependencia": dep_nom,
        "codigo_sector": sec_cod,
        "nombre_sector": sec_nom,
        "codigo_programa": prog_cod,
        "nombre_programa": prog_nom,
        "nombre_linea_estrategica": linea_nom,
        "nombre_secretario": form.nombre_secretario,
    }

    # Metas ordenadas
    metas = (
        db.query(Meta)
        .join(Metas, Metas.id_meta == Meta.id)
        .filter(Metas.id_formulario == form_id)
        .order_by(Meta.numero_meta)
        .all()
    )
    base["metas"] = [{"numero": m.numero_meta, "nombre": m.nombre_meta} for m in metas]

    # Estructura financiera
    ef_rows = (
        db.query(EstructuraFinanciera)
        .filter(EstructuraFinanciera.id_formulario == form_id)
        .all()
    )
    base["estructura_financiera"] = [
        {"anio": r.anio, "entidad": (r.entidad or "").strip().upper(), "valor": r.valor}
        for r in ef_rows
    ]

    # Variables seleccionadas
    sel_sec_ids = {
        r.id_variable_sectorial
        for r in db.query(VariablesSectorialRel)
        .filter(VariablesSectorialRel.id_formulario == form_id)
        .all()
    }
    sel_tec_ids = {
        r.id_variable_tecnico
        for r in db.query(VariablesTecnicoRel)
        .filter(VariablesTecnicoRel.id_formulario == form_id)
        .all()
    }
    # Catalogos completos para mapeo a flags por índice
    ids_sec = [v.id for v in db.query(VariableSectorial).order_by(VariableSectorial.id).all()]
    ids_tec = [v.id for v in db.query(VariableTecnico).order_by(VariableTecnico.id).all()]
    base["variables_sectorial_flags"] = [(vid in sel_sec_ids) for vid in ids_sec][:9] + [False] * max(0, 9 - len(ids_sec))
    base["variables_tecnico_flags"]   = [(vid in sel_tec_ids) for vid in ids_tec][:13] + [False] * max(0, 13 - len(ids_tec))

    # Politicas/Categorias/Subcategorias (en orden de id, limita si la plantilla lo exige)
    politicas = (
        db.query(Politica.nombre_politica, PoliticasRel.valor_destinado)
        .join(PoliticasRel, PoliticasRel.id_politica == Politica.id)
        .filter(PoliticasRel.id_formulario == form_id)
        .order_by(Politica.id)
        .all()
    )
    base["politicas"] = [{"nombre": p, "valor": v} for (p, v) in politicas]

    categorias = (
        db.query(Categoria)
        .join(CategoriasRel, CategoriasRel.id_categoria == Categoria.id)
        .filter(CategoriasRel.id_formulario == form_id)
        .order_by(Categoria.id)
        .all()
    )
    base["categorias"] = [{"id": c.id, "nombre": c.nombre_categoria, "id_politica": c.id_politica} for c in categorias]

    subcats = (
        db.query(Subcategoria)
        .join(SubcategoriasRel, SubcategoriasRel.id_subcategoria == Subcategoria.id)
        .filter(SubcategoriasRel.id_formulario == form_id)
        .order_by(Subcategoria.id)
        .all()
    )
    base["subcategorias"] = [{"id": s.id, "nombre": s.nombre_subcategoria, "id_categoria": s.id_categoria} for s in subcats]

    return base


# =========================
# EXCELS (uno por función)
# =========================
def excel_concepto_tecnico_sectorial(db: Session, form_id: int) -> Tuple[BytesIO, str]:
    base_dir = Path(__file__).resolve().parents[2]
    data = _context_excel_concepto(_fetch_base_context(db, form_id))
    out_path = fill_from_template(base_dir=base_dir, data=data)
    bio = BytesIO(out_path.read_bytes())
    bio.seek(0)
    return bio, out_path.name

def excel_cadena_valor(db: Session, form_id: int) -> Tuple[BytesIO, str]:
    # Placeholder para segundo Excel (cuando exista plantilla específica)
    raise NotImplementedError("Plantilla de Cadena de Valor aún no implementada.")

def excel_viabilidad_dependencias(db: Session, form_id: int) -> Tuple[BytesIO, str]:
    # Placeholder para tercer Excel (cuando exista plantilla específica)
    raise NotImplementedError("Plantilla de Viabilidad por Dependencias aún no implementada.")


def _context_excel_concepto(base: Dict[str, object]) -> Dict[str, object]:
    metas = base.get("metas", [])
    numero_meta = [m["numero"] for m in metas]
    nombre_meta = [m["nombre"] for m in metas]

    # Flags exactos por plantilla
    flags_sec = (base.get("variables_sectorial_flags") or [])[:9]
    flags_tec = (base.get("variables_tecnico_flags") or [])[:13]

    data = {
        "nombre_proyecto": base["nombre_proyecto"],
        "cod_id_mga": base["cod_id_mga"],
        "nombre_dependencia": base["nombre_dependencia"],
        "codigo_sector": base["codigo_sector"],
        "nombre_sector": base["nombre_sector"],
        "codigo_programa": base["codigo_programa"],
        "nombre_programa": base["nombre_programa"],
        "nombre_linea_estrategica": base["nombre_linea_estrategica"],

        "numero_meta": numero_meta,
        "nombre_meta": nombre_meta,

        "variables_sectorial": flags_sec,
        "variables_tecnico":  flags_tec,

        # Política/Categoría/Subcategoría (si tu plantilla usa solo 2, se limita aquí)
        "nombre_politica": [p["nombre"] for p in base.get("politicas", [])][:2],
        "valor_destinado": [p["valor"] for p in base.get("politicas", [])][:2],
        "nombre_categoria": [c["nombre"] for c in base.get("categorias", [])][:2],
        "nombre_focalización": [s["nombre"] for s in base.get("subcategorias", [])][:2],

        # Estructura financiera completa para la hoja que la use
        "estructura_financiera": base.get("estructura_financiera", []),
    }
    return data


# =========================
# WORDS (uno por función)
# =========================
TEMPLATE_MAP = {
    "carta": "2.carta_de_presentacion.docx",
    "cert_precios": "4.Certificacion_de_precios.docx",
    "no_doble_cofin": "5.No_doble_cofinanciacion.docx",
}

def word_carta(db: Session, form_id: int) -> Tuple[BytesIO, str]:
    base = _fetch_base_context(db, form_id)
    ctx = _context_word_common(base)
    _merge_ctx_carta(ctx, base)
    return _render_word("carta", form_id, ctx)

def word_cert_precios(db: Session, form_id: int) -> Tuple[BytesIO, str]:
    base = _fetch_base_context(db, form_id)
    ctx = _context_word_common(base)
    # Si este formato no usa metas ni EF, NO las inyectamos:
    # (agrega aquí solo lo que el doc realmente usa)
    return _render_word("cert_precios", form_id, ctx)

def word_no_doble_cofin(db: Session, form_id: int) -> Tuple[BytesIO, str]:
    base = _fetch_base_context(db, form_id)
    ctx = _context_word_common(base)
    # Si este formato requiere un texto/firmas/fechas, ya vienen en ctx común.
    return _render_word("no_doble_cofin", form_id, ctx)


def _context_word_common(base: Dict[str, object]) -> Dict[str, object]:
    now = _now_bogota()
    ctx = {
        "nombre_proyecto": base["nombre_proyecto"],
        "cod_id_mga": base["cod_id_mga"],
        "nombre_dependencia": base["nombre_dependencia"],
        "nombre_sector": base["nombre_sector"],
        "codigo_sector": base["codigo_sector"],
        "nombre_programa": base["nombre_programa"],
        "codigo_programa": base["codigo_programa"],
        "nombre_linea_estrategica": base["nombre_linea_estrategica"],
        "nombre_secretario": base.get("nombre_secretario"),

        "dia": now.day,
        "dia_numero": now.day,
        "dia_texto": _to_day_words(now.day),
        "mes": _spanish_month(now.month),
        "mes_texto": _spanish_month(now.month),
        "anio": now.year,
        "año": now.year,
    }
    return ctx

def _merge_ctx_carta(ctx: Dict[str, object], base: Dict[str, object]) -> None:
    ef_rows = list(base.get("estructura_financiera", []))
    ENT_ORDER = ["DEPARTAMENTO", "MUNICIPIO", "NACION", "OTRO"]
    years = sorted({r.get("anio") for r in ef_rows if r.get("anio") is not None})[:4]
    while len(years) < 4:
        years.append(None)

    lookup: Dict[tuple, Decimal] = {}
    for r in ef_rows:
        y = r.get("anio")
        e = (r.get("entidad") or "")
        e = (e or "").strip().upper()
        v = r.get("valor") or 0
        lookup[(y, e)] = lookup.get((y, e), Decimal("0")) + Decimal(str(v))

    # Celdas por año/entidad
    for i, y in enumerate(years, start=1):
        for e in ENT_ORDER:
            val = lookup.get((y, e), Decimal("0"))
            ctx[f"valor_{e.lower()}_{i}"] = val
            if y is not None:
                ctx[f"valor_{e.lower()}_{y}"] = val

    # Totales por entidad y por año + total proyecto
    totals_ent = {e: Decimal("0") for e in ENT_ORDER}
    totals_year = [Decimal("0")] * 4
    for i, y in enumerate(years, start=1):
        for e in ENT_ORDER:
            v = lookup.get((y, e), Decimal("0"))
            totals_ent[e] += v
            totals_year[i - 1] += v

    for e in ENT_ORDER:
        ctx[f"total_{e.lower()}"] = totals_ent[e]
    for i, v in enumerate(totals_year, start=1):
        ctx[f"total_anio_{i}"] = v
    ctx["total_proyecto"] = sum(totals_year)

    # Metas enumeradas
    metas = base.get("metas", [])
    for i, m in enumerate(metas, start=1):
        ctx[f"numero_meta_{i}"] = m["numero"]
        ctx[f"nombre_meta_{i}"] = m["nombre"]


def _render_word(key: str, form_id: int, context: Dict[str, object]) -> Tuple[BytesIO, str]:
    if key not in TEMPLATE_MAP:
        raise ValueError("Documento no soportado")
    base_dir = Path(__file__).resolve().parents[2]
    template_name = TEMPLATE_MAP[key]
    output_name = f"{form_id}_{template_name}"
    out_path = fill_docx(base_dir=base_dir, template_name=template_name, context=context, output_name=output_name)
    bio = BytesIO(out_path.read_bytes())
    bio.seek(0)
    return bio, out_path.name


# =========================
# COMPAT: wrappers antiguos
# =========================
def excel_formulario(db: Session, form_id: int) -> Tuple[BytesIO, str]:
    return excel_concepto_tecnico_sectorial(db, form_id)

def word_formulario(db: Session, form_id: int, doc: str, extras: Optional[Dict[str, object]] = None) -> Tuple[BytesIO, str]:
    if doc == "carta":
        return word_carta(db, form_id)
    if doc == "cert_precios":
        return word_cert_precios(db, form_id)
    if doc == "no_doble_cofin":
        return word_no_doble_cofin(db, form_id)
    raise ValueError("Documento no soportado")
