from pathlib import Path
from typing import Optional, List, Tuple
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter, coordinate_to_tuple
from openpyxl.worksheet.worksheet import Worksheet
import copy
import re

TEMPLATE_NAME = "3_y_4_Concepto_tecnico_y_sectorial_2025.xlsx"
OUTPUT_PATTERN = "{}_3_y_4_Concepto_tecnico_y_sectorial_2025.xlsx"


def _next_sequential_index(out_dir: Path) -> int:
    rx = re.compile(r"^(\d+)_3_y_4_Concepto_tecnico_y_sectorial_2025\.xlsx$", re.I)
    max_n = 0
    for p in out_dir.glob("*_3_y_4_Concepto_tecnico_y_sectorial_2025.xlsx"):
        m = rx.match(p.name)
        if m:
            try:
                n = int(m.group(1))
                if n > max_n:
                    max_n = n
            except ValueError:
                pass
    return max_n + 1


# ---------- Escritura segura sobre celdas combinadas ----------
def _anchor_of_merged(ws: Worksheet, coord: str) -> str:
    r, c = coordinate_to_tuple(coord)
    for mr in ws.merged_cells.ranges:
        if mr.min_row <= r <= mr.max_row and mr.min_col <= c <= mr.max_col:
            return ws.cell(row=mr.min_row, column=mr.min_col).coordinate
    return coord

def _write(ws: Worksheet, coord: str, value):
    ws[_anchor_of_merged(ws, coord)] = value


# ---------- Utilidades: estilos / merges por bloque ----------
def _copy_row_style(ws: Worksheet, src_row: int, dst_row: int):
    ws.row_dimensions[dst_row].height = ws.row_dimensions[src_row].height
    max_col = ws.max_column
    for col in range(1, max_col + 1):
        s = ws.cell(row=src_row, column=col)
        d = ws.cell(row=dst_row, column=col)
        if s.has_style:
            d.font = copy.copy(s.font)
            d.border = copy.copy(s.border)
            d.fill = copy.copy(s.fill)
            d.number_format = s.number_format
            d.protection = copy.copy(s.protection)
            d.alignment = copy.copy(s.alignment)

def _get_block_merges(ws: Worksheet, src_start: int, src_end: int) -> List[Tuple[int, int, int, int]]:
    out: List[Tuple[int, int, int, int]] = []
    for mr in ws.merged_cells.ranges:
        if mr.min_row >= src_start and mr.max_row <= src_end:
            out.append((mr.min_row, mr.min_col, mr.max_row, mr.max_col))
    return out

def _apply_block_merges(ws: Worksheet, merges: List[Tuple[int, int, int, int]], dst_start: int, src_start: int):
    off = dst_start - src_start
    for r1, c1, r2, c2 in merges:
        ws.merge_cells(start_row=r1 + off, start_column=c1, end_row=r2 + off, end_column=c2)

def _clone_block_styles_merges(ws: Worksheet, src_start: int, src_end: int, dst_start: int, merges_cache=None):
    for i in range(src_end - src_start + 1):
        _copy_row_style(ws, src_start + i, dst_start + i)
    merges = merges_cache if merges_cache is not None else _get_block_merges(ws, src_start, src_end)
    _apply_block_merges(ws, merges, dst_start, src_start)


# ---------- Detectar anclas de rótulo/valor ----------
def _find_label_anchor(ws: Worksheet, row: int, text: str):
    """Devuelve (row, col) de la celda cuyo valor coincide exactamente con 'text' en esa fila."""
    for col in range(1, ws.max_column + 1):
        if (ws.cell(row=row, column=col).value or "") == text:
            return (row, col)
    return None

