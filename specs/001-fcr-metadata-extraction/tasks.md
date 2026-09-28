---

description: "Task list for 001-fcr-metadata-extraction"
---

# Tasks: Extracción de metadata e imagen desde estudios FCR PRIMA

**Input**: Design documents from `specs/001-fcr-metadata-extraction/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/parsing-interfaces.md, quickstart.md

**Tests**: NO son opcionales en esta feature — el Principio III de la constitution
(`.specify/memory/constitution.md`) es NO NEGOCIABLE: todo cambio a `limpiar_datos_fcr.py` o a
`src/parser_fcr.py` requiere un test de regresión escrito y en rojo ANTES de la tarea de
implementación correspondiente. Todos los fixtures son sintéticos (Principio IV / Decisión 6 de
`research.md`) — ningún test lee archivos de `C:\Users\Usuario\Music\DatasetVetVision`.

**Organization**: Tareas agrupadas por historia de usuario (spec.md), en orden de prioridad
(US1 y US2 son P1, US3 es P2).

## Format: `[ID] [P?] [Story] Description`

## Phase 1: Setup

- [X] T001 [P] Crear `src/ddo_parser.py` vacío con docstring de módulo, listo para recibir las
  funciones extraídas de `limpiar_datos_fcr.py`
- [X] T002 [P] Crear `tests/test_ddo_parser.py` vacío con el import de pytest y de
  `src.ddo_parser` (fallará hasta T007 — esperado)

**Checkpoint**: no hay fase Foundational separada — según `data-model.md`/`contracts/`, ninguna
historia depende de una infraestructura compartida más allá de lo creado en Setup; cada historia
es independiente entre sí.

---

## Phase 2: User Story 1 - Leer metadata sin DDOView (Priority: P1) 🎯 MVP

**Goal**: extraer del `.ddo` binario los 8 campos de metadata sin depender de `MSCOMCTL.OCX`.

**Independent Test**: tomar un `.ddo` sintético, correr la extracción, verificar los 8 campos en
el `.txt` resultante (ver quickstart.md paso 1).

### Tests for User Story 1 (escribir y confirmar que fallan ANTES de implementar)

- [X] T003 [P] [US1] Test: `parse_ddo_bytes` sobre bytes `.ddo` sintéticos reconstruye ID
  paciente, nombre (con `^` reemplazado por espacio), sexo, fecha, región, menú de exposición,
  modalidad e institución — en `tests/test_ddo_parser.py`
- [X] T004 [P] [US1] Test de regresión FR-002: una secuencia anidada de largo indefinido cuyo tag
  de cierre es `(0xFFFE, 0xE0DD)` se parsea sin desincronizar los offsets de lectura del resto del
  archivo (reproduce el bug ya corregido documentado en `formato_ddo_hq_FCR_PRIMA.md`) — en
  `tests/test_ddo_parser.py`
- [X] T005 [P] [US1] Test: `fecha_dicom_a_puntos("20180411") == "11.04.2018"`, y una fecha que no
  tiene 8 dígitos se devuelve sin modificar (no lanza excepción) — en `tests/test_ddo_parser.py`
- [X] T006 [P] [US1] Test: `generar_txt_desde_ddo` escribe un `.txt` con las 8 líneas
  `Campo:Valor` esperadas (FR-003), usando un `.ddo` sintético con `tmp_path` — en
  `tests/test_ddo_parser.py`

### Implementation for User Story 1

- [X] T007 [US1] Mover `parse_ddo_bytes`, `get_tag` (renombrado desde `_get_tag`),
  `fecha_dicom_a_puntos` (renombrado desde `_fecha_dicom_a_puntos`), `generar_txt_desde_ddo`, y las
  constantes `ITEM`, `ITEM_DELIM`, `SEQ_DELIM = (0xFFFE, 0xE0DD)` desde `limpiar_datos_fcr.py`
  hacia `src/ddo_parser.py`, siguiendo las firmas de `contracts/parsing-interfaces.md` — depende de
  T001; T003-T006 deben estar en rojo antes de este paso
- [X] T008 [US1] Actualizar `limpiar_datos_fcr.py` para importar `parse_ddo_bytes` y
  `generar_txt_desde_ddo` desde `src.ddo_parser` en vez de definirlas localmente — depende de T007
- [X] T009 [US1] Correr `pytest tests/test_ddo_parser.py -v` y confirmar que T003-T006 pasan en
  verde — depende de T007, T008

**Checkpoint**: US1 funcional y testeable de forma independiente (FR-001, FR-002, FR-003).

---

## Phase 3: User Story 2 - Obtener la imagen de mayor calidad sin pérdida (Priority: P1)

**Goal**: decodificar cada `.hq` a `.png` de 16 bits sin normalizar, enrutando a revisión manual
lo que falle en vez de perderlo o interrumpir el lote.

**Independent Test**: decodificar un `.hq` sintético/mockeado y confirmar 16 bits sin normalizar;
forzar una decodificación fallida y confirmar que el lote sigue (ver quickstart.md paso 1-2).

### Tests for User Story 2

- [X] T010 [P] [US2] Test: `decodificar_y_guardar_hq`, con `decode_jpeg_lossless` mockeado para
  devolver un array `numpy` conocido, produce un `.png` de 16 bits cuyos valores de píxel
  coinciden exactamente con el array de entrada (sin reescalar a 0-255) — nuevo archivo
  `tests/test_limpiar_datos_fcr.py`
- [X] T011 [P] [US2] Test de integración FR-009: con `decode_jpeg_lossless` mockeado para lanzar
  excepción sobre un `.hq`, `procesar()` enruta ese estudio a `REVISAR` con el motivo de la
  excepción en el CSV, y el resto de los archivos del lote (`tmp_path` con 2+ estudios sintéticos)
  se siguen procesando — en `tests/test_limpiar_datos_fcr.py`

### Implementation for User Story 2

- [X] T012 [US2] Ejecutar T010; si falla, ajustar `decodificar_y_guardar_hq` en
  `limpiar_datos_fcr.py` hasta que pase (línea base esperada: ya pasa sin cambios, ver
  `research.md` Decisión 5) — depende de T010 — **confirmado: pasó sin cambios de código**
- [X] T013 [US2] Ejecutar T011; si falla, ajustar el manejo de excepción de `.hq` dentro de
  `procesar()` en `limpiar_datos_fcr.py` hasta que pase — depende de T011 — **confirmado: pasó sin
  cambios de código**

**Checkpoint**: US2 funcional e independiente de US1 (FR-004, FR-009).

---

## Phase 4: User Story 3 - Clasificar metadata en formatos reales no anticipados (Priority: P2)

**Goal**: que los códigos de región, vistas combinadas, menús sin vista, e IDs con guion
realmente observados en producción se clasifiquen correctamente en vez de caer en
`"DESCONOCIDA"` o fallar.

**Independent Test**: correr `parsear_metadata_fcr` sobre `.txt` sintéticos que reproduzcan cada
caso real conocido (ver quickstart.md paso 1).

### Tests for User Story 3

- [X] T014 [P] [US3] Test FR-005/SC-003: región `"CHEST"` → `"TORAX"`, `"NECK"` → `"CERVICAL"`,
  `"HEAD"` → `"CRANEO"`, `"UP_EXM"` y `"LOW_EXM"` → `"EXTREMIDADES"` (cuatro casos, uno por
  código) — en `tests/test_parser_fcr.py`
- [X] T015 [P] [US3] Test FR-006: menú `"CRANEO VD/DV FELINO"` produce `vista == "VD/DV"` — en
  `tests/test_parser_fcr.py`
- [X] T016 [P] [US3] Test FR-007: menú `"ESOFAGO CANINO"` (sin token de vista) produce
  `vista is None` sin lanzar excepción — en `tests/test_parser_fcr.py`
- [X] T017 [P] [US3] Test FR-008: ID de paciente con guion (sintético, `"999-1"`) produce
  `id_paciente == "999-1"` (guion preservado) — en `tests/test_parser_fcr.py`

### Implementation for User Story 3

- [X] T018 [US3] Agregar `"CRANEO"` a `REGIONES_VALIDAS` en `src/parser_fcr.py` — depende de T014
  en rojo
- [X] T019 [US3] Implementar `_normalizar_codigo_region()` (tabla `CHEST/NECK/HEAD/UP_EXM/LOW_EXM`
  → región canónica, ver `contracts/parsing-interfaces.md`) y aplicarla en `parsear_metadata_fcr`
  antes de la validación/fallback existente — depende de T018
- [X] T020 [US3] Agregar `"VD/DV"` a `VISTAS_VALIDAS` en `src/parser_fcr.py` — depende de T015 en
  rojo
- [X] T021 [US3] Correr `pytest tests/test_parser_fcr.py -v` y confirmar T014-T017 en verde,
  incluyendo T016/T017 que no deberían requerir cambio de código (ver `research.md` Decisión 4) —
  depende de T018, T019, T020

**Checkpoint**: las 3 historias son funcionales de forma independiente entre sí.

---

## Phase 5: Polish & Cross-Cutting Concerns

- [X] T022 [P] Correr `pytest` completo (toda la suite, no solo los archivos nuevos) y confirmar
  cero regresiones — **18/18 pasan**
- [X] T023 Ejecutar los pasos 2-4 de `quickstart.md` — **nota de desviación**:
  `C:\Users\Usuario\Music\DatasetVetVision` ya es el resultado LIMPIO (`--confirmar` ya corrido),
  no el material crudo de 8 archivos/estudio, así que re-correr `limpiar_datos_fcr.py` contra esa
  carpeta no mide SC-001/SC-002 (cada `.png`/`.txt` ya generado cae en "extensión no reconocida",
  esperado). SC-001 (8158/8158 `.ddo`→`.txt`), SC-002 (8015/8158 ≈ 98.2% `.hq`→`.png`) y SC-005
  (motivos legibles, ej. `"jpg chico pero sin 's' (2535 bytes)"`) ya quedaron validados contra el
  `reporte.csv` real de esa misma corrida original, inspeccionado antes en esta conversación —  no
  se regenera acá porque el material crudo ya no está disponible (fue limpiado). Corrida de humo
  ejecutada solo en modo simulación (sin `--confirmar`), sin efectos secundarios, CSV temporal
  borrado después
- [X] T024 Actualizar la sección "Known gotchas" de `CLAUDE.md`: quitar los ítems ya resueltos por
  esta feature (región en inglés sin mapear, `SEQ_DELIM` sin test de regresión) y dejar solo el
  gotcha de `_encontrar_jpg_pesado` (fuera de alcance de esta feature)

---

## Dependencies & Execution Order

- **Setup (Fase 1)**: sin dependencias, arranca de inmediato.
- **US1 (Fase 2)**: depende de Setup (T001, T002). Sin dependencia de US2 ni US3.
- **US2 (Fase 3)**: depende de Setup. Sin dependencia de US1 ni US3 — puede hacerse en paralelo a
  la Fase 2 si hay dos personas (Stiven/Lucas) trabajando a la vez.
- **US3 (Fase 4)**: depende de Setup. Sin dependencia de US1 ni US2.
- **Polish (Fase 5)**: depende de que las 3 historias estén completas.

### Dentro de cada historia

- Los tests marcados [P] de una misma historia se pueden escribir en paralelo (mismo archivo,
  pero sin dependencias entre sí) y DEBEN estar en rojo antes de la tarea de implementación
  correspondiente (Principio III).
- La verificación final de cada historia (T009, T012+T013, T021) depende de que toda la
  implementación de esa historia esté hecha.

### Parallel Opportunities

- T001 y T002 en paralelo.
- Dentro de US1: T003, T004, T005, T006 en paralelo (todos en el mismo archivo nuevo, pero
  redactables de forma independiente antes de correr `pytest`).
- Dentro de US3: T014, T015, T016, T017 en paralelo.
- US1, US2 y US3 completas se pueden repartir entre Stiven y Lucas y trabajarse en paralelo, ya
  que no tienen dependencias cruzadas.

---

## Implementation Strategy

### MVP primero (US1 + US2, ambas P1)

1. Fase 1 (Setup).
2. Fase 2 (US1) y Fase 3 (US2) — en paralelo si hay dos personas, o en secuencia si es una sola.
3. **Parar y validar**: correr quickstart.md pasos 1-2 con solo US1+US2 implementadas.
4. Esto ya es un MVP demostrable: el pipeline extrae metadata e imagen de alta calidad sin
   depender de software de Windows, con los bugs conocidos (SEQ_DELIM) cubiertos por test.

### Entrega incremental

1. Setup → Fundación lista.
2. US1 → validar independientemente → ya es demostrable.
3. US2 → validar independientemente → demostrable junto a US1.
4. US3 → validar independientemente → cierra la brecha de datos reales mal clasificados
   (el hallazgo original que motivó todo este spec).
5. Polish → confirma que nada se rompió y deja el CLAUDE.md al día.
