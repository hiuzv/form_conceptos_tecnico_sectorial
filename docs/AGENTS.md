# AGENTS.md — Implementación de importación de proyectos desde MGA.xml

## 1. Propósito del trabajo

Este archivo define las instrucciones que deben seguir los agentes de desarrollo para adaptar la aplicación y permitir que un proyecto pueda ser ingresado desde un archivo `.xml` exportado de MGA/PIIP, sin romper las funcionalidades existentes ni dañar proyectos ya guardados en la base de datos.

La implementación debe alinear las tres capas principales de la aplicación:

1. **Backend**
2. **Base de datos**
3. **Frontend**

La funcionalidad de importación debe integrarse con el formulario actual del proyecto, pero no debe convertir el código en un monolito. La solución debe reorganizarse progresivamente bajo una estructura tipo **MVC**, separando responsabilidades por dominio y por rol.

---

## 2. Principios obligatorios

### 2.1. No romper funcionalidades existentes

Antes de modificar código, identificar y conservar las funcionalidades ya implementadas, especialmente:

- Creación manual de proyectos.
- Edición de proyectos existentes.
- Consulta de proyectos guardados.
- Asociación de proyectos con sector, programa, línea estratégica, dependencia y metas PDD.
- Registro de estructura financiera.
- Flujo de revisión, evaluación u observaciones.
- Funcionalidades diferenciadas por rol.
- Generación o descarga de documentos, si ya existe.
- Validaciones actuales del formulario.
- Autenticación y autorización.

La importación desde XML debe ser una funcionalidad adicional, no un reemplazo destructivo del flujo actual.

### 2.2. No usar IDs externos como IDs internos

Los IDs provenientes del XML de MGA no deben insertarse directamente en columnas internas como:

- `formulario.id_sector`
- `formulario.id_programa`
- `formulario.id_dependencia`
- `metas.id_meta`
- Cualquier FK interna de la aplicación

Los IDs de MGA/PIIP y los IDs de la base de datos local son universos distintos.

Ejemplo crítico:

- `Project/SectorId = 46` no debe insertarse como `id_sector`.
- Debe usarse `Project/Sector/Code = 45` para buscar en la tabla local `sector.codigo_sector`.
- Luego se usa el `sector.id` local encontrado.

### 2.3. Separar `Project/Id` y `BPIN`

El XML contiene dos identificadores diferentes:

- `Project/Id`: identificador interno MGA/PIIP.
- `Project/BPIN`: código BPIN del proyecto.

Deben almacenarse separados:

- `Project/Id` → `formulario.cod_id_mga`
- `Project/BPIN` → `formulario.bpin`

No deben confundirse ni reemplazarse entre sí.

### 2.4. Importación segura e incremental

La importación debe hacerse por fases:

- **Fase 1:** precargar campos que ya existen en la base de datos.
- **Fase 2:** agregar nuevas tablas para guardar información MGA adicional.
- **Fase 3:** adaptar completamente el formulario frontend para capturar, mostrar y editar los nuevos campos.

No intentar guardar toda la información del XML en columnas que no corresponden.

---

## 3. Arquitectura esperada

La aplicación debe avanzar hacia una arquitectura MVC o modular equivalente.

### 3.1. Backend

Separar el backend mínimo en estas capas los nombres de los archivos son un ejemplo no deben ser usados exactamente como aparecen sino como mejor se adapte al proyecto:

```text
backend/
├── controllers/
│   ├── proyecto_controller.py
│   ├── importacion_mga_controller.py
│   ├── evaluacion_controller.py
│   └── roles_controller.py
│
├── services/
│   ├── proyecto_service.py
│   ├── importacion_mga_service.py
│   ├── mga_parser_service.py
│   ├── catalogo_mapping_service.py
│   ├── estructura_financiera_service.py
│   ├── validacion_importacion_service.py
│   └── descarga_service.py
│
├── repositories/
│   ├── proyecto_repository.py
│   ├── catalogo_repository.py
│   ├── importacion_mga_repository.py
│   ├── estructura_financiera_repository.py
│   ├── meta_repository.py
│   └── rol_repository.py
│
├── models/
│   ├── proyecto.py
│   ├── importacion_mga.py
│   ├── producto_mga.py
│   ├── actividad_mga.py
│   ├── riesgo_mga.py
│   ├── localizacion_mga.py
│   └── participante_mga.py
│
├── schemas/
│   ├── proyecto_schema.py
│   ├── importacion_mga_schema.py
│   ├── preview_importacion_schema.py
│   └── error_schema.py
│
└── utils/
    ├── xml_utils.py
    ├── number_utils.py
    ├── text_cleaner.py
    └── date_utils.py
```

La estructura exacta puede adaptarse al framework actual, pero deben mantenerse estas responsabilidades.

