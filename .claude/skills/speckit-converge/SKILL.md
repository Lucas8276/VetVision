---
name: "speckit-converge"
description: "Evalúa el código actual contra la spec, el plan y las tareas de la funcionalidad, y agrega el trabajo restante sin construir como tareas nuevas en tasks.md para que implement pueda completarlo."
compatibility: "Requiere la estructura de proyecto de spec-kit con el directorio .specify/"
metadata:
  author: "github-spec-kit"
  source: "templates/commands/converge.md"
user-invocable: true
disable-model-invocation: false
---


## Entrada del usuario

```text
$ARGUMENTS
```

**DEBES** considerar la entrada del usuario antes de continuar (si no está vacía).

## Verificaciones previas a la ejecución

**Buscar hooks de extensión (antes de la convergencia)**:
- Verificá si existe `.specify/extensions.yml` en la raíz del proyecto.
- Si existe, leelo y buscá las entradas bajo la clave `hooks.before_converge`
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

    Esperá el resultado del comando del hook antes de continuar con el Objetivo.
    ```
    Después de emitir el bloque anterior DEBES invocar realmente el hook y esperar a que termine antes de continuar. Ejecutalo de la misma forma en que ejecutarías el comando vos mismo en este agente/sesión (la invocación puede diferir del id literal `{command}` mostrado arriba; por ejemplo, un agente en modo skills lo ejecuta como `/skill:speckit-...` o `$speckit-...`). Emitir el bloque por sí solo no ejecuta el hook.
- Si no hay hooks registrados o no existe `.specify/extensions.yml`, omití este paso en silencio


## Objetivo

Cerrar la brecha entre lo que piden la especificación, el plan y las tareas de una funcionalidad y lo que el
código implementa hoy. Leé `spec.md`, `plan.md` y `tasks.md` como la **única fuente de
intención** (con la constitution como restricciones rectoras), evaluá el estado actual del código,
determiná qué requisitos, criterios de aceptación, decisiones del plan y tareas existentes están
sin cumplir, incompletos o satisfechos solo en parte, y **agregá cada pieza de trabajo restante como una tarea nueva y trazable**
al final de `tasks.md`, para que `/speckit-implement` pueda completarla. Este comando DEBE ejecutarse únicamente
después de que `/speckit-implement` se haya ejecutado sobre el `tasks.md` actual, y después de que `/speckit-tasks` haya producido un `tasks.md` completo.

Esto **no** es una herramienta de diff y **no** registra cambios. Evalúa el estado presente
del código en relación con los artefactos de la funcionalidad: sin git, sin comparación de ramas, sin historial.

## Restricciones de operación

**SOLO AGREGAR, NUNCA REESCRIBIR**: La **única** escritura del comando es agregar una nueva
sección `## Fase N: Convergencia` a `tasks.md`. NO DEBE:

- modificar `spec.md` ni `plan.md` de ninguna manera;
- reescribir, renumerar, reordenar ni eliminar ninguna tarea existente (incluidas las tareas de una
  fase de Convergencia anterior);
- modificar, crear ni eliminar código de la aplicación: completar las tareas agregadas es
  trabajo de `/speckit-implement`.

Cuando el código ya satisface todo, el comando DEBE dejar `tasks.md`
**idéntico byte por byte** (sin encabezado de Convergencia vacío) e informar un resultado limpio.

**Autoridad de la constitution**: La constitution del proyecto (`.specify/memory/constitution.md`) es
**innegociable**. El código que viola un principio DEBE es el hallazgo de mayor severidad y
produce la correspondiente tarea de remediación. Si la constitution es una plantilla sin completar,
omití las verificaciones de la constitution con naturalidad en lugar de fallar.

## Pasos de ejecución

### 1. Inicializar el contexto de convergencia

Ejecutá `.specify/scripts/powershell/check-prerequisites.ps1 -Json -RequireSpec -RequireTasks -IncludeTasks` una vez desde la raíz del repositorio y parseá el JSON para obtener FEATURE_DIR y AVAILABLE_DOCS. Derivá las rutas absolutas:

