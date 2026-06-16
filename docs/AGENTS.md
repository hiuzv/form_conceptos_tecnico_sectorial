# AGENTS.md - Guia de desarrollo del proyecto

Este documento define las reglas de trabajo para agentes y desarrolladores que modifiquen esta aplicacion. Su objetivo es proteger las funcionalidades actuales, ordenar la evolucion del backend/frontend/base de datos y guiar la futura importacion de proyectos desde `MGA.xml`.

## 1. Estado actual que debe conservarse

La aplicacion ya tiene flujos funcionales que no deben romperse durante refactors o nuevas funcionalidades.

### 1.1 Roles actuales

Actualmente no hay autenticacion real ni gestion de usuarios. La aplicacion permite cambiar rol manualmente desde la pantalla inicial. Esta capacidad debe mantenerse hasta que exista una gestion formal de usuarios.

Roles visibles:

- `dependencia`: crea y edita proyectos.
- `radicador`: registra radicado, fecha, BPIN y soportes.
- `evaluador`: genera documentos de observaciones, viabilidad y viabilidad ajustada.

Regla: aunque se agreguen permisos teoricos o guards, no eliminar el selector manual de rol mientras no exista autenticacion.

### 1.2 Funcionalidades frontend a preservar

- Listado paginado de proyectos.
- Filtros por radicado, nombre, codigo MGA y dependencia.
- Columna de radicado como primera columna del listado.
- Creacion manual de proyectos.
- Edicion de proyectos existentes.
- Guardado por pasos del formulario.
- Seleccion de dependencia, linea estrategica, sector, programa y metas PDD.
- Registro de estructura financiera base.
- Registro de estructura financiera ajustada para viabilidad ajustada.
- Radicacion del proyecto: numero de radicacion, fecha, BPIN, folios, planos, CDs y otros soportes.
- Editor enriquecido para evaluador.
- Pegado de tablas en el editor con normalizacion de ancho.
- Importacion de Word `.docx` al editor de evaluador.
- Insercion y ajuste de imagenes en el editor.
- Generacion de PDF para observaciones, viabilidad y viabilidad ajustada.
- Descarga de documentos Word y Excel existentes.

### 1.3 Funcionalidades backend a preservar

- CRUD parcial del formulario/proyecto.
- Listado de proyectos con paginacion y filtros.
- Catalogos: dependencias, lineas, sectores, programas, metas, variables, politicas, categorias, subcategorias, viabilidad y tipos de viabilidad.
- Asociacion del formulario con metas PDD.
- Guardado de estructura financiera base.
- Guardado de estructura financiera ajustada.
- Guardado de variables tecnicas, sectoriales y respuestas de viabilidad.
- Registro de observaciones/evaluaciones.
- Generacion de Excel, Word y PDF.
- Importacion de `.docx` para convertirlo en HTML editable.

## 2. Estructura actual del backend

El backend actual esta organizado principalmente asi:

```text
Backend/
  main.py
  schemas.py
  models/
  routes/
    proyecto.py
    descarga.py
  services/
    proyecto_service.py
    descarga_service.py
    excel_fill.py
    word_fill.py
  utils/
    config.py
    database.py
```

Regla: no meter mas logica pesada en `routes`. Las rutas deben delegar en servicios. Si una funcionalidad empieza a crecer, crear un servicio propio.

## 3. Migraciones existentes y responsabilidades

Antes de tocar modelos o tablas, revisar `Migrations/`.

### 3.1 Inventario de migraciones

| Archivo | Proposito |
|---|---|
| `01_Tablas.sql` | Crea la estructura inicial: catalogos, formulario, metas, estructura financiera, viabilidades, funcionarios, periodo lema y observaciones. |
| `02_inicial_prueba.sql` | Carga datos iniciales de catalogos: dependencias, lineas, sectores, programas, metas, politicas, categorias, subcategorias y variables. |
| `03_viabilidad_indicadores_meta_proyecto.sql` | Refuerza/crea soporte para indicadores de observacion/evaluacion y meta del proyecto asociada a metas. |
| `04_cargar_unidad_medida_meta_desde_plan_indicativo.sql` | Actualiza unidades de medida de metas desde plan indicativo. |

### 3.2 Tablas actuales que deben respetarse

