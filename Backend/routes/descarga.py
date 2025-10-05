# Backend/routes/descarga.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from Backend.utils.database import SessionLocal
from Backend.services import descarga_service

router = APIRouter(prefix="/descarga", tags=["descarga"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/excel/concepto-tecnico-sectorial/{form_id}")
def descargar_excel_concepto_tecnico_sectorial(form_id: int, db: Session = Depends(get_db)):
    try:
        bio, filename = descarga_service.excel_formulario(db, form_id)
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
        bio, filename = descarga_service.excel_formulario(db, form_id)
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
        bio, filename = descarga_service.excel_formulario(db, form_id)
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
