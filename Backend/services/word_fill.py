from __future__ import annotations
import re
import unicodedata
from pathlib import Path
from typing import Dict, Iterable, Optional, Tuple, Callable
from decimal import Decimal
from docx import Document

__all__ = ["fill_docx"]

PLACEHOLDER_RX = re.compile(r"\{\{\s*([^{}|]+?)\s*(?:\|\s*([a-z0-9_]+)\s*)?\}\}")

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
            return m.group(0)  # deja el placeholder si no existe
        val = lookup[nk]
        if raw_fmt and raw_fmt in _FORMATTERS:
            try:
                # intenta castear a numero cuando aplica
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

    lookup = _build_lookup(context)
    doc = Document(str(template_path))

    for p in _iter_all_paragraphs(doc):
        _replace_in_paragraph(p, lookup)

    out_dir = output_dir or base_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / (output_name or f"filled_{template_name}")
    doc.save(str(out_path))
    return out_path
