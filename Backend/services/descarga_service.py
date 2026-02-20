from __future__ import annotations
from collections import defaultdict
from decimal import Decimal
from io import BytesIO
from pathlib import Path
import re
import base64
import asyncio
import sys
from typing import Dict, Optional, Tuple
from sqlalchemy import text
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
    EstructuraFinanciera, Politica, Categoria, Subcategoria, PeriodoLema,
    Viabilidad, Viabilidades, FuncionarioViabilidad
)
from Backend.services.excel_fill import fill_from_template, fill_viabilidad_dependencias, fill_cadena_valor
from Backend.services.word_fill import fill_docx
from Backend.services import proyecto_service
from num2words import num2words as n2w
from decimal import Decimal, ROUND_HALF_UP

# =========================
# Utilidades de fecha/mes
# =========================

def numero_a_texto(valor: float) -> str:
    try:
        n = int(Decimal(str(valor)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    except Exception:
        n = int(valor or 0)
    return f"{n2w(n, lang='es').capitalize()} pesos M/cte."

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
    16: "diecisÃ©is", 17: "diecisiete", 18: "dieciocho", 19: "diecinueve",
    20: "veinte", 21: "veintiuno", 22: "veintidÃ³s", 23: "veintitrÃ©s",
    24: "veinticuatro", 25: "veinticinco", 26: "veintisÃ©is", 27: "veintisiete",
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
# Carga base (comÃºn) desde BD
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
        .outerjoin(Dependencia, Dependencia.id == Formulario.id_dependencia)
        .outerjoin(LineaEstrategica, LineaEstrategica.id == Formulario.id_linea_estrategica)
        .outerjoin(Sector, Sector.id == Formulario.id_sector)
        .outerjoin(Programa, Programa.id == Formulario.id_programa)
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
        "numero_radicacion": getattr(form, "numero_radicacion", None),
        "fecha_radicacion": getattr(form, "fecha_radicacion", None),
        "bpin": getattr(form, "bpin", None),
        "soportes_folios": getattr(form, "soportes_folios", 0),
        "soportes_planos": getattr(form, "soportes_planos", 0),
        "soportes_cds": getattr(form, "soportes_cds", 0),
        "soportes_otros": getattr(form, "soportes_otros", 0),
        "id_dependencia": form.id_dependencia,
        "nombre_dependencia": dep_nom or "",
        "codigo_sector": sec_cod or "",
        "nombre_sector": sec_nom or "",
        "codigo_programa": prog_cod or "",
        "nombre_programa": prog_nom or "",
        "nombre_linea_estrategica": linea_nom or "",
        "cargo_responsable": form.cargo_responsable,
        "nombre_secretario": form.nombre_secretario,
        "fuentes": getattr(form, "fuentes", None),
        "duracion_proyecto": getattr(form, "duracion_proyecto", None),
        "cantidad_beneficiarios": getattr(form, "cantidad_beneficiarios", None),
    }
    metas = (
        db.query(Meta)
        .join(Metas, Metas.id_meta == Meta.id)
        .filter(Metas.id_formulario == form_id)
        .order_by(Meta.numero_meta)
        .all()
    )
    base["metas"] = [
        {
            "numero": m.numero_meta,
            "nombre": m.nombre_meta,
            "codigo_producto": m.codigo_producto,
            "nombre_producto": m.nombre_producto,
            "codigo_indicador_producto": m.codigo_indicador_producto,
            "nombre_indicador_producto": m.nombre_indicador_producto,
        }
        for m in metas
    ]
    ef_rows = (
        db.query(EstructuraFinanciera)
        .filter(EstructuraFinanciera.id_formulario == form_id)
        .all()
    )
    base["estructura_financiera"] = [
        {"anio": r.anio, "entidad": (r.entidad or "").strip().upper(), "valor": r.valor}
        for r in ef_rows
    ]
    sec_rows = (
        db.query(VariablesSectorialRel.id_variable_sectorial, VariablesSectorialRel.respuesta)
        .filter(VariablesSectorialRel.id_formulario == form_id)
        .all()
    )
    sel_sec_ids = {vid for (vid, _resp) in sec_rows}
    res_sec_map = {vid: (resp or "").strip() for (vid, resp) in sec_rows}
    ids_sec = [v.id for v in db.query(VariableSectorial).order_by(VariableSectorial.id).all()]
    base["variables_sectorial"] = [vid in sel_sec_ids for vid in ids_sec][:9] + [""] * max(0, 9 - len(ids_sec))
    base["variables_sectorial_respuestas"] = [res_sec_map.get(vid, "") for vid in ids_sec][:9] + [""] * max(0, 9 - len(ids_sec))

    # ========== Variables TÃ‰CNICO ==========
    tec_rows = (
        db.query(VariablesTecnicoRel.id_variable_tecnico, VariablesTecnicoRel.respuesta)
        .filter(VariablesTecnicoRel.id_formulario == form_id)
        .all()
    )
    sel_tec_ids = {vid for (vid, _resp) in tec_rows}
    res_tec_map = {vid: (resp or "").strip() for (vid, resp) in tec_rows}
    ids_tec = [v.id for v in db.query(VariableTecnico).order_by(VariableTecnico.id).all()]
    base["variables_tecnico"] = [vid in sel_tec_ids for vid in ids_tec][:13] + [""] * max(0, 13 - len(ids_tec))
    base["variables_tecnico_respuestas"] = [res_tec_map.get(vid, "") for vid in ids_tec][:13] + [""] * max(0, 13 - len(ids_tec))
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
# EXCELS (uno por funciÃ³n)
# =========================
def excel_concepto_tecnico_sectorial(db: Session, form_id: int) -> Tuple[BytesIO, str]:
    base_dir = Path(__file__).resolve().parents[2]
    data = _context_excel_concepto(_fetch_base_context(db, form_id))
    now = _now_bogota()
    data["fecha_firma_texto"] = (f"Para constancia se firma el dÃ­a {now.day} del mes de {_spanish_month(now.month)} del aÃ±o {now.year}.")
    dep_nom = (data.get("nombre_dependencia") or "").strip()
    data["firma_secretaria_texto"] = f"Firma del Secretario(a)/Jefe de oficina de {dep_nom}."
    out_path = fill_from_template(base_dir=base_dir, data=data)
    bio = BytesIO(out_path.read_bytes())
    bio.seek(0)
    return bio, out_path.name

def _context_excel_concepto(base: Dict[str, object]) -> Dict[str, object]:
    metas = base.get("metas", [])
    numero_meta = [m["numero"] for m in metas]
    nombre_meta = [m["nombre"] for m in metas]

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

        "variables_sectorial_respuestas": base.get("variables_sectorial_respuestas", []),
        "variables_tecnico_respuestas":  base.get("variables_tecnico_respuestas", []),

        "nombre_politica": [p["nombre"] for p in base.get("politicas", [])][:2],
        "valor_destinado": [p["valor"] for p in base.get("politicas", [])][:2],
        "nombre_categoria": [c["nombre"] for c in base.get("categorias", [])][:2],
        "nombre_focalizaciÃ³n": [s["nombre"] for s in base.get("subcategorias", [])][:2],

        "estructura_financiera": base.get("estructura_financiera", []),
    }
    return data



