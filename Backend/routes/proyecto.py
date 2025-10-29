from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from Backend.utils.database import SessionLocal
from Backend.services import proyecto_service
from Backend import schemas

router = APIRouter(prefix="/proyecto", tags=["proyecto"])

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
        for r in proyecto_service.listar_lineas(db)
    ]

@router.get("/sectores", response_model=List[schemas.SectorRead])
def sectores(linea_id: int = Query(..., ge=1), db: Session = Depends(get_db)):
    return [
        schemas.SectorRead(id=r.id, codigo_sector=r.codigo_sector, nombre_sector=r.nombre_sector)
        for r in proyecto_service.listar_sectores(db, linea_id)
    ]

@router.get("/programas", response_model=List[schemas.ProgramaRead])
def programas(sector_id: int = Query(..., ge=1), db: Session = Depends(get_db)):
    return [
        schemas.ProgramaRead(id=r.id, codigo_programa=r.codigo_programa, nombre_programa=r.nombre_programa)
        for r in proyecto_service.listar_programas(db, sector_id)
    ]

@router.get("/metas", response_model=List[schemas.MetaRead])
def metas(programa_id: int = Query(..., ge=1), db: Session = Depends(get_db)):
    return [
        schemas.MetaRead(id=r.id, numero_meta=r.numero_meta, nombre_meta=r.nombre_meta)
        for r in proyecto_service.listar_metas(db, programa_id)
    ]

@router.get("/dependencias")
def dependencias(db: Session = Depends(get_db)):
    return proyecto_service.listar_dependencias(db)

@router.get("/variables_sectorial", response_model=List[schemas.VariableSectorialRead])
def variables_sectorial(db: Session = Depends(get_db)):
    return [
        schemas.VariableSectorialRead(id=r.id, nombre_variable=r.nombre_variable)
        for r in proyecto_service.listar_variables_sectorial(db)
    ]

@router.get("/variables_tecnico", response_model=List[schemas.VariableTecnicoRead])
def variables_tecnico(db: Session = Depends(get_db)):
    return [
        schemas.VariableTecnicoRead(id=r.id, nombre_variable=r.nombre_variable)
        for r in proyecto_service.listar_variables_tecnico(db)
    ]

@router.get("/politicas", response_model=List[schemas.PoliticaRead])
def politicas(db: Session = Depends(get_db)):
    return [
        schemas.PoliticaRead(id=r.id, nombre_politica=r.nombre_politica)
        for r in proyecto_service.listar_politicas(db)
    ]

@router.get("/categorias", response_model=List[schemas.CategoriaRead])
def categorias(politica_id: int = Query(..., ge=1), db: Session = Depends(get_db)):
    return [
        schemas.CategoriaRead(id=r.id, id_politica=r.id_politica, nombre_categoria=r.nombre_categoria)
        for r in proyecto_service.listar_categorias(db, politica_id)
    ]

@router.get("/subcategorias", response_model=List[schemas.SubcategoriaRead])
def subcategorias(categoria_id: int = Query(..., ge=1), db: Session = Depends(get_db)):
    return [
        schemas.SubcategoriaRead(id=r.id, id_categoria=r.id_categoria, nombre_subcategoria=r.nombre_subcategoria)
        for r in proyecto_service.listar_subcategorias(db, categoria_id)
    ]

