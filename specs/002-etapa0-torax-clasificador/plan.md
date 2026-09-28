# Implementation Plan: Clasificador de Etapa 0 — Tórax vs. No-Tórax

**Branch**: `002-etapa0-torax-clasificador` | **Date**: 2026-09-28 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/002-etapa0-torax-clasificador/spec.md`

## Summary

Etapa 0 pasa de clasificar 6 regiones anatómicas a ser binaria (TORAX/NO_TORAX), que es lo que el
resto del proyecto realmente necesita (Etapa 1/2 son exclusivamente torácicas). No es una feature
nueva en paralelo: **redefine** `VetVisionEtapa0Dataset` para derivar la etiqueta binaria del
campo `region` ya corregido (feature 001), excluir explícitamente los estudios `"DESCONOCIDA"`, y
ajustar la evaluación para reportar exactitud balanceada (no solo accuracy simple, que puede
esconder desbalance de clases). La arquitectura del modelo (`src/model.py`) no cambia — ya acepta
`num_classes` como parámetro, así que pasa de recibir 6 a recibir 2 sin tocar el backbone
preentrenado.

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**: `torch`, `torchvision`, `torchxrayvision` (backbone preentrenado,
DenseNet-121 sobre tórax humano), `opencv-python` + `albumentations` (preprocesamiento ya
existente), `scikit-learn` (`balanced_accuracy_score`, `f1_score` — ya en `requirements.txt`),
`mlflow` (tracking ya existente), `onnx`/`onnxruntime` (export ya existente). Sin dependencias
nuevas.

**Storage**: Sistema de archivos (`data/processed/`, pares `.txt`+jpg de la feature 001) +
`models/` para checkpoints + MLflow para métricas de cada corrida.

**Testing**: pytest, para la parte determinística (función de etiquetado). El entrenamiento en sí
se valida por las métricas de evaluación (SC-002), no por un test unitario — un modelo es
estocástico, no tiene un "resultado correcto" único que un test pueda afirmar.

**Target Platform**: Windows (entorno actual); el código ya soporta CPU/GPU vía
`torch.device("cuda" if available else "cpu")`.

**Project Type**: Single project — extiende módulos existentes en `src/`, no agrega estructura
nueva.

**Performance Goals**: SC-002 — al menos 90% de exactitud balanceada sobre un conjunto de
validación held-out.

**Constraints**: No debe requerir anotación clínica (FR-008); debe excluir explícitamente
`"DESCONOCIDA"` sin forzarla a ninguna clase (FR-003); debe reusar el backbone congelado ya
elegido, no reentrenar desde cero.

**Scale/Scope**: ~8000 estudios reales ya extraídos (feature 001), split train/validación dentro
de ese conjunto.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Gate | Estado |
|---|---|---|
| I. Spec-First Development | Este plan deriva de `spec.md` ya validado | PASS |
| II. Real-Data-Grounded Specs | La etiqueta binaria se deriva de `region`, ya corregido contra datos reales por la feature 001 — no hay normalización nueva que inventar acá | PASS |
| III. Test-First for Parsers (NO NEGOCIABLE) | Esta feature NO toca `limpiar_datos_fcr.py` ni `src/parser_fcr.py` (los archivos que el principio cubre explícitamente) — no aplica como gate directo. Se mantiene la práctica igual para la única lógica determinística nueva (la función de etiquetado): test antes que implementación | PASS (no bloqueante, aplicado por buena práctica) |
| IV. Patient Data Protection | El dataset de entrenamiento son imágenes + etiqueta binaria — ningún nombre/ID de paciente entra a MLflow (params/metrics deben limitarse a conteos y métricas, nunca a identificadores) | GATE — ver `research.md` |
| V. Simplicity / No Speculative Stages | Esta es exactamente la feature que el Principio V permite ahora (no depende de anotación pendiente); no se toca Etapa 1/2 | PASS |

Sin violaciones que requieran justificación en Complexity Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/002-etapa0-torax-clasificador/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
└── tasks.md              # Fase 2 (/speckit-tasks — no se crea acá)
```

### Source Code (repository root)

```text
src/
├── dataset.py    # MODIFICADO: VetVisionEtapa0Dataset ahora deriva TORAX/NO_TORAX de `region`
│                 #   (no 6 clases); nueva funcion region_a_etiqueta_binaria(); excluye
│                 #   "DESCONOCIDA" y expone el conteo de exclusiones
├── model.py       # SIN CAMBIOS — build_model_etapa0(num_classes) ya es generico
├── train.py        # MODIFICADO: usa la nueva ETIQUETAS_A_IDX (2 clases) en vez de REGIONES_A_IDX;
│                   #   loguea a MLflow el conteo de estudios excluidos por "DESCONOCIDA"
├── evaluate.py       # MODIFICADO: agrega balanced_accuracy_score; el umbral de promocion
│                     #   (UMBRAL_PROMOCION_ACC) se evalua sobre balanced accuracy, no accuracy simple
└── export_onnx.py     # SIN CAMBIOS — ya generico via num_classes

tests/
└── test_dataset_etapa0_binario.py   # NUEVO: test de region_a_etiqueta_binaria (deterministico)
```

**Structure Decision**: se **redefine** `VetVisionEtapa0Dataset`/Etapa 0 para que sea binaria, en
vez de crear una clase paralela — porque el spec ya establece que Etapa 0 pasa a ser
TORAX/NO_TORAX, no que se agregue una variante más. `src/model.py` no se toca: ya acepta
`num_classes` como parámetro genérico, así que pasar de 6 a 2 clases no requiere ningún cambio de
arquitectura ni de backbone.

## Complexity Tracking

*Sin violaciones — tabla omitida.*

**Re-chequeo post-diseño (tras Fase 1)**: `data-model.md` y `contracts/` no introducen elementos
nuevos que entren en conflicto con los principios. El Principio IV se resuelve en `research.md`
(Decisión 4: qué se loguea a MLflow) y queda como responsabilidad de la implementación verificar
que ningún log incluya identificadores de paciente. Todo lo demás: PASS.
