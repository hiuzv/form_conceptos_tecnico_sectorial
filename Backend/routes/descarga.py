from fastapi import APIRouter, Depends, Query, HTTPException
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

@router.get("/formulario/{form_id}/excel")
def descargar_formulario_excel(form_id: int, db: Session = Depends(get_db)):
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
