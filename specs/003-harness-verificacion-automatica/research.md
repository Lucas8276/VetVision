# Research: Harness de verificación automática

Sin `[NEEDS CLARIFICATION]` en el Technical Context. Cada decisión se apoya en un hecho verificado
en el repo o en una restricción del spec (las que vienen de una medición están marcadas).

## D1 — Arquitectura del validador de contratos

**Decision**: un registro de *verificadores* indexado por la ruta del campo dentro del YAML
(`model-tensor › etapas › etapa_0_torax › output_shape`, etc.). El validador recorre las hojas de cada
contrato y a cada una le asigna un estado: **ok**, **falla**, **pendiente** o **sin verificación**.
Una etapa se declara pendiente *en el propio spec* con un campo `estado: pendiente` (hoy las etapas 1
y 2, bloqueadas por la anotación clínica); cuando se implemente, se cambia a `implementado` y sus
campos sin verificador aparecen como "sin verificación" hasta que se registren.

**Rationale**: FR-003 y FR-004 piden que lo pendiente y lo no cubierto sean *visibles*, no silenciosos.
Que el estado viva en el spec (no en una lista dentro del código del validador) respeta la regla de
fondo: el spec manda.

**Alternatives considered**:
- *Lista de etapas pendientes dentro del validador* — rechazada: esconde en código una decisión que
  pertenece al spec.
- *Generar código o tests desde el YAML* — rechazada por sobre-ingeniería (Principio V).
- *Validar solo la forma del YAML con un esquema (pydantic/jsonschema)* — rechazada: comprueba que el
  spec esté bien escrito, no que el código lo cumpla, que es el problema real.

## D2 — Qué valor del código se compara con cada campo (verificado)

| Campo del contrato | Valor real del código |
|---|---|
| `input.canales` / `etapa_0.input_shape[0]` | `in_channels` de `features.conv0` del modelo construido |
| `input.size` | tamaño por defecto de `normalizar_jpg_veterinario` (512) y forma que devuelve `VetVisionEtapa0Dataset.__getitem__` |
| `etapa_0.output_shape` / `clases` | `classifier.out_features` y `ETIQUETAS_A_IDX` |
| `etapa_0.umbral_promocion_balanced_accuracy` | `UMBRAL_PROMOCION_ACC` de `src/evaluate.py` |
| `export.formato` / `export.opset` | valor por defecto de `exportar_onnx(opset=...)` |
| `proyecciones_admitidas` / `especies_admitidas` | `VISTAS_VALIDAS` / `ESPECIES_VALIDAS` de `src/parser_fcr.py` |
| `etapa_0.fuente`, `requiere_anotacion_manual` | (sin verificador — declarativo) |
| `resolucion_minima_px`, formatos de archivo, `anonimizacion` | (sin verificador — dependen del dataset o de un pipeline de anonimización que aún no existe) |

Los últimos dos renglones se informarán como "sin verificación": es cobertura visible, no un vacío.

## D3 — Desvíos que ya existen hoy (medido) y cómo se resuelven

Al comparar los tres contratos con el código real aparecieron dos divergencias:

1. **Formato de exportación**: el código exporta con `opset=17` por defecto pero el spec (corregido
   ayer contra el archivo realmente producido) dice **18**. *Resolución (el spec manda)*: el valor por
   defecto del código pasa a 18, alineado con lo que PyTorch 2.14 realmente genera.
2. **Vistas admitidas**: el código acepta `LAT, VD, DV, AP, VD/DV`; el `data-contract` lista solo
   `LAT, VD, DV` (y su propio comentario menciona `AP`). `VD/DV` sale de datos reales (feature 001).
   *Resolución (spec primero, Principio II)*: se actualiza el contrato a las cinco vistas, con la
   nota de por qué; recién después el código y el spec coinciden y el validador arranca en verde.

Es la primera evidencia concreta de que la validación hace falta: dos desvíos sobrevivieron sin que
nadie los notara.

## D3b — Construir el modelo sin pesos preentrenados (medido)

Validar el contrato del modelo requiere instanciar la arquitectura. `DenseNetEtapa0(num_classes=2,
weights=None)` funciona (verificado; `conv0.in_channels == 1`, salida 2) y tarda 13 s con imports.
CI no debe ni necesita descargar los ~27 MB de pesos: el contrato habla de formas, no de valores.

## D4 — Un solo comando, mismo veredicto en todas partes

**Decision**: `python -m harness [contratos|guardia|todo]` (default `todo`) ejecuta el validador, la
guardia sobre el árbol y pytest; devuelve código ≠ 0 si algo falla. Lo invocan los hooks, `pre-push` y
CI. El test que valida el repo real contra los contratos lleva un marcador para no correr dos veces
dentro de `todo`.

