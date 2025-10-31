from __future__ import annotations
from collections import defaultdict
from decimal import Decimal
from io import BytesIO
from pathlib import Path
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
        "id_dependencia": form.id_dependencia,
        "nombre_dependencia": dep_nom or "",
        "codigo_sector": sec_cod or "",
        "nombre_sector": sec_nom or "",
        "codigo_programa": prog_cod or "",
        "nombre_programa": prog_nom or "",
        "nombre_linea_estrategica": linea_nom or "",
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
    base["metas"] = [{"numero": m.numero_meta, "nombre": m.nombre_meta} for m in metas]
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

    # ========== Variables TÉCNICO ==========
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
# EXCELS (uno por función)
# =========================
def excel_concepto_tecnico_sectorial(db: Session, form_id: int) -> Tuple[BytesIO, str]:
    base_dir = Path(__file__).resolve().parents[2]
    data = _context_excel_concepto(_fetch_base_context(db, form_id))
    now = _now_bogota()
    data["fecha_firma_texto"] = (f"Para constancia se firma el día {now.day} del mes de {_spanish_month(now.month)} del año {now.year}.")
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
        "nombre_focalización": [s["nombre"] for s in base.get("subcategorias", [])][:2],

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
    ctx["gobernador"] = _persona_por_rol(db, "Gobernador")
    ctx["jefe_oap"]   = _persona_por_rol(db, "Jefe OAP")
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
        "año":  now.year,
    }
    
    dur = int(base.get("duracion_proyecto") or 0)
    ctx["duracion_numero"] = dur
    ctx["duracion_texto"]  = n2w(dur, lang="es").capitalize() if dur > 0 else ""

    return ctx

def _fmt(v: float) -> str:
    return "" if abs(v) < 0.005 else f"{v:.2f}"

def _merge_ctx_carta(db, form_id: int) -> dict:
    rows = db.execute(
        text("""
            SELECT anio, entidad, COALESCE(valor,0)::numeric
            FROM estructura_financiera
            WHERE id_formulario = :fid
        """),
        {"fid": form_id}
    ).fetchall()

    # --- 2) Determinar los 4 años ---
    ys = sorted({int(r[0]) for r in rows})
    if len(ys) != 4:
        if ys:
            y0 = min(ys)
            ys = [y0, y0 + 1, y0 + 2, y0 + 3]
        else:
            ys = [2025, 2026, 2027, 2028]
    y1, y2, y3, y4 = ys

    # --- 3) Inicializar contexto base con los años ---
    ctx = {
        "anio_1": str(y1),
        "anio_2": str(y2),
        "anio_3": str(y3),
        "anio_4": str(y4),
    }

    # --- 4) Normalizar datos por año/entidad ---
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

    # --- 6) Totales por año (sin doble conteo) ---
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

    # --- 10) Municipio / Nación / Otros ---
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

    # --- 12) Costo del proyecto (texto y número) ---
    ctx["costo_numero"] = _fmt(total_general).replace(",", "")
    ctx["costo_texto"] = numero_a_texto(total_general)

    rows = db.execute(text("""
        SELECT m.numero_meta, m.nombre_meta,
               m.codigo_producto, m.nombre_producto,
               m.codigo_indicador_producto, m.nombre_indicador_producto
        FROM metas rel
        JOIN meta m ON m.id = rel.id_meta
        WHERE rel.id_formulario = :fid
        ORDER BY m.numero_meta
    """), {"fid": form_id}).fetchall()
    metas_ctx = [{
        "cod_meta": r[0],
        "meta": r[1],
        "cod_producto": r[2],
        "producto": r[3],
        "cod_indicador_producto": r[4],
        "indicador_producto": r[5],
    } for r in rows]
    for i, m in enumerate(metas_ctx, start=1):
        ctx[f"numero_meta_{i}"] = m["cod_meta"]
        ctx[f"nombre_meta_{i}"] = m["meta"]
        ctx[f"cod_meta_{i}"] = m["cod_meta"]
        ctx[f"meta_{i}"] = m["meta"]
        ctx[f"cod_producto_{i}"] = m["cod_producto"]
        ctx[f"producto_{i}"] = m["producto"]
        ctx[f"cod_indicador_producto_{i}"] = m["cod_indicador_producto"]
        ctx[f"indicador_producto_{i}"] = m["indicador_producto"]
    ctx["__metas_ctx__"] = metas_ctx
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

    data = {
        "nombre_proyecto": base["nombre_proyecto"],
        "cod_id_mga": base["cod_id_mga"],
        "fecha_actual": f"{now.day} de {_spanish_month(now.month)} del {now.year}",
    }

    out_path = fill_cadena_valor(base_dir=base_dir, data=data)
    bio = BytesIO(out_path.read_bytes())
    bio.seek(0)
    return bio, out_path.name

def excel_viabilidad_dependencias(db: Session, form_id: int) -> Tuple[BytesIO, str]:
    base_dir = Path(__file__).resolve().parents[2]
    base = _fetch_base_context(db, form_id)
    now = _now_bogota()

    ef = base.get("estructura_financiera", [])
    years = sorted({r["anio"] for r in ef if r.get("anio")})[:4]
    while len(years) < 4: years.append(None)

    ENT_ORDER = [
        "PROPIOS", "SGP_LIBRE_INVERSION", "SGP_LIBRE_DESTINACION", "SGP_APSB",
        "SGP_EDUCACION", "SGP_ALIMENTACION_ESCOLAR", "SGP_CULTURA",
        "SGP_DEPORTE", "SGP_SALUD", "MUNICIPIO", "NACION", "OTROS"
    ]
    lookup = {(r["anio"], r["entidad"].strip().upper()): r["valor"] for r in ef if r.get("entidad")}

    viabilidades = [v.id for v in db.query(Viabilidad)
    .join(Viabilidades, Viabilidades.id_viabilidad == Viabilidad.id)
    .filter(Viabilidades.id_formulario == form_id)
    .all()]
    funcs = {f.id_tipo_viabilidad: f for f in db.query(FuncionarioViabilidad)
        .filter(FuncionarioViabilidad.id_formulario == form_id).all()}

    data = {
        "dependencia": base["nombre_dependencia"],
        "nombre_proyecto": base["nombre_proyecto"],
        "cod_id_mga": base["cod_id_mga"],
        "anios": years,
        "estructura_financiera": lookup,
        "viabilidades": viabilidades,
        "funcionarios": funcs,
        "nombre_secretario": base["nombre_secretario"],
        "fecha_actual": f"{now.day} de {_spanish_month(now.month)} del {now.year}",
    }

    out_path = fill_viabilidad_dependencias(base_dir=base_dir, data=data)
    bio = BytesIO(out_path.read_bytes())
    bio.seek(0)
    return bio, out_path.name