- `dependencia`
- `linea_estrategica`
- `sector`
- `programa`
- `formulario`
- `meta`
- `metas`
- `variable_sectorial`
- `variables_sectorial`
- `variable_tecnico`
- `variables_tecnico`
- `politica`
- `politicas`
- `categoria`
- `categorias`
- `subcategoria`
- `subcategorias`
- `estructura_financiera`
- `estructura_financiera_ajustada`
- `viabilidad`
- `viabilidades`
- `tipo_viabilidad`
- `funcionario_viabilidad`
- `periodo_lema`
- `observacion_evaluacion`
- `observacion_evaluacion_indicador`

Nota: `estructura_financiera_ajustada` existe como modelo actual y debe quedar reflejada en migraciones si el entorno destino no la tiene.

### 3.3 Reglas para nuevas migraciones

- No modificar datos de produccion manualmente.
- Toda tabla/columna nueva debe tener migracion.
- No borrar columnas ni tablas existentes sin plan de migracion.
- No cambiar tipos de columnas existentes sin migracion de datos.
- Crear indices para filtros frecuentes.
- Agregar constraints solo si los datos existentes ya cumplen.
- Cada migracion debe tener nombre descriptivo y estar ordenada.
- Si se agrega un modelo SQLAlchemy, debe existir migracion equivalente.

## 4. Convencion REST/API objetivo

Actualmente existen endpoints utiles, pero varios nombres mezclan singular/plural, guiones/underscore y acciones dentro de la URL. La evolucion debe llevarlos gradualmente a una API REST consistente.

### 4.1 Reglas de formato

- Prefijo recomendado: `/api/v1`.
- Recursos en plural: `/projects`, `/dependencies`, `/sectors`.
- Usar `kebab-case` en paths: `financial-structure`, no `estructura_financiera`.
- IDs como path params: `/projects/{project_id}`.
- Subrecursos bajo el recurso principal: `/projects/{project_id}/goals`.
- Acciones no CRUD solo cuando sea inevitable: `/preview`, `/render`, `/import`.
- Query params para filtros y paginacion: `?page=1&page_size=10&radicado=...`.
- Respuestas paginadas con formato estable:

```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "page_size": 10
}
```

### 4.2 Verbos HTTP

| Verbo | Uso |
|---|---|
| `GET` | Consultar recursos. |
| `POST` | Crear recursos o ejecutar procesos de generacion/importacion que producen resultado. |
| `PUT` | Reemplazar completamente un subrecurso o coleccion. |
| `PATCH` | Actualizar parcialmente un recurso. |
| `DELETE` | Eliminar o cancelar recursos, si se implementa. |

### 4.3 Formato de errores