def _find_value_anchor_col_for_row(ws: Worksheet, row: int, label_col: Optional[int]) -> int:
    """
    En la 'row', devuelve la columna ancla del primer merge horizontal que NO cubre la columna del rótulo.
    Si no hay merges, usa 3 (columna 'C').
    """
    candidates = []
    for mr in ws.merged_cells.ranges:
        if mr.min_row == row and mr.max_row == row:
            candidates.append(mr)
    candidates.sort(key=lambda r: (r.max_col - r.min_col, r.min_col), reverse=True)
    for mr in candidates:
        if label_col is None or not (mr.min_col <= label_col <= mr.max_col):
            return mr.min_col
    return 3 


# ---------- Utilidades: mover rango grande (simular “Insert Copied Cells”) ----------
def _collect_merges_in_rows(ws: Worksheet, start_row: int) -> List[Tuple[int, int, int, int]]:
    """Merges cuyo min_row >= start_row (todo lo que está desde start_row hacia abajo)."""
    out: List[Tuple[int, int, int, int]] = []
    for mr in ws.merged_cells.ranges:
        if mr.min_row >= start_row:
            out.append((mr.min_row, mr.min_col, mr.max_row, mr.max_col))
    return out

def _unmerge_ranges(ws: Worksheet, ranges: List[Tuple[int, int, int, int]]):
    for r1, c1, r2, c2 in ranges:
        try:
            ws.unmerge_cells(start_row=r1, start_column=c1, end_row=r2, end_column=c2)
        except Exception:
            pass

def _remerge_with_offset(ws: Worksheet, ranges: List[Tuple[int, int, int, int]], row_off: int):
    for r1, c1, r2, c2 in ranges:
        ws.merge_cells(start_row=r1 + row_off, start_column=c1, end_row=r2 + row_off, end_column=c2)

def _move_down_from_row(ws: Worksheet, start_row: int, row_off: int):
    """Mueve TODO desde start_row hacia abajo 'row_off' filas, preservando merges y alturas."""
    if row_off <= 0:
        return
    max_col_letter = get_column_letter(ws.max_column)
    max_row = ws.max_row
    heights = {r: ws.row_dimensions[r].height for r in range(start_row, max_row + 1)}
    merges = _collect_merges_in_rows(ws, start_row)
    _unmerge_ranges(ws, merges)
    ws.move_range(f"A{start_row}:{max_col_letter}{max_row}", rows=row_off, cols=0, translate=True)
    for r, h in heights.items():
        ws.row_dimensions[r + row_off].height = h
    _remerge_with_offset(ws, merges, row_off)