# =========================
# WORDS (uno por funciÃ³n)
# =========================
TEMPLATE_MAP = {
    "carta": "2.carta_de_presentacion.docx",
    "cert_precios": "4.Certificacion_de_precios.docx",
    "no_doble_cofin": "5.No_doble_cofinanciacion.docx",
}

def word_carta(db: Session, form_id: int) -> Tuple[BytesIO, str]:
    base = _fetch_base_context(db, form_id)
    ctx = _context_word_common(base)
    ctx["gobernador"] = _persona_por_rol(db, "Gobernador")
    ctx["jefe_oap"]   = _persona_por_rol(db, "SecretarÃ­a de PlaneaciÃ³n")
    pl = db.query(PeriodoLema).order_by(PeriodoLema.id.desc()).first()
    if pl:
        ctx["Periodo"] = f"{pl.inicio_periodo}-{pl.fin_periodo}"
        ctx["lema_periodo"] = pl.lema
    else:
        ctx["Periodo"] = ""
        ctx["lema_periodo"] = ""
    ctx.update(_merge_ctx_carta(db, form_id))
    return _render_word("carta", form_id, ctx)

def word_cert_precios(db: Session, form_id: int) -> Tuple[BytesIO, str]:
    base = _fetch_base_context(db, form_id)
    ctx = _context_word_common(base)
    return _render_word("cert_precios", form_id, ctx)

def word_no_doble_cofin(db: Session, form_id: int) -> Tuple[BytesIO, str]:
    base = _fetch_base_context(db, form_id)
    ctx = _context_word_common(base)
    return _render_word("no_doble_cofin", form_id, ctx)


def _context_word_common(base: Dict[str, object]) -> Dict[str, object]:
    now = _now_bogota()
    def _duracion_txt(n: int) -> str:
        try:
            n = int(n or 0)
        except Exception:
            n = 0
        if n <= 0:
            return ""
        return n2w(n, lang="es").capitalize()
    
    ctx = {
        "nombre_proyecto": base["nombre_proyecto"],
        "cod_id_mga": base["cod_id_mga"],
        "nombre_dependencia": base["nombre_dependencia"],

        "nombre_sector": base["nombre_sector"],
        "codigo_sector": base["codigo_sector"],
        "cod_sector":   base["codigo_sector"],
        "nombre_programa": base["nombre_programa"],
        "codigo_programa": base["codigo_programa"],
        "cod_programa":    base["codigo_programa"],
        "nombre_linea_estrategica": base["nombre_linea_estrategica"],
        
        "cargo_responsable": base.get("cargo_responsable") or "",
        "nombre_secretario": base.get("nombre_secretario"),
        "oficina_secretaria": base.get("nombre_dependencia") or "",
        "fuentes": base.get("fuentes") or "",
        "nombre_persona":     base.get("nombre_secretario") or "",

        "programa": base["nombre_programa"],
        "sector":   base["nombre_sector"],

        "cantidad_personas": base.get("cantidad_beneficiarios") or 0,

        "dia": now.day,
        "dia_numero": now.day,
        "dia_texto": _to_day_words(now.day),
        "mes": _spanish_month(now.month),
        "mes_texto": _spanish_month(now.month),
        "anio": now.year,
        "aÃ±o":  now.year,
    }

    ef = base.get("estructura_financiera", [])

    total_propios = 0
    total_sgp = 0

    for r in ef:
        ent = (r.get("entidad") or "").strip().upper()
        val = float(r.get("valor") or 0)

        if ent == "PROPIOS":
            total_propios += val

        if ent.startswith("SGP_"):
            total_sgp += val

    if total_propios > 0 and total_sgp > 0:
        recursos = "Recursos propios y Sistema General de Participaciones"
    elif total_propios > 0:
        recursos = "Recursos propios"
    elif total_sgp > 0:
        recursos = "Sistema General de Participaciones"
    else:
        recursos = ""

    ctx["recursos"] = recursos

    dur = int(base.get("duracion_proyecto") or 0)
    ctx["duracion_numero"] = dur
    ctx["duracion_texto"]  = n2w(dur, lang="es").capitalize() if dur > 0 else ""

    return ctx