Usar errores consistentes:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Mensaje claro para usuario/desarrollador",
    "details": []
  }
}
```

FastAPI puede seguir usando `HTTPException`, pero los endpoints nuevos deben intentar responder con este formato.

## 5. Mapeo de endpoints actuales a REST/API objetivo

No renombrar todo de golpe si rompe el frontend. Crear endpoints nuevos, migrar frontend y luego retirar endpoints viejos cuando no se usen.

### 5.1 Proyecto y listado

| Actual | Objetivo REST |
|---|---|
| `GET /proyecto/lista` | `GET /api/v1/projects` |
| `POST /proyecto/formulario` | `POST /api/v1/projects` |
| `POST /proyecto/formulario/minimo` | `POST /api/v1/projects/minimal` o eliminar si `POST /projects` soporta modo minimo |
| `GET /proyecto/formulario/{form_id}` | `GET /api/v1/projects/{project_id}` |
| `PATCH /proyecto/formulario/{form_id}/basicos` | `PATCH /api/v1/projects/{project_id}` |
| `PUT /proyecto/formulario/{form_id}/radicacion` | `PUT /api/v1/projects/{project_id}/filing` |

### 5.2 Catalogos

| Actual | Objetivo REST |
|---|---|
| `GET /proyecto/dependencias` | `GET /api/v1/dependencies` |
| `GET /proyecto/lineas` | `GET /api/v1/strategic-lines` |
| `GET /proyecto/sectores?linea_id=` | `GET /api/v1/sectors?strategic_line_id=` |
| `GET /proyecto/programas?sector_id=` | `GET /api/v1/programs?sector_id=` |
| `GET /proyecto/metas?programa_id=` | `GET /api/v1/goals?program_id=` |
| `GET /proyecto/politicas` | `GET /api/v1/policies` |
| `GET /proyecto/categorias` | `GET /api/v1/categories` |
| `GET /proyecto/subcategorias` | `GET /api/v1/subcategories` |
| `GET /proyecto/viabilidad` | `GET /api/v1/viability-criteria` |
| `GET /proyecto/tipos_viabilidad` | `GET /api/v1/viability-types` |

### 5.3 Subrecursos del proyecto

| Actual | Objetivo REST |
|---|---|
| `PUT /proyecto/formulario/{form_id}/metas` | `PUT /api/v1/projects/{project_id}/goals` |
| `PUT /proyecto/formulario/{form_id}/estructura-financiera` | `PUT /api/v1/projects/{project_id}/financial-structure` |
| `GET /proyecto/formulario/{form_id}/estructura-financiera-ajustada` | `GET /api/v1/projects/{project_id}/adjusted-financial-structure` |
| `PUT /proyecto/formulario/{form_id}/estructura-financiera-ajustada` | `PUT /api/v1/projects/{project_id}/adjusted-financial-structure` |
| `PUT /proyecto/formulario/{form_id}/politicas` | `PUT /api/v1/projects/{project_id}/policies` |
| `PUT /proyecto/formulario/{form_id}/categorias` | `PUT /api/v1/projects/{project_id}/categories` |
| `PUT /proyecto/formulario/{form_id}/subcategorias` | `PUT /api/v1/projects/{project_id}/subcategories` |
| `PUT /proyecto/formulario/{form_id}/variables-sectorial` | `PUT /api/v1/projects/{project_id}/sector-variables` |
| `GET /proyecto/formulario/{form_id}/variables-sectorial-respuestas` | `GET /api/v1/projects/{project_id}/sector-variable-answers` |
| `PUT /proyecto/formulario/{form_id}/variables-sectorial-respuestas` | `PUT /api/v1/projects/{project_id}/sector-variable-answers` |
| `PUT /proyecto/formulario/{form_id}/variables-tecnico` | `PUT /api/v1/projects/{project_id}/technical-variables` |
| `GET /proyecto/formulario/{form_id}/variables-tecnico-respuestas` | `GET /api/v1/projects/{project_id}/technical-variable-answers` |
| `PUT /proyecto/formulario/{form_id}/variables-tecnico-respuestas` | `PUT /api/v1/projects/{project_id}/technical-variable-answers` |
| `PUT /proyecto/formulario/{form_id}/viabilidades` | `PUT /api/v1/projects/{project_id}/viability-criteria` |
| `GET /proyecto/formulario/{form_id}/viabilidades-respuestas` | `GET /api/v1/projects/{project_id}/viability-answers` |
| `PUT /proyecto/formulario/{form_id}/viabilidades-respuestas` | `PUT /api/v1/projects/{project_id}/viability-answers` |
| `PUT /proyecto/formulario/{form_id}/funcionarios-viabilidad` | `PUT /api/v1/projects/{project_id}/viability-officials` |
| `GET /proyecto/formulario/{form_id}/observaciones` | `GET /api/v1/projects/{project_id}/evaluations` |
| `POST /proyecto/formulario/{form_id}/observaciones` | `POST /api/v1/projects/{project_id}/evaluations` |

### 5.4 Descargas y renderizado

| Actual | Objetivo REST |
|---|---|
| `GET /descarga/excel/concepto-tecnico-sectorial/{form_id}` | `GET /api/v1/projects/{project_id}/exports/technical-sector-concept.xlsx` |
| `GET /descarga/excel/cadena-valor/{form_id}` | `GET /api/v1/projects/{project_id}/exports/value-chain.xlsx` |
| `GET /descarga/excel/viabilidad-dependencias/{form_id}` | `GET /api/v1/projects/{project_id}/exports/dependency-viability.xlsx` |
| `GET /descarga/word/carta/{form_id}` | `GET /api/v1/projects/{project_id}/exports/presentation-letter.docx` |
| `GET /descarga/word/cert-precios/{form_id}` | `GET /api/v1/projects/{project_id}/exports/price-certificate.docx` |
| `GET /descarga/word/no-doble-cofin/{form_id}` | `GET /api/v1/projects/{project_id}/exports/no-double-cofinancing.docx` |
| `POST /descarga/evaluador/import-word` | `POST /api/v1/evaluator-documents/import-word` |
| `POST /descarga/evaluador/template/{doc_key}/{form_id}` | `POST /api/v1/projects/{project_id}/evaluator-documents/{doc_key}/render-html` |
| `POST /descarga/evaluador/pdf/{doc_key}/{form_id}` | `POST /api/v1/projects/{project_id}/evaluator-documents/{doc_key}/render-pdf` |

## 6. Estrategia para ajustar endpoints sin romper la app

1. Mantener endpoints actuales mientras el frontend los use.
2. Crear routers nuevos versionados (`/api/v1/...`) que llamen los mismos services.
3. Agregar schemas de respuesta estables.
4. Migrar el frontend endpoint por endpoint.
5. Dejar compatibilidad temporal en endpoints antiguos.
6. Documentar deprecaciones.
7. Retirar endpoints antiguos solo cuando no haya referencias en frontend.

Regla: no hacer un cambio masivo de rutas sin migrar y probar frontend.

## 7. Importacion MGA.xml

La importacion MGA debe implementarse como funcionalidad adicional, no como reemplazo del flujo manual.

### 7.1 Reglas obligatorias

- No guardar inmediatamente al subir XML.
- Primero generar preview.
- No usar IDs externos como FKs internas.
- Separar `Project/Id` y `Project/BPIN`.
- Mostrar advertencias y campos pendientes.
- No sobrescribir proyectos existentes sin confirmacion.
- Guardar importaciones de forma transaccional.
- Mantener trazabilidad del XML original.

### 7.2 Mapeo base desde XML

| XML | Destino actual | Regla |
|---|---|---|
| `Project/Name` | `formulario.nombre_proyecto` | Texto directo. |
| `Project/Id` | `formulario.cod_id_mga` | ID externo MGA/PIIP. |
| `Project/BPIN` | `formulario.bpin` | Codigo BPIN. |
| `Project/ObjectivePeople` | `formulario.cantidad_beneficiarios` | Convertir a entero. |
| `Project/Sector/Code` | `formulario.id_sector` | Buscar `sector.id` por `sector.codigo_sector`. |
| `Project/ProgramId` | `formulario.id_programa` | Buscar `programa.id` por `programa.codigo_programa`. |
| `Product/ProductCatalog/codigo` | `metas.id_meta` | Buscar `meta.id` por `meta.codigo_producto`. |
| `Product/AutomaticIndicatorGoal` | `metas.meta_proyecto` | Normalizar decimal. |
| `Project/PeriodZero` | Estructura financiera / UI | Usar como ano base. |

### 7.3 IDs que no deben insertarse directamente

- `Project/SectorId`
- `PublicationContribution/Program/Id`
- `MunicipalityId`
- `ActorId`
- `PositionId`
- `RiskType/Id`
- `Probability/Id`
- `Impact/Id`
- Cualquier ID de catalogo MGA que no sea codigo local validado.

### 7.4 Informacion MGA no cubierta por BD actual

El XML trae informacion que hoy no tiene destino normalizado:

- Problema central.
- Magnitud del problema.
- Causas y efectos.
- Objetivos especificos.
- Indicadores del objetivo general.
- Localizaciones y municipios.
- Alternativas.
- Productos MGA detallados.
- Actividades e insumos.
- Regionalizacion.
- Riesgos.
- Participantes.
- Beneficios economicos.
- Evaluaciones economicas.
- Auditoria externa MGA.

Ver tambien: `docs/analisis_importacion_mga_xml.md`.

## 8. Estructura financiera e importacion MGA

La BD actual espera:

```text
estructura_financiera(id_formulario, anio, entidad, valor)
```

El XML puede traer periodos o vigencias como `0`, `1`, `2`, etc. Estos no son anos reales. Deben convertirse asi:

```text
anio = Project/PeriodZero + vigencia_mga
```

No inventar fuentes de financiacion si el XML no trae una fuente compatible con:

- `DEPARTAMENTO`
- `PROPIOS`
- `SGP_*`
- `MUNICIPIO`
- `NACION`
- `OTROS`

Si el XML solo trae costos por actividad, insumo o regionalizacion, usar esos valores como referencia/advertencia, no como distribucion automatica por entidad financiadora.

## 9. Tablas nuevas recomendadas para MGA

Agregar solo cuando se implemente la fase correspondiente:

- `mga_importacion`
- `mga_xml_raw`
- `proyecto_localizacion`
- `proyecto_problema`
- `proyecto_causa`
- `proyecto_efecto`
- `proyecto_objetivo_especifico`
- `proyecto_objetivo_indicador`
- `proyecto_alternativa`
- `proyecto_producto_mga`
- `proyecto_actividad`
- `proyecto_insumo`
- `proyecto_riesgo`
- `proyecto_participante`
- `proyecto_beneficio`
- `proyecto_evaluacion_economica`

Cada tabla nueva debe tener:

- Modelo SQLAlchemy.
- Schema Pydantic.
- Migracion SQL.
- Indices/FKs razonables.
- Pruebas o verificacion manual documentada.

## 10. Arquitectura deseada

El objetivo es avanzar gradualmente hacia una estructura modular:

```text
Backend/
  routes/
    projects.py
    catalogs.py
    exports.py
    evaluator_documents.py
    mga_imports.py
  services/
    proyecto_service.py
    catalog_service.py
    export_service.py
    evaluator_document_service.py
    mga_parser_service.py
    mga_mapping_service.py
    mga_import_service.py
  repositories/
    project_repository.py
    catalog_repository.py
    mga_import_repository.py
  schemas/
    project_schema.py
    catalog_schema.py
    mga_import_schema.py
