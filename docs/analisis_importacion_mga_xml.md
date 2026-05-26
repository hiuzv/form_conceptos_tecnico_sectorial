# Analisis de importacion desde MGA.xml

Archivo analizado: `form_conceptos_tecnico_sectorial/MGA.xml`

Fecha del analisis: 2026-05-26

## Resumen ejecutivo

El XML de MGA contiene informacion suficiente para precargar una parte importante del formulario del proyecto: nombre, codigo interno MGA, BPIN, sector, programa, ano inicial, poblacion beneficiaria, localizacion municipal, objetivo general, productos, actividades, costos e indicadores.

La base de datos actual cubre principalmente:

- Datos basicos del formulario.
- Catalogos de dependencia, linea estrategica, sector, programa y metas PDD.
- Asociacion del formulario con metas PDD.
- Estructura financiera por ano y entidad.
- Variables tecnico/sectoriales y viabilidad como respuestas manuales.
- Observaciones/evaluaciones generadas por el evaluador.

El XML trae bastante informacion adicional de MGA que hoy no tiene tablas equivalentes: problema central, causas, efectos, alternativas, productos MGA detallados, actividades, insumos, localizaciones, riesgos, participantes, beneficios economicos, fuentes de verificacion e indicadores del objetivo general.

## Datos identificados en el XML

Valores principales observados:

| Campo XML | Valor detectado |
|---|---|
| `Project/Id` | `1681834` |
| `Project/Name` | `Desarrollo de intervenciones orientadas a la reducción de la reproducción de caninos y felinos en el Departamento del.. Cauca` |
| `Project/BPIN` | `202600000005404` |
| `Project/Sector/Code` | `45` |
| `Project/Sector/Description` | `Gobierno Territorial` |
| `Project/ProgramId` | `4501` |
| `Project/Program` | `4501 - Fortalecimiento de la convivencia y la seguridad ciudadana` |
| `Project/PeriodZero` | `2026` |
| `Project/AffectedPeople` | `1605145` |
| `Project/ObjectivePeople` | `15816` |
| `Project/Phase/Name` | `Factibilidad` |
| `Project/Status/DisplayName` | `Viable` |
| `Project/Entity/Name` | `Cauca` |
| `Project/PublicationContribution/DevelopmentPlan` | `Plan de Desarrollo Departamental 2024-2027 “La Fuerza del Pueblo”.` |
| `Project/PublicationContribution/Strategy` | `Cauca Productivo y sostenible` |
| `Project/PublicationContribution/ProgramDescription` | `Fortalecimiento de la convivencia y la seguridad ciudadana` |

Conteos relevantes:

| Seccion XML | Cantidad |
|---|---:|
| `Localizations/Localization` | 57 |
| `Alternatives/Alternative` | 2 |
| `Products/Product` | 1 |
| `Activities/Activity` | 2 |
| `Risks/Risk` | 4 |
| `Participants/Participant` | 3 |
| `ObjectiveIndicators/ObjectiveIndicator` | 2 |

## Informacion que podemos extraer directamente hacia el proyecto

Estos campos pueden poblar columnas existentes con conversion minima de tipo:

| XML | BD actual | Observacion |
|---|---|---|
| `Project/Name` | `formulario.nombre_proyecto` | Texto directo. |
| `Project/Id` | `formulario.cod_id_mga` | Entero directo. Corresponde al identificador interno del proyecto MGA/PIIP. |
| `Project/BPIN` | `formulario.bpin` | Texto directo. No debe confundirse con `cod_id_mga`. |
| `Project/PeriodZero` | `formulario.anio_inicio` en UI / estructura financiera | Ano base del proyecto. La tabla `formulario` no tiene `anio_inicio`; hoy se infiere desde `estructura_financiera`. |
| `Project/ObjectivePeople` | `formulario.cantidad_beneficiarios` | Entero directo. En el XML: `15816`. |
| `Project/Program` | Campo informativo de programa | El texto completo puede usarse para mostrar o validar, pero en BD se almacena el ID interno del catalogo `programa`. |
| `Project/Sector/Description` | Campo informativo de sector | El texto puede usarse para validar o buscar catalogo. |
| `Project/Entity/Name` | No hay columna directa, pero podria validar que es Cauca | La entidad territorial no se almacena como campo del formulario. |
| `Project/Phase/Name` | No hay columna directa | Podria usarse como dato documental: `Factibilidad`. |
| `Project/Status/DisplayName` | No hay columna directa | Podria usarse como dato documental: `Viable`. |

