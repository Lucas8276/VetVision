# Feature Specification: Harness v2 — incremento 1: verificación del documento

**Feature Branch**: `005-harness-v2`
**Created**: 2026-11-17
**Status**: Draft (versión abreviada). Los incrementos siguientes (verificadores de contratos
faltantes, salida `--json`, reglas de coherencia, terminología y sincronización) se agregan a este spec.
**Input**: el documento de entrega se redacta con asistencia de IA. La condición para hacerlo es que
exista un control automático equivalente al del código: ningún número sin fuente, ninguna cita sin
verificar, ningún dato personal, ninguna sección dada por final sin que una persona la haya revisado.

El **contenido** del documento es privado y no se versiona (`docs/privado/documento/`). A este
repositorio van el código del verificador, este spec y tests con documentos sintéticos.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Saber qué le falta al documento (Priority: P1)

Como autor, corro un comando y veo, con archivo y línea, cada marcador pendiente, cada número sin
respaldo, cada cita no permitida y cada sección sin revisar.

**Independent Test**: sobre un documento sintético correcto no hay hallazgos; al introducir cada tipo de
defecto aparece el hallazgo de la regla correspondiente, con su ubicación.

### User Story 2 - Bloquear una entrega incompleta (Priority: P1)

Como equipo, antes de entregar corro el modo de entrega: si queda un pendiente, una sección sin revisor
o un descargo faltante, el comando termina con error.

**Independent Test**: el mismo documento con un `[PENDIENTE: ...]` termina con código 0 en modo normal y
con código 1 en modo entrega.

### Edge Cases

- No existe el directorio privado (por ejemplo en CI): se informa `sin_verificacion` y no falla.
- Se pasa un directorio explícito que no existe: error de uso (código 2).
- Falta alguno de los archivos de datos (`hechos.yaml`, etc.): la regla que lo necesita informa la falla
  con el nombre del archivo; las demás reglas siguen.

## Requirements *(mandatory)*

### Estructura del directorio del documento

Capítulos en Markdown (`*.md`) y cinco archivos de datos:

| Archivo | Contenido |
|---|---|
| `normativa.yaml` | `secciones_obligatorias` (archivo y `palabras_minimas`), `descargo` (`frases` y `archivos` donde debe aparecer), `citas` (`acceso_libre_obligatorio`, `anio_minimo_por_tema`) |
| `hechos.yaml` | `hechos`: lista de `clave`, `valor`, `unidad`, `fuente` (`archivo#ancla`, relativo a la raíz del repo), `verificado_en`; opcional `valor_en_fuente` cuando el número figura con otro formato |
| `fuentes.yaml` | `fuentes`: lista de `clave`, `anio`, `tema`, `verificada`, `acceso_libre`; opcional `clasico` |
| `estado-sync.yaml` | `secciones`: por archivo, `estado` (`borrador` o `final`), `revisor`, `fecha`, `asistencia_ia` |
| `declaracion-uso-ia.yaml` | `registros`: lista de `apartado`, `herramienta`, `fecha`, `tipo_de_ayuda` |

En el texto: los números técnicos se escriben `{{hecho:clave}}`, las citas `[@clave]` y lo no resuelto
`[PENDIENTE: motivo]`.

### Functional Requirements

- **FR-001**: `python -m harness documento [--dir RUTA] [--entrega]` DEBE validar el documento con los
  mismos códigos de salida que el resto del harness (0 sin fallas, 1 con fallas, 2 error interno o de uso).
- **FR-002 (D-ESTRUCTURA)**: cada sección obligatoria DEBE existir; si tiene menos palabras que su
  mínimo se informa como pendiente.
- **FR-003 (D-PENDIENTE)**: cada `[PENDIENTE`, `[A completar` y `[Completar` DEBE listarse con archivo y
  línea.
- **FR-004 (D-HECHO)**: cada `{{hecho:clave}}` DEBE existir en `hechos.yaml`; cada hecho DEBE tener
  fuente y fecha de verificación, su archivo fuente DEBE existir y el valor DEBE figurar en ese archivo.
  Así un número del documento deja de pasar la verificación cuando cambia en el repositorio.
- **FR-005 (D-CITA)**: cada `[@clave]` DEBE existir en `fuentes.yaml`, estar verificada, ser de lectura
  libre cuando la normativa lo exige, y cumplir el año mínimo de su tema salvo que sea un clásico.
- **FR-006 (D-DATOS)**: el texto del documento DEBE pasar las reglas de datos personales de la guardia.
- **FR-007 (D-LIMITE)**: cada archivo listado en `descargo.archivos` DEBE contener al menos una de las
  frases de descargo.
- **FR-008 (D-REVISION)**: una sección marcada `final` DEBE tener revisor y fecha. En modo entrega,
  toda sección obligatoria DEBE estar en `final`.
- **FR-009 (D-IA)**: toda sección con `asistencia_ia: true` DEBE figurar en `declaracion-uso-ia.yaml`.
- **FR-010**: Los mensajes NUNCA repiten el dato detectado: solo regla, archivo y línea.
- **FR-011**: En modo normal, lo que es trabajo por hacer (D-PENDIENTE, sección corta, descargo
  faltante, sección sin revisar) se informa `pendiente` y no produce error. Lo que es un defecto
  (D-HECHO, D-CITA, D-DATOS, D-IA, sección `final` sin revisor, sección faltante) es `falla` siempre.
  En modo entrega todo `pendiente` pasa a `falla`.
- **FR-012**: `python -m harness` (todo) DEBE incluir una sola línea de resumen del documento cuando el
  directorio privado existe, sin bloquear el trabajo sobre el código.

## Success Criteria *(mandatory)*

- **SC-001**: Cada regla (FR-002 a FR-009) tiene al menos un test que la dispara y uno que no.
- **SC-002**: Los tests corren en CI sin el directorio privado.
- **SC-003**: Sobre el documento real, el conteo de D-PENDIENTE coincide con el conteo manual del día de
  la importación (35 `[PENDIENTE` y 12 `[A completar`).
- **SC-004**: `python -m harness` en verde.

## Assumptions

- Un capítulo por archivo; el orden lo da el nombre del archivo.
- Coincidencia del valor de un hecho con su fuente: búsqueda de texto exacta (simple y explicable); no
  interpreta tablas ni unidades.
