# Tasks: 007-evaluacion-modelo — incremento 1 (partición por paciente)

**Input**: `specs/007-evaluacion-modelo/spec.md` (versión abreviada, sin plan.md separado).
**Tests**: primero, y se ve que fallan antes de implementar.

## Tests (antes del código)

- [X] T001 [US1] `tests/test_particion_paciente.py`: `grupo_paciente` ignora sufijo, espacios y
  mayúsculas; sin identificador devuelve `None`; el grupo es un hash, no el identificador.
- [X] T002 [US1] `particion_por_grupos`: ningún grupo en ambos lados; fracción de validación entre
  15 % y 25 %; dos clases en cada lado; determinista con la misma semilla.
- [X] T003 [US1] `VetVisionEtapa0Dataset.grupos` queda alineado con `samples`.

## Implementación

- [X] T004 [US1] `src/particion.py`: `grupo_paciente`, `particion_por_grupos`, `huella_particion`,
  `PARTICION_POR_DEFECTO`.
- [X] T005 [US1] `src/dataset.py`: exponer `grupos` (hash) por muestra.
- [X] T006 [US1] `src/train.py`: parámetros `split` y `model_path`; registrar en MLflow solo conteos y
  huella; no sobrescribir el checkpoint de la Corrida 3.
- [X] T007 [US1] `specs/model-tensor.spec.yaml` + verificador en `harness/contratos.py` (FR-006).

## Verificación

- [X] T008 Prueba de humo del entrenamiento con datos sintéticos (1 época) antes de la corrida larga.
- [X] T009 Comprobar SC-001 y SC-002 sobre el dataset real (solo conteos).
- [ ] T010 Lanzar la Corrida 4 en segundo plano y evaluarla; registrar en `ENTRENAMIENTOS.md` (SC-003).
- [X] T011 `python -m harness` en verde (SC-004).