Tambien se puede extraer contenido textual util para documentos, aunque no haya columna especifica:

| XML | Uso potencial |
|---|---|
| `Project/ParticipantsCoordination` | Texto para antecedentes/coordinacion institucional. |
| `Project/Scope` | Resumen largo del alcance del proyecto. |
| `Project/CentralProblem/CentralProblem` | Problema central del proyecto. |
| `Project/GeneralObjective/GeneralObjective` | Objetivo general, aunque en este XML parece repetir el problema central. |
| `Project/CentralProblem/Causes/Cause/SpecificObjective/SpecificObjective` | Objetivos especificos. |

## Informacion que puede extraerse pero tiene formato diferente

Estos datos existen, pero habria que formatearlos antes de insertarlos en plantillas o compararlos con la UI.

| XML | Formato XML | Formato esperado / sugerido |
|---|---|---|
| `Project/AffectedPeople` | Numero entero sin separadores: `1605145` | Mostrar como `1.605.145` si va a documentos. |
| `Project/ObjectivePeople` | Numero entero sin separadores: `15816` | Mostrar como `15.816`; guardar como entero. |
| `Product/Amount` | Decimal MGA: `4519.0000` | Para metas: entero o decimal normalizado `4519`; para texto: `4.519`. |
| `Product/AutomaticIndicatorGoal` | Decimal MGA: `4519.0000` | Igual que meta del indicador. |
| `Activity/Cost` | Decimal con punto: `849572000.00` | En BD `NUMERIC(18,2)`; en documento `$849.572.000` o `849.572.000,00`. |
| `Input/WeightValue` | Decimal con punto: `147000000.00` | En documento financiero debe formatearse como pesos. |
| `Regionalization/Input/Cost` | Decimal por municipio | Sumar o agrupar si se quiere llevar a estructura financiera. |
| `Created`, `Modified`, `VigenciaDesde`, `VigenciaHasta` | ISO datetime | Convertir a fecha local o descartar hora si solo se necesita fecha. |
| `BenefitCostEvaluation`, `CostEfficiencyEvaluation`, `MultiCriteriaEvaluation` | `1` / `0` | Convertir a booleano o `SI` / `NO` si se usa en documentos. |

### Casos numero a texto

El XML entrega numeros; si los documentos requieren texto en letras, hay que transformar:

| Dato | Valor XML | Posible salida textual |
|---|---:|---|
| Costo actividad principal | `849572000.00` | `Ochocientos cuarenta y nueve millones quinientos setenta y dos mil pesos M/cte.` |
| Costo actividad secundaria | `7546730.00` | `Siete millones quinientos cuarenta y seis mil setecientos treinta pesos M/cte.` |
| Total actividades detectadas | `857118730.00` | `Ochocientos cincuenta y siete millones ciento dieciocho mil setecientos treinta pesos M/cte.` |
| Beneficiarios objetivo | `15816` | `Quince mil ochocientos dieciseis` |

Nota: el backend ya tiene una utilidad `numero_a_texto` en `descarga_service.py`, pero hoy no hay flujo de importacion desde XML que la use.

## Informacion que podemos extraer, pero requiere transformacion de IDs

La mayor parte de los catalogos de MGA usan IDs propios que no son necesariamente los IDs internos de nuestra BD. Por eso no conviene insertar directamente esos IDs en `formulario.id_sector`, `formulario.id_programa`, `metas.id_meta`, etc. Hay que mapear por codigo o por descripcion.