---

## 4. Responsabilidades por capa

## 4.1. Backend

El backend debe encargarse de:

- Recibir el archivo `.xml`.
- Validar que sea un archivo permitido.
- Leer el XML de forma segura.
- Extraer datos desde nodos MGA.
- Normalizar textos, números, fechas y booleanos.
- Mapear códigos MGA contra catálogos locales.
- Detectar datos faltantes o ambiguos.
- Construir una vista previa antes de guardar.
- Guardar la importación de forma transaccional.
- Evitar duplicados por `radicado`, `bpin` o `cod_id_mga`.
- Registrar errores de importación.
- No sobrescribir información existente sin control.
- Separar funcionalidades por rol.

### 4.1.1. Flujo recomendado de backend

```text
POST /api/importacion-mga/preview
    Recibe XML.
    Parsea archivo.
    Extrae datos.
    Mapea catálogos.
    Retorna vista previa con campos detectados, advertencias y errores.

POST /api/importacion-mga/confirmar
    Recibe payload validado desde la vista previa.
    Crea o actualiza proyecto según reglas.
    Guarda datos base.
    Guarda metas.
    Guarda estructura financiera si hay regla definida.
    Guarda tablas MGA extendidas si existen.
    Retorna proyecto creado/actualizado.

GET /api/importacion-mga/{id}/estado
    Consulta estado de una importación.

GET /api/importacion-mga/{id}/errores
    Consulta errores o advertencias de importación.
```

### 4.1.2. Nunca guardar directamente desde el primer upload

No debe existir un flujo donde el usuario suba el XML y la aplicación guarde inmediatamente sin revisión.

Debe existir una etapa de **preview** donde el usuario vea:

- Proyecto detectado.
- BPIN.
- Código interno MGA.
- Sector detectado.
- Programa detectado.
- Año inicial.
- Beneficiarios.
- Productos/metas detectadas.
- Actividades y costos.
- Riesgos detectados.
- Información que no se pudo mapear.
- Campos que requieren selección manual.

---

## 4.2. Base de datos

La base de datos debe proteger la información existente.

### 4.2.1. Reglas de migración

Toda modificación de base de datos debe hacerse mediante migraciones, nunca editando manualmente la BD en producción.

Cada migración debe:

- Ser reversible cuando sea posible.
- No borrar columnas actuales.
- No cambiar tipos de datos actuales sin plan de migración.
- No eliminar datos existentes.
- Crear índices para búsquedas frecuentes.
- Crear constraints solo después de limpiar o validar datos existentes.
- Incluir comentarios o documentación de propósito.

### 4.2.2. Tablas existentes que deben respetarse

La aplicación ya trabaja principalmente con:

- `formulario`
- Catálogo de `dependencia`
- Catálogo de `linea_estrategica`
- Catálogo de `sector`
- Catálogo de `programa`
- Catálogo de `meta`
- Asociación de formulario con metas PDD
- `estructura_financiera`
- Respuestas técnico-sectoriales o de viabilidad
- Observaciones/evaluaciones

La importación no debe romper esta estructura.

### 4.2.3. Campos actuales que se pueden precargar

En la primera fase, se deben cargar los campos que ya tienen destino claro:

| Fuente XML | Destino BD actual | Regla |
|---|---|---|
| `Project/Name` | `formulario.nombre_proyecto` | Texto directo |
| `Project/Id` | `formulario.cod_id_mga` | Guardar como ID externo MGA |
| `Project/BPIN` | `formulario.bpin` | Guardar como BPIN |
| `Project/ObjectivePeople` | `formulario.cantidad_beneficiarios` | Convertir a entero |
| `Project/Sector/Code` | `formulario.id_sector` | Buscar `sector.id` por `sector.codigo_sector` |
| `Project/ProgramId` | `formulario.id_programa` | Buscar `programa.id` por `programa.codigo_programa` |
| `Product/ProductCatalog/codigo` | Meta asociada | Buscar por `meta.codigo_producto` |
| `Product/AutomaticIndicatorGoal` | `meta_proyecto` o equivalente | Normalizar decimal |

### 4.2.4. Campos que no deben inventarse

No se debe inventar información para:

- `id_dependencia`
- `id_linea_estrategica`
- Fuentes de financiación
- Entidad financiadora de estructura financiera
- Municipios si no existe catálogo
- Roles o responsables internos
- Estados internos del sistema

Si el XML no trae un dato compatible con la BD actual, debe quedar como pendiente para selección manual o guardarse en una tabla extendida de importación.

### 4.2.5. Tablas nuevas recomendadas

Para aprovechar mejor el XML, crear progresivamente estas tablas:

