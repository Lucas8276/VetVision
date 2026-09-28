---

description: "Task list for 002-etapa0-torax-clasificador"
---

# Tasks: Clasificador de Etapa 0 — Tórax vs. No-Tórax

**Input**: Design documents from `specs/002-etapa0-torax-clasificador/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/interfaces.md,
quickstart.md

**Tests**: el Principio III (test-first no negociable) está scoped a `limpiar_datos_fcr.py` y
`src/parser_fcr.py` — esta feature no los toca, así que no es un gate obligatorio acá. Se mantiene
la práctica de todos modos para la única lógica determinística nueva (`region_a_etiqueta_binaria`,
`VetVisionEtapa0Dataset`); el entrenamiento en sí NO se testea por unidad (ver `research.md`
Decisión 5) — se valida corriendo `quickstart.md` contra datos reales.

**Organization**: agrupadas por historia de usuario (US1 y US2 son P1, US3 es P2).

## Phase 1: Setup

- [X] T001 [P] Crear `tests/test_dataset_etapa0_binario.py` vacío con el import de pytest y de
  `src.dataset` (fallará hasta T006 — esperado)

**Checkpoint**: sin fase Foundational separada — ninguna historia depende de infraestructura
compartida más allá de Setup.

---

## Phase 2: User Story 1 - Etiquetar automáticamente tórax/no-tórax (Priority: P1) 🎯 MVP

**Goal**: derivar `TORAX`/`NO_TORAX`/excluido de `region` sin anotación clínica.

**Independent Test**: correr `region_a_etiqueta_binaria` y `VetVisionEtapa0Dataset` sobre datos
sintéticos y confirmar las 3 salidas posibles (ver quickstart.md paso 1).

### Tests for User Story 1

- [X] T002 [P] [US1] Test: `region_a_etiqueta_binaria("TORAX") == "TORAX"` — en
  `tests/test_dataset_etapa0_binario.py`
- [X] T003 [P] [US1] Test: `region_a_etiqueta_binaria(r) == "NO_TORAX"` para cada
  `r in {"CERVICAL", "ABDOMEN", "PELVIS", "EXTREMIDADES", "CRANEO"}` — en
  `tests/test_dataset_etapa0_binario.py`
- [X] T004 [P] [US1] Test: `region_a_etiqueta_binaria("DESCONOCIDA") is None` (FR-003) — en
  `tests/test_dataset_etapa0_binario.py`
- [X] T005 [P] [US1] Test: `VetVisionEtapa0Dataset` sobre un directorio sintético (`tmp_path`) con
  2 estudios `TORAX`, 1 `NO_TORAX` y 1 `DESCONOCIDA` (`.txt`+jpg mínimos) produce
  `len(dataset) == 3` y `dataset.n_excluidos_desconocida == 1` — en
  `tests/test_dataset_etapa0_binario.py`
- [X] **[No planificada]** Test de regresión: `_encontrar_jpg_pesado` no debe emparejar un
  estudio con la imagen de otro por coincidencia de *prefijo* (bug real encontrado corriendo
  contra el dataset de 8015 imágenes — `glob(f"{stem}*.jpg")` matcheaba `FCR1` con `FCR10.jpg`) —
  en `tests/test_dataset_etapa0_binario.py`
- [X] **[No planificada]** Test de regresión: `__getitem__` devuelve 1 canal en rango
  `~[-1024, 1024]` (bug real: el backbone de TorchXRayVision espera 1 canal, no RGB; y ese rango,
  no `[0,1]`/imagenet — nunca se había corrido el pipeline completo antes de esta feature) — en
  `tests/test_dataset_etapa0_binario.py`

### Implementation for User Story 1

- [X] T006 [US1] Implementar `region_a_etiqueta_binaria()` y `ETIQUETAS_A_IDX =
  {"NO_TORAX": 0, "TORAX": 1}` en `src/dataset.py` — depende de T002-T004 en rojo
- [X] T007 [US1] Modificar `VetVisionEtapa0Dataset.__init__` para usar
  `region_a_etiqueta_binaria()` en vez de `REGIONES_A_IDX`, y exponer
  `n_excluidos_desconocida` — depende de T006; T005 debe estar en rojo antes
- [X] T008 [US1] Correr `pytest tests/test_dataset_etapa0_binario.py -v` y confirmar T002-T005 en
  verde — depende de T006, T007
- [X] **[No planificada]** Corregir `_encontrar_jpg_pesado` (lookup por stem exacto, indexado una
  sola vez) y `src/preprocessing.py`/`src/dataset.py.__getitem__` (1 canal,
  `xrv.utils.normalize`) — encontrados al intentar correr `quickstart.md` contra el dataset real
  (ver `ENTRENAMIENTOS.md`, Corrida 1, y `CLAUDE.md` "Known gotchas")

**Checkpoint**: US1 funcional e independiente (FR-001, FR-002, FR-003).

---

## Phase 3: User Story 2 - Entrenar con desempeño medible (Priority: P1)

**Goal**: entrenar el modelo binario y medir su desempeño sin que el desbalance de clases
esconda un mal resultado.

**Independent Test**: correr `quickstart.md` pasos 2-3 sobre `data/processed` real.

### Implementation for User Story 2

- [X] T009 [US2] Actualizar `src/train.py`: `build_model_etapa0(num_classes=len(ETIQUETAS_A_IDX))`
  en vez de `len(REGIONES_A_IDX)`; loguear a MLflow `n_excluidos_desconocida` como param (nunca
  IDs de estudios individuales — Principio IV) — depende de T007
- [X] **[No planificada]** Fijar semilla (`seed=42`) en el split train/val de `src/train.py` y
  persistir los índices de validación (`models/etapa0_region_val_indices.json`) — sin esto,
  `evaluate.py` no puede reconstruir un held-out real para medir después (ver
  `ENTRENAMIENTOS.md`, nota metodológica de la Corrida 1)
- [X] T010 [US2] Actualizar `src/evaluate.py`: agregar `balanced_accuracy_score` de
  `sklearn.metrics`, subir `UMBRAL_PROMOCION_ACC` de 0.85 a 0.90, y calcular `promovible` contra
  `balanced_accuracy` en vez de `accuracy`; además, usar los índices de validación persistidos
  (si existen) en vez de evaluar sobre el dataset completo — depende de T007
- [ ] T011 [US2] Ejecutar `quickstart.md` pasos 2-3 (entrenar + evaluar) sobre `data/processed`
  real y confirmar: (a) el run de MLflow no contiene nombre/ID de paciente, (b) se reportan
  `accuracy`, `balanced_accuracy`, `f1_macro`, `promovible` — depende de T009, T010; **requiere
  `data/processed` poblado con el dataset real, no se puede correr en modo simulación**.
  **Progreso parcial**: Corrida 1 (3 épocas, ver `ENTRENAMIENTOS.md`) validó el pipeline
  completo end-to-end y dio `val_acc=81.22%` (accuracy simple, sin semilla fija todavía) — no
  cuenta como T011 completa porque no se midió `balanced_accuracy`/F1 sobre un held-out
  reconstruible. Pendiente: corrida completa (15 épocas) con el fix de semilla ya aplicado.

**Checkpoint**: US2 funcional e independiente de US1 en términos de código (depende de sus datos).

---

## Phase 4: User Story 3 - Clasificar un estudio nuevo (Priority: P2)

**Goal**: aplicar el modelo entrenado y obtener una decisión explícita `TORAX`/`NO_TORAX`.

**Independent Test**: `quickstart.md` paso 4.

### Implementation for User Story 3

- [X] T012 [US3] Confirmar que `build_model_etapa0` y `export_onnx.py` siguen funcionando sin
  cambios de firma con `num_classes=2` — depende de T007. **Encontrado y corregido**: a
  diferencia de lo asumido en `plan.md`, `export_onnx.py` sí necesitaba un cambio (importaba
  `REGIONES_A_IDX`, que ya no existe) y su `dummy_input` tenía 3 canales en vez de 1
- [ ] T013 [US3] Ejecutar `quickstart.md` paso 4 sobre un estudio real no usado en
  entrenamiento/evaluación y confirmar que devuelve `TORAX`/`NO_TORAX` explícito, no un tensor
  crudo (FR-007) — depende de T011 (modelo ya entrenado)

**Checkpoint**: las 3 historias son funcionales de forma independiente.

---

## Phase 5: Polish & Cross-Cutting Concerns

- [X] T014 [P] Correr `pytest` completo (toda la suite) y confirmar cero regresiones — **24/24
  pasan** (incluye 2 tests de regresión no planificados, ver US1)
- [X] T015 Actualizar `CLAUDE.md`: reflejar que Etapa 0 es ahora binaria (TORAX/NO_TORAX), no de
  6 regiones; actualizar la sección de arquitectura y el umbral de promoción — también documenta
  el gotcha de `PYTHONIOENCODING` en Windows y la corrección de canales/normalización
- [X] T016 Actualizar `specs/ground-truth-annotation.spec.yaml`: `etapa_0_region_anatomica` pasa a
  `clases: [TORAX, NO_TORAX]` (cierra la nota "fuera de alcance" dejada en el `research.md` de la
  feature 001-fcr-metadata-extraction)
- [X] T017 Agregar una sección `etapa_0_torax` a `specs/model-tensor.spec.yaml` — **ajustado**:
  `input_shape: [1, 512, 512]` (no `[3, ...]`, ver el bug de canales encontrado en US1) y se
  corrigió también el bloque `input:` global del archivo (`formato: GRAYSCALE`, `canales: 1`,
  normalización real de TorchXRayVision), que estaba mal desde antes de esta feature
- [X] **[No planificada]** Crear `ENTRENAMIENTOS.md` en la raíz (commiteado, no gitignoreado) —
  log de corridas de entrenamiento para que Lucas tenga visibilidad sin levantar MLflow local
- [X] **[No planificada]** Gitignorear `mlflow.db` (quedaba suelto sin ignorar en la raíz)

---

## Dependencies & Execution Order

- **Setup (Fase 1)**: sin dependencias.
- **US1 (Fase 2)**: depende de Setup. Bloquea a US2 y US3 (ambas necesitan `ETIQUETAS_A_IDX` y el
  dataset ya modificado).
- **US2 (Fase 3)**: depende de US1 (T007). T011 además depende de tener `data/processed` real
  poblado — si no lo está, esta tarea queda pendiente hasta que lo esté, no es un bloqueo de
  código.
- **US3 (Fase 4)**: depende de US1 (T007) para T012; T013 depende de que US2 haya producido un
  modelo entrenado (T011).
- **Polish (Fase 5)**: depende de que el código de las 3 historias esté completo (no depende de
  T011/T013, que son verificaciones contra datos reales que pueden demorar más).

### Parallel Opportunities

- T002, T003, T004, T005 en paralelo dentro de US1.
- T009 y T010 tocan archivos distintos (`train.py` vs `evaluate.py`) — en paralelo.
- T016 y T017 tocan specs distintos — en paralelo, y en paralelo con T015 (`CLAUDE.md`).

---

## Implementation Strategy

### MVP primero (US1)

1. Fase 1 (Setup).
2. Fase 2 (US1) — ya deja el dataset etiquetado correctamente, verificable con datos sintéticos
   sin depender de tener `data/processed` real poblado.
3. **Parar y validar**: `pytest tests/test_dataset_etapa0_binario.py -v`.

### Entrega incremental

1. US1 → validable con datos sintéticos, sin esperar al dataset real.
2. US2 → requiere `data/processed` real poblado (T011) — si todavía no está, el código
   (T009, T010) se puede completar y revisar igual, dejando T011 pendiente.
3. US3 → requiere que US2 haya producido un modelo entrenado real.
4. Polish → cierra la deuda de specs que quedó abierta desde la feature 001.
