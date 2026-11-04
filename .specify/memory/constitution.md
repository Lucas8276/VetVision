<!--
Informe de impacto de la sincronización
- Cambio de versión: 1.0.0 → 1.0.1 (PATCH: traducción al español, sin cambios de reglas;
  se corrige además la mención de ONNX de opset 17 a 18, para coincidir con
  specs/model-tensor.spec.yaml y con la exportación real)
- Principios vigentes (sin cambios):
  1. Spec primero (INNEGOCIABLE)
  2. Specs basados en datos reales
  3. Pruebas primero para los parsers (INNEGOCIABLE)
  4. Protección de datos de pacientes
  5. Simplicidad / sin etapas especulativas
- Secciones: Restricciones adicionales (stack/entorno), Flujo de desarrollo
  (pipeline SDD, restricción de calendario, convenciones de commits), Gobernanza
- Elementos diferidos: ninguno
- Plantillas que requieren seguimiento: las plantillas de .specify/templates/ también se
  tradujeron al español; los marcadores técnicos ([NEEDS CLARIFICATION], FR-, SC-, P1,
  [P], [US1], CHK) se conservan en inglés porque los skills y los specs existentes los usan
-->

# Constitution de VetVision AI

## Principios fundamentales

### I. Spec primero (INNEGOCIABLE)
Ninguna funcionalidad no trivial, cambio de parser o cambio del pipeline del modelo se
implementa directamente a partir de un pedido informal. DEBE pasar por `/speckit-specify` →
`/speckit-plan` → `/speckit-tasks` → `/speckit-implement` antes de escribir código. Las
correcciones triviales (una errata, formato, el cambio de versión de una sola dependencia)
quedan exentas.
**Justificación**: este proyecto existe en parte para aprender bien el Desarrollo Guiado por
Specs (SDD); saltarse el flujo por comodidad anula el propósito y reintroduce el estado
sin documentar y basado en conocimiento tácito que los specs vinieron a corregir (ver
`specs/*.spec.yaml`, que existían como intención y sin ningún mecanismo de cumplimiento
antes de esta constitution).

### II. Specs basados en datos reales
Los specs y la lógica de validación DEBEN escribirse contra valores realmente observados en
el dataset de producción, no contra valores supuestos. Antes de escribir o actualizar un
spec que toque campos de metadata (región, vista, especie, etc.), hay que muestrear salidas
reales de `.txt`/`.ddo` y codificar el conjunto de valores observados. Las discrepancias
reales ya descubiertas DEBEN tratarse como insumos obligatorios del spec, no dejarse como
alternativas silenciosas: los códigos de región anatómica llegan en inglés/códigos del
equipo (`CHEST`, `NECK`, `HEAD`, `UP_EXM`, `LOW_EXM`), no en el conjunto en español que
validaba `src/parser_fcr.py`; el campo "vista" puede ser un token combinado (`VD/DV`) o
estar ausente; los IDs de paciente pueden contener un guion (`123-4`).
**Justificación**: los conjuntos `REGIONES_VALIDAS`/`VISTAS_VALIDAS` originales se escribieron
por suposición y clasificaban mal en silencio la mayoría de los registros reales como
`"DESCONOCIDA"`: un defecto que solo se encontró muestreando directamente el dataset real,
no leyendo el código ni el spec anterior.

### III. Pruebas primero para los parsers (INNEGOCIABLE)
Todo cambio en el manejo binario de `.ddo`/`.hq` de `limpiar_datos_fcr.py` o en el parseo
de metadata de `src/parser_fcr.py` DEBE tener primero una prueba de regresión escrita, que
cubra el modo de falla específico, antes de escribir la corrección. Esto se aplica de forma
retroactiva a todo bug conocido ya corregido: el código DEBE incluir una prueba que
verifique el comportamiento de `SEQ_DELIM == (0xFFFE, 0xE0DD)` (no el espejado
`(0xFFFE, 0xDD00)`), para que no pueda regresar en silencio.
**Justificación**: se trata de ingeniería inversa de un formato binario sin documentar y
sin especificación oficial contra la cual verificar (ver `formato_ddo_hq_FCR_PRIMA.md`): la
única red de seguridad posible son pruebas que codifiquen lo que ya se aprendió por las
malas.

### IV. Protección de datos de pacientes
Los identificadores crudos de pacientes (nombre, ID original) DEBEN eliminarse o
convertirse en hash antes de que cualquier dato salga del almacenamiento local o
controlado por DVC, según la sección `anonimizacion` de `specs/data-contract.spec.yaml`.
Los archivos crudos de imágenes y metadata DEBEN permanecer ignorados por git (`*.jpg`,
`*.png`, `*.ddo`, `*.hq`, `*.std`, `*.dsp`, `*.edk`, `*.edr`, `data/raw/`,
`data/processed/`) y las credenciales del remoto de DVC DEBEN vivir en `.dvc/config.local`
o en variables de entorno (`dvc remote modify --local`), nunca en el `.dvc/config`
versionado.
**Justificación**: el dataset contiene registros reales de pacientes y dueños del Hospital
de Clínicas F.C.V. (UNNE); es una obligación de manejo de datos del hospital, no una
preferencia de estilo, y el equipo (Stiven + Lucas) está obligado por esa relación
independientemente del encuadre académico o comercial del proyecto.