```text
mga_importacion
mga_xml_raw
proyecto_localizacion
proyecto_problema
proyecto_causa
proyecto_efecto
proyecto_objetivo_especifico
proyecto_objetivo_indicador
proyecto_alternativa
proyecto_producto_mga
proyecto_actividad
proyecto_insumo
proyecto_riesgo
proyecto_participante
proyecto_beneficio
proyecto_evaluacion_economica
```

### 4.2.6. Tabla `mga_importacion`

Debe registrar cada intento de importación.

Campos sugeridos:

```sql
id
id_formulario
cod_id_mga
bpin
nombre_archivo
hash_archivo
estado
errores_json
advertencias_json
created_at
created_by
updated_at
```

Estados posibles:

```text
PENDIENTE
PREVISUALIZADA
CONFIRMADA
CONFIRMADA_CON_ADVERTENCIAS
ERROR
CANCELADA
```

### 4.2.7. Tabla `mga_xml_raw`

Debe guardar el XML original o una referencia segura al archivo.

Campos sugeridos:

```sql
id
id_importacion
xml_original
xml_normalizado
hash_archivo
created_at
```

Si el XML es grande, puede guardarse en almacenamiento externo y registrar solo la ruta y hash.

### 4.2.8. Constraints recomendados

Agregar restricciones sin romper datos existentes:

```sql
UNIQUE NULLS DISTINCT (bpin)
UNIQUE NULLS DISTINCT (cod_id_mga)
INDEX formulario(bpin)
INDEX formulario(cod_id_mga)
INDEX sector(codigo_sector)
INDEX programa(codigo_programa)
INDEX meta(codigo_producto)
INDEX mga_importacion(hash_archivo)
```

Si el motor de BD no soporta `UNIQUE NULLS DISTINCT`, usar índices únicos parciales cuando aplique.

---

## 4.3. Frontend

El frontend debe adaptarse al flujo de importación y a los nuevos campos.

### 4.3.1. Objetivo del frontend

El usuario debe poder:

1. Crear un proyecto manualmente como antes.
2. Subir un archivo `.xml` de MGA.
3. Ver una vista previa clara de la información encontrada.
4. Corregir campos no detectados o no mapeados.
5. Confirmar la importación.
6. Continuar editando el proyecto con el formulario normal.
7. Guardar toda la información necesaria del proyecto sin perder datos.

### 4.3.2. Flujo visual recomendado

```text
Paso 1: Seleccionar método de creación
    - Crear manualmente
    - Importar desde MGA.xml

Paso 2: Subir archivo XML
    - Validar extensión
    - Mostrar nombre del archivo
    - Mostrar peso
    - Enviar a preview

Paso 3: Vista previa de datos detectados
    - Datos básicos
    - Sector/programa/metas detectadas
    - Beneficiarios
    - Año inicial
    - Productos
    - Actividades y costos
    - Localizaciones
    - Riesgos
    - Participantes
    - Advertencias

Paso 4: Resolver campos pendientes
    - Dependencia
    - Línea estratégica
    - Fuentes de financiación
    - Entidades financiadoras
    - Campos que el XML no trae
    - Catálogos no encontrados

Paso 5: Confirmar importación
    - Resumen final
    - Botón guardar
    - Confirmación de no sobrescritura accidental

Paso 6: Formulario completo del proyecto
    - Permitir editar y completar
    - Guardar normalmente
```

### 4.3.3. Adaptación del formulario

El formulario debe estar alineado con los nuevos campos. No debe forzar toda la información en una sola pantalla.

Separar el formulario por pasos:

```text
1. Datos básicos del proyecto
2. Clasificación PDD / sector / programa / metas
3. Población beneficiaria y localización
4. Problema, causas, efectos y objetivos
5. Productos, indicadores y metas
6. Actividades e insumos
7. Estructura financiera
8. Riesgos
9. Participantes
10. Beneficios y evaluación económica
11. Revisión final
```

Cada paso debe poder guardar parcialmente si la arquitectura actual lo permite.

### 4.3.4. Manejo visual de datos importados

Los campos importados desde XML deben marcarse visualmente:

- `Importado desde MGA`
- `Editado manualmente`
- `Pendiente por validar`
- `No encontrado en catálogo local`
- `Requiere selección manual`

Esto evita que el usuario crea que todo fue validado automáticamente.

### 4.3.5. No ocultar advertencias

El frontend debe mostrar advertencias importantes, por ejemplo:

- Sector detectado, pero mapeado por código local.
- Programa detectado, pero validado por código.
- BPIN ya existe.
- Proyecto MGA ya existe.
- Existen costos, pero no fuentes de financiación.
- Existen municipios, pero no hay catálogo local de municipios.
- Hay riesgos en XML, pero la BD actual no tiene tabla de riesgos.
- Hay campos no guardados por falta de estructura en BD.

---

## 5. Reglas de importación desde XML

## 5.1. Parser XML

