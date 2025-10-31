import re
import unicodedata
import copy
from pathlib import Path
from typing import Dict, Optional, Callable
from decimal import Decimal
from docx import Document
from docx.table import Table

__all__ = ["fill_docx"]

PLACEHOLDER_RX = re.compile(r"\{\{\s*([^{}|]+?)\s*(?:\|\s*([a-z0-9_]+)\s*)?\}\}")
_NUM_META_RX = re.compile(r"\{\{\s*(?:cod_?meta|meta)(?:_(\d+))\s*\}\}", re.IGNORECASE)

def _has_numbered_meta_placeholders(doc: Document) -> bool:
    for tbl in doc.tables:
        for row in tbl.rows:
            for cell in row.cells:
                if _NUM_META_RX.search(cell.text or ""):
                    return True
    for p in doc.paragraphs:
        if _NUM_META_RX.search(p.text or ""):
            return True
    return False

def _strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))

def _norm_key(s: str) -> str:
    s = str(s or "")
    s = _strip_accents(s).lower()
    s = s.replace(" ", "")
    return s

def _fmt_moneda(x) -> str:
    try:
        d = Decimal(str(x or 0))
        return f"${d:,.0f}".replace(",", ".")
    except Exception:
        return str(x)

def _fmt_entero(x) -> str:
    try:
        d = int(Decimal(str(x or 0)))
        return f"{d:,}".replace(",", ".")
    except Exception:
        return str(x)

def _fmt_dec2(x) -> str:
    try:
        d = Decimal(str(x or 0))
        return f"{d:,.2f}".replace(",", ".")
    except Exception:
        return str(x)

_FORMATTERS: Dict[str, Callable[[object], str]] = {
    "moneda": _fmt_moneda,
    "entero": _fmt_entero,
    "dec2": _fmt_dec2,
}

