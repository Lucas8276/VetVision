# Implementation Plan: Extracción de metadata e imagen desde estudios FCR PRIMA

**Branch**: `001-fcr-metadata-extraction` | **Date**: 2026-09-28 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-fcr-metadata-extraction/spec.md`

## Summary

El parser `.ddo`→`.txt`/`.hq`→`.png` ya funciona en producción sobre ~8000 estudios, pero su lógica
binaria vive sin tests dentro de un script de nivel raíz (`limpiar_datos_fcr.py`), y el
clasificador de metadata (`src/parser_fcr.py`) solo reconoce nombres de región en español, cuando
el equipo entrega códigos en inglés en la mayoría de los estudios reales. El enfoque técnico es:
(1) extraer la lógica de parsing binario del `.ddo` a un módulo testeable en `src/`, (2) agregar
una tabla de normalización de región/vista que cubra los códigos reales observados antes de la
validación existente, y (3) fijar con tests de regresión cada caso ya descubierto (bug de
`SEQ_DELIM`, ID con guion, vista ausente, vista combinada) — sin tocar el comportamiento de
clasificación de archivos (CONSERVAR/SOBRANTE/REVISAR) que ya funciona.

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**: `struct` (stdlib, parsing binario), `pylibjpeg` + `pylibjpeg-libjpeg`
(decodificación JPEG-Lossless del `.hq`), `numpy` + `Pillow` (escritura de PNG 16-bit) — todas ya
declaradas en `requirements.txt`, no se agregan dependencias nuevas.

**Storage**: Sistema de archivos local (entrada: estudios FCR PRIMA; salida: `.txt`/`.png`/`.jpg` +
reporte CSV). Sin base de datos.

**Testing**: pytest (ya en uso en `tests/test_parser_fcr.py`)

**Target Platform**: Windows (entorno de desarrollo actual, PowerShell); el código no debe asumir
rutas ni comandos POSIX-only.

**Project Type**: Single project — librería de parsing en `src/` + script CLI en la raíz
(`limpiar_datos_fcr.py`)

**Performance Goals**: Sin objetivo nuevo de performance — mantener el throughput actual (el
pipeline ya procesa ~8000+ estudios reales en producción); ningún cambio de esta feature debe
degradarlo perceptiblemente.

**Constraints**: No depender de DDOView ni `MSCOMCTL.OCX` (restricción original del proyecto, ya
cumplida); no introducir dependencia de red ni de servicio externo.

**Scale/Scope**: ~8000 estudios en el pool ya procesado, con un universo de hasta ~25.000
radiografías UNNE si se amplía la fuente más adelante — la solución no puede asumir un tamaño de
dataset fijo.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Gate | Estado |
|---|---|---|
| I. Spec-First Development | Este plan deriva de `spec.md` ya validado, no de un pedido informal | PASS |
| II. Real-Data-Grounded Specs | Toda regla de normalización (región/vista) debe basarse en valores realmente observados (`CHEST/NECK/HEAD/UP_EXM/LOW_EXM`, `VD/DV`), no en suposición | PASS — ver `research.md` |
| III. Test-First for Parsers (NO NEGOCIABLE) | `/speckit-tasks` DEBE secuenciar la creación de cada test de regresión (SEQ_DELIM, región, vista, ID con guion) ANTES de la tarea de implementación correspondiente | GATE ABIERTO — se aplica en `/speckit-tasks`, no en este plan |
| IV. Patient Data Protection | Los fixtures de test que representen `.ddo`/`.txt` reales NO pueden contener datos de pacientes reales (nombres/IDs vistos en `C:\Users\Usuario\Music\DatasetVetVision`) — deben ser sintéticos | GATE — ver `research.md` y `quickstart.md` |
| V. Simplicity / No Speculative Stages | Esta feature no toca Etapa 1/2 ni arquitectura de modelo | PASS |

Sin violaciones que requieran justificación en Complexity Tracking.

**Re-chequeo post-diseño (tras Fase 1)**: `data-model.md` y `contracts/parsing-interfaces.md` no
introducen ningún elemento nuevo que entre en conflicto con los principios. Punto a vigilar
explícitamente en `/speckit-tasks`: el Principio IV (fixtures sintéticos, Decisión 6 de
`research.md`) y el Principio III (orden test-antes-que-implementación) son gates de proceso, no de
diseño — no se pueden validar en el plan, quedan como responsabilidad de la secuencia de tareas y
de la implementación. Todo lo demás: PASS.

## Project Structure

### Documentation (this feature)

```text
specs/001-fcr-metadata-extraction/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md         # Phase 1 output
├── quickstart.md         # Phase 1 output
├── contracts/            # Phase 1 output
└── tasks.md              # Phase 2 output (/speckit-tasks - not created here)
```

### Source Code (repository root)

```text
limpiar_datos_fcr.py         # CLI: clasifica archivos, decodifica .hq, delega parsing de .ddo a src/
src/
├── ddo_parser.py             # NUEVO: extraído de limpiar_datos_fcr.py — parse_ddo_bytes,
│                              #   get_tag, generar_txt_desde_ddo, fecha_dicom_a_puntos
├── parser_fcr.py              # EXISTENTE: parsear_metadata_fcr + tablas de normalización región/vista
├── dataset.py, model.py, ...  # sin cambios — consumen src/parser_fcr.py como hoy

tests/
├── test_ddo_parser.py        # NUEVO: parseo binario del .ddo, incluye regresión SEQ_DELIM
└── test_parser_fcr.py         # EXTENDIDO: casos reales (región en inglés, vista combinada,
                                #   vista ausente, ID con guion)
```

**Structure Decision**: Opción de proyecto único (no hay frontend/backend ni mobile). La única
decisión estructural real es sacar el parsing binario del `.ddo` de `limpiar_datos_fcr.py` (donde
hoy no es testeable como unidad aislada) a `src/ddo_parser.py`, siguiendo el mismo patrón que ya
existe para `src/parser_fcr.py`. `limpiar_datos_fcr.py` pasa a ser un wrapper CLI delgado que
importa de `src/` en vez de contener la lógica de parsing.

## Complexity Tracking

*Sin violaciones — tabla omitida.*