- SPEC = FEATURE_DIR/spec.md
- PLAN = FEATURE_DIR/plan.md
- TASKS = FEATURE_DIR/tasks.md
- CONSTITUTION = `.specify/memory/constitution.md` (si existe)
Si falta `spec.md`, `plan.md` o `tasks.md`, DETENETE con un mensaje claro y accionable que nombre el
comando prerrequisito a ejecutar (`/speckit-specify` si falta la spec, `/speckit-plan` si falta el plan,
`/speckit-tasks` si faltan las tareas). No produzcas una salida parcial.
Para las comillas simples en los argumentos, como "I'm Groot", usá la sintaxis de escape: p. ej. 'I'\''m Groot' (o comillas dobles si es posible: "I'm Groot").

### 2. Cargar los artefactos (divulgación progresiva)

Cargá solo el contexto mínimo necesario de cada artefacto:

**De spec.md:**

- Requisitos funcionales (FR-###)
- Criterios de éxito (SC-###): incluí solo los que requieren trabajo construible; excluí
  las métricas de resultado posteriores al lanzamiento y los KPI de negocio
- Historias de usuario y sus escenarios de aceptación
- Casos límite (si los hay)

**De plan.md:**

- Elecciones de arquitectura/stack y decisiones técnicas
- Referencias al modelo de datos
- Fases y puntos de contacto nombrados (archivos/componentes que el plan dice que se crearán o editarán)
- Restricciones técnicas

**De tasks.md:**

- IDs de tarea (para calcular el próximo ID y el próximo número de fase)
- Descripciones, agrupación por fase y rutas de archivo referenciadas

**De la constitution (si no es una plantilla sin completar):**

- Nombres de los principios y declaraciones normativas DEBE/DEBERÍA

### 3. Construir el inventario de intención

Creá un modelo interno (no repitas los artefactos crudos):

- **Inventario de requisitos**: una clave estable por cada FR-### / SC-### / escenario de aceptación de
  historia de usuario (p. ej. `US1/AC2`), más las decisiones del plan y los principios de la constitution que
  imponen obligaciones construibles.
- **Mapa del alcance del código**: a partir de las rutas de archivo nombradas en `plan.md` y `tasks.md`, más una búsqueda
  por palabras clave de los conceptos que describe cada requisito, derivá el conjunto de archivos fuente y
  componentes dentro del alcance de la evaluación. Acotá la evaluación a ellos: **no** infieras
  un alcance mayor al que definen los artefactos.

### 4. Evaluar el código y clasificar los hallazgos

Por cada elemento del inventario de intención, inspeccioná el código actual dentro del alcance y producí un
`Hallazgo` solo donde haya una brecha. Clasificá cada hallazgo por **tipo de brecha**:

- **`missing`** (falta): el trabajo requerido está completamente ausente del código.
- **`partial`** (parcial): el trabajo existe pero todavía no satisface por completo el requisito /
  criterio de aceptación / decisión del plan.
- **`contradicts`** (contradice): el código hace algo que entra en conflicto con la intención declarada o con un
  principio DEBE de la constitution.
- **`unrequested`** (no pedido): el código contiene trabajo que no piden la spec, el plan ni las tareas
  (se muestra para tomar conocimiento: converge **no** borra código, solo agrega una tarea para
  revisarlo/justificarlo o eliminarlo).

Cada `Hallazgo` registra: un id estable, el `source-ref` al que se remonta, el `gap-type`, una
severidad y una descripción breve legible con la evidencia (el archivo/área observado).

**Casos límite:**

- **Poco o ningún código todavía**: tratá todo el alcance especificado como trabajo restante `missing`
  en lugar de fallar.
- **No queda nada**: producí cero hallazgos y seguí la rama de convergencia lograda del Paso 7.

### 5. Asignar severidad

- **CRÍTICO**: viola un principio DEBE de la constitution, o una brecha `missing`/`contradicts`
  que bloquea la funcionalidad base de una historia de usuario P1.
- **ALTO**: una brecha `missing` o `partial` en un requisito funcional central o un criterio de
  aceptación.
- **MEDIO**: una brecha `partial` en un requisito secundario, o una adición `unrequested` con
  justificación poco clara.
- **BAJO**: brechas parciales menores, pulido, o adiciones `unrequested` de bajo riesgo.

### 6. Presentar el resumen de hallazgos en la sesión

Antes de agregar nada, mostrá un resumen compacto graduado por severidad (todavía sin escribir archivos):

## Hallazgos de convergencia

| ID | Tipo de brecha | Severidad | Origen | Evidencia | Trabajo restante |
|----|----------------|-----------|--------|-----------|------------------|
| F1 | missing        | ALTO      | FR-008 | Ejemplo: no se detecta protección de solo-agregar en path/to/module.py al escribir tasks.md | Agregar el cumplimiento de solo-agregar |

**Métricas del resumen:**

- Requisitos / criterios de aceptación verificados
- Decisiones del plan verificadas
- Principios de la constitution verificados (o "omitido: plantilla")
- Hallazgos por tipo de brecha (missing / partial / contradicts / unrequested)
- Hallazgos por severidad

### 7. Agregar las tareas de convergencia (o informar que ya convergió)

**Si hay uno o más hallazgos accionables** (resultado `tasks_appended`):

Agregá al **final** de `tasks.md`, según el contrato de agregado:

1. Escaneá todos los IDs de tarea existentes; sea `M` el máximo. Determiná el próximo número de fase `N`
   (la fase más alta existente + 1).
2. Escribí un único encabezado de sección nuevo `## Fase N: Convergencia`.
3. Emití un ítem de checklist por hallazgo accionable, ordenados con los CRÍTICOS/ALTOS primero, asignando
   IDs con ceros a la izquierda `T{M+1:03d}, T{M+2:03d}, …`:

   ```markdown
   - [ ] T042 <descripción imperativa> según <source-ref> (<gap-type>)
   ```

   `<source-ref>` remonta la tarea a su origen: p. ej. `FR-003`, `SC-002`,
   `US1/AC2`, `plan: decisión de almacenamiento`, `Constitution II`.

   `<gap-type>` es uno de `missing`, `partial`, `contradicts`, `unrequested`.

   Las tareas por violación de la constitution DEBEN emitirse primero y describirse como
   `CRÍTICO`.
4. Nunca reutilices ni renumeres IDs existentes. Si ya existe una fase de Convergencia previa, agregá una nueva,
   con numeración propia, debajo: no toques la anterior.

**Si no hay hallazgos accionables** (resultado `converged`):

- **No** modifiques `tasks.md` en absoluto: ni siquiera un encabezado de fase vacío.
- Informá: **"✅ Convergió: la implementación satisface la spec, el plan y las tareas."**
- Incluí los conteos resumidos de lo que se verificó.

### 8. Indicar las próximas acciones (traspaso)

- En `tasks_appended`: indicá cuántas tareas se agregaron en qué fase y recomendá
  ejecutar `/speckit-implement` para completarlas; aclará que una nueva ejecución de converge
  encontrará menos elementos pendientes, o ninguno.
- En `converged`: recomendá pasar a la revisión / abrir un PR. No hace falta otra pasada de implement
  para el alcance especificado de esta funcionalidad.

### 9. Buscar hooks de extensión

Después de producir el resultado, verificá si existe `.specify/extensions.yml` en la raíz del proyecto.

Informá el resultado de la convergencia (`converged` o `tasks_appended`) en la sesión antes de listar
cualquier hook, para que los usuarios puedan decidir si ejecutan comandos opcionales de seguimiento.

- Si existe, leelo y buscá las entradas bajo la clave `hooks.after_converge`
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

