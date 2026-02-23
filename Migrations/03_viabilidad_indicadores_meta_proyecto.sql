ALTER TABLE metas
ADD COLUMN IF NOT EXISTS meta_proyecto TEXT;

ALTER TABLE meta
ADD COLUMN IF NOT EXISTS unidad_medida TEXT;

CREATE TABLE IF NOT EXISTS observacion_evaluacion_indicador (
    id SERIAL PRIMARY KEY,
    id_observacion_evaluacion INT NOT NULL REFERENCES observacion_evaluacion(id) ON DELETE CASCADE,
    orden INT NOT NULL DEFAULT 0,
    indicador_objetivo_general TEXT NOT NULL DEFAULT '',
    unidad_medida TEXT NOT NULL DEFAULT '',
    meta_resultado TEXT NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS ix_obs_eval_indicador_obs
    ON observacion_evaluacion_indicador (id_observacion_evaluacion, orden, id);