def _fmt(v: float) -> str:
    return "" if abs(v) < 0.5 else str(int(round(v)))

def _merge_ctx_carta(db, form_id: int) -> dict:
    rows = db.execute(
        text("""
            SELECT anio, entidad, COALESCE(valor,0)::numeric
            FROM estructura_financiera
            WHERE id_formulario = :fid
        """),
        {"fid": form_id}
    ).fetchall()

    # --- 2) Determinar los 4 aÃ±os ---
    ys = sorted({int(r[0]) for r in rows})
    if len(ys) != 4:
        if ys:
            y0 = min(ys)
            ys = [y0, y0 + 1, y0 + 2, y0 + 3]
        else:
            ys = [2025, 2026, 2027, 2028]
    y1, y2, y3, y4 = ys

    # --- 3) Inicializar contexto base con los aÃ±os ---
    ctx = {
        "anio_1": str(y1),
        "anio_2": str(y2),
        "anio_3": str(y3),
        "anio_4": str(y4),
    }

    # --- 4) Normalizar datos por aÃ±o/entidad ---
    by_year = {y: {} for y in ys}
    for y, ent, val in rows:
        y = int(y)
        ent = str(ent or "").strip().upper()
        by_year.setdefault(y, {})[ent] = float(val or 0.0)

    def _val(y, k):
        return float(by_year.get(y, {}).get(k, 0.0))

    # --- 5) Calcular DEPARTAMENTO = PROPIOS + todos los SGP_* ---
    SGP_KEYS = [
        "SGP_LIBRE_INVERSION", "SGP_LIBRE_DESTINACION", "SGP_APSB",
        "SGP_EDUCACION", "SGP_ALIMENTACION_ESCOLAR", "SGP_CULTURA",
        "SGP_DEPORTE", "SGP_SALUD"
    ]
    dep_por_anio = {y: _val(y, "PROPIOS") + sum(_val(y, k) for k in SGP_KEYS) for y in ys}

    # --- 6) Totales por aÃ±o (sin doble conteo) ---
    tot_por_anio = {
        y: dep_por_anio[y] + _val(y, "MUNICIPIO") + _val(y, "NACION") + _val(y, "OTROS")
        for y in ys
    }

    def _sum_ent(k: str) -> float:
        if k == "DEPARTAMENTO":
            return sum(dep_por_anio[y] for y in ys)
        return sum(_val(y, k) for y in ys)

    # --- 7) Departamento (derivado) ---
    ctx["valor_departamento_1"] = _fmt(dep_por_anio[y1])
    ctx["valor_departamento_2"] = _fmt(dep_por_anio[y2])
    ctx["valor_departamento_3"] = _fmt(dep_por_anio[y3])
    ctx["valor_departamento_4"] = _fmt(dep_por_anio[y4])
    ctx["valor_sum_departamento"] = _fmt(_sum_ent("DEPARTAMENTO"))

    # --- 8) Propios ---
    ctx["valor_propios_1"] = _fmt(_val(y1, "PROPIOS"))
    ctx["valor_propios_2"] = _fmt(_val(y2, "PROPIOS"))
    ctx["valor_propios_3"] = _fmt(_val(y3, "PROPIOS"))
    ctx["valor_propios_4"] = _fmt(_val(y4, "PROPIOS"))
    ctx["valor_sum_propios"] = _fmt(_sum_ent("PROPIOS"))

    # --- 9) SGPs (corto + largo, por compatibilidad con tu plantilla) ---
    sgp_name_map = {
        "SGP_LIBRE_INVERSION":     ("sgp_inver",  "sgp_libre_inversion"),
        "SGP_LIBRE_DESTINACION":   ("sgp_desti",  "sgp_libre_destinacion"),
        "SGP_APSB":                ("sgp_apsb",   "sgp_apsb"),
        "SGP_EDUCACION":           ("sgp_educa",  "sgp_educacion"),
        "SGP_ALIMENTACION_ESCOLAR":("sgp_alimen", "sgp_alimentacion_escolar"),
        "SGP_CULTURA":             ("sgp_cultura","sgp_cultura"),
        "SGP_DEPORTE":             ("sgp_deporte","sgp_deporte"),
        "SGP_SALUD":               ("sgp_salud",  "sgp_salud"),
    }

    for key, (alias_short, alias_long) in sgp_name_map.items():
        v1, v2, v3, v4 = _val(y1, key), _val(y2, key), _val(y3, key), _val(y4, key)
        for alias in [alias_short, alias_long]:
            ctx[f"valor_{alias}_1"] = _fmt(v1)
            ctx[f"valor_{alias}_2"] = _fmt(v2)
            ctx[f"valor_{alias}_3"] = _fmt(v3)
            ctx[f"valor_{alias}_4"] = _fmt(v4)
            ctx[f"valor_sum_{alias}"] = _fmt(_sum_ent(key))

    # Parche de typo: valor_sgp_inve_2 (sin r)
    if "valor_sgp_inver_2" in ctx and "valor_sgp_inve_2" not in ctx:
        ctx["valor_sgp_inve_2"] = ctx["valor_sgp_inver_2"]

    # --- 10) Municipio / NaciÃ³n / Otros ---
    for key, alias in [("MUNICIPIO", "municipio"), ("NACION", "nacion"), ("OTROS", "otros")]:
        ctx[f"valor_{alias}_1"] = _fmt(_val(y1, key))
        ctx[f"valor_{alias}_2"] = _fmt(_val(y2, key))
        ctx[f"valor_{alias}_3"] = _fmt(_val(y3, key))
        ctx[f"valor_{alias}_4"] = _fmt(_val(y4, key))
        ctx[f"valor_sum_{alias}"] = _fmt(_sum_ent(key))

    # --- 11) Totales por periodo y general ---
    ctx["valor_sum_periodo_1"] = _fmt(tot_por_anio[y1])
    ctx["valor_sum_periodo_2"] = _fmt(tot_por_anio[y2])
    ctx["valor_sum_periodo_3"] = _fmt(tot_por_anio[y3])
    ctx["valor_sum_periodo_4"] = _fmt(tot_por_anio[y4])
    total_general = sum(tot_por_anio[y] for y in ys)
    ctx["valor_sum_total"] = _fmt(total_general)

    # --- 12) Costo del proyecto (texto y nÃºmero) ---
    ctx["costo_numero"] = _fmt(total_general).replace(",", "")
    ctx["costo_texto"] = numero_a_texto(total_general)

        # --- 13) Metas / productos / indicadores asociados al formulario ---
    rows = db.execute(text("""
        SELECT m.numero_meta, m.nombre_meta,
               m.codigo_producto, m.nombre_producto,
               m.codigo_indicador_producto, m.nombre_indicador_producto
        FROM metas rel
        JOIN meta m ON m.id = rel.id_meta
        WHERE rel.id_formulario = :fid
        ORDER BY m.numero_meta
    """), {"fid": form_id}).fetchall()

    # Construimos el contexto base de metas
    metas_ctx = [{
        "cod_meta": r[0],
        "meta": r[1],
        "cod_producto": r[2],
        "producto": r[3],
        "cod_indicador_producto": r[4],
        "indicador_producto": r[5],
    } for r in rows]

    # ðŸ”¹ DEDUPLICAR: nos quedamos solo con combinaciones Ãºnicas
    # (meta, producto, indicador) para evitar duplicados en la carta
    vistos = set()
    metas_unicas = []
    for m in metas_ctx:
        llave = (m["cod_meta"], m["cod_producto"], m["cod_indicador_producto"])
        if llave in vistos:
            continue
        vistos.add(llave)
        metas_unicas.append(m)

    metas_ctx = metas_unicas

    # Cargamos tambiÃ©n variables enumeradas por compatibilidad con la plantilla
    for i, m in enumerate(metas_ctx, start=1):
        ctx[f"numero_meta_{i}"] = m["cod_meta"]
        ctx[f"nombre_meta_{i}"] = m["meta"]
        ctx[f"cod_meta_{i}"] = m["cod_meta"]
        ctx[f"meta_{i}"] = m["meta"]
        ctx[f"cod_producto_{i}"] = m["cod_producto"]
        ctx[f"producto_{i}"] = m["producto"]
        ctx[f"cod_indicador_producto_{i}"] = m["cod_indicador_producto"]
        ctx[f"indicador_producto_{i}"] = m["indicador_producto"]

    # Contexto de metas que usa word_fill._expand_table1_and_table3
    ctx["__metas_ctx__"] = metas_ctx

    # Variables "planas" (sin Ã­ndice) para el primer producto/meta
    if metas_ctx:
        first = metas_ctx[0]
        ctx["cod_meta"] = first["cod_meta"]
        ctx["meta"] = first["meta"]
        ctx["producto"] = first["producto"]
        ctx["cod_producto"] = first["cod_producto"]
        ctx["indicador_producto"] = first["indicador_producto"]
        ctx["cod_indicador_producto"] = first["cod_indicador_producto"]

    return ctx


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

