# Implementation Plan: Harness de verificación automática

**Branch**: `003-harness-verificacion-automatica` | **Date**: 2026-09-30 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/003-harness-verificacion-automatica/spec.md`

## Summary

El proyecto sigue SDD pero nada lo hace cumplir: los contratos `specs/*.spec.yaml` son documentación
(ya derivaron dos veces, y hoy hay dos desvíos más sin detectar), no existe CI, y una filtración real
de datos de pacientes llegó a un repositorio público sin que nadie la viera. El enfoque técnico es un
paquete chico `harness/` con **un único comando** (`python -m harness`) que corre tres verificaciones
— validación de contratos contra el código, guardia de datos personales/secretos y tests — y que se
engancha en **tres capas** con el mismo veredicto: hooks del asistente (al editar y antes de commitear),
hooks de git locales (`pre-commit`/`pre-push`, la única capa que realmente *previene* una filtración,
porque CI corre después del push) y CI en GitHub Actions como red de contención. Además: versionar
`.claude/` (skills + `settings.json`), un documento de memoria compartida importado desde `CLAUDE.md`,
y la enmienda de la constitution con la regla "spec primero".

## Technical Context

**Language/Version**: Python 3.13 (igual que el entorno actual)

**Primary Dependencies**: solo biblioteca estándar para la guardia y los hooks (deben funcionar con
cualquier Python, sin el venv); PyYAML (ya presente, se declara en `requirements.txt`) y el propio
código del proyecto (`torch`, `torchxrayvision`) para validar contratos del modelo; `pytest`;
GitHub Actions para CI. Sin dependencias externas de detección de secretos (ver research D5).

**Storage**: archivos versionados en el repositorio (contratos YAML, lista de valores ficticios,
documento de memoria). Sin base de datos.

**Testing**: pytest. Los tests de la guardia construyen sus muestras "filtradas" dinámicamente para
que los archivos de test no se marquen a sí mismos.

**Target Platform**: desarrollo en Windows (PowerShell/Git Bash); CI en `ubuntu-latest`. Ningún
verificador puede depender de rutas o comandos específicos de un sistema operativo.

**Project Type**: single project + paquete de herramientas `harness/` en la raíz.

**Performance Goals**: CI completo ≤ 10 min (SC-002); guardia sobre archivos preparados para commit
< 2 s (no puede volver lento cada commit); validación de contratos del modelo ~15 s (medido: construir
la arquitectura sin pesos tarda 13 s incluyendo imports).

**Constraints**: la guardia NO contiene datos reales (FR-011); sus reportes NO reproducen el valor
detectado (los logs de CI de un repo público también son públicos); las verificaciones corren sin el
dataset real (FR-006); las claves/tokens no se necesitan en ninguna parte del flujo.

**Scale/Scope**: 2 personas, ~30 archivos rastreados, 3 contratos YAML, ~10 comprobaciones de
contrato, ~6 reglas de guardia.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Gate | Estado |
|---|---|---|
| I. Spec-First Development | Este plan deriva de `spec.md` validado; los dos desvíos ya detectados se corrigen empezando por el spec, no por el código | PASS |
| II. Real-Data-Grounded Specs | Los contratos se validan contra el código *real* (no contra suposiciones); el ajuste de vistas admitidas se basa en valores observados en el dataset (`VD/DV`) | PASS |
| III. Test-First for Parsers | No toca parsers. Se aplica igual por buena práctica y por criticidad de seguridad: tests de la guardia y del validador escritos antes que su implementación | PASS (no bloqueante) |
| IV. Patient Data Protection | Esta feature ES el mecanismo de cumplimiento. Gate propio: la guardia, sus tests y su lista de valores aprobados no contienen datos reales; sus reportes no los repiten | GATE — ver research D5 |
| V. Simplicity / No Speculative Stages | Riesgo de sobre-ingeniería (validador + guardia + 3 capas de enganche + memoria + CI). Cada pieza responde a un requisito del spec; se rechazan explícitamente: base de datos de memoria, herramientas externas de detección, generación de código desde specs | PASS con justificación (ver Complexity Tracking) |

**Enmienda propuesta a la constitution** (FR-017): nuevo Principio VI "Los specs son la fuente de
verdad" → versión 1.1.0 (MINOR: principio nuevo). Se ejecuta con `/speckit-constitution` durante la
implementación, no se edita a mano.

**Re-chequeo post-diseño (tras Fase 1)**: `data-model.md` y `contracts/` no introducen nada que choque
con los principios. Puntos de proceso a vigilar en `/speckit-tasks`: (1) los tests de guardia y
validador van antes que su implementación; (2) los desvíos de contrato ya detectados se corrigen
(spec primero) **antes** de activar el validador, para que su primera corrida sobre el repo real pase;
(3) ningún fixture de guardia contiene datos reales.

## Project Structure

### Documentation (this feature)

```text
specs/003-harness-verificacion-automatica/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── harness-interfaces.md
└── tasks.md              # Fase 2 (/speckit-tasks — no se crea acá)
```

### Source Code (repository root)

```text
harness/                          # NUEVO — herramientas de verificación
├── __init__.py
├── __main__.py                   # `python -m harness [contratos|guardia|todo]`
├── contratos.py                  # validador specs<->código + registro de verificadores
├── guardia.py                    # datos personales / archivos crudos / secretos (solo stdlib)
├── hooks.py                      # entradas para los hooks del asistente (leen JSON por stdin)
├── lanzar.py                     # lanzador solo-stdlib: ubica el Python del venv y delega
└── valores_ficticios.txt         # lista de valores de ejemplo aprobados (solo ficticios)

.githooks/                        # NUEVO — capa preventiva local (se activa una vez por clon)
├── pre-commit                    # guardia sobre lo preparado para commit
└── pre-push                      # `python -m harness todo`
scripts/instalar_hooks.py         # NUEVO — activa core.hooksPath en el clon (acción explícita)

.github/workflows/verificar.yml   # NUEVO — CI (push + pull_request)
requirements-ci.txt               # NUEVO — dependencias mínimas de CI (CPU-only)
docs/MEMORIA.md                   # NUEVO — memoria compartida (importada desde CLAUDE.md)

.claude/settings.json             # EXISTE (reglas ask) → se AMPLÍA con hooks; se versiona
.gitignore                        # MODIFICADO — deja de ignorar .claude/skills y settings.json
CLAUDE.md                         # MODIFICADO — importa docs/MEMORIA.md
requirements.txt                  # MODIFICADO — agrega pyyaml
src/export_onnx.py                # MODIFICADO — opset por defecto 18 (el spec manda)
specs/data-contract.spec.yaml     # MODIFICADO (spec primero) — vistas AP y VD/DV
specs/*.spec.yaml                 # MODIFICADO — campo `estado` en secciones pendientes

tests/
├── test_harness_contratos.py     # NUEVO — validador + derivas reintroducidas + repo real
├── test_harness_guardia.py       # NUEVO — casos bloqueados, aprobados y falsos positivos
└── test_harness_config.py        # NUEVO — reglas ask, .gitignore, import de memoria, CI presente
```

**Structure Decision**: un único paquete `harness/` en la raíz (no dentro de `src/`, que es código del
modelo/datos) con un solo punto de entrada. Los hooks del asistente, los hooks de git y CI llaman al
mismo comando, de modo que el veredicto es idéntico en las tres capas y en la máquina de cualquier
integrante (FR-007, SC-006).

## Complexity Tracking

| Elemento | Por qué hace falta | Alternativa más simple rechazada porque |
|---|---|---|
| Paquete nuevo `harness/` | Las tres verificaciones deben compartir un solo comando y un solo formato de reporte | Scripts sueltos por capa: tres implementaciones que derivan entre sí (justo lo que se quiere evitar) |
| Hooks de git **además** de CI y hooks del asistente | CI corre *después* del push: en un repo público no puede evitar una filtración, solo detectarla. Los hooks locales sí | Solo CI: habría detectado la filtración original ya pública |
| `requirements-ci.txt` aparte | `requirements.txt` incluye paquetes pesados (`dvc[s3]`, `mlflow`, `flask`) que ninguna verificación usa; instalarlos alarga CI sin valor | Instalar todo: excede el presupuesto de 10 min y varía con cada dependencia nueva |
| Lanzador `lanzar.py` | Los hooks se ejecutan con el Python del sistema, que no tiene torch; el validador necesita el del venv | Exigir el venv activado: los hooks fallarían en silencio |
