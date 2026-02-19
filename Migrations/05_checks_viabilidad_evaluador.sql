ALTER TABLE observacion_evaluacion
    ADD COLUMN IF NOT EXISTS concepto_tecnico_favorable_dep TEXT;

ALTER TABLE observacion_evaluacion
    ADD COLUMN IF NOT EXISTS concepto_sectorial_favorable_dep TEXT;

ALTER TABLE observacion_evaluacion
    ADD COLUMN IF NOT EXISTS proyecto_viable_dep TEXT;