Crear un servicio dedicado:

```text
mga_parser_service.py
```

Responsabilidades:

- Leer XML.
- Validar estructura mínima.
- Extraer nodos principales.
- Manejar nodos repetidos.
- Manejar nodos faltantes.
- Limpiar caracteres no imprimibles.
- Normalizar Unicode.
- Convertir números.
- Convertir fechas.
- Convertir booleanos.
- Devolver un objeto intermedio independiente de la BD.

No mezclar parsing con consultas SQL.

### 5.1.1. Estructura intermedia recomendada

```json
{
  "project": {
    "mga_id": "1681834",
    "bpin": "202600000005404",
    "name": "...",
    "sector_code": "45",
    "sector_description": "Gobierno Territorial",
    "program_code": "4501",
    "program_description": "Fortalecimiento de la convivencia y la seguridad ciudadana",
    "period_zero": 2026,
    "affected_people": 1605145,
    "objective_people": 15816,
    "phase": "Factibilidad",
    "status": "Viable",
    "entity_name": "Cauca"
  },
  "products": [],
  "activities": [],
  "inputs": [],
  "localizations": [],
  "risks": [],
  "participants": [],
  "benefits": [],
  "objective_indicators": [],
  "warnings": [],
  "errors": []
}
```

---

## 5.2. Mapping de catálogos

Crear un servicio dedicado:

```text
catalogo_mapping_service.py
```

Responsabilidades:

- Buscar sector local por `codigo_sector`.
- Buscar programa local por `codigo_programa`.
- Buscar meta local por `codigo_producto`.
- Validar nombres/descripciones como respaldo.
- Reportar coincidencias ambiguas.
- Reportar catálogos no encontrados.
- Nunca crear catálogos automáticamente sin instrucción explícita.

### 5.2.1. Reglas de sector

```text
XML: Project/Sector/Code
BD: sector.codigo_sector
Resultado: sector.id local
```

No usar:

```text
Project/SectorId
```

### 5.2.2. Reglas de programa

```text
XML: Project/ProgramId
BD: programa.codigo_programa
Resultado: programa.id local
```

No usar:

```text
PublicationContribution/Program/Id
```

### 5.2.3. Reglas de metas/productos

```text
XML: Product/ProductCatalog/codigo
BD: meta.codigo_producto
Resultado: meta.id local o asociación equivalente
```

Validar adicionalmente con:

```text
Product/AutoIndicatorName
```

---

## 5.3. Estructura financiera

La estructura financiera actual de la aplicación debe quedar ligada a la estructura financiera que llega desde el XML de MGA, usando las **vigencias MGA** como base para construir los años reales del proyecto.

El XML puede traer valores financieros asociados a vigencias como:

```text
Vigencia 0
Vigencia 1
Vigencia 2
Vigencia 3
```

Estas vigencias no deben guardarse literalmente como años. Deben convertirse a años reales tomando como base el año inicial del proyecto.

Ejemplo:

```text
Project/PeriodZero = 2026

Vigencia MGA 0 → Año 2026
Vigencia MGA 1 → Año 2027
Vigencia MGA 2 → Año 2028
Vigencia MGA 3 → Año 2029
```

La fórmula general debe ser:

```text
anio_estructura_financiera = Project/PeriodZero + vigencia_mga
```

Por tanto, si la MGA trae costos por vigencia, estos valores deben usarse como referencia para construir o validar la estructura financiera anual de la aplicación.

La BD actual espera algo similar a:

```text
estructura_financiera(id_formulario, anio, entidad, valor)
```

Sin embargo, la MGA no trae las **fuentes de financiación** que maneja la aplicación. Por eso, el sistema debe importar o calcular el valor total por vigencia/año, pero dejar pendiente la distribución entre fuentes de financiación.

### 5.3.1. Regla obligatoria

La aplicación debe relacionar cada valor financiero de la MGA con un año real de la estructura financiera local usando:

```text
Project/PeriodZero + vigencia_mga
```

No se debe llenar automáticamente `estructura_financiera.entidad` si el XML no trae una fuente financiadora equivalente.

Las fuentes de financiación deben quedar como información pendiente de diligenciar o distribuir manualmente por el usuario.

### 5.3.2. Manejo de fuentes de financiación pendientes

Cuando el XML tenga valores financieros por vigencia, pero no tenga fuentes de financiación compatibles, el frontend debe permitir repartir el valor de cada vigencia entre las fuentes disponibles en la aplicación.

Ejemplo:

```text
Año 2026 / Vigencia 0
Valor MGA esperado: $100.000.000

Distribución pendiente:
- Departamento: $______
- Municipio: $______
- Nación: $______
- Otros: $______
```

El usuario debe poder distribuir el valor de la vigencia entre diferentes fuentes de financiación.