**Rationale**: FR-007 y SC-006 exigen que el veredicto local coincida con el de CI; con una sola
implementación no hay cómo divergir.

## D5 — Guardia de datos personales: detectar sin almacenar lo detectado

**Decision** (respeta FR-009 a FR-012): reglas estructurales + lista de valores *ficticios* aprobados,
nunca una lista de nombres prohibidos.

| Regla | Detecta | Aprueba si |
|---|---|---|
| `R-ARCHIVO-CRUDO` | rutas/extensiones de datos crudos del equipo de rayos X, imágenes del dataset (`FCR<n>.*`), `data/raw`, `data/processed`, bases locales (`*.db`), checkpoints | (nunca; se bloquea) |
| `R-CAMPO-PACIENTE` | campo `Nombre del paciente:` o etiqueta DICOM de nombre con un valor | el valor está en `valores_ficticios.txt` o es un marcador de plantilla (`{...}`) |
| `R-NOMBRE-DICOM` | patrón `APELLIDO^NOMBRE` | está en la lista de aprobados |
| `R-ID-PACIENTE` | campo `ID del paciente:` con valor, e IDs sueltos con forma `NNN(N)-N` (con lookaround para no confundir fechas ni versiones) | está en la lista de aprobados |
| `R-SECRETO` | claves de nube, tokens de GitHub, bloques de clave privada, asignaciones `password=`/`api_key=` con valor largo | (nunca; se bloquea) |
| `R-CONTACTO` (solo `docs/MEMORIA.md`) | correos, teléfonos, tratamiento + apellido (`Dra. …`) | (nunca en ese archivo) |

**Reporte**: `archivo:línea [regla] valor redactado` — jamás el valor. Los logs de CI de un repo
público son públicos: un reporte que imprime el hallazgo repetiría la filtración.

**Fixtures de la guardia**: los tests arman las muestras "filtradas" concatenando fragmentos en
tiempo de ejecución, así el texto del archivo de test no coincide con las reglas y no se marca a sí
mismo, sin abrir una excepción por ruta (una excepción sería un agujero).

**Limitación asumida** (Assumptions del spec): es heurística. Un nombre real fuera de un campo o
patrón reconocible no se detecta; por eso el documento de memoria y la revisión de cambios siguen
siendo parte de la defensa.

**Alternatives considered**:
- *Lista de valores prohibidos* — rechazada: sería en sí misma una filtración (FR-011). Una variante
  con hashes de los valores reales también se descarta: un hash de un nombre corto es reversible por
  fuerza bruta y complica el mantenimiento.
- *`gitleaks`/`detect-secrets`* para secretos — rechazadas por ahora: agregan dependencia y
  configuración para cubrir un caso que hoy es chico (el proyecto no maneja claves). Se reevalúa si
  aparecen credenciales reales.
- *Excluir por ruta los tests de la guardia* — rechazada: cada exclusión es un agujero.

## D6 — CI llega tarde: la prevención tiene que ser local

**Decision**: tres capas con el mismo comando.
1. **Hooks del asistente** (`.claude/settings.json`): antes de un `git commit` corre la guardia sobre
   lo preparado y bloquea si hay hallazgos; tras editar código/specs/tests corre las verificaciones.
2. **Hooks de git** (`.githooks/pre-commit`, `pre-push`): cubren los commits hechos a mano. Se activan
   con `python scripts/instalar_hooks.py` (`core.hooksPath`), **una vez por clon y de forma explícita**:
   no se modifica la configuración de git automáticamente.
3. **CI** (GitHub Actions): red de contención sobre todo el árbol en cada push y pull request.

**Rationale**: la filtración original habría pasado CI igual — el problema no es que faltara un
chequeo en el servidor, es que el dato ya estaba público cuando el servidor lo viera. Solo las capas 1
y 2 pueden impedirlo; la 3 detecta lo que las otras no frenaron (p. ej. quien no activó los hooks).

**Riesgo asumido**: un integrante que nunca corra `instalar_hooks.py` y commitee a mano queda solo con
CI. Mitigación: `python -m harness` avisa si `core.hooksPath` no está activado, y `CLAUDE.md` lo
documenta.

## D7 — CI

**Decision**: `.github/workflows/verificar.yml`, disparado por `push` y `pull_request`;
`ubuntu-latest`, Python 3.13; instala **PyTorch CPU** desde el índice CPU de PyTorch (el `torch` por
defecto en Linux arrastra ~2.5 GB de librerías CUDA que sobran) y el resto desde `requirements-ci.txt`;
ejecuta `python -m harness`. Permisos mínimos (`contents: read`), sin secretos. Acciones oficiales
`actions/checkout` y `actions/setup-python` fijadas a su versión mayor.