@router.post("/formulario", response_model=schemas.FormularioRead)
def crear_formulario(payload: schemas.FormularioCreate, db: Session = Depends(get_db)):
    form = proyecto_service.crear_formulario(db, payload)

    if payload.metas:
        proyecto_service.asignar_metas(db, form.id, payload.metas)
    if payload.variables_sectorial:
        proyecto_service.asignar_variables_sectorial(db, form.id, payload.variables_sectorial)
    if payload.variables_tecnico:
        proyecto_service.asignar_variables_tecnico(db, form.id, payload.variables_tecnico)
    if payload.politicas:
        proyecto_service.asignar_politicas(db, form.id, payload.politicas, payload.valores_politicas)
    if payload.categorias:
        proyecto_service.asignar_categorias(db, form.id, payload.categorias)
    if payload.subcategorias:
        proyecto_service.asignar_subcategorias(db, form.id, payload.subcategorias)
    if payload.estructura_financiera:
        proyecto_service.asignar_estructura_financiera(db, form.id, payload.estructura_financiera)

    form_db = proyecto_service.obtener_formulario(db, form.id)
    metas_db = proyecto_service.listar_metas_por_formulario(db, form.id)
    vars_sectorial_db = proyecto_service.listar_variables_sectorial_por_formulario(db, form.id)
    vars_tecnico_db   = proyecto_service.listar_variables_tecnico_por_formulario(db, form.id)
    pols_db = proyecto_service.listar_politicas_por_formulario(db, form.id)
    cats_db = proyecto_service.listar_categorias_por_formulario(db, form.id)
    subcats_db = proyecto_service.listar_subcategorias_por_formulario(db, form.id)
    est_fin_db = proyecto_service.listar_estructura_financiera(db, form.id)

    return schemas.FormularioRead(
        id=form_db.id,
        nombre_proyecto=form_db.nombre_proyecto,
        cod_id_mga=form_db.cod_id_mga,
        id_dependencia=form_db.id_dependencia,
        id_linea_estrategica=form_db.id_linea_estrategica,
        id_programa=form_db.id_programa,
        id_sector=form_db.id_sector,
        nombre_secretario=form_db.nombre_secretario,
        fuentes=getattr(form_db, "fuentes", None) or "",
        duracion_proyecto=getattr(form_db, "duracion_proyecto", None) or 0,
        cantidad_beneficiarios=getattr(form_db, "cantidad_beneficiarios", None) or 0,
        metas=[schemas.MetaRead(id=m.id, numero_meta=m.numero_meta, nombre_meta=m.nombre_meta) for m in metas_db],
        variables_sectorial=[schemas.VariableSectorialRead(id=v.id, nombre_variable=v.nombre_variable) for v in vars_sectorial_db],
        variables_tecnico=[schemas.VariableTecnicoRead(id=v.id, nombre_variable=v.nombre_variable) for v in vars_tecnico_db],
        politicas = [schemas.PoliticaRead(id=p.id, nombre_politica=p.nombre_politica, valor_destinado=valor)
            for (p, valor) in pols_db
        ],
        categorias=[schemas.CategoriaRead(id=c.id, id_politica=c.id_politica, nombre_categoria=c.nombre_categoria) for c in cats_db],
        subcategorias=[schemas.SubcategoriaRead(id=s.id, id_categoria=s.id_categoria, nombre_subcategoria=s.nombre_subcategoria) for s in subcats_db],
        estructura_financiera=[schemas.EstructuraFinancieraRow(id=e.id, anio=e.anio, entidad=e.entidad, valor=e.valor) for e in est_fin_db],
    )

@router.get("/formulario/{form_id}", response_model=schemas.FormularioRead)
def obtener_formulario(form_id: int, db: Session = Depends(get_db)):
    form_db = proyecto_service.obtener_formulario(db, form_id)
    if not form_db:
        raise HTTPException(status_code=404, detail="Formulario no encontrado")
    metas_db            = proyecto_service.listar_metas_por_formulario(db, form_id)
    vars_sectorial_db   = proyecto_service.listar_variables_sectorial_por_formulario(db, form_id)
    vars_tecnico_db     = proyecto_service.listar_variables_tecnico_por_formulario(db, form_id)
    pols_db             = proyecto_service.listar_politicas_por_formulario(db, form_id)
    cats_db             = proyecto_service.listar_categorias_por_formulario(db, form_id)
    subcats_db          = proyecto_service.listar_subcategorias_por_formulario(db, form_id)
    est_fin_db          = proyecto_service.listar_estructura_financiera(db, form_id)
    viab_db = proyecto_service.listar_viabilidades_por_formulario(db, form_id)
    func_db = proyecto_service.listar_funcionarios_viabilidad(db, form_id)

    return schemas.FormularioRead(
        id=form_db.id,
        nombre_proyecto=form_db.nombre_proyecto or "",
        cod_id_mga=form_db.cod_id_mga or 0,
        id_dependencia=form_db.id_dependencia or 0,
        id_linea_estrategica=form_db.id_linea_estrategica or 0,
        id_programa=form_db.id_programa or 0,
        id_sector=form_db.id_sector or 0,
        nombre_secretario=form_db.nombre_secretario or "",
        fuentes=getattr(form_db, "fuentes", None) or "",
        duracion_proyecto=getattr(form_db, "duracion_proyecto", None) or 0,
        cantidad_beneficiarios=getattr(form_db, "cantidad_beneficiarios", None) or 0,
        metas=[schemas.MetaRead(id=m.id, numero_meta=m.numero_meta, nombre_meta=m.nombre_meta) for m in metas_db] or [],
        variables_sectorial=[schemas.VariableSectorialRead(id=v.id, nombre_variable=v.nombre_variable) for v in vars_sectorial_db] or [],
        variables_tecnico=[schemas.VariableTecnicoRead(id=v.id, nombre_variable=v.nombre_variable) for v in vars_tecnico_db] or [],
        politicas=[schemas.PoliticaRead(id=p.id, nombre_politica=p.nombre_politica, valor_destinado=valor) for (p, valor) in pols_db] or [],
        categorias=[schemas.CategoriaRead(id=c.id, id_politica=c.id_politica, nombre_categoria=c.nombre_categoria) for c in cats_db] or [],
        subcategorias=[schemas.SubcategoriaRead(id=s.id, id_categoria=s.id_categoria, nombre_subcategoria=s.nombre_subcategoria) for s in subcats_db] or [],
        estructura_financiera=[schemas.EstructuraFinancieraRow(id=e.id, anio=e.anio, entidad=e.entidad, valor=e.valor) for e in est_fin_db] or [],
        viabilidades=[schemas.ViabilidadRead(id=v.id, nombre=v.nombre) for v in viab_db] or [],
        funcionarios_viabilidad=[schemas.FuncionarioViabilidadIn(id_tipo_viabilidad=f.id_tipo_viabilidad, nombre=f.nombre, cargo=f.cargo) for f in func_db] or [],
    )