def _persona_por_rol(db: Session, rol: str) -> str:
    row = db.execute(text("SELECT nombre FROM personas WHERE LOWER(rol)=LOWER(:r) LIMIT 1"), {"r": rol}).first()
    return row[0] if row else ""

def word_formulario(db: Session, form_id: int, doc: str, extras: Optional[Dict[str, object]] = None) -> Tuple[BytesIO, str]:
    if doc == "carta":
        return word_carta(db, form_id)
    if doc == "cert_precios":
        return word_cert_precios(db, form_id)
    if doc == "no_doble_cofin":
        return word_no_doble_cofin(db, form_id)
    raise ValueError("Documento no soportado")

def excel_cadena_valor(db: Session, form_id: int) -> Tuple[BytesIO, str]:
    base_dir = Path(__file__).resolve().parents[2]
    base = _fetch_base_context(db, form_id)
    now = _now_bogota()

    metas_base = base.get("metas", []) or []
    metas = [
        {
            "numero_meta": m.get("numero"),
            "nombre_meta": m.get("nombre"),
        }
        for m in metas_base
    ]

    data = {
        "nombre_proyecto": base["nombre_proyecto"],
        "cod_id_mga": base["cod_id_mga"],
        "fecha_actual": f"{now.day} de {_spanish_month(now.month)} del {now.year}",
        "metas": metas,
    }

    out_path = fill_cadena_valor(base_dir=base_dir, data=data)
    bio = BytesIO(out_path.read_bytes())
    bio.seek(0)
    return bio, out_path.name