El sistema debe calcular:

```text
valor_total_mga_por_vigencia
valor_total_distribuido_por_fuentes
diferencia = valor_total_mga_por_vigencia - valor_total_distribuido_por_fuentes
```

### 5.3.3. Validación por vigencia

La validación debe hacerse por cada vigencia convertida a año.

Ejemplo:

```text
Project/PeriodZero = 2026

Vigencia 0 / Año 2026:
Valor MGA: $100.000.000
Valor distribuido en fuentes: $100.000.000
Diferencia: $0

Vigencia 1 / Año 2027:
Valor MGA: $150.000.000
Valor distribuido en fuentes: $140.000.000
Diferencia: $10.000.000
Advertencia: la distribución no coincide con el valor MGA de la vigencia.
```

Por ahora, esta validación debe ser una **advertencia no bloqueante**.

Esto significa que el sistema debe permitir guardar el proyecto aunque existan diferencias, pero debe mostrar claramente la inconsistencia al usuario.

### 5.3.4. Estados sugeridos para la estructura financiera importada

Cada año financiero puede tener un estado de validación:

```text
PENDIENTE_DISTRIBUCION
DISTRIBUIDO_CONCUERDA
DISTRIBUIDO_CON_ADVERTENCIA
SIN_VALOR_MGA
```

Uso sugerido:

- `PENDIENTE_DISTRIBUCION`: existe valor MGA por vigencia, pero aún no se ha repartido entre fuentes.
- `DISTRIBUIDO_CONCUERDA`: la suma por fuentes coincide con el valor MGA esperado.
- `DISTRIBUIDO_CON_ADVERTENCIA`: la suma por fuentes no coincide con el valor MGA esperado.
- `SIN_VALOR_MGA`: no se encontró valor financiero claro para esa vigencia.

### 5.3.5. Preview financiero

En la vista previa de importación, el backend debe entregar un resumen financiero por vigencia/año:

```json
{
  "estructura_financiera_mga": [
    {
      "vigencia_mga": 0,
      "anio": 2026,
      "valor_mga": 100000000,
      "valor_distribuido": 0,
      "diferencia": 100000000,
      "estado": "PENDIENTE_DISTRIBUCION",
      "advertencias": [
        "La MGA no trae fuente de financiación. Debe distribuir el valor entre las fuentes disponibles."
      ]
    },
    {
      "vigencia_mga": 1,
      "anio": 2027,
      "valor_mga": 150000000,
      "valor_distribuido": 0,
      "diferencia": 150000000,
      "estado": "PENDIENTE_DISTRIBUCION",
      "advertencias": [
        "La MGA no trae fuente de financiación. Debe distribuir el valor entre las fuentes disponibles."
      ]
    }
  ]
}
```

### 5.3.6. Validaciones financieras

El sistema debe comparar:

```text
Total MGA por vigencia
Total actividades por vigencia, si existe
Total insumos por vigencia, si existe
Total regionalización por vigencia, si existe
Total distribuido por fuentes en la estructura financiera local
```

La validación principal debe ser:

```text
Total MGA por vigencia/año = Total distribuido entre fuentes para ese mismo año
```

Si no coincide, mostrar advertencia no bloqueante.

No se debe impedir el guardado del proyecto por diferencias financieras mientras esta regla se encuentre en fase de advertencia.

### 5.3.7. No hacer

No hacer lo siguiente:

- No ignorar las vigencias MGA.
- No guardar `vigencia 0`, `vigencia 1`, `vigencia 2` como si fueran años.
- No inventar fuentes de financiación.
- No asignar todo automáticamente a una fuente sin confirmación del usuario.
- No bloquear el guardado solo porque la distribución financiera no coincida.
- No mezclar valores de diferentes vigencias en un mismo año.
- No validar únicamente el total global del proyecto; la validación debe hacerse por vigencia/año.

---

## 6. Separación por roles

Las funcionalidades de cada rol deben estar separadas en backend y frontend.

### 6.1. Roles sugeridos

Adaptar los nombres a los roles reales del sistema.

```text
Administrador (Acceso completo)
Formulador (Dependencia)
Radicador (Radicador)
Evaluador (Evaluador)
Consulta/Lectura (Pendiente una ventana de visualización de información completa de todos los proyectos)
```

AUNQUE CREEMOS LOS ROLES SEGUIMOS MANTENIENDO LA FUNCIONALIDA DE CAMBIAR ROL PARA PODER USAR LAS DIFERENTES FUNCIONALIDADES SIN TENER GESTIÓN DE USUARIOS AUN

### 6.2. Permisos mínimos