| XML | Valor XML | BD actual | Transformacion requerida |
|---|---|---|---|
| `Project/Sector/Code` | `45` | `sector.codigo_sector` | Buscar `sector.id` donde `codigo_sector = 45`. No usar `Project/SectorId = 46` directamente. |
| `Project/Sector/Description` | `Gobierno Territorial` | `sector.nombre_sector` | Usar como respaldo para validar el codigo. |
| `Project/ProgramId` | `4501` | `programa.codigo_programa` | Buscar `programa.id` donde `codigo_programa = 4501`. |
| `Project/PublicationContribution/Program/Id` | `1181` | No coincide con `programa.id` local | No insertar directo; es ID de catalogo MGA. |
| `Product/ProductCatalog/codigo` | `4501061` | `meta.codigo_producto` | Buscar metas PDD que tengan `codigo_producto = 4501061`. |
| `Product/AutoIndicatorName` | `Animales atendidos` | `meta.nombre_indicador_producto` | Validar con texto y/o codigo de indicador. |
| `Product/AutomaticIndicatorMeasureTypeId` | `13` | `meta.unidad_medida` o catalogo no existente | Requiere traducir ID de unidad a texto. En el XML aparece unidad como `Número de animales` en `MeasureType/Description`. |
| `Localizations/Localization/MunicipalityId` | Ej. `374` | No existe catalogo municipal en BD | Si se quisiera guardar municipios, se requiere nueva tabla o mapeo externo por DANE/codigo. |
| `Localization/Municipality/Code` | Ej. `19532` | No existe catalogo municipal en BD | Usar codigo DANE si se crea tabla de municipios. |
| `Participant/ActorId`, `PositionId`, `EntityId` | IDs MGA | No existen tablas equivalentes | Requiere catalogos nuevos si se quiere normalizar participantes. |
| `Risk/RiskType/Id`, `Probability/Id`, `Impact/Id` | IDs MGA | No existen tablas equivalentes | Requiere catalogos de riesgos o guardar texto plano. |
| `ObjectiveIndicator/MeasureUnitId` | `13`, `15` | No existe catalogo de unidades general | Requiere mapa ID -> unidad o usar descripciones disponibles cuando existan. |

### Mapeos que parecen viables con la BD actual

| Elemento | Evidencia |
|---|---|
| Sector `Gobierno Territorial` codigo `45` | Existe en migracion `02_inicial_prueba.sql` como sector. |
| Programa `4501 - Fortalecimiento de la convivencia y la seguridad ciudadana` | Existe en migracion `02_inicial_prueba.sql`. |
| Producto `4501061 - Servicio de atención integral a la fauna` | Existe en migracion `02_inicial_prueba.sql`. |
| Indicador `450106100 - Animales atendidos` | Existe en migracion `02_inicial_prueba.sql`. |
| Meta PDD relacionada | En migracion aparece la meta `15.000 animales atendidos a través de actividades de bienestar animal`. |

## Informacion que podemos extraer, pero no encaja directamente en la estructura financiera actual

La BD actual tiene:

```text
estructura_financiera(id_formulario, anio, entidad, valor)
```

El XML analizado contiene costos de actividades, insumos y regionalizacion, pero no se observa una seccion clara de fuentes de financiacion tipo `DEPARTAMENTO`, `MUNICIPIO`, `NACION`, `OTROS`, `SGP_*` como espera la UI.

Datos financieros disponibles:

| XML | Que representa |
|---|---|
| `Activities/Activity/Cost` | Costo total por actividad. |
| `Inputs/Input/WeightValue` | Valor por insumo dentro de una actividad. |
| `Regionalization/Region/Inputs/Input/Cost` | Costo regionalizado por municipio/localizacion. |
| `Benefits/Benefit/BenefitDetails/TotalValue` | Valor de beneficios economicos, no fuente de financiacion. |

Conclusion: se puede calcular un costo total del proyecto desde actividades o regionalizacion, pero no se puede llenar automaticamente la estructura financiera por entidad financiadora sin una regla adicional. Se requeriria definir:

- Si todo va a `DEPARTAMENTO`.
- Si se distribuye por participantes.
- Si existe otro XML/seccion con fuentes de financiacion que no esta presente en este archivo.

## Informacion no considerada actualmente en nuestras BD

Estas secciones existen en el XML, pero no tienen tablas/campos equivalentes directos en el modelo actual.