def _build_lookup(context: Dict[str, object]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for k, v in (context or {}).items():
        nk = _norm_key(k)
        out[nk] = "" if v is None else str(v)
        
        if nk.startswith("nombre_meta_"):
            suf = nk.split("nombre_meta_")[-1]
            out[_norm_key(f"meta_{suf}")] = out[nk]
        if nk.startswith("numero_meta_"):
            suf = nk.split("numero_meta_")[-1]
            out[_norm_key(f"cod_meta_{suf}")] = out[nk]
        # dia/día espejos
        if "dia" in nk and "texto" in nk:
            out[nk.replace("dia", "día")] = out[nk]
        if "día" in k or "dia" in k:
            out[_norm_key(k.replace("día", "dia"))] = out[nk]
            out[_norm_key(k.replace("dia", "día"))] = out[nk]
    return out

def _replace_text(text: str, lookup: Dict[str, str]) -> str:
    def repl(m):
        raw_key = m.group(1)
        raw_fmt = m.group(2)
        nk = _norm_key(raw_key)
        if nk not in lookup:
            return m.group(0)
        val = lookup[nk]
        if raw_fmt and raw_fmt in _FORMATTERS:
            try:
                num_val = Decimal(val.replace(".", "").replace("$", "").replace(",", "."))
            except Exception:
                num_val = val
            return _FORMATTERS[raw_fmt](num_val)
        return val
    return PLACEHOLDER_RX.sub(repl, text)

def _replace_in_run_level(paragraph, lookup: Dict[str, str]) -> bool:
    joined = "".join(r.text for r in paragraph.runs)
    if not PLACEHOLDER_RX.search(joined):
        return True
    for r in paragraph.runs:
        if PLACEHOLDER_RX.search(r.text or ""):
            r.text = _replace_text(r.text, lookup)
    after = "".join(r.text for r in paragraph.runs)
    return not PLACEHOLDER_RX.search(after)

def _replace_in_paragraph(paragraph, lookup: Dict[str, str]) -> None:
    if _replace_in_run_level(paragraph, lookup):
        return
    full_text = "".join(r.text for r in paragraph.runs)
    new_text = _replace_text(full_text, lookup)
    if paragraph.runs:
        paragraph.runs[0].text = new_text
        for r in paragraph.runs[1:]:
            r.text = ""
    else:
        paragraph.add_run(new_text)

def _iter_all_paragraphs(doc: Document):
    for p in doc.paragraphs:
        yield p
    for tbl in doc.tables:
        for row in tbl.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    yield p

def fill_docx(
    base_dir: Path,
    template_name: str,
    context: Dict[str, object],
    output_name: Optional[str] = None,
    output_dir: Optional[Path] = None,
) -> Path:
    template_path = base_dir / template_name
    if not template_path.exists():
        raise FileNotFoundError(f"No se encontró el template: {template_path}")
    doc = Document(str(template_path))
    metas = context.get("__metas_ctx__") or []
    use_numbered = _has_numbered_meta_placeholders(doc)
    if metas:
        _expand_table1_and_table3(doc, metas, use_numbered=use_numbered)
    lookup = _build_lookup(context)
    for p in _iter_all_paragraphs(doc):
        _replace_in_paragraph(p, lookup)
    for tbl in doc.tables:
        for row in tbl.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    _replace_in_paragraph(p, lookup)
    out_dir = output_dir or base_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / (output_name or f"filled_{template_name}")
    doc.save(str(out_path))
    return out_path

def _replace_text_runs_in_cell(cell, repl: dict):
    for p in cell.paragraphs:
        for r in p.runs:
            t = r.text or ""
            for k, v in repl.items():
                t = t.replace(k, "" if v is None else str(v))
            r.text = t

def _clone_row_after(row, table):
    tr = row._tr
    new_tr = copy.deepcopy(tr)
    tr.addnext(new_tr)
    for r in table.rows:
        if r._tr is new_tr:
            return r
    return table.rows[-1]

def _insert_table_after(existing_table):
    src_tbl = existing_table._tbl
    new_tbl_elm = copy.deepcopy(src_tbl)
    src_tbl.addnext(new_tbl_elm)
    return Table(new_tbl_elm, existing_table._parent)

def _expand_table1_and_table3(doc: Document, metas: list, use_numbered: bool = False):
    if not metas or len(metas) == 0:
        return
    t1 = doc.tables[0] if len(doc.tables) >= 1 else None
    if t1:
        template_row = None
        for row in t1.rows:
            row_text = " || ".join(c.text for c in row.cells)
            if ("{{cod_meta" in row_text) or ("{{meta" in row_text) or ("{{ numero_meta" in row_text) or ("{{ nombre_meta" in row_text):
                template_row = row
                break
        if template_row:
            anchor = template_row
            for _ in range(len(metas) - 1):
                anchor = _clone_row_after(anchor, t1)
            block_rows = []
            take = len(metas)
            seen = False
            for row in t1.rows:
                row_text = " || ".join(c.text for c in row.cells)
                if not seen and (("{{cod_meta" in row_text) or ("{{meta" in row_text) or ("{{ numero_meta" in row_text) or ("{{ nombre_meta" in row_text)):
                    seen = True
                if seen and take > 0:
                    block_rows.append(row)
                    take -= 1
                if take == 0:
                    break

            for idx, row in enumerate(block_rows, start=1):
                m = metas[idx-1]
                repl = {
                    "{{cod_meta}}": m.get("cod_meta", ""),
                    "{{meta}}": m.get("meta", ""),
                    "{{numero_meta}}": m.get("cod_meta", ""),
                    "{{nombre_meta}}": m.get("meta", ""),
                    f"{{{{cod_meta_{idx}}}}}": m.get("cod_meta", ""),
                    f"{{{{meta_{idx}}}}}": m.get("meta", ""),
                    f"{{{{numero_meta_{idx}}}}}": m.get("cod_meta", ""),
                    f"{{{{nombre_meta_{idx}}}}}": m.get("meta", ""),
                }
                for c in row.cells:
                    _replace_text_runs_in_cell(c, repl)
    t3 = doc.tables[2] if len(doc.tables) >= 3 else None
    if t3:
        m1 = metas[0]
        repl1 = {
            "{{producto}}": m1.get("producto", ""),
            "{{cod_producto}}": m1.get("cod_producto", ""),
            "{{indicador_producto}}": m1.get("indicador_producto", ""),
            "{{cod_indicador_producto}}": m1.get("cod_indicador_producto", ""),
            "{{meta_indicador}}": "",
            "{{cod_meta}}": m1.get("cod_meta", ""),
            "{{meta}}": m1.get("meta", ""),
            "{{producto_1}}": m1.get("producto", ""),
            "{{cod_producto_1}}": m1.get("cod_producto", ""),
            "{{indicador_producto_1}}": m1.get("indicador_producto", ""),
            "{{cod_indicador_producto_1}}": m1.get("cod_indicador_producto", ""),
            "{{cod_meta_1}}": m1.get("cod_meta", ""),
            "{{meta_1}}": m1.get("meta", ""),
        }
        for row in t3.rows:
            for cell in row.cells:
                _replace_text_runs_in_cell(cell, repl1)
        anchor_tbl = t3
        for i in range(1, len(metas)):
            mi = metas[i]
            new_tbl = _insert_table_after(anchor_tbl)
            repl = {
                "{{producto}}": mi.get("producto", ""),
                "{{cod_producto}}": mi.get("cod_producto", ""),
                "{{indicador_producto}}": mi.get("indicador_producto", ""),
                "{{cod_indicador_producto}}": mi.get("cod_indicador_producto", ""),
                "{{meta_indicador}}": "",
                "{{cod_meta}}": mi.get("cod_meta", ""),
                "{{meta}}": mi.get("meta", ""),
                f"{{{{producto_{i+1}}}}}": mi.get("producto", ""),
                f"{{{{cod_producto_{i+1}}}}}": mi.get("cod_producto", ""),
                f"{{{{indicador_producto_{i+1}}}}}": mi.get("indicador_producto", ""),
                f"{{{{cod_indicador_producto_{i+1}}}}}": mi.get("cod_indicador_producto", ""),
                f"{{{{cod_meta_{i+1}}}}}": mi.get("cod_meta", ""),
                f"{{{{meta_{i+1}}}}}": mi.get("meta", ""),
            }
            for row in new_tbl.rows:
                for cell in row.cells:
                    _replace_text_runs_in_cell(cell, repl)
            anchor_tbl = new_tbl