| Funcionalidad | Administrador | Formulador | Radicador | Evaluador | Consulta |
|---|---:|---:|---:|---:|---:|
| Subir XML | Sí | Sí | No | No | No |
| Ver preview XML | Sí | Sí | Sí | Sí | No |
| Confirmar importación | Sí | Sí | No | No | No |
| Editar datos base | Sí | Sí | No/Solo observación | No/Solo observación | No |
| Editar estructura financiera | Sí | Sí | No | No | No |
| Editar riesgos | Sí | Sí | No | No | No |
| Ver proyecto | Sí | Sí | Sí | Sí | Sí |
| Eliminar importación | Sí | No | No | No | No |
| Reprocesar XML | Sí | Sí, si es propietario | No | No | No |
| Radicar | Sí | No | Sí | No | No |
| Evaluar | Sí | No | No | Sí | No |

### 6.3. Backend por roles

No dejar validaciones solo en frontend.

Cada endpoint sensible debe validar permisos:

```text
POST /api/importacion-mga/preview
POST /api/importacion-mga/confirmar
PUT /api/proyectos/{id}
DELETE /api/proyectos/{id}
```

### 6.4. Frontend por roles

Separar vistas o componentes por rol:

```text
frontend/
├── roles/
│   ├── admin/
│   ├── formulador/
│   ├── evaluador/
│   ├── revisor/
│   └── consulta/
```

También puede hacerse con guards y componentes compartidos, pero la lógica de permisos no debe quedar dispersa.

---

## 7. Manejo de proyectos existentes

## 7.1. Identificación de duplicados

Antes de guardar, buscar proyectos existentes por:

```text
radicado
bpin
cod_id_mga
nombre_proyecto
hash_archivo
```

Prioridad:

1. `cod_id_mga`
2. `radicado`
3. `bpin`
4. coincidencia aproximada de nombre
5. `hash_archivo`

### 7.2. Si el proyecto ya existe

El sistema debe ofrecer:

```text
- Cancelar importación
- Crear nuevo proyecto como copia
- Actualizar solo campos vacíos
- Actualizar campos seleccionados manualmente
- Reimportar XML como nueva versión
```

No debe sobrescribir todo automáticamente.

### 7.3. Historial de cambios

Toda importación que actualice un proyecto existente debe registrar:

- Usuario.
- Fecha.
- Campos modificados.
- Valor anterior.
- Valor nuevo.
- Origen del cambio: `MGA_XML`.

---

## 8. Validaciones obligatorias

## 8.1. Validaciones del archivo

- Extensión `.xml`.
- Tamaño máximo permitido.
- XML bien formado.
- Nodo `Project` existente.
- Presencia mínima de `Project/Name`, `Project/Id` o `Project/BPIN`.
- Rechazo de contenido peligroso.
- Desactivar resolución de entidades externas XML para evitar XXE.

## 8.2. Validaciones de datos

- `Project/Id` debe guardarse como identificador MGA externo.
- `BPIN` debe conservar ceros si existen.
- `PeriodZero` debe ser año válido.
- `ObjectivePeople` debe convertirse a entero.
- Valores monetarios deben convertirse a decimal.
- Fechas ISO deben convertirse correctamente.
- Booleanos `1/0` deben transformarse a `true/false` o `SI/NO`, según el caso.
- Textos largos deben normalizarse.
- Caracteres raros deben limpiarse sin destruir tildes ni ñ.

## 8.3. Validaciones de catálogos

- Sector debe mapearse por código.
- Programa debe mapearse por código.
- Meta/producto debe mapearse por código de producto.
- Descripciones deben usarse como validación secundaria.
- Si hay múltiples coincidencias, pedir selección manual.
- Si no hay coincidencia, marcar como pendiente.

---

## 9. Nuevos campos y secciones del formulario

El XML contiene información adicional que debe considerarse para ampliar el formulario.

### 9.1. Datos básicos

- Nombre del proyecto.
- Código interno MGA.
- BPIN.
- Año inicial.
- Estado MGA.
- Fase MGA.
- Entidad territorial.
- Población afectada.
- Población objetivo.

### 9.2. Clasificación

- Sector.
- Programa.
- Plan de desarrollo.
- Estrategia.
- Programa del plan.
- Línea estratégica local.
- Dependencia local.

### 9.3. Problema y objetivos

- Problema central.
- Magnitud del problema.
- Causas.
- Efectos.
- Objetivo general.
- Objetivos específicos.

### 9.4. Productos e indicadores

- Producto MGA.
- Código de producto.
- Indicador automático.
- Meta del producto.
- Unidad de medida.
- Fuente de verificación.

### 9.5. Actividades e insumos

- Actividades.
- Etapa.
- Costo.
- Insumos.
- Tipo de insumo.
- Valor del insumo.

### 9.6. Localización

- Región.
- Departamento.
- Municipio.
- Código DANE.
- Tipo de localización.
- Beneficiarios por municipio.
- Costos regionalizados.