@router.post("", response_model=schemas.FormularioRead)
def crear_borrador_endpoint(db: Session = Depends(get_db)):
    form = proyecto_service.crear_borrador(db)
    return schemas.FormularioRead(
        id=form.id, nombre_proyecto=form.nombre_proyecto, cod_id_mga=form.cod_id_mga,
        id_dependencia=form.id_dependencia, id_linea_estrategica=form.id_linea_estrategica,
        id_programa=form.id_programa, id_sector=form.id_sector, nombre_secretario=form.nombre_secretario,
        metas=[], variables_sectorial=[], variables_tecnico=[], estructura_financiera=[], politicas=[], categorias=[], subcategorias=[]
    )

@router.patch("/formulario/{form_id}/basicos", response_model=schemas.FormularioRead)
def upsert_basicos(form_id:int, payload: schemas.FormularioUpsertBasicos, db: Session = Depends(get_db)):
    proyecto_service.update_formulario_basicos(db, form_id, payload)
    return obtener_formulario(form_id, db)

@router.put("/formulario/{form_id}/metas", response_model=schemas.FormularioRead)
def upsert_metas(form_id:int, body: schemas.IdsIn, db: Session = Depends(get_db)):
    proyecto_service.replace_metas(db, form_id, body.ids or [])
    return obtener_formulario(form_id, db)

@router.put("/formulario/{form_id}/estructura-financiera", response_model=schemas.FormularioRead)
def upsert_ef(form_id:int, body: schemas.EstructuraFinancieraRead, db: Session = Depends(get_db)):
    filas = getattr(body, "filas", []) or []
    proyecto_service.asignar_estructura_financiera(db, form_id, filas)
    return obtener_formulario(form_id, db)

@router.put("/formulario/{form_id}/variables-sectorial", response_model=schemas.FormularioRead)
def upsert_vs(form_id:int, body: schemas.IdsIn, db: Session = Depends(get_db)):
    proyecto_service.replace_variables_sectorial(db, form_id, body.ids or [])
    return obtener_formulario(form_id, db)

@router.put("/formulario/{form_id}/variables-tecnico", response_model=schemas.FormularioRead)
def upsert_vt(form_id:int, body: schemas.IdsIn, db: Session = Depends(get_db)):
    proyecto_service.replace_variables_tecnico(db, form_id, body.ids or [])
    return obtener_formulario(form_id, db)

@router.put("/formulario/{form_id}/politicas", response_model=schemas.FormularioRead)
def upsert_politicas(form_id:int, body: schemas.PoliticasUpsertIn, db: Session = Depends(get_db)):
    proyecto_service.replace_politicas(db, form_id, body.politicas or [], body.valores_politicas or [])
    return obtener_formulario(form_id, db)

@router.put("/formulario/{form_id}/categorias", response_model=schemas.FormularioRead)
def upsert_categorias(form_id:int, body: schemas.IdsIn, db: Session = Depends(get_db)):
    proyecto_service.replace_categorias(db, form_id, body.ids or [])
    return obtener_formulario(form_id, db)

@router.put("/formulario/{form_id}/subcategorias", response_model=schemas.FormularioRead)
def upsert_subcats(form_id:int, body: schemas.IdsIn, db: Session = Depends(get_db)):
    proyecto_service.replace_subcategorias(db, form_id, body.ids or [])
    return obtener_formulario(form_id, db)

