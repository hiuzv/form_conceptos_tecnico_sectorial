INSERT INTO dependencia (nombre_dependencia) VALUES
  ('General'),
  ('Salud'),
  ('Infraestructura');

INSERT INTO linea_estrategica (nombre_linea_estrategica) VALUES
  ('Uno'),
  ('Dos'),
  ('Tres');

INSERT INTO programa (codigo_programa, nombre_programa, id_linea_estrategica) VALUES
  (1, 'Uno', 1),
  (2, 'Dos', 2),
  (3, 'Tres', 3);

INSERT INTO sector (codigo_sector, nombre_sector, id_programa) VALUES
  (1, 'Uno', 1),
  (2, 'Dos', 2),
  (3, 'Tres', 3);

INSERT INTO meta (numero_meta, nombre_meta, id_sector) VALUES
  (1, 'Uno', 1),
  (2, 'Dos', 2),
  (3, 'Tres', 3);

INSERT INTO variable (nombre_variable) VALUES
  ('ES COMPETENCIA DE LA DEPENDENCIA SECTORIAL PROPONENTE, LA IMPLEMENTACIÓN DEL PROYECTO'),
  ('LAS METAS  DEL PROYECTO, ESTAN CLARAMENTE DEFINIDAS Y CUANTIFICADAS Y CONTRINUYEN EFECTIVAMENTE AL LOGRO DE METAS DEL PROGRAMA DEL PLAN DEPARTAMENTAL DE DESARROLLO'),
  ('EL PROYECTO DA RESPUESTA A LAS NECESIDADES DEL SECTOR PARA EL QUE FUE FORMULADO'),
  ('EL PROBLEMA ESTA BIEN DEFINIDO, SON CLARAS SUS CAUSAS Y SUS EFETOS DIRECTOS E INDIRECTOS'),
  ('ESTAN CLARAMENTE DETERMINADOS EL OBJETIVO GENERAL Y LOS OBJETIVOS ESPECIFICOS'),
  ('EL PROYECTO TIENE DEFINIDA LA LOCALIZACIÓN DE LA INTERVENCIÓN'),
  ('EL PROYECTO TIENE DEFINIDA LA POBLACIÓN OBJETO DE LA INTERVENCIÓN'),
  ('LA ALTERNATIVA SELECCIONADA SOLUCIONA EFECTIVAMENTE EL PROBLEMA ENUNCIADO POR ESTA DEPENDENCIA'),
  ('LAS ACTIVIDADES PLANTEADAS SON COHERENTES CON LOS PRODUCTOS Y ESTOS CON  LOS OBJETIVOS ESPECIFICOS');

INSERT INTO politica (nombre_politica) VALUES
  ('Uno'),
  ('Dos'),
  ('Tres');

INSERT INTO categoria (nombre_categoria, id_politica) VALUES
  ('Uno', 1),
  ('Dos', 2),
  ('Tres', 3);

INSERT INTO subcategoria (nombre_subcategoria, id_categoria) VALUES
  ('Uno', 1),
  ('Dos', 2),
  ('Tres', 3);