### 9.7. Riesgos

- Tipo de riesgo.
- Descripción.
- Probabilidad.
- Impacto.
- Efectos.
- Medidas de mitigación.

### 9.8. Participantes

- Actor.
- Entidad.
- Posición.
- Experiencia.
- Tipo de aporte.
- Observaciones.

### 9.9. Beneficios

- Beneficio económico.
- Cantidad.
- Valor unitario.
- Valor total.
- Año.
- Evaluaciones económicas.

---

## 10. Contrato de datos entre frontend y backend

El frontend no debe depender directamente de la estructura cruda del XML.

El backend debe entregar un DTO estable.

### 10.1. DTO de preview

```json
{
  "archivo": {
    "nombre": "MGA.xml",
    "hash": "...",
    "estado": "PREVISUALIZADA"
  },
  "proyecto": {
    "nombre": "...",
    "cod_id_mga": "1681834",
    "bpin": "202600000005404",
    "anio_inicio": 2026,
    "cantidad_beneficiarios": 15816
  },
  "catalogos": {
    "sector": {
      "codigo_xml": "45",
      "descripcion_xml": "Gobierno Territorial",
      "id_local": 1,
      "estado": "MAPEADO"
    },
    "programa": {
      "codigo_xml": "4501",
      "descripcion_xml": "Fortalecimiento de la convivencia y la seguridad ciudadana",
      "id_local": 1,
      "estado": "MAPEADO"
    }
  },
  "pendientes": [
    {
      "campo": "id_dependencia",
      "motivo": "El XML no contiene dependencia interna de la aplicación."
    },
    {
      "campo": "estructura_financiera.entidad",
      "motivo": "El XML contiene costos, pero no fuente de financiación compatible."
    }
  ],
  "advertencias": [],
  "errores": []
}
```

---

## 11. Manejo de errores

Los errores deben ser entendibles para el usuario y útiles para el desarrollador.

### 11.1. Errores bloqueantes

Ejemplos:

```text
XML inválido.
No se encontró nodo Project.
No se encontró nombre del proyecto.
No se encontró código MGA.
Error de lectura del archivo.
El archivo supera el tamaño máximo permitido.
```

### 11.2. Advertencias no bloqueantes

Ejemplos:

```text
No se encontró dependencia local.
No se encontró línea estratégica local.
El sector fue mapeado por código, pero la descripción no coincide exactamente.
El XML contiene riesgos, pero la BD aún no tiene tabla de riesgos.
El XML contiene costos, pero no fuentes de financiación.
El proyecto ya existe con el mismo BPIN.
```

---

## 12. Pruebas obligatorias

## 12.1. Pruebas de backend

Crear pruebas para:

- XML válido.
- XML inválido.
- XML sin `Project`.
- XML sin BPIN.
- XML con `Project/Id` y BPIN.
- Sector mapeado correctamente por código.
- Programa mapeado correctamente por código.
- Rechazo de IDs externos como IDs internos.
- Detección de proyecto duplicado.
- Preview sin guardar datos.
- Confirmación con transacción.
- Rollback si falla una parte del guardado.
- Limpieza de caracteres raros.
- Conversión de valores monetarios.
- Conversión de fechas.
- Conversión de booleanos.
- Prevención XXE.

## 12.2. Pruebas de base de datos

Verificar:

- Migraciones aplican correctamente.
- Migraciones no borran proyectos existentes.
- Índices se crean correctamente.
- FKs nuevas no rompen registros viejos.
- Importación crea registros relacionados.
- Rollback funciona.
- No se duplican proyectos por BPIN.
- No se duplican proyectos por `cod_id_mga`.

## 12.3. Pruebas de frontend

Verificar:

- Carga de archivo XML.
- Visualización de preview.
- Campos detectados.
- Campos pendientes.
- Advertencias.
- Confirmación.
- Cancelación.
- Proyecto existente.
- Permisos por rol.
- Formulario por pasos.
- Guardado parcial.
- Edición posterior al importado.

---

## 13. Seguridad

### 13.1. XML seguro

El parser XML debe:

- Desactivar DTD.
- Desactivar entidades externas.
- Evitar XXE.
- Limitar tamaño del archivo.
- Limitar profundidad del árbol si es posible.
- No ejecutar contenido del XML.
- No confiar en rutas internas del XML.

### 13.2. Autorización

POR AHORA ESTO ES A MANERA TEORICA, SIN IMPLEMENTAR Cada acción debe validar:

- Usuario autenticado.
- Rol autorizado.
- Permiso sobre el proyecto.
- Propiedad o dependencia asignada, si aplica.

### 13.3. Auditoría

Registrar:

- Usuario que sube XML.
- Fecha de carga.
- IP o sesión si el sistema lo maneja.
- Resultado de validación.
- Confirmación de importación.
- Cambios aplicados a proyecto existente.

