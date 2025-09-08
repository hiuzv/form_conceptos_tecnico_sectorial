from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from Backend.utils.database import SessionLocal
from Backend.services import llenado_service
from Backend import schemas

router = APIRouter(prefix="/llenado", tags=["llenado"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/lineas", response_model=List[schemas.LineaRead])
def lineas(db: Session = Depends(get_db)):
    return [
        schemas.LineaRead(id=r.id, nombre=r.nombre_linea_estrategica)
        for r in llenado_service.listar_lineas(db)
    ]

@router.get("/sectores", response_model=List[schemas.SectorRead])
def sectores(linea_id: int = Query(..., ge=1), db: Session = Depends(get_db)):
    return [
        schemas.SectorRead(id=r.id, codigo_sector=r.codigo_sector, nombre_sector=r.nombre_sector)
        for r in llenado_service.listar_sectores(db, linea_id)
    ]

@router.get("/programas", response_model=List[schemas.ProgramaRead])
def programas(sector_id: int = Query(..., ge=1), db: Session = Depends(get_db)):
    return [
        schemas.ProgramaRead(id=r.id, codigo_programa=r.codigo_programa, nombre_programa=r.nombre_programa)
        for r in llenado_service.listar_programas(db, sector_id)
    ]

@router.get("/metas", response_model=List[schemas.MetaRead])
def metas(programa_id: int = Query(..., ge=1), db: Session = Depends(get_db)):
    return [
        schemas.MetaRead(id=r.id, numero_meta=r.numero_meta, nombre_meta=r.nombre_meta)
        for r in llenado_service.listar_metas(db, programa_id)
    ]

@router.get("/dependencias")
def dependencias(db: Session = Depends(get_db)):
    return llenado_service.listar_dependencias(db)

@router.get("/variables", response_model=List[schemas.VariableRead])
def variables(db: Session = Depends(get_db)):
    return [
        schemas.VariableRead(id=r.id, nombre_variable=r.nombre_variable)
        for r in llenado_service.listar_variables(db)
    ]

@router.get("/politicas", response_model=List[schemas.PoliticaRead])
def politicas(db: Session = Depends(get_db)):
    return [
        schemas.PoliticaRead(id=r.id, nombre_politica=r.nombre_politica)
        for r in llenado_service.listar_politicas(db)
    ]

@router.get("/categorias", response_model=List[schemas.CategoriaRead])
def categorias(politica_id: int = Query(..., ge=1), db: Session = Depends(get_db)):
    return [
        schemas.CategoriaRead(id=r.id, id_politica=r.id_politica, nombre_categoria=r.nombre_categoria)
        for r in llenado_service.listar_categorias(db, politica_id)
    ]

@router.get("/subcategorias", response_model=List[schemas.SubcategoriaRead])
def subcategorias(categoria_id: int = Query(..., ge=1), db: Session = Depends(get_db)):
    return [
        schemas.SubcategoriaRead(id=r.id, id_categoria=r.id_categoria, nombre_subcategoria=r.nombre_subcategoria)
        for r in llenado_service.listar_subcategorias(db, categoria_id)
    ]

@router.post("/formulario", response_model=schemas.FormularioRead)
def crear_formulario(payload: schemas.FormularioCreate, db: Session = Depends(get_db)):
    form = llenado_service.crear_formulario(db, payload)

    if payload.metas:
        llenado_service.asignar_metas(db, form.id, payload.metas)
    if payload.variables:
        llenado_service.asignar_variables(db, form.id, payload.variables)
    if payload.politicas:
        llenado_service.asignar_politicas(db, form.id, payload.politicas, payload.valores_politicas)
    if payload.categorias:
        llenado_service.asignar_categorias(db, form.id, payload.categorias)
    if payload.subcategorias:
        llenado_service.asignar_subcategorias(db, form.id, payload.subcategorias)

    form_db = llenado_service.obtener_formulario(db, form.id)
    metas_db = llenado_service.listar_metas_por_formulario(db, form.id)
    vars_db = llenado_service.listar_variables_por_formulario(db, form.id)
    pols_db = llenado_service.listar_politicas_por_formulario(db, form.id)
    cats_db = llenado_service.listar_categorias_por_formulario(db, form.id)
    subcats_db = llenado_service.listar_subcategorias_por_formulario(db, form.id)

    return schemas.FormularioRead(
        id=form_db.id,
        nombre_proyecto=form_db.nombre_proyecto,
        cod_id_mga=form_db.cod_id_mga,
        id_dependencia=form_db.id_dependencia,
        id_linea_estrategica=form_db.id_linea_estrategica,
        id_programa=form_db.id_programa,
        id_sector=form_db.id_sector,
        metas=[schemas.MetaRead(id=m.id, numero_meta=m.numero_meta, nombre_meta=m.nombre_meta) for m in metas_db],
        variables=[schemas.VariableRead(id=v.id, nombre_variable=v.nombre_variable) for v in vars_db],
        politicas = [schemas.PoliticaRead(id=p.id, nombre_politica=p.nombre_politica, valor_destinado=valor)
            for (p, valor) in pols_db
        ],
        categorias=[schemas.CategoriaRead(id=c.id, id_politica=c.id_politica, nombre_categoria=c.nombre_categoria) for c in cats_db],
        subcategorias=[schemas.SubcategoriaRead(id=s.id, id_categoria=s.id_categoria, nombre_subcategoria=s.nombre_subcategoria) for s in subcats_db],
    )

@router.get("/formulario/{form_id}", response_model=schemas.FormularioRead)
def obtener_formulario(form_id: int, db: Session = Depends(get_db)):
    form_db = llenado_service.obtener_formulario(db, form_id)
    if not form_db:
        raise HTTPException(status_code=404, detail="Formulario no encontrado")

    metas_db = llenado_service.listar_metas_por_formulario(db, form_id)
    vars_db = llenado_service.listar_variables_por_formulario(db, form_id)
    pols_db = llenado_service.listar_politicas_por_formulario(db, form_id)
    cats_db = llenado_service.listar_categorias_por_formulario(db, form_id)
    subcats_db = llenado_service.listar_subcategorias_por_formulario(db, form_id)

    return schemas.FormularioRead(
        id=form_db.id,
        nombre_proyecto=form_db.nombre_proyecto,
        cod_id_mga=form_db.cod_id_mga,
        id_dependencia=form_db.id_dependencia,
        id_linea_estrategica=form_db.id_linea_estrategica,
        id_programa=form_db.id_programa,
        id_sector=form_db.id_sector,
        metas=[schemas.MetaRead(id=m.id, numero_meta=m.numero_meta, nombre_meta=m.nombre_meta) for m in metas_db],
        variables=[schemas.VariableRead(id=v.id, nombre_variable=v.nombre_variable) for v in vars_db],
        politicas=[schemas.PoliticaRead(id=p.id, nombre_politica=p.nombre_politica, valor_destinado=valor)
            for (p, valor) in pols_db
        ],
        categorias=[schemas.CategoriaRead(id=c.id, id_politica=c.id_politica, nombre_categoria=c.nombre_categoria) for c in cats_db],
        subcategorias=[schemas.SubcategoriaRead(id=s.id, id_categoria=s.id_categoria, nombre_subcategoria=s.nombre_subcategoria) for s in subcats_db],
    )
