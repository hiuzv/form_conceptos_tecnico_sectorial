-- DROP ALL
DROP TABLE periodo_lema;
DROP TABLE funcionario_viabilidad;
DROP TABLE tipo_viabilidad;
DROP TABLE viabilidades;
DROP TABLE viabilidad;
DROP TABLE personas;
DROP TABLE estructura_financiera;
DROP TABLE subcategorias;
DROP TABLE subcategoria;
DROP TABLE categorias;
DROP TABLE categoria;
DROP TABLE politicas;
DROP TABLE politica;
DROP TABLE variables_sectorial;
DROP TABLE variable_sectorial;
DROP TABLE variables_tecnico;
DROP TABLE variable_tecnico;
DROP TABLE metas;
DROP TABLE meta;
DROP TABLE formulario;
DROP TABLE programa;
DROP TABLE sector;
DROP TABLE linea_estrategica;
DROP TABLE dependencia;

-- Tabla: dependencia
CREATE TABLE dependencia (
    id SERIAL PRIMARY KEY,
    nombre_dependencia TEXT NOT NULL
);

-- Tabla: linea_estrategica
CREATE TABLE linea_estrategica (
    id SERIAL PRIMARY KEY,
    nombre_linea_estrategica TEXT NOT NULL
);

-- Tabla: sector
CREATE TABLE sector (
    id SERIAL PRIMARY KEY,
    id_linea_estrategica INT NOT NULL REFERENCES linea_estrategica,
    codigo_sector INT NOT NULL,
    nombre_sector TEXT NOT NULL
);

-- Tabla: programa
CREATE TABLE programa (
    id SERIAL PRIMARY KEY,
    id_sector INT NOT NULL REFERENCES sector,
    codigo_programa INT NOT NULL,
    nombre_programa TEXT NOT NULL
);

-- Tabla: formulario
CREATE TABLE formulario (
    id SERIAL PRIMARY KEY,
    nombre_proyecto TEXT NOT NULL,
    cod_id_mga INT NOT NULL,
    id_dependencia INT NOT NULL REFERENCES dependencia,
    id_linea_estrategica INT REFERENCES linea_estrategica,
    id_programa INT REFERENCES programa,
    id_sector INT REFERENCES sector,
    nombre_secretario TEXT,
    oficina_secretario TEXT,
    duracion_proyecto INT,
    cantidad_beneficiarios INT
);

-- Tabla: meta
CREATE TABLE meta (
    id SERIAL PRIMARY KEY,
    id_programa INT NOT NULL REFERENCES programa,
    numero_meta INT NOT NULL,
    nombre_meta TEXT NOT NULL
);

-- Tabla: metas
CREATE TABLE metas (
    id SERIAL PRIMARY KEY,
    id_meta INT NOT NULL REFERENCES meta,
    id_formulario INT NOT NULL REFERENCES formulario
);

-- Tabla: variable_sectorial 
CREATE TABLE variable_sectorial (
    id SERIAL PRIMARY KEY,
    nombre_variable TEXT NOT NULL
);

-- Tabla: variables_sectorial
CREATE TABLE variables_sectorial (
    id SERIAL PRIMARY KEY,
    id_variable_sectorial INT NOT NULL REFERENCES variable_sectorial,
    id_formulario INT NOT NULL REFERENCES formulario
);

-- Tabla: variable_tecnico
CREATE TABLE variable_tecnico (
    id SERIAL PRIMARY KEY,
    nombre_variable TEXT NOT NULL
);

-- Tabla: variables_tecnico
CREATE TABLE variables_tecnico (
    id SERIAL PRIMARY KEY,
    id_variable_tecnico INT NOT NULL REFERENCES variable_tecnico,
    id_formulario INT NOT NULL REFERENCES formulario
);

-- Tabla: politica
CREATE TABLE politica (
    id SERIAL PRIMARY KEY,
    nombre_politica TEXT NOT NULL
);

-- Tabla: politicas
CREATE TABLE politicas (
    id SERIAL PRIMARY KEY,
    id_politica INT NOT NULL REFERENCES politica,
    id_formulario INT NOT NULL REFERENCES formulario,
    valor_destinado NUMERIC(18,2)
);

-- Tabla: categoria
CREATE TABLE categoria (
    id SERIAL PRIMARY KEY,
    id_politica INT NOT NULL REFERENCES politica,
    nombre_categoria TEXT NOT NULL
);

-- Tabla: categorias
CREATE TABLE categorias (
    id SERIAL PRIMARY KEY,
    id_categoria INT NOT NULL REFERENCES categoria,
    id_formulario INT NOT NULL REFERENCES formulario
);

-- Tabla: subcategoria
CREATE TABLE subcategoria (
    id SERIAL PRIMARY KEY,
    id_categoria INT NOT NULL REFERENCES categoria,
    nombre_subcategoria TEXT NOT NULL
);

-- Tabla: subcategorias
CREATE TABLE subcategorias (
    id SERIAL PRIMARY KEY,
    id_subcategoria INT NOT NULL REFERENCES subcategoria,
    id_formulario INT NOT NULL REFERENCES formulario
);

-- Tabla: estructura_financiera
CREATE TABLE estructura_financiera (
    id SERIAL PRIMARY KEY,
    id_formulario INT NOT NULL REFERENCES formulario,
    anio INT,
    entidad TEXT NOT NULL,
    valor NUMERIC(18,2)
);

-- Tabla: personas
CREATE TABLE personas (
    id SERIAL PRIMARY KEY,
    nombre TEXT NOT NULL,
    rol TEXT NOT NULL
);

-- Tabla: viabilidad
CREATE TABLE viabilidad (
    id SERIAL PRIMARY KEY,
    nombre TEXT NOT NULL
);

-- Tabla: viabilidades
CREATE TABLE viabilidades (
    id SERIAL PRIMARY KEY,
    id_viabilidad INT NOT NULL REFERENCES viabilidad,
    id_formulario INT NOT NULL REFERENCES formulario
);

-- Tabla: tipo_viabilidad
CREATE TABLE tipo_viabilidad (
    id SERIAL PRIMARY KEY,
    nombre TEXT NOT NULL
);

-- Tabla: funcionario_viabilidad
CREATE TABLE funcionario_viabilidad (
    id SERIAL PRIMARY KEY,
    nombre TEXT NOT NULL,
    cargo TEXT NOT NULL,
    id_tipo_viabilidad INT NOT NULL REFERENCES tipo_viabilidad,
    id_formulario INT NOT NULL REFERENCES formulario
);

-- Tabla: periodo_lema
CREATE TABLE periodo_lema (
    id SERIAL PRIMARY KEY,
    inicio_periodo INT NOT NULL,
    fin_periodo INT NOT NULL,
    lema TEXT NOT NULL
);