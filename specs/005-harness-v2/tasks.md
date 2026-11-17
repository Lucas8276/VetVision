# Tasks: 005-harness-v2 — incremento 1 (verificación del documento)

**Input**: `specs/005-harness-v2/spec.md` (versión abreviada, sin plan.md separado).

## Tests

- [X] T001 `tests/test_harness_documento.py`: 13 tests con documentos sintéticos; cada regla tiene un
  caso que la dispara y uno que no (SC-001). Nota: los tests se escribieron antes que el código, pero
  esta vez no se registró la corrida en rojo previa a la implementación.

## Implementación

- [X] T002 `harness/documento.py`: reglas D-ESTRUCTURA, D-PENDIENTE, D-HECHO, D-CITA, D-DATOS,
  D-LIMITE, D-REVISION y D-IA; `validar_documento` y `resumen_documento`.
- [X] T003 `harness/__main__.py`: subcomando `documento` con `--dir`, `--raiz` y `--entrega`; una línea
  de resumen dentro de `todo` (FR-012).

## Verificación

- [X] T004 Corrida sobre el documento real el 2026-11-17: 0 fallas, 49 marcadores pendientes
  (35 `[PENDIENTE`, 12 `[A completar` y 2 `[Completar`), 6 secciones todavía en plantilla, 2 secciones
  sin descargo y 19 sin revisión humana (SC-003).
- [ ] T005 `python -m harness` en verde con la suite completa (SC-004).

## Incrementos siguientes (sin empezar)

- Reglas D-COHERENCIA, D-TERMINO y D-SYNC.
- Verificadores para los campos de contrato `sin_verificacion`; salida `--json`.
