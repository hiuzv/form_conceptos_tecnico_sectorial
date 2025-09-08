# Backend/services/excel_fill.py
from pathlib import Path
from typing import Optional
from openpyxl import load_workbook
from openpyxl.utils.cell import coordinate_to_tuple
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


# --- Escritura segura en celdas combinadas ---
def _anchor_of_merged(ws, coord: str) -> str:
    r, c = coordinate_to_tuple(coord)  # (row, col)
    for mr in ws.merged_cells.ranges:
        if mr.min_row <= r <= mr.max_row and mr.min_col <= c <= mr.max_col:
            return ws.cell(row=mr.min_row, column=mr.min_col).coordinate
    return coord

def _write(ws, coord: str, value):
    ws[_anchor_of_merged(ws, coord)] = value


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
    # 1) Datos básicos (sin metas)
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
    # 2) Variables (AHORA: H26..H34)
    # ---------------------------
    variables = data.get("variables", [])
    var_cells = [f"H{row}" for row in range(26, 35)]  # H26..H34
    for i, cell in enumerate(var_cells):
        if i < len(variables):
            v = variables[i]
            if isinstance(v, bool):
                _write(ws, cell, "Sí" if v else "No")
            else:
                _write(ws, cell, "Sí" if (str(v).strip() != "") else "No")
        else:
            _write(ws, cell, "No")

    # ---------------------------
    # 3) Políticas / Categorías / Subcategorías / Valor destinado
    # (AHORA: E38/G38, E39/G39, E40/G40, E41/G41)
    # ---------------------------
    def _pair(lst, default=""):
        a = lst[0] if len(lst) >= 1 else default
        b = lst[1] if len(lst) >= 2 else default
        return a, b

    # nombre_politica → E38, G38
    nombre_politica = data.get("nombre_politica", []) or data.get("nombre_politica".replace("ó", "o"), [])
    p1, p2 = _pair(list(map(str, nombre_politica)))
    _write(ws, "E38", p1); _write(ws, "G38", p2)

    # nombre_categoria → E39, G39
    nombre_categoria = data.get("nombre_categoria", [])
    c1, c2 = _pair(list(map(str, nombre_categoria)))
    _write(ws, "E39", c1); _write(ws, "G39", c2)

    # nombre_subcategoria / focalización → E40, G40
    nombre_focalizacion = data.get("nombre_focalización", []) or data.get("nombre_focalizacion", [])
    f1, f2 = _pair(list(map(str, nombre_focalizacion)))
    _write(ws, "E40", f1); _write(ws, "G40", f2)

    # valor_destinado → E41, G41
    valores = data.get("valor_destinado", [])
    v1 = valores[0] if len(valores) > 0 else None
    v2 = valores[1] if len(valores) > 1 else None
    _write(ws, "E41", v1 if v1 is not None else "")
    _write(ws, "G41", v2 if v2 is not None else "")

    # --- No llenamos metas (bloque 12..19 se deja intacto) ---

    # ---------------------------
    # 4) Guardar
    # ---------------------------
    out_dir = output_dir or base_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    n = force_index if force_index is not None else _next_sequential_index(out_dir)
    out_path = out_dir / OUTPUT_PATTERN.format(n)

    wb.save(str(out_path))
    return out_path
