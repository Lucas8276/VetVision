---
name: "speckit-constitution"
description: "Crea o actualiza la constitution del proyecto a partir de principios ingresados de forma interactiva o provistos."
argument-hint: "Principios o valores para la constitution del proyecto"
compatibility: "Requiere la estructura de proyecto de spec-kit con el directorio .specify/"
metadata:
  author: "github-spec-kit"
  source: "templates/commands/constitution.md"
user-invocable: true
disable-model-invocation: false
---


## Entrada del usuario

```text
$ARGUMENTS
```

**DEBES** considerar la entrada del usuario antes de continuar (si no está vacía).

## Límite de alcance

El trabajo de este comando se limita a actualizar la constitution del proyecto en sí. Las plantillas y
los comandos dependientes leen la constitution en tiempo de ejecución y acá no se modifican.

- Clasificá cada parte de la entrada del usuario como contenido de la constitution o como una
  intención distinta, ajena a la gobernanza.
- Si la entrada incluye pedidos de implementación de funcionalidades, generación de código,
  refactorización, compilación o despliegue, **NO DEBES** ejecutarlos. Extraelos como intenciones
  diferidas.
- **NO DEBES** crear, modificar ni eliminar archivos fuente de la aplicación, rutas de funcionalidades,
  componentes, pruebas, archivos de despliegue ni otros artefactos ajenos al flujo de la
  constitution.
- Si no está claro si una instrucción es contenido de la constitution, pedí una aclaración antes de
  hacer cambios.
- Después de completar la actualización de la constitution, incluí una sección `Próximas acciones` por cada
  intención diferida. Listá la intención original y sugerí el comando de Spec Kit de seguimiento
  adecuado, como `/speckit-specify`, sin invocarlo.
- Si no hay intenciones ajenas a la gobernanza, omití la sección `Próximas acciones`.

## Verificaciones previas a la ejecución

**Buscar hooks de extensión (antes de actualizar la constitution)**:
- Verificá si existe `.specify/extensions.yml` en la raíz del proyecto.
- Si existe, leelo y buscá las entradas bajo la clave `hooks.before_constitution`
- Si el YAML no se puede parsear o no es válido, no lo omitas en silencio: avisale al usuario que no se pudo leer `.specify/extensions.yml` (incluí el error del parser) y que no se verificó ningún hook, incluidos los obligatorios (`optional: false`) registrados ahí, y luego continuá normalmente
- Descartá los hooks cuyo campo `enabled` sea explícitamente `false`. Los hooks sin campo `enabled` se consideran habilitados por defecto.
- Para cada hook restante, **no** intentes interpretar ni evaluar las expresiones del campo `condition`:
  - Si el hook no tiene campo `condition`, o es nulo/vacío, tratá el hook como ejecutable
  - Si el hook define un `condition` no vacío, omití el hook y dejá la evaluación de la condición a la implementación de HookExecutor
- Al armar las invocaciones de comandos a partir de los nombres de comando de los hooks, reemplazá los puntos (`.`) por guiones (`-`). Por ejemplo, `speckit.git.commit` → `/speckit-git-commit`.
- Para cada hook ejecutable, emití lo siguiente según su indicador `optional`:
  - **Hook opcional** (`optional: true`):
    ```
    ## Hooks de extensión

    **Pre-hook opcional**: {extension}
    Comando: `/{command}`
    Descripción: {description}

    Prompt: {prompt}
    Para ejecutarlo: `/{command}`
    ```
  - **Hook obligatorio** (`optional: false`):
    ```
    ## Hooks de extensión

    **Pre-hook automático**: {extension}
    Ejecutando: `/{command}`
    EXECUTE_COMMAND: {command}

    Esperá el resultado del comando del hook antes de continuar con el Esquema.
    ```
    Después de emitir el bloque anterior DEBES invocar realmente el hook y esperar a que termine antes de continuar. Ejecutalo de la misma forma en que ejecutarías el comando vos mismo en este agente/sesión (la invocación puede diferir del id literal `{command}` mostrado arriba; por ejemplo, un agente en modo skills lo ejecuta como `/skill:speckit-...` o `$speckit-...`). Emitir el bloque por sí solo no ejecuta el hook.