def excel_viabilidad_dependencias(db: Session, form_id: int) -> Tuple[BytesIO, str]:
    base_dir = Path(__file__).resolve().parents[2]
    base = _fetch_base_context(db, form_id)

    # 1) Metas asociadas al formulario
    metas = [
        {
            "numero_meta": m.numero_meta,
            "nombre_meta": m.nombre_meta,
            "codigo_producto": m.codigo_producto,
            "nombre_producto": m.nombre_producto,
            "codigo_indicador_producto": m.codigo_indicador_producto,
            "nombre_indicador_producto": m.nombre_indicador_producto,
        }
        for m in (
            db.query(Meta)
            .join(Metas, Metas.id_meta == Meta.id)
            .filter(Metas.id_formulario == form_id)
            .order_by(Meta.numero_meta)
            .all()
        )
    ]

    now = _now_bogota()

    # 2) Estructura financiera â†’ aÃ±os y lookup
    ef = base.get("estructura_financiera", [])
    years = sorted({r["anio"] for r in ef if r.get("anio")})[:4]
    while len(years) < 4:
        years.append(None)

    lookup = {
        (r["anio"], (r["entidad"] or "").strip().upper()): r["valor"]
        for r in ef
        if r.get("entidad")
    }

    # 3) Viabilidades seleccionadas
    viabilidades_respuestas = proyecto_service.leer_respuestas_viab(db, form_id)

    # 4) Funcionarios que certifican viabilidad
    funcs = {
        f.id_tipo_viabilidad: f
        for f in db.query(FuncionarioViabilidad)
        .filter(FuncionarioViabilidad.id_formulario == form_id)
        .all()
    }

    # Detectar si existe meta 411
    tiene_meta_411 = False
    for m in metas:   # metas viene del formulario y ya existe aquÃ­
        try:
            if int(m.get("numero_meta")) == 411:
                tiene_meta_411 = True
                break
        except:
            pass
    proyecto_fortalecimiento = "SI" if tiene_meta_411 else "NO"

    # 5) Armar data para el llenado del Excel
    data = {
        "dependencia": base["nombre_dependencia"],
        "nombre_proyecto": base["nombre_proyecto"],
        "cod_id_mga": base["cod_id_mga"],
        "anios": years,
        "estructura_financiera": lookup,
        "viabilidades_respuestas": viabilidades_respuestas,
        "funcionarios": funcs,
        "nombre_secretario": base["nombre_secretario"],
        "fecha_actual": f"{now.day} de {_spanish_month(now.month)} del {now.year}",
        "metas": metas,
        "proyecto_fortalecimiento": proyecto_fortalecimiento,
    }

    out_path = fill_viabilidad_dependencias(base_dir=base_dir, data=data)
    bio = BytesIO(out_path.read_bytes())
    bio.seek(0)
    return bio, out_path.name


_EVAL_TEMPLATE_MAP = {
    "observaciones": "observaciones.html",
    "viabilidad": "viabilidad.html",
}


def _fmt_money_eval(v: float | int | None) -> str:
    try:
        n = float(v or 0)
    except Exception:
        n = 0.0
    if abs(n) < 0.005:
        return ""
    return f"{n:,.0f}".replace(",", ".")


def _fmt_fecha_doc_es(d) -> str:
    if not d:
        return ""
    try:
        day = int(getattr(d, "day"))
        month = int(getattr(d, "month"))
        year = int(getattr(d, "year"))
    except Exception:
        return str(d)
    mes = _spanish_month(month)
    if mes:
        mes = mes.capitalize()
    return f"{day:02d}-{mes}-{year}"


def _years_and_lookup(estructura_financiera: list[dict]) -> tuple[list[int], dict[tuple[int, str], float]]:
    years = sorted({int(r.get("anio")) for r in estructura_financiera if r.get("anio") is not None})
    if not years:
        now = _now_bogota()
        years = [now.year, now.year + 1, now.year + 2, now.year + 3]
    while len(years) < 4:
        years.append(years[-1] + 1)
    years = years[:4]

    lookup: dict[tuple[int, str], float] = {}
    for r in estructura_financiera:
        anio = r.get("anio")
        ent = (r.get("entidad") or "").strip().upper()
        if anio is None or not ent:
            continue
        try:
            lookup[(int(anio), ent)] = float(r.get("valor") or 0)
        except Exception:
            lookup[(int(anio), ent)] = 0.0
    return years, lookup


def _build_eval_tokens(base: dict, nombre_evaluador: str, cargo_evaluador: str = "") -> dict[str, str]:
    ef = base.get("estructura_financiera", []) or []
    years, lookup = _years_and_lookup(ef)

    def get_val(y: int, ent: str) -> float:
        return float(lookup.get((y, ent), 0.0))

    nacion = [get_val(y, "NACION") for y in years]
    depto = [get_val(y, "DEPARTAMENTO") for y in years]
    muni = [get_val(y, "MUNICIPIO") for y in years]
    otros = [get_val(y, "OTROS") for y in years]
    subtotal = [nacion[i] + depto[i] + muni[i] + otros[i] for i in range(4)]

    now = _now_bogota()
    fecha_default = _fmt_fecha_doc_es(now)
    fecha_radic = base.get("fecha_radicacion")
    if fecha_radic:
        fecha_rad_txt = _fmt_fecha_doc_es(fecha_radic)
    else:
        fecha_rad_txt = fecha_default
    programa_txt = " - ".join(
        [x for x in [str(base.get("codigo_programa") or "").strip(), str(base.get("nombre_programa") or "").strip()] if x]
    )
    sector_txt = " - ".join(
        [x for x in [str(base.get("codigo_sector") or "").strip(), str(base.get("nombre_sector") or "").strip()] if x]
    )
    dependencia = str(base.get("nombre_dependencia") or "").strip()

    tokens: dict[str, str] = {
        "proyecto": str(base.get("nombre_proyecto") or ""),
        "programa": programa_txt,
        "municipio": "Cauca",
        "cod_rad": str(base.get("numero_radicacion") or ""),
        "fecha_rad": fecha_rad_txt,
        "sector": sector_txt,
        "fecha_etapa": fecha_rad_txt,
        "folios": str(base.get("soportes_folios") or 0),
        "planos": str(base.get("soportes_planos") or 0),
        "cds": str(base.get("soportes_cds") or 0),
        "otros_adj": str(base.get("soportes_otros") or 0),
        "pb_municipios": "0",
        "pb_personas": str(base.get("cantidad_beneficiarios") or ""),
        "pb_viviendas": "0",
        "pb_afro": "0",
        "pb_indigena": "0",
        "dependencia_p": dependencia,
        "ssepi": str(base.get("bpin") or "Por definir"),
        "nombre": (nombre_evaluador or "").strip(),
        "cargo_evaluador": (cargo_evaluador or "").strip(),
        "dependencia": "Secretaría de Planeación",
    }

    for i in range(4):
        idx = i + 1
        tokens[f"f_vig_nac{idx}"] = _fmt_money_eval(nacion[i])
        tokens[f"f_vig_dep{idx}"] = _fmt_money_eval(depto[i])
        tokens[f"f_vig_mun{idx}"] = _fmt_money_eval(muni[i])
        tokens[f"f_vig_otr{idx}"] = _fmt_money_eval(otros[i])
        tokens[f"f_vig_tot{idx}"] = _fmt_money_eval(subtotal[i])
        tokens[f"f_tot{idx}"] = _fmt_money_eval(subtotal[i])

    tokens["f_vig_nac5"] = _fmt_money_eval(sum(nacion))
    tokens["f_vig_dep5"] = _fmt_money_eval(sum(depto))
    tokens["f_vig_mun5"] = _fmt_money_eval(sum(muni))
    tokens["f_vig_otr5"] = _fmt_money_eval(sum(otros))
    tokens["f_vig_tot5"] = _fmt_money_eval(sum(subtotal))
    tokens["f_tot5"] = _fmt_money_eval(sum(subtotal))
    return tokens


