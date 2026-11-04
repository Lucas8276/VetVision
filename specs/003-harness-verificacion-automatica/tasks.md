---

description: "Task list for 003-harness-verificacion-automatica"
---

# Tasks: Harness de verificación automática

**Input**: Design documents from `specs/003-harness-verificacion-automatica/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/harness-interfaces.md,
quickstart.md

**Tests**: obligatorios en esta feature (no opcionales). La guardia de datos personales es
código de seguridad y el validador es lo que hace cumplir la regla central del equipo; ambos se
prueban ANTES de implementarse. Ningún fixture contiene datos reales: las muestras "filtradas" se
arman concatenando fragmentos en tiempo de ejecución (research D5).

**Regla de trabajo (aprendida en las features 001 y 002)**: marcar `[X]` solo cuando la tarea está
hecha y verificada, nunca por adelantado. Todo `git commit` y `git push` de este trabajo pasa por
las dos confirmaciones explícitas del usuario (FR-019/FR-020).

**Organization**: por historia de usuario. Las tres P1 (US1, US2, US3) son las que hacen cumplir el
spec; se ordenan US1 → US3 → US2 porque US2 (CI y comando único) agrega lo que US1 y US3 producen.

## Format: `[ID] [P?] [Story] Description`

## Phase 1: Setup

- [X] T001 Crear el paquete `harness/` con `__init__.py` y los módulos vacíos `contratos.py`,
  `guardia.py`, `hooks.py`, `lanzar.py` y `__main__.py`, según la estructura de `plan.md`
- [X] T002 [P] Agregar `pyyaml>=6.0` a `requirements.txt` (hoy llega solo como dependencia
  transitiva; el validador la usa directamente — research D12)
- [X] T003 [P] Crear `pytest.ini` en la raíz registrando el marcador `contratos` (el test que
  valida el repo real contra los contratos; `python -m harness todo` lo excluye para no correrlo dos
  veces — research D4)

---

## Phase 2: Foundational (bloquea a todas las historias)

**Purpose**: la unidad común de resultado y el esqueleto del comando. Todas las verificaciones
informan con la misma estructura (`data-model.md`, entidad Resultado).

- [X] T004 [P] Test de `Resultado` en `tests/test_harness_nucleo.py`: `estado` solo admite
  `ok | falla | pendiente | sin_verificacion`; `formatear()` produce `ESTADO  verificacion
  ubicacion  [regla]  mensaje`; `resumen()` cuenta los cuatro estados; solo `falla` produce código
  de salida 1 (contracts §1)
- [X] T005 Implementar en `harness/__init__.py` el dataclass `Resultado` (campos: `verificacion`,
  `estado`, `ubicacion`, `regla`, `esperado`, `obtenido`, `mensaje`), `formatear()`, `resumen()` y
  `codigo_de_salida()` — depende de T004 en rojo
- [X] T006 [P] Test del despacho de `python -m harness` en `tests/test_harness_nucleo.py`:
  subcomandos `contratos | guardia | todo` (default `todo`); una excepción interna del harness
  devuelve código 2 y **nunca** 0; subcomando desconocido → 2
- [X] T007 Implementar el esqueleto de `harness/__main__.py`: parseo de subcomando y de las
  opciones `--preparados`, `--archivos`, `--rapido`; captura de excepciones internas → código 2 —
  depende de T005, T006

**Checkpoint**: existe el comando y el formato de reporte; las historias pueden empezar.

---

## Phase 3: User Story 1 - Detectar cuando el código se desvía del spec (Priority: P1) 🎯 MVP

**Goal**: los contratos `specs/*.spec.yaml` se validan contra el código real; una divergencia es un
fallo con campo, valor del spec y valor del código.

**Independent Test**: reintroducir cada deriva conocida y ver que falla nombrando el campo;
revertir y ver que pasa (quickstart §2).

### Spec primero (corregir los desvíos que ya existen, antes de activar el validador — research D3)

- [X] T008 [US1] En `specs/data-contract.spec.yaml`, `proyecciones_admitidas` pasa de
  `[LAT, VD, DV]` a `[LAT, VD, DV, AP, VD/DV]`, con un comentario que explique que `VD/DV` sale de
  los menús reales del equipo (feature 001) y que `AP` ya figuraba en el comentario del campo `vista`
- [X] T009 [P] [US1] En `specs/model-tensor.spec.yaml`, agregar `estado: pendiente` a
  `etapa_1_triaje` y `etapa_2_diagnostico` (las dos bloqueadas por la anotación clínica)
- [X] T010 [P] [US1] En `specs/ground-truth-annotation.spec.yaml`, agregar `estado: pendiente` a
  `etapa_1_triaje` y `etapa_2_diagnostico`
- [X] T011 [US1] En `src/export_onnx.py`, cambiar el valor por defecto del parámetro `opset` de 17 a
  18, para que el código coincida con el spec (el spec manda; el archivo realmente exportado ya es
  opset 18)

### Tests de User Story 1 (escribir y confirmar que fallan antes de implementar)

- [X] T012 [P] [US1] En `tests/test_harness_contratos.py`, test marcado `@pytest.mark.contratos`:
  validar el repo real (specs reales + código real) no produce ningún `falla`
- [X] T013 [P] [US1] En `tests/test_harness_contratos.py`, tests de deriva reintroducida sobre una
  copia del diccionario del spec (sin tocar los archivos): `input.canales` = 3, `export.opset` = 17 y
  quitar `VD/DV` de `proyecciones_admitidas`; cada uno produce un `falla` cuyo `esperado` y
  `obtenido` son los valores correctos y cuya `ubicacion` nombra el campo (SC-001)
- [X] T014 [P] [US1] En `tests/test_harness_contratos.py`, tests de cobertura: las secciones con
  `estado: pendiente` se informan `pendiente` (una línea por sección) y los campos sin verificador
  (`resolucion_minima_px`, `formato_archivos_por_paciente.*`, `anonimizacion.*`, `fuente`,
  `requiere_anotacion_manual`) se informan `sin_verificacion` — ni pasan en silencio ni fallan (FR-003,
  FR-004)

### Implementación de User Story 1

- [X] T015 [US1] En `harness/contratos.py`: cargar los tres contratos con PyYAML y recorrer sus
  hojas generando la ruta del campo (`model-tensor › etapas › etapa_0_torax › output_shape`);
  respetar `estado: pendiente` a nivel de sección — depende de T007, T009, T010, T012–T014 en rojo
- [X] T016 [US1] En `harness/contratos.py`: registro de verificadores según la tabla de research D2
  (canales = `features.conv0.in_channels`; salida = `classifier.out_features` y `ETIQUETAS_A_IDX`;
  umbral = `UMBRAL_PROMOCION_ACC`; `export` = valor por defecto de `exportar_onnx`; vistas y especies =
  `VISTAS_VALIDAS` / `ESPECIES_VALIDAS`; tamaño de entrada = forma que devuelve
  `VetVisionEtapa0Dataset.__getitem__` sobre una imagen sintética generada en un directorio temporal).
  El modelo se construye una sola vez por corrida con `DenseNetEtapa0(num_classes=2, weights=None)`
  (sin descargar pesos — research D3b)
- [X] T017 [US1] En `harness/contratos.py`: `validar_contratos(specs=None)` devuelve la lista de
  `Resultado` (acepta los specs como argumento para los tests de deriva) y se conecta a
  `python -m harness contratos`, que imprime una línea por campo más el resumen
- [X] T018 [US1] Correr `pytest tests/test_harness_contratos.py` y `python -m harness contratos`:
  ambos en verde con el repo real. Si aparece una divergencia nueva, se corrige empezando por el
  spec, no por el validador

**Checkpoint**: US1 funcional e independiente (FR-001 a FR-004, FR-018).

---

## Phase 4: User Story 3 - Guardia contra datos personales (Priority: P1)

**Goal**: detectar datos de pacientes/dueños, archivos crudos y secretos antes de que entren al
repositorio, sin que la guardia contenga ni repita datos reales.

**Independent Test**: probar los tres casos bloqueados y uno aprobado (quickstart §3) y confirmar que
el reporte no repite el valor.

### Tests de User Story 3 (escribir y confirmar que fallan antes de implementar)

- [X] T019 [US3] Crear `harness/valores_ficticios.txt` con los valores ficticios aprobados de
  `data-model.md` (`PACIENTE^PRUEBA`, `PACIENTE PRUEBA`, `0000-1`, `123-4`, `456-7`, `999-1`, `999`,
  `12345`, `1`), un valor por línea, `#` para comentarios. Solo valores evidentemente inventados
- [X] T020 [P] [US3] En `tests/test_harness_guardia.py`, tests de las reglas de texto, con muestras
  armadas por concatenación en tiempo de ejecución: `R-CAMPO-PACIENTE` marca un valor no aprobado y
  deja pasar uno aprobado y un marcador de plantilla `{...}`; `R-NOMBRE-DICOM` (`APELLIDO^NOMBRE`);
  `R-ID-PACIENTE` (campo `ID del paciente:` e ID suelto `NNN(N)-N`); y NO se marcan fechas
  (`2026-09-30`), versiones, ni identificadores como `FR-018` o `SC-002`
- [X] T021 [P] [US3] En `tests/test_harness_guardia.py`, tests de archivos y secretos:
  `R-ARCHIVO-CRUDO` bloquea las extensiones `.ddo .hq .dsp .std .edk .edr`, archivos `FCR<n>.*`,
  rutas `data/raw/` y `data/processed/`, `*.db`, `*.pt`, `*.onnx`; `R-SECRETO` bloquea claves de
  nube, tokens de GitHub y bloques de clave privada (muestras armadas en ejecución)
- [X] T022 [P] [US3] En `tests/test_harness_guardia.py`, tests de salida y modos: **el reporte
  nunca contiene el valor detectado** (se afirma que la muestra no aparece en stdout ni stderr);
  `--archivos` sobre archivos puntuales; `--preparados` sobre un repositorio git temporal
  (`git init` en `tmp_path`) revisa solo lo agregado al índice; códigos de salida 0/1/2
- [X] T023 [P] [US3] En `tests/test_harness_guardia.py`, test de integración: la guardia sobre los
  archivos rastreados del repo real (`git ls-files`) no produce hallazgos, incluyendo los propios
  archivos de la guardia y sus tests (FR-011, FR-012)

### Implementación de User Story 3

- [X] T024 [US3] En `harness/guardia.py`: tabla de reglas (`id`, `alcance`, `patron`, `aprobable`)
  con `R-CAMPO-PACIENTE`, `R-NOMBRE-DICOM` y `R-ID-PACIENTE` según research D5 (lookaround para no
  confundir fechas ni versiones); carga de `valores_ficticios.txt` (sin distinguir mayúsculas, sin
  espacios sobrantes) — depende de T019 y de T020–T023 en rojo
- [X] T025 [US3] En `harness/guardia.py`: reglas `R-ARCHIVO-CRUDO` (por ruta y extensión) y
  `R-SECRETO` (patrones de claves/tokens/bloques privados; ninguna dependencia externa — research D5)
- [X] T026 [US3] En `harness/guardia.py`: modos de entrada — árbol completo (`git ls-files`),
  `--preparados` (nombres con `git diff --cached --name-only --diff-filter=ACMR` y solo las líneas
  agregadas con `git diff --cached -U0`) y `--archivos`; convertir cada `Hallazgo` en `Resultado`
  con `ubicacion` `archivo:línea`, `regla` y `mensaje` **sin el valor**; conectar a
  `python -m harness guardia` (solo biblioteca estándar)
- [X] T027 [US3] Correr la guardia sobre el repo y triar cada hallazgo: si es un dato real, se
  corrige el archivo; si es un valor evidentemente ficticio, se agrega a `valores_ficticios.txt` con
  un comentario de justificación. Nunca se agrega un valor real a la lista
- [X] T028 [US3] Correr `pytest tests/test_harness_guardia.py`: todo en verde

**Checkpoint**: US3 funcional e independiente (FR-008 a FR-012, FR-018).

---

## Phase 5: User Story 2 - Verificación automática al subir cambios (Priority: P1)

**Goal**: un único comando (`python -m harness`) con el mismo veredicto en la máquina de cualquiera
y en CI, que corre solo en cada push y pull request.

**Independent Test**: subir un cambio roto y uno correcto y ver el veredicto en CI (quickstart §8);
correr el comando local y obtener el mismo resultado.

### Tests de User Story 2 (escribir y confirmar que fallan antes de implementar)

- [X] T029 [P] [US2] En `tests/test_harness_config.py`, tests de la configuración de CI:
  existe `.github/workflows/verificar.yml`; dispara en `push` y `pull_request`; declara
  `permissions: contents: read` y nada más; ejecuta `python -m harness`; instala PyTorch desde el
  índice CPU; existe `requirements-ci.txt` y no lista `dvc`, `mlflow` ni `flask` (contracts §5)
- [ ] T030 [P] [US2] En `tests/test_harness_nucleo.py`, tests del comando `todo`: agrega los
  resultados de contratos, guardia y pytest (excluyendo el marcador `contratos`); devuelve 1 si
  cualquiera falla; `--rapido` omite lo lento y lo informa como `sin_verificacion` con el motivo;
  si `core.hooksPath` no apunta a `.githooks`, imprime un aviso que **no** cambia el código de salida

### Implementación de User Story 2

- [X] T031 [US2] En `harness/__main__.py`: implementar `todo` — correr contratos, guardia sobre el
  árbol y `sys.executable -m pytest -q -m "not contratos"`, unificar el reporte, imprimir el resumen
  con los conteos y devolver el código de salida (contracts §1) — depende de T017, T026, T030
- [X] T032 [US2] En `harness/__main__.py`: modo `--rapido` y aviso de `core.hooksPath` sin activar
  (research D6, riesgo asumido)
- [X] T033 [P] [US2] Crear `requirements-ci.txt` con el conjunto mínimo de research D12 (`torch` se
  instala aparte desde el índice CPU): `torchvision`, `torchxrayvision`, `opencv-python-headless`,
  `numpy`, `Pillow`, `pylibjpeg`, `pylibjpeg-libjpeg`, `scikit-learn`, `pyyaml`, `pytest`
- [X] T034 [US2] Crear `.github/workflows/verificar.yml` según contracts §5: disparadores `push` y
  `pull_request`, `ubuntu-latest`, `actions/checkout` y `actions/setup-python` (Python 3.13) fijados
  a su versión mayor, instalación de PyTorch CPU + `requirements-ci.txt`, paso `python -m harness`,
  `permissions: contents: read`, sin secretos
- [X] T035 [US2] Correr `python -m harness` en local, medir el tiempo total y confirmar código 0;
  anotar el tiempo para validar contra el presupuesto de 10 min de CI (SC-002)
- [ ] T036 [US2] Primera corrida de CI (**requiere aprobación del usuario: es un push**, con las
  dos confirmaciones): subir una rama de prueba con un test roto a propósito, confirmar rojo con el
  motivo visible en menos de 10 min, corregir y confirmar verde. Es además la primera corrida de la
  suite en Linux: registrar y arreglar cualquier falla de portabilidad (research D7)
- [ ] T037 [US2] Verificar que el nombre del chequeo de `verificar.yml` coincide con el que usa
  `quickstart.md` §8 y dejar redactada la acción del dueño (Lucas): exigir ese chequeo en
  *Settings › Branches* para que un fallo bloquee la fusión (FR-005)

**Checkpoint**: US1, US3 y US2 completas (las tres P1). Esto es el MVP del harness.

---

## Phase 6: User Story 4 - Configuración compartida del asistente y hooks (Priority: P2)

**Goal**: que un clon limpio traiga los comandos `/speckit-*` y las reglas automáticas (reglas `ask`
de commit/push más los hooks), y que los commits hechos a mano también pasen por la guardia.

**Independent Test**: quickstart §4, §5 y §6.

### Tests de User Story 4 (escribir y confirmar que fallan antes de implementar)

- [X] T038 [P] [US4] En `tests/test_harness_config.py`, tests de `.claude/settings.json`: existen
  las 8 reglas `ask` (commit y push × Bash y PowerShell, incluida la variante con opciones
  intermedias `git * commit *`); ninguna regla cubre commit y push a la vez (FR-019/FR-020); están
  declarados el hook `PreToolUse` de `git commit` y el `PostToolUse` de ediciones en `src/`,
  `specs/` y `tests/`; y, con `git check-ignore`, `.claude/settings.local.json` **está** ignorado
  mientras `.claude/skills/` y `.claude/settings.json` **no**
- [X] T039 [P] [US4] En `tests/test_harness_hooks.py`, tests de `harness/hooks.py` con JSON
  sintético por stdin: `pre-commit` con un comando `git commit` y un archivo preparado con una
  muestra no aprobada en un repo git temporal → código 2 y stderr con la regla pero sin el valor;
  con lo preparado limpio → 0; comando que no es un commit → 0; `post-edit` sobre una ruta de
  `src/` ejecuta las verificaciones aplicables y sobre una ruta ajena no hace nada
- [ ] T040 [P] [US4] En `tests/test_harness_hooks.py`, tests de `harness/lanzar.py` (ubica
  `venv/Scripts/python.exe` o `venv/bin/python`, cae en `sys.executable` si no hay venv, propaga el
  código de salida) y de `scripts/instalar_hooks.py` (idempotente: deja
  `core.hooksPath=.githooks` en la configuración **local** del clon y nunca toca la global)

### Implementación de User Story 4

- [X] T041 [US4] Implementar `harness/lanzar.py`: lanzador solo biblioteca estándar que ubica el
  Python del venv y delega en él (research D8) — depende de T040 en rojo
- [X] T042 [US4] Implementar `harness/hooks.py`: subcomandos `pre-commit` y `post-edit` que leen el
  JSON del hook por stdin; `pre-commit` corre la guardia sobre lo preparado y devuelve 2 con el
  motivo; `post-edit` corre las verificaciones aplicables a la ruta editada — depende de T026, T039
- [ ] T043 [P] [US4] Crear `.githooks/pre-commit` (`harness/lanzar.py guardia --preparados`) y
  `.githooks/pre-push` (`harness/lanzar.py todo`) y marcarlos ejecutables en el índice de git
- [X] T044 [P] [US4] Crear `scripts/instalar_hooks.py`: `git config --local core.hooksPath
  .githooks`, acción explícita e idempotente, que informa lo que hizo
- [X] T045 [US4] Ampliar `.claude/settings.json` **sin reemplazar** las reglas `ask` existentes:
  hook `PreToolUse` sobre `git commit` (`python harness/lanzar.py hook pre-commit`) y `PostToolUse`
  sobre ediciones de `src/**`, `specs/**`, `tests/**` (`python harness/lanzar.py hook post-edit`,
  en segundo plano). Seguir el flujo del skill `update-config`: probar el comando crudo con una
  prueba de tubería, escribir, validar el JSON, y dejar sin silenciar los errores
- [X] T046 [US4] Actualizar `.gitignore`: reemplazar `.claude/` por `.claude/*` con las excepciones
  `!.claude/skills/` y `!.claude/settings.json`; repetir la búsqueda de secretos sobre lo que pasa a
  versionarse y confirmar con `git check-ignore` y `git status` (research D9)
- [ ] T047 [US4] Comprobar que los hooks realmente se disparan dentro de la sesión (un centinela
  temporal y su limpieza); si el observador de configuración no los cargó, indicar al usuario que
  abra `/hooks` o reinicie la sesión — no afirmar que funcionan sin evidencia

**Checkpoint**: US4 funcional e independiente (FR-013, FR-014, FR-019, FR-020).

---

## Phase 7: User Story 5 - Memoria compartida del proyecto (Priority: P2)

**Goal**: un documento versionado con el contexto del proyecto, cargado solo por el asistente en
cualquier clon, sin datos personales.

**Independent Test**: quickstart §7.

### Tests de User Story 5 (escribir y confirmar que fallan antes de implementar)

- [ ] T048 [P] [US5] En `tests/test_harness_guardia.py`, tests de `R-CONTACTO` (correos, teléfonos
  y tratamiento + apellido, con muestras armadas en ejecución) marcados **solo** cuando el archivo es
  `docs/MEMORIA.md`; el mismo texto en otro archivo no dispara esa regla. En
  `tests/test_harness_config.py`: `docs/MEMORIA.md` existe, tiene el encabezado de política y las cinco
  secciones de `data-model.md`, y `CLAUDE.md` contiene la línea `@docs/MEMORIA.md`

### Implementación de User Story 5

- [ ] T049 [US5] Agregar la regla `R-CONTACTO` (alcance `docs/MEMORIA.md`) a `harness/guardia.py`
  — depende de T048 en rojo
- [ ] T050 [US5] Escribir `docs/MEMORIA.md` **desde cero** (no se copian los archivos de memoria
  locales): encabezado con la política de contenido y las cinco secciones (objetivo y plazos;
  arquitectura y decisiones; convenciones; lecciones aprendidas; estado). Integrantes por nombre de
  pila, colaboradores externos por rol, sin otros proyectos, sin datos de pacientes ni credenciales
- [ ] T051 [US5] Agregar a `CLAUDE.md` la línea `@docs/MEMORIA.md` y la convención de actualizarla
  cuando se toma una decisión durable (ese cambio pasa por las dos confirmaciones)
- [ ] T052 [US5] Verificación manual **a cargo del usuario**: abrir una sesión nueva y preguntar
  por un dato que solo figure en `docs/MEMORIA.md` para confirmar que el import `@` se carga solo
  (research D10, "a verificar")

**Checkpoint**: US5 funcional e independiente (FR-015, FR-016).

---

## Phase 8: User Story 6 - Regla "spec primero" en la constitution (Priority: P3)

**Goal**: la regla de fondo queda escrita como principio, con versión incrementada.

**Independent Test**: leer la constitution (quickstart §9).

- [ ] T053 [P] [US6] En `tests/test_harness_config.py`, test de que
  `.specify/memory/constitution.md` contiene el Principio VI sobre specs como fuente de verdad y
  `Version**: 1.1.0`, y que el Principio IV referencia la guardia
- [ ] T054 [US6] Ejecutar `/speckit-constitution` (no editar a mano) para agregar el Principio VI
  "Los specs son la fuente de verdad" con su justificación (los casos de deriva: canales, opset,
  vistas, y la filtración de datos) y la referencia en el Principio IV; versión 1.1.0 (MINOR) — depende
  de T053 en rojo

---

## Phase 9: Polish & Cross-Cutting Concerns

- [ ] T055 Verificar la visibilidad real del repositorio (`gh repo view Lucas8276/VetVision --json
  visibility`) y actualizar la sección Assumptions y el FR-016 de `spec.md` para que reflejen lo
  verificado, no lo que se supone (spec primero)
- [ ] T056 Actualizar la estructura de `plan.md` para incluir `tests/test_harness_nucleo.py`,
  `tests/test_harness_hooks.py` y cualquier desvío aparecido durante la implementación
- [ ] T057 Documentar en `CLAUDE.md`: el comando `python -m harness`, cómo activar los hooks de git
  (`python scripts/instalar_hooks.py`), la arquitectura de tres capas y que CI llega después del push
- [ ] T058 Correr `quickstart.md` de punta a punta (§1 a §9) y registrar el resultado de cada paso
- [ ] T059 Preparar los commits **en grupos lógicos** y pasar cada uno por las dos confirmaciones:
  (a) documentos de la feature 003; (b) correcciones de specs y `src/export_onnx.py`; (c) `harness/`
  y sus tests; (d) CI y `requirements-ci.txt`; (e) `.claude/` compartido, hooks y `.gitignore`;
  (f) memoria compartida y constitution. Los archivos de la demo web (`server.py`, la página HTML,
  `support.js`, y los cambios de `requirements.txt` para Flask) **no** forman parte de esta feature y
  quedan afuera
- [ ] T060 Avisar al dueño del repo (Lucas): activar la protección de rama con el chequeo de CI
  obligatorio, y que cada integrante corra `python scripts/instalar_hooks.py` una vez por clon

---

## Dependencies & Execution Order

- **Setup (Fase 1)** → **Foundational (Fase 2)** → todas las historias.
- **US1 (Fase 3)** y **US3 (Fase 4)**: independientes entre sí, pueden hacerse en paralelo.
- **US2 (Fase 5)**: depende de US1 y US3 (`todo` agrega lo que producen); los tests de configuración
  de CI (T029) y la redacción de `verificar.yml` pueden adelantarse.
- **US4 (Fase 6)**: depende de US3 (los hooks llaman a la guardia) y de US2 (`pre-push` llama a
  `todo`).
- **US5 (Fase 7)**: depende de US3 (la regla `R-CONTACTO` vive en la guardia).
- **US6 (Fase 8)**: independiente de las demás.
- **Polish (Fase 9)**: al final.

### Dentro de cada historia

- Los tests van primero y deben fallar antes de implementar.
- Spec primero: T008–T011 (desvíos de contrato) antes que T015–T017.

### Parallel Opportunities

- T002 y T003 (Setup).
- T004 y T006 (Foundational).
- T009 y T010 (specs distintos); T012, T013, T014 (mismo archivo de test pero independientes).
- T020, T021, T022, T023 (casos de test independientes).
- T029 y T030; T038, T039, T040; T043 y T044.
- US1 y US3 completas, repartidas entre dos personas.

---

## Implementation Strategy

### MVP primero

1. Fases 1 y 2.
2. **US1** (validador de contratos): ya hace cumplir la regla central y destapa los desvíos reales.
3. **Parar y validar**: quickstart §1 y §2.

### Entrega incremental

1. US1 → US3 (la guardia, prioridad de seguridad) → US2 (CI y comando único): con estas tres queda
   el MVP del harness.
2. US4 y US5 (P2): comparten la configuración con Lucas y dan memoria común.
3. US6 (P3) y Polish: gobernanza y cierre.

---

## Notes

- Esta feature fue especificada antes de programarse (regla del equipo). Si durante la
  implementación aparece algo que contradice `spec.md` o `plan.md`, se corrige el documento primero.
- La demo web no forma parte de esta feature: queda pendiente retro-especificarla como una feature
  aparte (004).
