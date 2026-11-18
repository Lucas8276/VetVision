---
name: "speckit-taskstoissues"
description: "Convierte las tareas existentes en issues de GitHub accionables y ordenados por dependencias para la funcionalidad, a partir de los artefactos de diseño disponibles."
argument-hint: "Filtro o etiqueta opcional para los issues de GitHub"
compatibility: "Requiere la estructura de proyecto de spec-kit con el directorio .specify/"
metadata:
  author: "github-spec-kit"
  source: "templates/commands/taskstoissues.md"
user-invocable: true
disable-model-invocation: false
---


## Entrada del usuario

```text
$ARGUMENTS
```

**DEBES** considerar la entrada del usuario antes de continuar (si no está vacía).

## Verificaciones previas a la ejecución

**Buscar hooks de extensión (antes de la conversión de tareas a issues)**:
- Verificá si existe `.specify/extensions.yml` en la raíz del proyecto.
- Si existe, leelo y buscá las entradas bajo la clave `hooks.before_taskstoissues`
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

1. Ejecutá `.specify/scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks` desde la raíz del repositorio y parseá FEATURE_DIR y la lista AVAILABLE_DOCS. Todas las rutas deben ser absolutas. Para las comillas simples en los argumentos, como "I'm Groot", usá la sintaxis de escape: p. ej. 'I'\''m Groot' (o comillas dobles si es posible: "I'm Groot").
1. **SI EXISTE**: Cargá `.specify/memory/constitution.md` para conocer los principios del proyecto y las restricciones de gobernanza.
1. Del script ejecutado, extraé la ruta a **tasks**.
1. Obtené el remoto de Git ejecutando:

```bash
git config --get remote.origin.url
```

> [!CAUTION]
> SOLO CONTINUÁ CON LOS PASOS SIGUIENTES SI EL REMOTO ES UNA URL DE GITHUB

1. **Obtener los issues existentes para deduplicar**: Antes de crear nada, armá el conjunto de IDs de tarea que vas a procesar a partir de `tasks.md` (cada uno es una `T` seguida de **al menos** tres dígitos, p. ej. `T001`; `/speckit-converge` asigna los IDs nuevos con `T{M+1:03d}`, que es un piso y no un tope, así que cuando un archivo supera las 999 tareas los IDs tienen cuatro dígitos o más). Luego usá la herramienta `list_issues` del servidor MCP de GitHub para buscar los issues que ya cubren esos IDs. No pases un valor de `state`, ya que omitirlo hace que la herramienta devuelva tanto los issues abiertos como los cerrados. Pedí `perPage: 100` para reducir la cantidad de llamadas y, como la herramienta usa paginación por cursor, pedí las páginas con el parámetro `after` (usando el `endCursor` de la respuesta anterior). Para el título de cada issue, buscá coincidencias con el patrón de ID de tarea `\bT\d{3,}\b` (el `{3,}` acepta IDs de cuatro dígitos o más: con `\d{3}`, un título que contenga `T1000` no coincidiría en absoluto, porque el `\b` final no puede caer entre dos dígitos, y esa tarea quedaría silenciosamente sin deduplicar y sin crear; los límites de palabra igualmente impiden que un token como `ST001` coincida y obligan a consumir toda la secuencia de dígitos, de modo que `T100` nunca puede coincidir dentro de `T1000`; esto también reconoce títulos escritos como `T001 ...`, `T001: ...` o `[T001] ...`) y, cuando coincida con uno de tus IDs de tarea, marcá ese ID como que ya tiene un issue. Dejá de paginar apenas todos los IDs de tarea hayan coincidido, o cuando no queden más páginas, para no seguir trayendo todo el historial de issues del repositorio una vez que todos los IDs estén contabilizados. Esto acota la cantidad de llamadas en repositorios con historiales de issues grandes y aun así evita duplicados cuando el comando se vuelve a ejecutar después de regenerar `tasks.md` o cuando se vuelve a invocar el skill.
1. Para cada tarea de la lista, usá el servidor MCP de GitHub para crear un issue nuevo en el repositorio que corresponda al remoto de Git. Las líneas de tareas en `tasks.md` empiezan con una casilla de markdown, así que primero quitá el `- [ ]` inicial (y cualquier marcador `[P]` / `[US#]`) para recuperar el ID de la tarea y su descripción. Creá el issue con un único título canónico de la forma `T001: <descripción>`, con el ID escrito una sola vez seguido de la descripción de la tarea (por ejemplo, la línea `- [ ] T001 Crear la estructura del proyecto` se convierte en el título `T001: Crear la estructura del proyecto`).
   - **Omití** toda tarea cuyo ID ya esté presente en el conjunto de issues existentes del paso anterior, e informalo (por ejemplo, `T001 ya tiene un issue, se omite`).
   - Creá issues solo para las tareas que todavía no tengan un issue que coincida.

> [!CAUTION]
> BAJO NINGUNA CIRCUNSTANCIA CREES ISSUES EN REPOSITORIOS QUE NO COINCIDAN CON LA URL DEL REMOTO

## Verificaciones posteriores a la ejecución

**Buscar hooks de extensión (después de la conversión de tareas a issues)**:
Verificá si existe `.specify/extensions.yml` en la raíz del proyecto.
- Si existe, leelo y buscá las entradas bajo la clave `hooks.after_taskstoissues`
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