def _replace_tokens_in_html(html: str, tokens: dict[str, str]) -> str:
    out = html
    for k, v in tokens.items():
        out = out.replace(f"${k}", v)
    out = re.sub(r"\$[a-zA-Z0-9_]+", "", out)
    return out


def _inject_section_html(template_html: str, heading_text: str, content_html: str) -> str:
    pattern = re.compile(
        rf"(<th[^>]*>\s*{re.escape(heading_text)}\s*</th>\s*</tr>\s*<tr>\s*<td[^>]*>)(.*?)(</td>\s*</tr>)",
        re.IGNORECASE | re.DOTALL,
    )
    return pattern.sub(rf"\1{content_html}\3", template_html, count=1)


def _inject_viabilidad_checks(
    template_html: str,
    concepto_tecnico_dep: str | None,
    concepto_sectorial_dep: str | None,
    proyecto_viable_dep: str | None,
) -> str:
    def _mark(v: str | None, want: str) -> str:
        return "X" if (v or "").strip().upper() == want else "&nbsp;"

    rows = [
        ("CONCEPTO TECNICO FAVORABLE", concepto_tecnico_dep),
        ("CONCEPTO SECTORIAL FAVORABLE", concepto_sectorial_dep),
        ("EL PROYECTO ES VIABLE", proyecto_viable_dep),
    ]
    out = template_html
    for label, val in rows:
        row_html = (
            f"<tr>"
            f"<td style=\"width: 35%;\">{label}</td>"
            f"<td class=\"c\" style=\"width: 10%;\">&nbsp;</td>"
            f"<td class=\"c\" style=\"width: 10%;\">&nbsp;</td>"
            f"<td class=\"c\" style=\"width: 12%;\">{_mark(val, 'SI')}</td>"
            f"<td class=\"c\" style=\"width: 13%;\">{_mark(val, 'NO')}</td>"
            f"<td class=\"c\" style=\"width: 10%;\">&nbsp;</td>"
            f"<td class=\"c\" style=\"width: 10%;\">&nbsp;</td>"
            f"</tr>"
        )
        pat = re.compile(
            rf"<tr>\s*<td[^>]*>\s*{re.escape(label)}\s*</td>.*?</tr>",
            re.IGNORECASE | re.DOTALL,
        )
        out = pat.sub(row_html, out, count=1)
    return out


def _inject_viabilidad_productos(template_html: str, metas: list[dict]) -> str:
    filas = metas[:8] if metas else []
    if not filas:
        return template_html

    rows_html = ""
    for m in filas:
        rows_html += (
            "<tr>"
            f"<td class=\"d\" style=\"width:140px\">{m.get('codigo_producto') or ''}</td>"
            f"<td class=\"d\" style=\"width:140px\">{m.get('nombre_producto') or ''}</td>"
            f"<td class=\"d\" style=\"width:140px\">&nbsp;</td>"
            f"<td class=\"d\" style=\"width:140px\">{m.get('codigo_indicador_producto') or ''}</td>"
            f"<td class=\"d\" style=\"width:140px\">{m.get('nombre_indicador_producto') or ''}</td>"
            f"<td class=\"d\" style=\"width:140px\">{m.get('nombre') or ''}</td>"
            f"<td class=\"d\" style=\"width:140px\">{m.get('numero') or ''}</td>"
            f"<td class=\"d\" style=\"width:140px\">&nbsp;</td>"
            "</tr>"
        )

    pat = re.compile(
        r"(<table\s+class=\"tbl\"[^>]*>\s*<thead>.*?CODIGO DE PRODUCTO.*?</thead>\s*<tbody>)(.*?)(</tbody>\s*</table>)",
        re.IGNORECASE | re.DOTALL,
    )
    return pat.sub(rf"\1{rows_html}\3", template_html, count=1)


