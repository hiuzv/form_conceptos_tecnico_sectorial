# Backend/services/excel_fill.py
from pathlib import Path
from typing import List, Optional
from openpyxl import load_workbook
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
    ws = wb.active  

    ws["D3"] = data.get("nombre_proyecto", "")
    ws["C5"] = data.get("cod_id_mga", "")
    ws["F5"] = data.get("nombre_dependencia", "")
    ws["C8"] = data.get("codigo_sector", "")
    ws["F8"] = data.get("nombre_sector", "")
    ws["C9"] = data.get("codigo_programa", "")
    ws["F9"] = data.get("nombre_programa", "")
    ws["C10"] = data.get("nombre_linea_estrategica", "")

    numero_meta: List[str] = list(map(str, data.get("numero_meta", [])))[:3]
    nombre_meta: List[str] = list(map(str, data.get("nombre_meta", [])))[:3]

    metas_num_cells = ["C12", "C15", "C18"]
    metas_nom_cells = ["C13", "C16", "C19"]

    for i, cell in enumerate(metas_num_cells):
        ws[cell] = numero_meta[i] if i < len(numero_meta) else ""

    for i, cell in enumerate(metas_nom_cells):
        ws[cell] = nombre_meta[i] if i < len(nombre_meta) else ""

    variables = data.get("variables", [])
    var_cells = [f"H{row}" for row in range(31, 40)] 
    for i, cell in enumerate(var_cells):
        if i < len(variables):
            v = variables[i]
            if isinstance(v, bool):
                ws[cell] = "Sí" if v else "No"
            else:
                ws[cell] = "Sí" if (str(v).strip() != "") else "No"
        else:
            ws[cell] = "No" 

    def _pair(lst, default=""):
        a = lst[0] if len(lst) >= 1 else default
        b = lst[1] if len(lst) >= 2 else default
        return a, b

    nombre_politica = data.get("nombre_politica", []) or data.get("nombre_politica".replace("ó","o"), [])
    p1, p2 = _pair(list(map(str, nombre_politica)))
    ws["E43"] = p1
    ws["G43"] = p2

    valores = data.get("valor_destinado", [])
    v1 = valores[0] if len(valores) > 0 else None
    v2 = valores[1] if len(valores) > 1 else None
    ws["E46"] = v1 if v1 is not None else ""
    ws["G46"] = v2 if v2 is not None else ""

    nombre_categoria = data.get("nombre_categoria", [])
    c1, c2 = _pair(list(map(str, nombre_categoria)))
    ws["E44"] = c1
    ws["G44"] = c2

    nombre_focalizacion = (
        data.get("nombre_focalización", [])
        or data.get("nombre_focalizacion", [])
    )
    f1, f2 = _pair(list(map(str, nombre_focalizacion)))
    ws["E45"] = f1
    ws["G45"] = f2

    out_dir = output_dir or base_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    n = force_index if force_index is not None else _next_sequential_index(out_dir)
    out_path = out_dir / OUTPUT_PATTERN.format(n)

    wb.save(str(out_path))
    return out_path