- Si no hay hooks registrados o no existe `.specify/extensions.yml`, omití este paso en silencio

## Esquema

Estás actualizando la constitution del proyecto en `.specify/memory/constitution.md`. El esqueleto
activo de la constitution se resuelve en tiempo de ejecución del comando a partir de `constitution-template`
mediante la pila de resolución de presets/plantillas de Spec Kit.

Seguí este flujo de ejecución:

1. Ejecutá `.specify/scripts/powershell/resolve-template.ps1 constitution-template -Json` desde la raíz del repositorio y parseá `TEMPLATE_CONTENT` como la plantilla activa.
   - El resolvedor compartido aplica las sobrescrituras del proyecto, las capas de presets que se componen y las capas de extensiones
     antes de recurrir a la plantilla base. DEBE tener éxito antes de continuar.
   - Si falla, detenete e informá el error de resolución; no continúes con una sola capa de plantilla
     contribuyente.
   - Si existe `.specify/memory/constitution.md`, cargalo como fuente de los valores y enmiendas
     vigentes específicos del proyecto. Conservá la información que siga siendo aplicable al aplicar el
     esqueleto recién resuelto.
   - Si no existe, usá la plantilla resuelta como documento inicial.
   - No escribas de vuelta en ninguna capa de plantilla versionada.
   - Identificá cada token de marcador de posición con la forma `[IDENTIFICADOR_EN_MAYUSCULAS]`.
   **IMPORTANTE**: El usuario puede necesitar menos o más principios que los usados en la plantilla. Si se especifica un número, respetalo y seguí la plantilla general. Actualizarás el documento en consecuencia.

2. Recopilá/derivá los valores de los marcadores de posición:
   - Si la entrada del usuario (conversación) aporta un valor, usalo.
   - Si no, inferilo del contexto existente del repositorio (README, docs, versiones previas de la constitution si están incorporadas).
   - Para las fechas de gobernanza: `RATIFICATION_DATE` es la fecha original de adopción (si se desconoce, preguntá o marcá TODO), `LAST_AMENDED_DATE` es hoy si se hacen cambios, y si no se mantiene la anterior.
   - `CONSTITUTION_VERSION` debe incrementarse según las reglas de versionado semántico:
     - MAJOR: eliminaciones o redefiniciones de gobernanza/principios incompatibles hacia atrás.
     - MINOR: se agrega un principio/sección nuevo o se amplía materialmente la guía.
     - PATCH: aclaraciones, redacción, correcciones de erratas, refinamientos no semánticos.
   - Si el tipo de incremento de versión es ambiguo, proponé el razonamiento antes de cerrarlo.

3. Redactá el contenido actualizado de la constitution usando la plantilla resuelta como estructura obligatoria:
   - Reemplazá cada marcador de posición con texto concreto (sin dejar tokens entre corchetes, salvo los espacios de la plantilla que se conserven a propósito porque el proyecto eligió no definirlos todavía; justificá explícitamente cada uno que quede).
   - Conservá la jerarquía de encabezados; los comentarios pueden eliminarse una vez reemplazados, salvo que sigan aportando una guía aclaratoria.
   - Asegurate de que cada sección de Principio tenga: una línea de nombre breve, un párrafo (o lista de viñetas) que capture las reglas innegociables y una justificación explícita si no es obvia.
   - Asegurate de que la sección de Gobernanza liste el procedimiento de enmienda, la política de versionado y las expectativas de revisión de cumplimiento.

4. Producí un Informe de impacto de la sincronización como comentario HTML al comienzo del archivo de la constitution, después de la actualización.
   Este informe es material de trabajo temporal para que una persona revise la enmienda, no contenido
   de gobernanza; se espera que se elimine antes de versionar el archivo de la constitution enmendada.
   - Cambio de versión: anterior → nueva
   - Lista de principios modificados (título anterior → título nuevo si se renombró)
   - Secciones agregadas
   - Secciones eliminadas
   - Pendientes de seguimiento (TODO) si algún marcador de posición se difirió a propósito.

