-- Historial de observaciones / viabilidades del evaluador
CREATE TABLE IF NOT EXISTS observacion_evaluacion (
    id SERIAL PRIMARY KEY,
    id_formulario INT NOT NULL REFERENCES formulario(id) ON DELETE CASCADE,
    tipo_documento TEXT NOT NULL CHECK (tipo_documento IN ('OBSERVACIONES', 'VIABILIDAD')),
    contenido_html TEXT NOT NULL,
    nombre_evaluador TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_observacion_evaluacion_formulario
    ON observacion_evaluacion (id_formulario);

CREATE INDEX IF NOT EXISTS ix_observacion_evaluacion_created_at
    ON observacion_evaluacion (created_at DESC);