### V. Simplicidad / sin etapas especulativas
No se construye código, modelos ni clases de dataset de la Etapa 1 (triaje) o la Etapa 2
(diagnóstico) antes de contar con la anotación clínica de la que dependen
(`specs/ground-truth-annotation.spec.yaml` marca ambas con `requiere_anotacion_manual:
true`). La Etapa 2 DEBE inicializarse a partir de los pesos ajustados de la Etapa 1 cuando
llegue a construirse: no se debe preparar de antemano ningún camino de entrenamiento
independiente "por las dudas". Solo se construye lo que sustentan los datos disponibles y
anotados hoy.
**Justificación**: responde a la restricción real del PFG: la anotación sigue pendiente, el
equipo tuvo disponibilidad reducida hasta el 2026-10-19 y la fecha límite final es el
2026-11-18; el andamiaje especulativo para etapas sin anotar consume tiempo que el equipo
no tiene.

## Restricciones adicionales

- **Stack**: Python 3.13, PyTorch/TorchVision, TorchXRayVision (backbone DenseNet-121,
  preentrenado en radiografías de tórax humano; no existe un modelo fundacional
  veterinario), OpenCV + Albumentations para operaciones de imagen, MLflow para el
  seguimiento de experimentos, DVC para el versionado de datos, ONNX (opset 18) para la
  exportación, pytest para las pruebas.
- **Entorno**: el desarrollo principal se hace en Windows (PowerShell); los scripts y el
  manejo de rutas no deben asumir un entorno exclusivamente POSIX.
- **Dependencias**: toda dependencia de ejecución nueva que use un script versionado DEBE
  agregarse a `requirements.txt` en el mismo cambio: no se debe dejar que un script dependa
  de un paquete no declarado (ya ocurrió una vez con `limpiar_datos_fcr.py` y
  `numpy`/`Pillow`/`pylibjpeg`).
- **Herramientas de IA de terceros**: no se instala ninguna extensión de agente, servidor
  MCP ni plugin de CLI de terceros con scripts de instalación sin revisar o sin aprobar, ni
  a nivel global de la máquina, para este proyecto. Se prefieren las herramientas oficiales
  (spec-kit de github/spec-kit, la memoria integrada de Claude Code) frente a paquetes sin
  verificar.

## Flujo de desarrollo

- Seguir el pipeline SDD de spec-kit (`/speckit-constitution` → `/speckit-specify` →
  `/speckit-plan` → `/speckit-tasks` → `/speckit-implement`) para el trabajo de
  funcionalidades; usar `/speckit-converge` cuando se redacta un spec sobre código que ya
  existe (por ejemplo, el parser `.ddo`→`.txt`).
- Los mensajes de commit se escriben en español, en modo imperativo/descriptivo, con los
  prefijos al estilo Conventional Commits ya en uso (`docs:`, `chore:`, `feat:`, `fix:`).
  Las líneas de atribución siguen lo que pida el usuario en cada commit; no se asume una
  regla permanente en ningún sentido.
- Dada la disponibilidad reducida del equipo hasta el 2026-10-19 (práctica profesional
  obligatoria) y la fecha límite del PFG el 2026-11-18, se prefieren incrementos pequeños e
  integrables de forma independiente frente a cambios grandes agrupados: un cambio que no
  se pueda mostrar ni probar antes de la siguiente reunión de seguimiento debe dividirse.

## Gobernanza

Esta constitution prevalece sobre la práctica informal en todo lo que cubre. Las enmiendas
se hacen volviendo a ejecutar `/speckit-constitution` con el cambio propuesto, lo que
actualiza este archivo y registra un Informe de impacto de la sincronización con qué
cambió y por qué.

**Política de versionado** (versionado semántico para este documento):
- MAJOR: se elimina un principio o se lo redefine de forma incompatible hacia atrás.
- MINOR: se agrega un principio nuevo o se amplía materialmente una sección.
- PATCH: correcciones de redacción o aclaraciones sin cambio de reglas.

Toda salida de `/speckit-plan` DEBE contrastarse con estos principios antes de ejecutar
`/speckit-tasks`; un plan que entre en conflicto con un principio debe revisarse o el
conflicto debe justificarse de forma explícita en el plan de esa funcionalidad (la
complejidad o la excepción deben justificarse, no anularse en silencio). Usar `CLAUDE.md`
como guía de desarrollo del día a día (comandos, mapa de arquitectura, problemas
conocidos): este documento es para los principios de gobierno, no para el detalle
operativo.

**Versión**: 1.0.1 | **Ratificada**: 2026-09-28 | **Última enmienda**: 2026-11-04
