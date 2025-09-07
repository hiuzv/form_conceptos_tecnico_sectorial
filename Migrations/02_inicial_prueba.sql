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
  ('Uno'),
  ('Dos'),
  ('Tres');

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