```

No es obligatorio hacer toda la reorganizacion en una sola tarea. Priorizar cambios pequenos y verificables.

## 11. Seguridad

### 11.1 XML

- Validar extension `.xml`.
- Limitar tamano.
- Validar nodo raiz `Project`.
- Desactivar DTD y entidades externas.
- Evitar XXE.
- Normalizar Unicode y limpiar caracteres no imprimibles.
- No ejecutar ni interpretar contenido del XML como codigo.

### 11.2 Archivos Word

- Aceptar solo `.docx`.
- Limitar tamano.
- No confiar en nombres de archivo.
- Convertir contenido a HTML sanitizado/controlado.

### 11.3 Roles

Mientras no haya autenticacion real, las reglas de permisos son principalmente de UI. Si se implementan endpoints sensibles nuevos, deben quedar preparados para validar permisos en backend cuando exista usuario real.

## 12. Pruebas y verificacion obligatoria

Segun el cambio, ejecutar:

### Backend

```powershell
python -m py_compile Backend/routes/proyecto.py Backend/services/proyecto_service.py
python -m py_compile Backend/routes/descarga.py Backend/services/descarga_service.py
```

### Frontend

```powershell
npm.cmd run build
```

En este entorno, el build puede fallar dentro del sandbox por permisos de Windows/esbuild. Si falla por `Acceso denegado` al resolver `vite.config.ts`, repetir fuera del sandbox con aprobacion.

### Base de datos

- Revisar migraciones antes de cambiar modelos.
- Confirmar que `Base.metadata.create_all` no se use como sustituto de migraciones en entornos controlados.
- Si se agrega tabla nueva, probar migracion en base limpia y en base con datos existentes.

## 13. No hacer

- No romper el selector manual de roles.
- No cambiar endpoints usados por frontend sin migracion gradual.
- No borrar migraciones existentes.
- No modificar catalogos iniciales sin entender su impacto.
- No insertar IDs MGA como FKs locales.
- No confundir `Project/Id` con `BPIN`.
- No guardar XML sin preview.
- No sobrescribir proyectos existentes automaticamente.
- No inventar dependencia, linea estrategica o fuentes de financiacion.
- No esconder advertencias al usuario.
- No mezclar parsing XML, reglas de negocio y SQL en un mismo bloque.
- No dejar nuevos modelos sin migracion.
- No dejar salidas de build como `tsconfig.tsbuildinfo` si no deben versionarse.

## 14. Orden recomendado de trabajo

1. Documentar el estado actual y el contrato esperado.
2. Crear endpoints REST versionados en paralelo a los actuales.
3. Migrar frontend gradualmente a `/api/v1`.
4. Agregar tests/verificaciones por cada migracion.
5. Implementar preview MGA sin guardar.
6. Implementar confirmacion MGA transaccional.
7. Agregar tablas extendidas MGA por fases.
8. Separar servicios y repositorios solo cuando reduzca complejidad real.

## 15. Criterios de aceptacion para futuras tareas MGA/API

Una tarea relacionada con MGA/API debe considerarse completa solo si:

- Mantiene funcionales los tres roles actuales.
- Mantiene listado, filtros y paginacion.
- Mantiene creacion manual y edicion.
- Mantiene generacion de documentos.
- Respeta migraciones existentes.
- Usa endpoints REST/API nuevos o documenta la compatibilidad temporal.
- No inserta IDs externos como internos.
- Muestra preview y advertencias antes de guardar XML.
- Compila frontend/backend o documenta por que no pudo verificarse.