5. Validación antes de la salida final:
   - No quedan tokens entre corchetes sin explicar.
   - La línea de versión coincide con el informe.
   - Las fechas están en formato ISO AAAA-MM-DD.
   - Los principios son declarativos, verificables y sin lenguaje vago ("debería" → reemplazar por DEBE/DEBERÍA con justificación cuando corresponda).

6. Escribí la constitution completa de vuelta en `.specify/memory/constitution.md` (sobrescribir).

7. Mostrá un resumen final al usuario con:
   - La versión nueva y la justificación del incremento.
   - Cualquier marcador TODO o elemento diferido que requiera seguimiento manual.
   - Un mensaje de commit sugerido (p. ej., `docs: enmendar la constitution a vX.Y.Z (nuevos principios + actualización de gobernanza)`).
   - Una sección `Próximas acciones` para toda intención diferida ajena a la gobernanza.

Requisitos de formato y estilo:

- Usá los encabezados Markdown exactamente como en la plantilla (no bajes ni subas niveles).
- Cortá las líneas largas de justificación para mantener la legibilidad (idealmente <100 caracteres), pero sin imponerlo con cortes forzados e incómodos.
- Dejá una sola línea en blanco entre secciones.
- Evitá espacios al final de las líneas.

Si el usuario aporta actualizaciones parciales (p. ej., la revisión de un solo principio), igualmente realizá la validación y la decisión de versión.

Si falta información crítica (p. ej., la fecha de ratificación realmente se desconoce), insertá `TODO(<NOMBRE_DEL_CAMPO>): explicación` e incluilo en el Informe de impacto de la sincronización dentro de los elementos diferidos.

Escribí solo `.specify/memory/constitution.md`; no crees ni modifiques los archivos fuente de las plantillas.

## Verificaciones posteriores a la ejecución

**Buscar hooks de extensión (después de actualizar la constitution)**:
Verificá si existe `.specify/extensions.yml` en la raíz del proyecto.
- Si existe, leelo y buscá las entradas bajo la clave `hooks.after_constitution`
- Si el YAML no se puede parsear o no es válido, no lo omitas en silencio: avisale al usuario que no se pudo leer `.specify/extensions.yml` (incluí el error del parser) y que no se verificó ningún hook, incluidos los obligatorios (`optional: false`) registrados ahí, y luego continuá normalmente
- Descartá los hooks cuyo campo `enabled` sea explícitamente `false`. Los hooks sin campo `enabled` se consideran habilitados por defecto.
- Para cada hook restante, **no** intentes interpretar ni evaluar las expresiones del campo `condition`:
  - Si el hook no tiene campo `condition`, o es nulo/vacío, tratá el hook como ejecutable
  - Si el hook define un `condition` no vacío, omití el hook y dejá la evaluación de la condición a la implementación de HookExecutor
- Al armar las invocaciones de comandos a partir de los nombres de comando de los hooks, reemplazá los puntos (`.`) por guiones (`-`). Por ejemplo, `speckit.git.commit` → `/speckit-git-commit`.
- Para cada hook ejecutable, emití lo siguiente según su indicador `optional`:
  - **Hook opcional** (`optional: true`):
    ```
    ## Hooks de extensión

    **Hook opcional**: {extension}
    Comando: `/{command}`
    Descripción: {description}

    Prompt: {prompt}
    Para ejecutarlo: `/{command}`
    ```
  - **Hook obligatorio** (`optional: false`):
    ```
    ## Hooks de extensión

    **Hook automático**: {extension}
    Ejecutando: `/{command}`
    EXECUTE_COMMAND: {command}
    ```
    Después de emitir el bloque anterior DEBES invocar realmente el hook y esperar a que termine antes de continuar. Ejecutalo de la misma forma en que ejecutarías el comando vos mismo en este agente/sesión (la invocación puede diferir del id literal `{command}` mostrado arriba; por ejemplo, un agente en modo skills lo ejecuta como `/skill:speckit-...` o `$speckit-...`). Emitir el bloque por sí solo no ejecuta el hook.
- Si no hay hooks registrados o no existe `.specify/extensions.yml`, omití este paso en silencio