def fill_from_template(
    base_dir: Path,
    data: dict,
    force_index: Optional[int] = None,
    output_dir: Optional[Path] = None,
) -> Path:
    template_path = base_dir / TEMPLATE_NAME
    if not template_path.exists():
        raise FileNotFoundError(f"No se encontró el template: {template_path}")

    wb = load_workbook(filename=str(template_path))
    ws = wb.active  # Hoja principal

    # ---------------------------
    # 0) Preparar espacio para metas (simular "Insert Copied Cells")
    # ---------------------------
    numero_meta: List[str] = list(map(str, data.get("numero_meta", [])))
    nombre_meta: List[str] = list(map(str, data.get("nombre_meta", [])))
    total_metas = max(len(numero_meta), len(nombre_meta))
    extra = max(0, total_metas - 1)  # metas adicionales
    shift = extra * 3

    if shift > 0:
        _move_down_from_row(ws, start_row=15, row_off=shift)
        merges_base = _get_block_merges(ws, 12, 14)
        for i in range(2, total_metas + 1):
            dst_start = 12 + (i - 1) * 3  # 15, 18, 21...
            _clone_block_styles_merges(ws, 12, 14, dst_start, merges_cache=merges_base)
            # Replicar rótulos fijos (sin valores)
            lbl_num = _find_label_anchor(ws, 12, "NÚMERO DE META")
            lbl_nom = _find_label_anchor(ws, 13, "META DE CUATRIENIO")
            if lbl_num:
                _write(ws, f"{get_column_letter(lbl_num[1])}{dst_start}", "NÚMERO DE META")
            if lbl_nom:
                _write(ws, f"{get_column_letter(lbl_nom[1])}{dst_start+1}", "META DE CUATRIENIO")

    # ---------------------------
    # 1) Datos básicos
    # ---------------------------
    _write(ws, "D3",  data.get("nombre_proyecto", ""))
    _write(ws, "C5",  data.get("cod_id_mga", ""))
    _write(ws, "F5",  data.get("nombre_dependencia", ""))
    _write(ws, "C8",  data.get("codigo_sector", ""))
    _write(ws, "F8",  data.get("nombre_sector", ""))
    _write(ws, "C9",  data.get("codigo_programa", ""))
    _write(ws, "F9",  data.get("nombre_programa", ""))
    _write(ws, "C10", data.get("nombre_linea_estrategica", ""))

    # ---------------------------
    # 2) Variables SECTORIALES
    # ---------------------------
    variables_sec = data.get("variables_sectorial", None)
    if variables_sec is None:
        variables_sec = data.get("variables", [])

    for i, base_row in enumerate(range(26, 35)):
        cell = f"H{base_row + shift}"
        v = variables_sec[i] if i < len(variables_sec) else False
        _write(ws, cell, "Sí" if bool(v) else "No")

    # ---------------------------
    # 2.1) Variables TÉCNICAS
    # ---------------------------
    import unicodedata

    def _norm(s: str) -> str:
        return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c)).lower()

    def _get_sheet_fuzzy(wb, target_name: str):
        try:
            return wb[target_name]
        except KeyError:
            pass
        tnorm = _norm(target_name)
        for name in wb.sheetnames:
            if _norm(name) == tnorm or tnorm in _norm(name):
                return wb[name]
        raise KeyError(f"No se encontró la hoja '{target_name}'")

    ws_tecnico = _get_sheet_fuzzy(wb, "Concepto Técnico General")
    variables_tec = data.get("variables_tecnico", [])

    for i, base_row in enumerate(range(25, 38)):  # 25..37
        cell = f"H{base_row}"
        v = variables_tec[i] if i < len(variables_tec) else False
        _write(ws_tecnico, cell, "Sí" if bool(v) else "No")


    # ---------------------------
    # 3) Políticas / Categorías / Subcategorías / Valor destinado 
    # ---------------------------
    def _pair(lst, default=""):
        a = lst[0] if len(lst) >= 1 else default
        b = lst[1] if len(lst) >= 2 else default
        return a, b

    nombre_politica = data.get("nombre_politica", []) or data.get("nombre_politica".replace("ó", "o"), [])
    p1, p2 = _pair(list(map(str, nombre_politica)))
    _write(ws, f"E{38 + shift}", p1); _write(ws, f"G{38 + shift}", p2)

    nombre_categoria = data.get("nombre_categoria", [])
    c1, c2 = _pair(list(map(str, nombre_categoria)))
    _write(ws, f"E{39 + shift}", c1); _write(ws, f"G{39 + shift}", c2)

    nombre_focalizacion = data.get("nombre_focalización", []) or data.get("nombre_focalizacion", [])
    f1, f2 = _pair(list(map(str, nombre_focalizacion)))
    _write(ws, f"E{40 + shift}", f1); _write(ws, f"G{40 + shift}", f2)

    valores = data.get("valor_destinado", [])
    v1 = valores[0] if len(valores) > 0 else None
    v2 = valores[1] if len(valores) > 1 else None
    _write(ws, f"E{41 + shift}", v1 if v1 is not None else "")
    _write(ws, f"G{41 + shift}", v2 if v2 is not None else "")

    # ---------------------------
    # 4.5) Estructura financiera (resuelve casillas aquí)
    # ---------------------------
    ef_rows = data.get("estructura_financiera", [])
    if ef_rows:
        years = sorted({row.get("anio") for row in ef_rows if row.get("anio") is not None})[:4]
        while len(years) < 4:
            years.append(None)

        ENT_ORDER = ["DEPARTAMENTO", "MUNICIPIO", "NACION", "OTRO"]
        row_by_ent = {"DEPARTAMENTO": 18, "MUNICIPIO": 19, "NACION": 20, "OTRO": 21}
        col_by_idx = {0: "C", 1: "E", 2: "F", 3: "G"}

        from decimal import Decimal
        lookup = {}
        for r in ef_rows:
            anio = r.get("anio")
            ent = (r.get("entidad") or "").strip().upper()
            valor = r.get("valor")
            if ent in row_by_ent:
                lookup[(anio, ent)] = valor if valor is not None else Decimal("0")

        for yi, y in enumerate(years):
            for ent in ENT_ORDER:
                base_row = row_by_ent[ent]
                col = col_by_idx[yi]
                dest = f"{col}{base_row + shift}"
                val = lookup.get((y, ent), Decimal("0"))
                _write(ws, dest, val)
    
    # === Duplicar Estructura Financiera en hoja "Concepto Técnico General" (sin shift) ===
    if ef_rows:
        ENT_ORDER = ["DEPARTAMENTO", "MUNICIPIO", "NACION", "OTRO"]
        row_by_ent = {"DEPARTAMENTO": 17, "MUNICIPIO": 18, "NACION": 19, "OTRO": 20}
        col_by_idx = {0: "C", 1: "E", 2: "F", 3: "G"}

        from decimal import Decimal
        for yi, y in enumerate(years):
            for ent in ENT_ORDER:
                base_row = row_by_ent[ent]
                col = col_by_idx[yi]
                dest = f"{col}{base_row}"
                val = lookup.get((y, ent), Decimal("0"))
                _write(ws_tecnico, dest, val)

    # ---------------------------
    # 4) Llenar las METAS
    # ---------------------------
    lbl_num = _find_label_anchor(ws, 12, "NÚMERO DE META")
    lbl_nom = _find_label_anchor(ws, 13, "META DE CUATRIENIO")
    lbl_num_col = lbl_num[1] if lbl_num else 2 
    lbl_nom_col = lbl_nom[1] if lbl_nom else 2

    num_val_col = _find_value_anchor_col_for_row(ws, 12, lbl_num_col)
    nom_val_col = _find_value_anchor_col_for_row(ws, 13, lbl_nom_col)

    total = total_metas
    for i in range(1, total + 1):
        dst_start = 12 + (i - 1) * 3
        if i - 1 < len(numero_meta):
            _write(ws, f"{get_column_letter(num_val_col)}{dst_start}", numero_meta[i - 1])
        else:
            _write(ws, f"{get_column_letter(num_val_col)}{dst_start}", "")
        if i - 1 < len(nombre_meta):
            _write(ws, f"{get_column_letter(nom_val_col)}{dst_start + 1}", nombre_meta[i - 1])
        else:
            _write(ws, f"{get_column_letter(nom_val_col)}{dst_start + 1}", "")

        # ---------------------------
    # 4.5) Estructura financiera (resuelve casillas aquí)
    # ---------------------------
    ef_rows = data.get("estructura_financiera", [])
    if ef_rows:
        years = sorted({row.get("anio") for row in ef_rows if row.get("anio") is not None})[:4]
        while len(years) < 4:
            years.append(None)

        header_cols = ["C", "E", "F", "G"]
        for yi, col in enumerate(header_cols):
            _write(ws, f"{col}{17 + shift}", years[yi] if years[yi] is not None else "")

        ENT_ORDER = ["DEPARTAMENTO", "MUNICIPIO", "NACION", "OTRO"]
        row_by_ent = {"DEPARTAMENTO": 18, "MUNICIPIO": 19, "NACION": 20, "OTRO": 21}
        col_by_idx = {0: "C", 1: "E", 2: "F", 3: "G"}

        from decimal import Decimal
        lookup = {}
        for r in ef_rows:
            anio = r.get("anio")
            ent = (r.get("entidad") or "").strip().upper()
            valor = r.get("valor")
            if ent in row_by_ent:
                lookup[(anio, ent)] = valor if valor is not None else Decimal("0")

        for yi, y in enumerate(years):
            for ent in ENT_ORDER:
                base_row = row_by_ent[ent]
                col = col_by_idx[yi]
                dest = f"{col}{base_row + shift}"
                val = lookup.get((y, ent), Decimal("0"))
                _write(ws, dest, val)

    if ef_rows:
        header_cols = ["C", "E", "F", "G"]
        for yi, col in enumerate(header_cols):
            _write(ws_tecnico, f"{col}{16}", years[yi] if years[yi] is not None else "")

        ENT_ORDER = ["DEPARTAMENTO", "MUNICIPIO", "NACION", "OTRO"]
        row_by_ent = {"DEPARTAMENTO": 17, "MUNICIPIO": 18, "NACION": 19, "OTRO": 20}
        col_by_idx = {0: "C", 1: "E", 2: "F", 3: "G"}

        from decimal import Decimal
        for yi, y in enumerate(years):
            for ent in ENT_ORDER:
                base_row = row_by_ent[ent]
                col = col_by_idx[yi]
                dest = f"{col}{base_row}"
                val = lookup.get((y, ent), Decimal("0"))
                _write(ws_tecnico, dest, val)

    # ---------------------------
    # 4.9) Llenar las METAS Concepto Tecnico General
    # ---------------------------
    if total_metas > 1:
        extra2 = total_metas - 1
        _move_down_from_row(ws_tecnico, start_row=14, row_off=extra2 * 3)
        merges_base_tecnico = _get_block_merges(ws_tecnico, 11, 13)
        for i in range(2, total_metas + 1):
            dst_start2 = 11 + (i - 1) * 3
            _clone_block_styles_merges(ws_tecnico, 11, 13, dst_start2, merges_cache=merges_base_tecnico)
            lbl_num2 = _find_label_anchor(ws_tecnico, 11, "NÚMERO DE META")
            lbl_nom2 = _find_label_anchor(ws_tecnico, 12, "META DE CUATRIENIO")
            if lbl_num2:
                _write(ws_tecnico, f"{get_column_letter(lbl_num2[1])}{dst_start2}", "NÚMERO DE META")
            if lbl_nom2:
                _write(ws_tecnico, f"{get_column_letter(lbl_nom2[1])}{dst_start2+1}", "META DE CUATRIENIO")

    lbl_num2 = _find_label_anchor(ws_tecnico, 11, "NÚMERO DE META")
    lbl_nom2 = _find_label_anchor(ws_tecnico, 12, "META DE CUATRIENIO")
    lbl_num2_col = lbl_num2[1] if lbl_num2 else 2
    lbl_nom2_col = lbl_nom2[1] if lbl_nom2 else 2
    num_val2_col = _find_value_anchor_col_for_row(ws_tecnico, 11, lbl_num2_col)
    nom_val2_col = _find_value_anchor_col_for_row(ws_tecnico, 12, lbl_nom2_col)

    for i in range(1, total_metas + 1):
        dst_start2 = 11 + (i - 1) * 3
        _write(ws_tecnico, f"{get_column_letter(num_val2_col)}{dst_start2}",
               numero_meta[i - 1] if i - 1 < len(numero_meta) else "")
        _write(ws_tecnico, f"{get_column_letter(nom_val2_col)}{dst_start2 + 1}",
               nombre_meta[i - 1] if i - 1 < len(nombre_meta) else "")



    # ---------------------------
    # 5) Guardar
    # ---------------------------
    out_dir = output_dir or base_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    n = force_index if force_index is not None else _next_sequential_index(out_dir)
    out_path = out_dir / OUTPUT_PATTERN.format(n)

    wb.save(str(out_path))
    return out_path