**Rationale**: SC-002 pide menos de 10 min. Sin el dataset real (FR-006): los tests ya usan datos
sintéticos y el validador construye el modelo sin pesos (D3b). Un pull request de un fork corre sin
acceso a secretos, que de todos modos no existen.

**Riesgos**:
- La suite nunca corrió en Linux; el primer CI es una prueba de integración. Se hace primero en una
  rama de prueba.
- Que un fallo "bloquee" el cambio requiere **protección de rama** (exigir el chequeo antes de
  fusionar): es un ajuste del repositorio que solo puede hacer el dueño. Sin él, CI marca rojo pero no
  impide fusionar. Queda documentado en `quickstart.md` como acción del dueño.

## D8 — Hooks del asistente (mecánica)

**Decision**: en `.claude/settings.json`, junto a las reglas `ask` ya existentes:
- `PreToolUse` sobre `git commit`: `python harness/lanzar.py hook pre-commit` — corre la guardia sobre
  lo preparado; código de salida 2 bloquea el commit y muestra el motivo al asistente.
- `PostToolUse` sobre ediciones de `src/**`, `specs/**` y `tests/**`: corre las verificaciones
  aplicables en segundo plano; si fallan, despierta al asistente para corregir (evita bloquear cada
  edición por los ~15 s del validador).

Los comandos usan solo `python` y leen el JSON del hook por stdin (sin `jq` ni sintaxis propia de una
shell), para que funcionen igual en PowerShell y en bash. `lanzar.py` (solo stdlib) ubica el venv
(`venv/Scripts/python.exe` o `venv/bin/python`) y delega. La sintaxis exacta del filtro `if` y el
comportamiento asíncrono se comprueban con una prueba de tubería (pipe-test) al implementar.

**Nota**: los hooks de un proyecto compartido requieren que cada integrante confíe en el proyecto la
primera vez que lo abre; es esperable y correcto.

## D9 — Compartir `.claude/` (auditoría hecha)

**Decision**: `.gitignore` pasa de `.claude/` a `.claude/*` con excepciones `!.claude/skills/` y
`!.claude/settings.json`; `settings.local.json` y cualquier otro archivo personal siguen ignorados.

**Rationale**: la auditoría del spec confirmó que `.claude/` contiene solo 10 archivos `SKILL.md` de
spec-kit sin secretos. Con esto un clon limpio trae los comandos `/speckit-*` y las reglas
(`ask` + hooks) sin pasos de instalación (SC-004).

## D10 — Memoria compartida

**Decision**: `docs/MEMORIA.md`, importado desde `CLAUDE.md` con la sintaxis `@docs/MEMORIA.md` para
que se cargue solo al iniciar sesión. Encabezado con la política de contenido; secciones fijas
(objetivo y plazos, arquitectura y decisiones, convenciones, lecciones aprendidas, estado). Se
actualiza por convención cuando se toma una decisión durable, y ese cambio pasa por las dos
confirmaciones. La guardia aplica al archivo la regla extra `R-CONTACTO` (D5).

**Contenido**: se **reescribe** desde cero a partir de lo importante para el proyecto, no se copian
los archivos de memoria locales (contienen nombres de contactos externos, datos personales de los
integrantes e información de otros proyectos, todo excluido por FR-016). Los integrantes figuran por
nombre de pila; los colaboradores externos, por rol ("el hospital", "una radióloga colaboradora").

**Alternatives considered**: base de datos (descartada en el spec por simplicidad); copiar el
directorio de memoria local (descartado por su contenido personal); wiki externa (fuera del repo,
no se carga sola).

**A verificar al implementar**: que el import `@` de `CLAUDE.md` cargue el archivo (se prueba abriendo
una sesión nueva y preguntando por un dato que solo esté en `MEMORIA.md`).

## D11 — Enmienda de la constitution

**Decision**: agregar el Principio VI "Los specs son la fuente de verdad" (si el código no coincide,
el código está mal; primero se especifica, después se codea) con su justificación (los cuatro casos de
deriva: canales, opset, vistas y la filtración de datos), y una referencia en el Principio IV a la
guardia. Versión 1.1.0 (MINOR). Se hace con `/speckit-constitution` en la fase de implementación.

## D12 — Dependencias

`pyyaml` se agrega a `requirements.txt` (hoy llega solo como dependencia transitiva de otros
paquetes; el validador la usa directamente). `requirements-ci.txt` lista solo lo que las verificaciones
importan: `torch` (CPU), `torchvision`, `torchxrayvision`, `opencv-python-headless`, `numpy`,
`Pillow`, `pylibjpeg`, `pylibjpeg-libjpeg`, `scikit-learn`, `pyyaml`, `pytest`, y `onnx`/`onnxruntime`/
`onnxscript` solo si la comprobación de `opset` sobre el archivo exportado se activa (D2 usa el valor
por defecto del código, que no las necesita).