@router.get("/lista")
def listar_proyectos_api(
    nombre: str | None = None,
    cod_id_mga: str | None = Query(None),
    id_dependencia: int | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    rows, total = proyecto_service.listar_proyectos_pag(db, nombre, cod_id_mga, id_dependencia, page, page_size)
    items = [
        {"id": r.id, "nombre": r.nombre_proyecto, "cod_id_mga": r.cod_id_mga, "id_dependencia": r.id_dependencia}
        for r in rows
    ]
    return {"items": items, "total": total, "page": page, "page_size": page_size}

@router.post("/formulario/minimo", response_model=schemas.FormularioId)
def crear_minimo(payload: schemas.FormularioCreateMinimo, db: Session = Depends(get_db)):
    form = proyecto_service.crear_formulario_minimo(db, payload)
    return schemas.FormularioId(id=form.id)

@router.get("/viabilidad", response_model=List[schemas.ViabilidadRead])
def viabilidad(db: Session = Depends(get_db)):
    return proyecto_service.listar_viabilidad(db)

@router.get("/tipos_viabilidad", response_model=List[schemas.TipoViabilidadRead])
def tipos_viabilidad(db: Session = Depends(get_db)):
    return proyecto_service.listar_tipos_viabilidad(db)

@router.put("/formulario/{form_id}/viabilidades", response_model=schemas.FormularioRead)
def upsert_viabilidades(form_id:int, body: schemas.IdsIn, db: Session = Depends(get_db)):
    proyecto_service.replace_viabilidades(db, form_id, body.ids or [])
    return obtener_formulario(form_id, db)

@router.put("/formulario/{form_id}/funcionarios-viabilidad", response_model=schemas.FormularioRead)
def upsert_funcionarios_viabilidad(form_id:int, body: schemas.FuncionariosViabilidadUpsertIn, db: Session = Depends(get_db)):
    filas = getattr(body, "funcionarios", []) or []
    proyecto_service.replace_funcionarios_viabilidad(db, form_id, [f.dict() for f in filas])
    return obtener_formulario(form_id, db)

@router.get("/formulario/{form_id}/variables-sectorial-respuestas", response_model=list[schemas.VarRespuestaRead])
def get_vars_sec_resp(form_id:int, db:Session=Depends(get_db)):
    form = proyecto_service.obtener_formulario(db, form_id)
    if not form: raise HTTPException(404, "Formulario no encontrado")
    cat = proyecto_service.listar_cat_variables_sectorial(db)
    res = proyecto_service.leer_respuestas_sectorial(db, form_id)
    out = []
    for v in cat:
        out.append(schemas.VarRespuestaRead(
            id=v.id, nombre=v.nombre_variable, no_aplica=bool(v.no_aplica),
            respuesta=res.get(v.id)
        ))
    return out

@router.put("/formulario/{form_id}/variables-sectorial-respuestas")
def put_vars_sec_resp(form_id:int, body:schemas.VarsRespuestaUpsertIn, db:Session=Depends(get_db)):
    pares = [(int(x.id), (x.respuesta or "").upper()) for x in (body.respuestas or [])]
    proyecto_service.upsert_respuestas_sectorial(db, form_id, pares)
    return {"ok": True}

@router.get("/formulario/{form_id}/variables-tecnico-respuestas", response_model=list[schemas.VarRespuestaRead])
def get_vars_tec_resp(form_id:int, db:Session=Depends(get_db)):
    form = proyecto_service.obtener_formulario(db, form_id)
    if not form: raise HTTPException(404, "Formulario no encontrado")
    cat = proyecto_service.listar_cat_variables_tecnico(db)
    res = proyecto_service.leer_respuestas_tecnico(db, form_id)
    return [schemas.VarRespuestaRead(id=v.id, nombre=v.nombre_variable, no_aplica=bool(v.no_aplica), respuesta=res.get(v.id)) for v in cat]

@router.put("/formulario/{form_id}/variables-tecnico-respuestas")
def put_vars_tec_resp(form_id:int, body:schemas.VarsRespuestaUpsertIn, db:Session=Depends(get_db)):
    pares = [(int(x.id), (x.respuesta or "").upper()) for x in (body.respuestas or [])]
    proyecto_service.upsert_respuestas_tecnico(db, form_id, pares)
    return {"ok": True}

@router.get("/formulario/{form_id}/viabilidades-respuestas", response_model=list[schemas.VarRespuestaRead])
def get_viab_resp(form_id:int, db:Session=Depends(get_db)):
    form = proyecto_service.obtener_formulario(db, form_id)
    if not form: raise HTTPException(404, "Formulario no encontrado")
    cat = proyecto_service.listar_cat_viabilidad(db)
    res = proyecto_service.leer_respuestas_viab(db, form_id)
    return [schemas.VarRespuestaRead(id=v.id, nombre=v.nombre, no_aplica=bool(v.no_aplica), respuesta=res.get(v.id)) for v in cat]

@router.put("/formulario/{form_id}/viabilidades-respuestas")
def put_viab_resp(form_id:int, body:schemas.VarsRespuestaUpsertIn, db:Session=Depends(get_db)):
    pares = [(int(x.id), (x.respuesta or "").upper()) for x in (body.respuestas or [])]
    proyecto_service.upsert_respuestas_viab(db, form_id, pares)
    return {"ok": True}