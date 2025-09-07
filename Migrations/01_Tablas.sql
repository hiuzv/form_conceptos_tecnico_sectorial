-- DROP ALL
DROP TABLE subcategorias;
DROP TABLE subcategoria;
DROP TABLE categorias;
DROP TABLE categoria;
DROP TABLE politicas;
DROP TABLE politica;
DROP TABLE variables;
DROP TABLE variable;
DROP TABLE metas;
DROP TABLE meta;
DROP TABLE formulario;
DROP TABLE sector;
DROP TABLE programa;
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

-- Tabla: programa
CREATE TABLE programa (
    id SERIAL PRIMARY KEY,
    id_linea_estrategica INT NOT NULL REFERENCES linea_estrategica,
    codigo_programa INT NOT NULL,
    nombre_programa TEXT NOT NULL
);

-- Tabla: sector
CREATE TABLE sector (
    id SERIAL PRIMARY KEY,
    id_programa INT NOT NULL REFERENCES programa,
    codigo_sector INT NOT NULL,
    nombre_sector TEXT NOT NULL
);

-- Tabla: formulario
CREATE TABLE formulario (
    id SERIAL PRIMARY KEY,
    nombre_proyecto TEXT NOT NULL,
    cod_id_mga INT NOT NULL,
    id_dependencia INT NOT NULL REFERENCES dependencia,
    id_linea_estrategica INT NOT NULL REFERENCES linea_estrategica,
    id_programa INT NOT NULL REFERENCES programa,
    id_sector INT NOT NULL REFERENCES sector
);

-- Tabla: meta
CREATE TABLE meta (
    id SERIAL PRIMARY KEY,
    id_sector INT NOT NULL REFERENCES sector,
    numero_meta INT NOT NULL,
    nombre_meta TEXT NOT NULL
);

-- Tabla: metas
CREATE TABLE metas (
    id SERIAL PRIMARY KEY,
    id_meta INT NOT NULL REFERENCES meta,
    id_formulario INT NOT NULL REFERENCES formulario
);

-- Tabla: variable
CREATE TABLE variable (
    id SERIAL PRIMARY KEY,
    nombre_variable TEXT NOT NULL
);

-- Tabla: variables
CREATE TABLE variables (
    id SERIAL PRIMARY KEY,
    id_variable INT NOT NULL REFERENCES variable,
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
