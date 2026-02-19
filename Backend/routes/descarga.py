# Backend/routes/descarga.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from Backend.utils.database import SessionLocal
from Backend.services import descarga_service

router = APIRouter(prefix="/descarga", tags=["descarga"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class EvaluadorTemplateIn(BaseModel):
    contenido_html: str
    nombre_evaluador: str
    cargo_evaluador: str | None = None
    concepto_tecnico_favorable_dep: str | None = None
    concepto_sectorial_favorable_dep: str | None = None
    proyecto_viable_dep: str | None = None

@router.get("/excel/concepto-tecnico-sectorial/{form_id}")
def descargar_excel_concepto_tecnico_sectorial(form_id: int, db: Session = Depends(get_db)):
    try:
        bio, filename = descarga_service.excel_concepto_tecnico_sectorial(db, form_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando Excel: {e}")

    if bio.getbuffer().nbytes == 0:
        raise HTTPException(status_code=404, detail="No hay datos para exportar")

    return StreamingResponse(
        bio,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

@router.get("/excel/cadena-valor/{form_id}")
def descargar_excel_cadena_valor(form_id: int, db: Session = Depends(get_db)):
    try:
        bio, filename = descarga_service.excel_cadena_valor(db, form_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando Excel: {e}")

    if bio.getbuffer().nbytes == 0:
        raise HTTPException(status_code=404, detail="No hay datos para exportar")

    return StreamingResponse(
        bio,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

@router.get("/excel/viabilidad-dependencias/{form_id}")
def descargar_excel_viabilidad_dependencias(form_id: int, db: Session = Depends(get_db)):
    try:
        bio, filename = descarga_service.excel_viabilidad_dependencias(db, form_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando Excel: {e}")

    if bio.getbuffer().nbytes == 0:
        raise HTTPException(status_code=404, detail="No hay datos para exportar")

    return StreamingResponse(
        bio,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

@router.get("/word/carta/{form_id}")
def descargar_word_carta(form_id: int, db: Session = Depends(get_db)):
    try:
        bio, filename = descarga_service.word_formulario(db, form_id, doc="carta")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando Word: {e}")

    if not bio.getvalue():
        raise HTTPException(status_code=404, detail="No hay datos para exportar")

    return StreamingResponse(
        bio,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

@router.get("/word/cert-precios/{form_id}")
def descargar_word_cert_precios(form_id: int, db: Session = Depends(get_db)):
    try:
        bio, filename = descarga_service.word_formulario(db, form_id, doc="cert_precios")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando Word: {e}")

    if not bio.getvalue():
        raise HTTPException(status_code=404, detail="No hay datos para exportar")

    return StreamingResponse(
        bio,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

@router.get("/word/no-doble-cofin/{form_id}")
def descargar_word_no_doble_cofin(form_id: int, db: Session = Depends(get_db)):
    try:
        bio, filename = descarga_service.word_formulario(db, form_id, doc="no_doble_cofin")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando Word: {e}")

    if not bio.getvalue():
        raise HTTPException(status_code=404, detail="No hay datos para exportar")

    return StreamingResponse(
        bio,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.post("/evaluador/template/{doc_key}/{form_id}")
def render_template_evaluador(doc_key: str, form_id: int, body: EvaluadorTemplateIn, db: Session = Depends(get_db)):
    try:
        html, filename = descarga_service.render_evaluador_template_html(
            db=db,
            form_id=form_id,
            template_key=doc_key,
            contenido_html=body.contenido_html,
            nombre_evaluador=body.nombre_evaluador,
            cargo_evaluador=body.cargo_evaluador,
            concepto_tecnico_favorable_dep=body.concepto_tecnico_favorable_dep,
            concepto_sectorial_favorable_dep=body.concepto_sectorial_favorable_dep,
            proyecto_viable_dep=body.proyecto_viable_dep,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando plantilla: {e}")

    return {"html": html, "filename": filename}


@router.post("/evaluador/pdf/{doc_key}/{form_id}")
async def render_pdf_evaluador(doc_key: str, form_id: int, body: EvaluadorTemplateIn, db: Session = Depends(get_db)):
    try:
        bio, filename = await descarga_service.render_evaluador_template_pdf_async(
            db=db,
            form_id=form_id,
            template_key=doc_key,
            contenido_html=body.contenido_html,
            nombre_evaluador=body.nombre_evaluador,
            cargo_evaluador=body.cargo_evaluador,
            concepto_tecnico_favorable_dep=body.concepto_tecnico_favorable_dep,
            concepto_sectorial_favorable_dep=body.concepto_sectorial_favorable_dep,
            proyecto_viable_dep=body.proyecto_viable_dep,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando PDF: {repr(e)}")

    return StreamingResponse(
        bio,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