def _inject_cargo_evaluador(template_html: str, cargo: str) -> str:
    cargo_txt = (cargo or "").strip()
    if not cargo_txt:
        return template_html
    pat = re.compile(
        r"(<tr>\s*<th[^>]*>\s*CARGO\s*</th>\s*<td[^>]*>)(.*?)(</td>\s*<td[^>]*>Profesional Universitario</td>\s*</tr>)",
        re.IGNORECASE | re.DOTALL,
    )
    return pat.sub(rf"\1{cargo_txt}\3", template_html, count=1)


def _logo_data_uri(base_dir: Path) -> str:
    candidates = list(base_dir.glob("Logo-sec-planeacion.png"))
    if not candidates:
        return ""
    try:
        raw = candidates[0].read_bytes()
        b64 = base64.b64encode(raw).decode("ascii")
        return f"data:image/png;base64,{b64}"
    except Exception:
        return ""


def render_evaluador_template_html(
    db: Session,
    form_id: int,
    template_key: str,
    contenido_html: str,
    nombre_evaluador: str,
    cargo_evaluador: str | None = None,
    concepto_tecnico_favorable_dep: str | None = None,
    concepto_sectorial_favorable_dep: str | None = None,
    proyecto_viable_dep: str | None = None,
) -> tuple[str, str]:
    filled, file_name, base_dir = _render_evaluador_filled_content(
        db=db,
        form_id=form_id,
        template_key=template_key,
        contenido_html=contenido_html,
        nombre_evaluador=nombre_evaluador,
        cargo_evaluador=cargo_evaluador,
        concepto_tecnico_favorable_dep=concepto_tecnico_favorable_dep,
        concepto_sectorial_favorable_dep=concepto_sectorial_favorable_dep,
        proyecto_viable_dep=proyecto_viable_dep,
    )

    logo_uri = _logo_data_uri(base_dir)
    logo_html = f"<img src=\"{logo_uri}\" alt=\"Logo Gobernacion\" />" if logo_uri else ""
    full_html = (
        "<!doctype html><html><head><meta charset='utf-8'/>"
        "<title> </title>"
        "<style>"
        "@page{margin:26mm 8mm 22mm 8mm;}"
        "body{margin:0;padding:0;background:#fff;}"
        ".doc-shell{max-width:730px;margin:0 auto;}"
        ".doc-header{text-align:center;margin:0;line-height:1;}"
        ".doc-header img{width:120px;max-width:30vw;height:auto;display:inline-block;}"
        ".doc-content{display:block;}"
        ".doc-footer{text-align:center;font-size:11px;line-height:1.35;margin:0;page-break-inside:avoid;}"
        ".doc-footer .nota{font-weight:700;}"
        "@media print{"
        "  body{padding:0 !important;}"
        "  .doc-header{position:fixed;top:0mm;left:0;right:0;margin:0;z-index:10;}"
        "  .doc-footer{position:fixed;bottom:0mm;left:0;right:0;margin:0;z-index:10;}"
        "  .doc-shell{max-width:730px;margin:0 auto;}"
        "}"
        "</style>"
        "</head><body>"
        "<div class='doc-shell'>"
        f"<div class='doc-header'>{logo_html}</div>"
        f"<div class='doc-content'>{filled}</div>"
        "<div class='doc-footer'>"
        "<div><span class='nota'>Nota:</span> Este documento NO es valido como certificacion</div>"
        "<div>Calle 4 Carrera 7 Esquina Quinto piso</div>"
        "<div>Telefonos 8244515 - 8242973</div>"
        "</div>"
        "</div>"
        "</body></html>"
    )
    return full_html, file_name


def _render_evaluador_filled_content(
    db: Session,
    form_id: int,
    template_key: str,
    contenido_html: str,
    nombre_evaluador: str,
    cargo_evaluador: str | None = None,
    concepto_tecnico_favorable_dep: str | None = None,
    concepto_sectorial_favorable_dep: str | None = None,
    proyecto_viable_dep: str | None = None,
) -> tuple[str, str, Path]:
    if template_key not in _EVAL_TEMPLATE_MAP:
        raise ValueError("Template no soportado")

    base_dir = Path(__file__).resolve().parents[2]
    template_path = base_dir / _EVAL_TEMPLATE_MAP[template_key]
    if not template_path.exists():
        raise ValueError(f"No existe plantilla: {_EVAL_TEMPLATE_MAP[template_key]}")

    base = _fetch_base_context(db, form_id)
    tokens = _build_eval_tokens(base, nombre_evaluador, cargo_evaluador or "")
    raw = template_path.read_text(encoding="utf-8", errors="ignore")
    filled = _replace_tokens_in_html(raw, tokens)

    heading = (
        "EVALUANDO EL PROYECTO, SE HACEN LAS SIGUIENTES OBSERVACIONES"
        if template_key == "observaciones"
        else "MOTIVACION DE LA VIABILIDAD"
    )
    filled = _inject_section_html(filled, heading, contenido_html)
    if template_key == "viabilidad":
        filled = _inject_viabilidad_checks(
            filled,
            concepto_tecnico_dep=concepto_tecnico_favorable_dep,
            concepto_sectorial_dep=concepto_sectorial_favorable_dep,
            proyecto_viable_dep=proyecto_viable_dep,
        )
        filled = _inject_viabilidad_productos(filled, base.get("metas", []) or [])
    filled = _inject_cargo_evaluador(filled, cargo_evaluador or "")

    file_name = "observaciones.pdf" if template_key == "observaciones" else "viabilidad.pdf"
    return filled, file_name, base_dir


