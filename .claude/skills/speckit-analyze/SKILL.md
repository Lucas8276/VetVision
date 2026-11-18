---
name: "speckit-analyze"
description: "Realiza un análisis no destructivo de consistencia y calidad entre artefactos sobre spec.md, plan.md y tasks.md, después de generar las tareas."
argument-hint: "Áreas de enfoque opcionales para el análisis"
compatibility: "Requiere la estructura de proyecto de spec-kit con el directorio .specify/"
metadata:
  author: "github-spec-kit"
  source: "templates/commands/analyze.md"
user-invocable: true
disable-model-invocation: false
---


## Entrada del usuario

```text
$ARGUMENTS
```

**DEBES** considerar la entrada del usuario antes de continuar (si no está vacía).

## Verificaciones previas a la ejecución

**Buscar hooks de extensión (antes del análisis)**:
- Verificá si existe `.specify/extensions.yml` en la raíz del proyecto.
- Si existe, leelo y buscá las entradas bajo la clave `hooks.before_analyze`
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

Identificar inconsistencias, duplicaciones, ambigüedades y elementos subespecificados entre los tres artefactos centrales (`spec.md`, `plan.md`, `tasks.md`) antes de la implementación. Este comando DEBE ejecutarse únicamente después de que `/speckit-tasks` haya producido con éxito un `tasks.md` completo.

## Restricciones de operación

**ESTRICTAMENTE DE SOLO LECTURA**: **No** modifiques ningún archivo. Mostrá un informe de análisis estructurado. Ofrecé un plan de remediación opcional (el usuario debe aprobarlo de forma explícita antes de que se invoque manualmente cualquier comando de edición posterior).

**Autoridad de la constitution**: La constitution del proyecto (`.specify/memory/constitution.md`) es **innegociable** dentro del alcance de este análisis. Los conflictos con la constitution son automáticamente CRÍTICOS y exigen ajustar la spec, el plan o las tareas, no diluir, reinterpretar ni ignorar en silencio el principio. Si un principio en sí necesita cambiar, eso debe hacerse en una actualización de la constitution separada y explícita, fuera de `/speckit-analyze`.

## Pasos de ejecución

### 1. Inicializar el contexto del análisis

Ejecutá `.specify/scripts/powershell/check-prerequisites.ps1 -Json -RequireSpec -RequireTasks -IncludeTasks` una vez desde la raíz del repositorio y parseá el JSON para obtener FEATURE_DIR y AVAILABLE_DOCS. Derivá las rutas absolutas:

- SPEC = FEATURE_DIR/spec.md
- PLAN = FEATURE_DIR/plan.md
- TASKS = FEATURE_DIR/tasks.md

Abortá con un mensaje de error si falta algún archivo requerido (indicale al usuario que ejecute el comando prerrequisito que falta).
Para las comillas simples en los argumentos, como "I'm Groot", usá la sintaxis de escape: p. ej. 'I'\''m Groot' (o comillas dobles si es posible: "I'm Groot").

### 2. Cargar los artefactos (divulgación progresiva)

Cargá solo el contexto mínimo necesario de cada artefacto:

**De spec.md:**

- Resumen/Contexto
- Requisitos funcionales
- Criterios de éxito (resultados medibles, p. ej.: rendimiento, seguridad, disponibilidad, éxito del usuario, impacto en el negocio)
- Historias de usuario
- Casos límite (si los hay)

**De plan.md:**

- Elecciones de arquitectura/stack
- Referencias al modelo de datos
- Fases
- Restricciones técnicas

**De tasks.md:**

- IDs de tarea
- Descripciones
- Agrupación por fase
- Marcadores de paralelismo [P]
- Rutas de archivo referenciadas

**De la constitution:**

- Cargá `.specify/memory/constitution.md` para validar los principios

### 3. Construir modelos semánticos

Creá representaciones internas (no incluyas los artefactos crudos en la salida):