| Seccion XML | Informacion | Estado en BD actual |
|---|---|---|
| `CentralProblem` | Problema central, magnitud, causas, efectos, objetivos especificos | No hay tablas de problema/causas/efectos/objetivos. |
| `GeneralObjective/ObjectiveIndicators` | Indicadores de objetivo general, metas, fuentes de verificacion | Solo hay indicadores manuales asociados a observacion de evaluacion; no como parte del formulario base. |
| `Localizations` | Region, departamento, municipio, tipo de localizacion, codigos DANE | No hay tabla de municipios/localizacion del proyecto. |
| `Participants` | Actores, entidades, tipo de aporte, experiencia | No hay tabla de participantes del proyecto. |
| `Alternatives` | Alternativas, estado, seleccion, analisis tecnico | No hay tabla de alternativas. |
| `AnalyzedFactors` | Factores analizados para alternativa | No hay tabla equivalente. |
| `ServiceGoods` | Bien/servicio, oferta, demanda, deficit historico | No hay tabla equivalente. |
| `Products` | Producto MGA, complemento, beneficiarios, fuente de verificacion, regionalizacion | La BD tiene catalogo `meta`, pero no detalle de producto MGA por proyecto. |
| `Activities` | Actividades, costos, etapa | No hay tabla de actividades por producto. |
| `Inputs` | Insumos por actividad, tipo de insumo, valores | No hay tabla de insumos. |
| `Regionalization` | Metas, beneficiarios y costos por municipio | No hay tabla de regionalizacion. |
| `Risks` | Riesgos, probabilidad, impacto, efectos, mitigacion | No hay tabla de riesgos. |
| `Benefits` | Beneficios economicos, cantidades, valores unitarios, totales | No hay tabla de beneficios. |
| `EconomicEvaluations` | Evaluaciones economicas | No hay tabla equivalente. |
| `ProjectType`, `Process`, `Phase`, `BankType`, `Status` | Catalogos de estado/fase/proceso MGA | No se almacenan en `formulario`. |
| `Created`, `Modified`, `CreatedBy`, `ModifiedBy`, `Formulator` | Auditoria MGA | No hay campos de auditoria externa MGA. |

## Recomendacion de importacion por fases

### Fase 1: precarga segura sin cambiar modelo de BD

Se puede importar hacia campos existentes:

| Destino actual | Fuente XML |
|---|---|
| `formulario.nombre_proyecto` | `Project/Name` |
| `formulario.cod_id_mga` | `Project/Id` |
| `formulario.bpin` | `Project/BPIN` |
| `formulario.cantidad_beneficiarios` | `Project/ObjectivePeople` |
| `formulario.id_sector` | Buscar por `Project/Sector/Code` |
| `formulario.id_programa` | Buscar por `Project/ProgramId` |
| `metas` | Buscar meta por `Product/ProductCatalog/codigo` y `AutoIndicatorName` |
| `metas.meta_proyecto` | `Product/AutomaticIndicatorGoal` o `Product/Amount` |

Pendiente de definir:

- `formulario.id_dependencia`: el XML trae entidad territorial `Cauca`, pero no la dependencia interna departamental que usa la app.
- `formulario.id_linea_estrategica`: podria inferirse de `PublicationContribution/Strategy`, pero requiere validar que coincida con el catalogo local.
- `estructura_financiera`: el XML trae costos, pero no fuentes financiadoras compatibles con la UI actual.

### Fase 2: importacion enriquecida con nuevas tablas

Si se quiere aprovechar mas del XML, convendria agregar tablas para:

- `mga_importacion` o `mga_xml_raw`: guardar XML original y metadatos de importacion.
- `proyecto_localizacion`: municipios, region, departamento, tipo de localizacion.
- `proyecto_problema`: problema central, magnitud, causas, efectos.
- `proyecto_objetivo_indicador`: indicadores del objetivo general.
- `proyecto_alternativa`: alternativas y analisis tecnico.
- `proyecto_producto_mga`: productos por proyecto.
- `proyecto_actividad`: actividades y costos.
- `proyecto_insumo`: insumos por actividad.
- `proyecto_riesgo`: riesgos, probabilidad, impacto y mitigacion.
- `proyecto_participante`: participantes y aportes.
- `proyecto_beneficio`: beneficios economicos.

## Observaciones de calidad de datos

- `Project/Id` y `Project/BPIN` son distintos. Deben guardarse separados.
- `Project/SectorId = 46`, pero `Project/Sector/Code = 45`. Para nuestra BD conviene mapear por `Code = 45`, no por `SectorId`.
- `Project/ProgramId = 4501` funciona como codigo de programa; `PublicationContribution/Program/Id = 1181` es otro identificador MGA y no debe insertarse directo.
- El XML tiene caracteres raros en algunos textos de magnitud del problema; se recomienda normalizar Unicode/limpiar caracteres no imprimibles antes de guardar texto largo.
- `Project/Status` aparece como valor simple `101` y tambien como nodo complejo `Status`; el parser debe manejar nodos repetidos con el mismo nombre.
- `ProjectSummary.xml` en Descargas esta vacio; el archivo util analizado fue `form_conceptos_tecnico_sectorial/MGA.xml`.