---

## 14. Reglas para refactorizar código existente

### 14.1. Evitar monolito

No agregar toda la lógica al controlador actual del formulario.

Mal ejemplo:

```text
formulario_controller.py
    - parsea XML
    - consulta catálogos
    - valida roles
    - guarda proyecto
    - guarda metas
    - guarda estructura financiera
    - genera documentos
```

Buen ejemplo:

```text
importacion_mga_controller.py
    - recibe request
    - llama servicios
    - retorna response

mga_parser_service.py
    - extrae datos del XML

catalogo_mapping_service.py
    - resuelve IDs locales

importacion_mga_service.py
    - coordina preview y confirmación

proyecto_repository.py
    - guarda proyecto

meta_repository.py
    - guarda metas

estructura_financiera_repository.py
    - guarda valores financieros
```

### 14.2. Refactor gradual

No reescribir toda la aplicación al mismo tiempo.

Orden recomendado:

1. Crear servicios nuevos para importación.
2. Crear endpoint de preview.
3. Crear DTO estable.
4. Crear frontend de carga y preview.
5. Crear endpoint de confirmación.
6. Agregar tablas nuevas mínimas.
7. Separar componentes del formulario por pasos.
8. Separar vistas por rol.
9. Mover lógica antigua a servicios/repositories poco a poco.

---

## 15. Criterios de aceptación

La tarea se considera correctamente implementada cuando:

- El usuario puede subir un `MGA.xml`.
- El sistema genera una vista previa sin guardar inmediatamente.
- Se detectan nombre, código MGA, BPIN, sector, programa, año inicial y beneficiarios.
- Sector y programa se mapean usando códigos, no IDs externos.
- `Project/Id` y `BPIN` quedan separados.
- El sistema muestra campos pendientes para dependencia, línea estratégica y financiación.
- El usuario puede corregir o completar campos pendientes.
- La confirmación guarda el proyecto sin romper registros existentes.
- Si el proyecto ya existe, no se sobrescribe sin confirmación.
- La importación queda registrada.
- El XML original queda trazable.
- El formulario frontend queda dividido en pasos lógicos.
- Las funcionalidades por rol siguen funcionando.
- Las pruebas cubren importación, duplicados, roles y rollback.
- El código queda separado en controladores, servicios, repositorios, modelos/schemas y componentes frontend.

---

## 16. No hacer

No realizar estas acciones:

- No insertar `Project/SectorId` como `formulario.id_sector`.
- No insertar `PublicationContribution/Program/Id` como `formulario.id_programa`.
- No confundir `Project/Id` con BPIN.
- No guardar el XML sin preview.
- No sobrescribir proyectos existentes automáticamente.
- No inventar dependencia.
- No inventar línea estratégica.
- No inventar fuentes de financiación.
- No meter toda la lógica en un solo archivo.
- No mezclar parsing XML con SQL.
- No dejar permisos solo en frontend.
- No borrar datos viejos con migraciones.
- No crear catálogos automáticamente sin validación.
- No ocultar advertencias al usuario.

---

## 17. Orden sugerido de implementación

### Sprint 1 — Base técnica

- Crear `mga_parser_service`.
- Crear `catalogo_mapping_service`.
- Crear DTO de preview.
- Crear endpoint `/importacion-mga/preview`.
- Crear pruebas del parser.
- Crear pruebas de mapping.

### Sprint 2 — Vista previa frontend

- Crear pantalla para subir XML.
- Crear componente de preview.
- Mostrar datos detectados.
- Mostrar advertencias y pendientes.
- Validar roles para subir XML.

### Sprint 3 — Confirmación segura

- Crear migración `mga_importacion`.
- Crear migración `mga_xml_raw` o almacenamiento equivalente.
- Crear endpoint `/importacion-mga/confirmar`.
- Guardar proyecto en transacción.
- Detectar duplicados.
- Registrar auditoría.

### Sprint 4 — Formulario por pasos

- Dividir formulario actual.
- Adaptar campos nuevos.
- Marcar campos importados.
- Permitir completar campos pendientes.
- Mantener creación manual.

### Sprint 5 — Importación enriquecida

- Crear tablas de problema, productos, actividades, riesgos, participantes, localizaciones y beneficios.
- Guardar información extendida.
- Mostrar nuevas secciones en frontend.
- Agregar pruebas integrales.

---

## 18. Resultado esperado

Al finalizar, la aplicación debe permitir registrar proyectos desde un archivo MGA.xml de manera controlada, validada y trazable. El sistema debe conservar las funcionalidades actuales, mejorar la organización del código, separar responsabilidades por capa y rol, proteger los IDs internos, respetar la información ya guardada y preparar el formulario para capturar toda la información relevante del proyecto.
