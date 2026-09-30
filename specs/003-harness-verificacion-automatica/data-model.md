# Data Model: Harness de verificación automática

## Resultado (unidad común de todas las verificaciones)

Todas las capas informan con esta misma estructura; el reporte impreso y el código de salida se
derivan de ella.

| Campo | Tipo | Regla |
|---|---|---|
| `verificacion` | `contratos` \| `guardia` \| `tests` | qué verificación lo produjo |
| `estado` | `ok` \| `falla` \| `pendiente` \| `sin_verificacion` | solo `falla` hace que el comando devuelva código ≠ 0 |
| `ubicacion` | texto | contrato + ruta del campo (`model-tensor › etapas › etapa_0_torax › output_shape`) **o** `archivo:línea` |
| `regla` | texto \| vacío | identificador de regla de la guardia (`R-…`) |
| `esperado` | texto \| vacío | valor del spec (solo contratos) |
| `obtenido` | texto \| vacío | valor del código (solo contratos) |
| `mensaje` | texto | accionable: qué corregir. **Nunca** incluye el valor detectado por la guardia (FR-018, D5) |

**Transiciones**: un campo pasa `sin_verificacion → ok/falla` cuando se registra su verificador; una
sección pasa `pendiente → (ok/falla/sin_verificacion)` cuando el spec cambia `estado: pendiente` a
`implementado`.

## Contrato (`specs/*.spec.yaml`)

| Elemento | Detalle |
|---|---|
| Archivo | `model-tensor`, `ground-truth-annotation`, `data-contract` |
| Hoja | cada valor terminal del YAML, identificado por su ruta |
| `estado` (nuevo, opcional, por sección) | `pendiente` \| `implementado`; ausente = `implementado` |

## Verificador (registro interno de `contratos.py`)

| Campo | Regla |
|---|---|
| `ruta` | ruta de la hoja del contrato que cubre |
| `obtener()` | función que devuelve el valor real del código (importa el código del proyecto; construye el modelo con `weights=None`, una sola vez por corrida) |
| `comparar` | igualdad exacta, o pertenencia de conjunto para listas (orden irrelevante) |

## Regla de guardia

| Campo | Regla |
|---|---|
| `id` | `R-ARCHIVO-CRUDO`, `R-CAMPO-PACIENTE`, `R-NOMBRE-DICOM`, `R-ID-PACIENTE`, `R-SECRETO`, `R-CONTACTO` |
| `alcance` | glob de archivos a los que aplica (`**` por defecto; `docs/MEMORIA.md` para `R-CONTACTO`) |
| `patron` | expresión regular estructural (no contiene valores reales) |
| `aprobable` | si un valor de `valores_ficticios.txt` la satisface (todas menos `R-ARCHIVO-CRUDO`, `R-SECRETO`, `R-CONTACTO`) |

## Valor ficticio aprobado (`harness/valores_ficticios.txt`)

Una línea por valor; `#` inicia comentario. Contiene **solo** valores obviamente inventados
(`PACIENTE^PRUEBA`, `PACIENTE PRUEBA`, `0000-1`, `123-4`, `456-7`, `999-1`, `12345`, etc.).
Agregar un valor requiere que sea evidentemente ficticio y pasa por revisión como cualquier cambio.

## Documento de memoria compartida (`docs/MEMORIA.md`)

| Sección fija | Contenido permitido |
|---|---|
| Objetivo y plazos | qué es VetVision, fechas de entrega y de disponibilidad del equipo |
| Arquitectura y decisiones | decisiones durables y su porqué (cascada, Etapa 0 binaria, fine-tuning parcial) |
| Convenciones | reglas de trabajo (dos confirmaciones, spec primero, datos ficticios) |
| Lecciones aprendidas | bugs reales y cómo se detectaron |
| Estado | qué está hecho / bloqueado, sin datos personales |

**Prohibido** (FR-016): datos de pacientes/dueños, nombres de contactos externos (se usa el rol),
información de otros proyectos de los integrantes, credenciales, correos y teléfonos.

## Configuración compartida del asistente

| Elemento | Se versiona | Notas |
|---|---|---|
| `.claude/skills/**` | sí | comandos `/speckit-*` |
| `.claude/settings.json` | sí | reglas `ask` (commit/push) + hooks |
| `.claude/settings.local.json` y demás | no | personal; sigue ignorado |

## Entradas de los hooks del asistente

JSON por stdin (campos usados): `tool_name`, `tool_input.file_path` (ediciones) o
`tool_input.command` (Bash/PowerShell). Salida por código de salida: `0` = continuar, `2` = bloquear
con el motivo en stderr.