def render_evaluador_template_pdf(
    db: Session,
    form_id: int,
    template_key: str,
    contenido_html: str,
    nombre_evaluador: str,
    concepto_tecnico_favorable_dep: str | None = None,
    concepto_sectorial_favorable_dep: str | None = None,
    proyecto_viable_dep: str | None = None,
) -> tuple[BytesIO, str]:
    filled, file_name, base_dir = _render_evaluador_filled_content(
        db=db,
        form_id=form_id,
        template_key=template_key,
        contenido_html=contenido_html,
        nombre_evaluador=nombre_evaluador,
        concepto_tecnico_favorable_dep=concepto_tecnico_favorable_dep,
        concepto_sectorial_favorable_dep=concepto_sectorial_favorable_dep,
        proyecto_viable_dep=proyecto_viable_dep,
    )

    try:
        from playwright.sync_api import sync_playwright
    except Exception as e:
        raise ValueError(f"Playwright no disponible para PDF: {e}")

    logo_uri = _logo_data_uri(base_dir)
    header_logo = f"<div style='width:100%;text-align:center;'><img src='{logo_uri}' style='height:76px;' /></div>" if logo_uri else "<div></div>"
    footer_html = (
        "<div style='width:100%;font-size:9px;text-align:center;line-height:1.2;'>"
        "<div><b>Nota:</b> Este documento NO es valido como certificacion</div>"
        "<div>Calle 4 Carrera 7 Esquina Quinto piso</div>"
        "<div>Telefonos 8244515 - 8242973</div>"
        "</div>"
    )

    html = (
        "<!doctype html><html><head><meta charset='utf-8'/>"
        "<style>@page{size:A4;} body{margin:0;padding:0;} .doc{max-width:730px;margin:0 auto;}</style>"
        "</head><body>"
        f"<div class='doc'>{filled}</div>"
        "</body></html>"
    )

    try:
        with sync_playwright() as p:
            executable = p.chromium.executable_path
            if not executable or not Path(executable).exists():
                raise ValueError(
                    "Chromium de Playwright no instalado. Ejecuta: python -m playwright install chromium"
                )
            browser = p.chromium.launch()
            page = browser.new_page()
            page.set_content(html, wait_until="networkidle")
            pdf_bytes = page.pdf(
                format="A4",
                print_background=True,
                display_header_footer=True,
                header_template=header_logo,
                footer_template=footer_html,
                margin={"top": "36mm", "bottom": "28mm", "left": "8mm", "right": "8mm"},
            )
            browser.close()
    except Exception as e:
        raise ValueError(f"Fallo Playwright al generar PDF: {repr(e)}")

    bio = BytesIO(pdf_bytes)
    bio.seek(0)
    return bio, file_name


async def render_evaluador_template_pdf_async(
    db: Session,
    form_id: int,
    template_key: str,
    contenido_html: str,
    nombre_evaluador: str,
    cargo_evaluador: str | None = None,
    concepto_tecnico_favorable_dep: str | None = None,
    concepto_sectorial_favorable_dep: str | None = None,
    proyecto_viable_dep: str | None = None,
) -> tuple[BytesIO, str]:
    filled, file_name, base_dir = _render_evaluador_filled_content(
        db=db,
        form_id=form_id,
        template_key=template_key,
        contenido_html=contenido_html,
        nombre_evaluador=nombre_evaluador,
        cargo_evaluador=cargo_evaluador,
        concepto_tecnico_favorable_dep=concepto_tecnico_favorable_dep,
        concepto_sectorial_favorable_dep=concepto_sectorial_favorable_dep,
        proyecto_viable_dep=proyecto_viable_dep,
    )

    logo_uri = _logo_data_uri(base_dir)
    header_logo = f"<div style='width:100%;text-align:center;'><img src='{logo_uri}' style='height:76px;' /></div>" if logo_uri else "<div></div>"
    footer_html = (
        "<div style='width:100%;font-size:9px;text-align:center;line-height:1.2;'>"
        "<div><b>Nota:</b> Este documento NO es valido como certificacion</div>"
        "<div>Calle 4 Carrera 7 Esquina Quinto piso</div>"
        "<div>Telefonos 8244515 - 8242973</div>"
        "</div>"
    )
    html = (
        "<!doctype html><html><head><meta charset='utf-8'/>"
        "<style>@page{size:A4;} body{margin:0;padding:0;} .doc{max-width:730px;margin:0 auto;}</style>"
        "</head><body>"
        f"<div class='doc'>{filled}</div>"
        "</body></html>"
    )

    try:
        pdf_bytes = await asyncio.to_thread(
            _generate_pdf_sync_playwright,
            html,
            header_logo,
            footer_html,
        )
    except Exception as e:
        raise ValueError(f"Fallo Playwright al generar PDF: {repr(e)}")

    bio = BytesIO(pdf_bytes)
    bio.seek(0)
    return bio, file_name


def _generate_pdf_sync_playwright(html: str, header_logo: str, footer_html: str) -> bytes:
    try:
        if sys.platform.startswith("win"):
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        from playwright.sync_api import sync_playwright
    except Exception as e:
        raise ValueError(f"Playwright no disponible para PDF: {e}")

    with sync_playwright() as p:
        executable = p.chromium.executable_path
        if not executable or not Path(executable).exists():
            raise ValueError(
                "Chromium de Playwright no instalado. Ejecuta: python -m playwright install chromium"
            )
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content(html, wait_until="networkidle")
        pdf_bytes = page.pdf(
            format="A4",
            print_background=True,
            display_header_footer=True,
            header_template=header_logo,
            footer_template=footer_html,
            margin={"top": "30mm", "bottom": "30mm", "left": "8mm", "right": "8mm"},
        )
        browser.close()
    return pdf_bytes

