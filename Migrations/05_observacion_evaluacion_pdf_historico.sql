ALTER TABLE observacion_evaluacion
    ADD COLUMN IF NOT EXISTS pdf_bytes BYTEA;

ALTER TABLE observacion_evaluacion
    ADD COLUMN IF NOT EXISTS pdf_filename TEXT;

ALTER TABLE observacion_evaluacion
    ADD COLUMN IF NOT EXISTS pdf_content_type TEXT;

ALTER TABLE observacion_evaluacion
    ADD COLUMN IF NOT EXISTS productos_ajustados JSONB;

ALTER TABLE observacion_evaluacion
    ADD COLUMN IF NOT EXISTS resultados_ajustados JSONB;

ALTER TABLE observacion_evaluacion
    ADD COLUMN IF NOT EXISTS numero_documento TEXT;