- **Inventario de requisitos**: Por cada requisito funcional (FR-###) y criterio de éxito (SC-###), registrá una clave estable. Usá el identificador explícito FR-/SC- como clave principal cuando exista y, opcionalmente, derivá también un slug en frase imperativa para facilitar la lectura (p. ej., "El usuario puede subir un archivo" → `user-can-upload-file`). Incluí solo los criterios de éxito que requieren trabajo construible (p. ej., infraestructura de pruebas de carga, herramientas de auditoría de seguridad) y excluí las métricas de resultado posteriores al lanzamiento y los KPI de negocio (p. ej., "Reducir los tickets de soporte en un 50 %").
- **Inventario de historias/acciones de usuario**: Acciones discretas del usuario con sus criterios de aceptación
- **Mapa de cobertura de tareas**: Asigná cada tarea a uno o más requisitos o historias (inferencia por palabras clave / patrones de referencia explícita como IDs o frases clave)
- **Conjunto de reglas de la constitution**: Extraé los nombres de los principios y las declaraciones normativas DEBE/DEBERÍA

### 4. Pasadas de detección (análisis eficiente en tokens)

Concentrate en hallazgos de alta señal. Limitá el total a 50 hallazgos; agregá el resto en un resumen de excedente.

#### A. Detección de duplicación

- Identificá requisitos casi duplicados
- Marcá la redacción de menor calidad para consolidarla

#### B. Detección de ambigüedad

- Marcá adjetivos vagos (rápido, escalable, seguro, intuitivo, robusto) que carezcan de criterios medibles
- Marcá marcadores de posición sin resolver (TODO, TKTK, ???, `<placeholder>`, etc.)

#### C. Subespecificación

- Requisitos con verbos pero sin objeto o sin resultado medible
- Historias de usuario sin alineación con criterios de aceptación
- Tareas que referencian archivos o componentes no definidos en la spec/plan

#### D. Alineación con la constitution

- Cualquier requisito o elemento del plan que entre en conflicto con un principio DEBE
- Secciones obligatorias o puertas de calidad de la constitution que faltan

#### E. Brechas de cobertura

- Requisitos con cero tareas asociadas
- Tareas sin requisito/historia asignado
- Criterios de éxito que requieren trabajo construible (rendimiento, seguridad, disponibilidad) y no están reflejados en las tareas

#### F. Inconsistencia

- Deriva terminológica (el mismo concepto con nombres distintos en distintos archivos)
- Entidades de datos referenciadas en el plan pero ausentes en la spec (o viceversa)
- Contradicciones en el orden de las tareas (p. ej., tareas de integración antes que las de preparación de fundamentos, sin nota de dependencia)
- Requisitos en conflicto (p. ej., uno exige Next.js y otro especifica Vue)

### 5. Asignación de severidad

Usá esta heurística para priorizar los hallazgos:

- **CRÍTICO**: Viola un DEBE de la constitution, falta un artefacto central de la spec, o hay un requisito con cero cobertura que bloquea la funcionalidad base
- **ALTO**: Requisito duplicado o en conflicto, atributo de seguridad/rendimiento ambiguo, criterio de aceptación no verificable
- **MEDIO**: Deriva terminológica, falta cobertura de tareas no funcionales, caso límite subespecificado
- **BAJO**: Mejoras de estilo/redacción, redundancia menor que no afecta el orden de ejecución

### 6. Producir un informe de análisis compacto

Mostrá un informe en Markdown (sin escribir archivos) con la siguiente estructura:

## Informe de análisis de la especificación

| ID | Categoría | Severidad | Ubicación(es) | Resumen | Recomendación |
|----|-----------|-----------|---------------|---------|---------------|
| A1 | Duplicación | ALTO | spec.md:L120-134 | Dos requisitos similares ... | Unificar la redacción; conservar la versión más clara |

(Agregá una fila por hallazgo; generá IDs estables con el prefijo de la inicial de la categoría.)

**Tabla de resumen de cobertura:**

| Clave del requisito | ¿Tiene tarea? | IDs de tarea | Notas |
|---------------------|---------------|--------------|-------|

**Problemas de alineación con la constitution:** (si los hay)

**Tareas sin mapear:** (si las hay)

**Métricas:**

- Total de requisitos
- Total de tareas
- % de cobertura (requisitos con >=1 tarea)
- Cantidad de ambigüedades
- Cantidad de duplicaciones
- Cantidad de problemas críticos

### 7. Indicar las próximas acciones

Al final del informe, mostrá un bloque conciso de Próximas acciones:

- Si existen problemas CRÍTICOS: recomendá resolverlos antes de `/speckit-implement`
- Si solo hay BAJOS/MEDIOS: el usuario puede continuar, pero dá sugerencias de mejora
- Dá sugerencias explícitas de comandos: p. ej., "Ejecutá /speckit-specify con un refinamiento", "Ejecutá /speckit-plan para ajustar la arquitectura", "Editá manualmente tasks.md para agregar cobertura de 'performance-metrics'"

### 8. Ofrecer remediación

Preguntale al usuario: "¿Querés que sugiera ediciones concretas de remediación para los N problemas principales?" (NO las apliques automáticamente.)

### 9. Buscar hooks de extensión

Después de informar, verificá si existe `.specify/extensions.yml` en la raíz del proyecto.
- Si existe, leelo y buscá las entradas bajo la clave `hooks.after_analyze`
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


## Principios de operación

### Eficiencia de contexto

- **Mínimos tokens de alta señal**: Concentrate en hallazgos accionables, no en documentación exhaustiva
- **Divulgación progresiva**: Cargá los artefactos de forma incremental; no vuelques todo el contenido en el análisis
- **Salida eficiente en tokens**: Limitá la tabla de hallazgos a 50 filas; resumí el excedente
- **Resultados deterministas**: Volver a ejecutar sin cambios debe producir IDs y conteos consistentes

### Pautas de análisis

- **NUNCA modifiques archivos** (es un análisis de solo lectura)
- **NUNCA inventes secciones faltantes** (si faltan, informalo con exactitud)
- **Priorizá las violaciones de la constitution** (siempre son CRÍTICAS)
- **Usá ejemplos en lugar de reglas exhaustivas** (citá casos concretos, no patrones genéricos)
- **Informá con naturalidad cuando no haya problemas** (emití un informe de éxito con estadísticas de cobertura)

## Contexto

$ARGUMENTS
