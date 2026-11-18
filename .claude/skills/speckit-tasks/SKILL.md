---
name: "speckit-tasks"
description: "Genera un tasks.md accionable y ordenado por dependencias para la funcionalidad, a partir de los artefactos de diseño disponibles."
argument-hint: "Restricciones opcionales para la generación de tareas"
compatibility: "Requiere la estructura de proyecto de spec-kit con el directorio .specify/"
metadata:
  author: "github-spec-kit"
  source: "templates/commands/tasks.md"
user-invocable: true
disable-model-invocation: false
---


## Entrada del usuario

```text
$ARGUMENTS
```

**DEBES** considerar la entrada del usuario antes de continuar (si no está vacía).

## Verificaciones previas a la ejecución

**Buscar hooks de extensión (antes de generar las tareas)**:
- Verificá si existe `.specify/extensions.yml` en la raíz del proyecto.
- Si existe, leelo y buscá las entradas bajo la clave `hooks.before_tasks`
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

1. **Preparación**: Ejecutá `.specify/scripts/powershell/setup-tasks.ps1 -Json` desde la raíz del repositorio y parseá FEATURE_DIR, TASKS_TEMPLATE_CONTENT, TASKS_TEMPLATE y la lista AVAILABLE_DOCS. `FEATURE_DIR` y `TASKS_TEMPLATE` deben ser rutas absolutas cuando se provean. `AVAILABLE_DOCS` es una lista de nombres de documentos/rutas relativas disponibles bajo `FEATURE_DIR` (por ejemplo `research.md` o `contracts/`). Para las comillas simples en los argumentos, como "I'm Groot", usá la sintaxis de escape: p. ej. 'I'\''m Groot' (o comillas dobles si es posible: "I'm Groot").

2. **Cargar los documentos de diseño**: Leé desde FEATURE_DIR:
   - **Obligatorios**: plan.md (stack técnico, bibliotecas, estructura), spec.md (historias de usuario con prioridades)
   - **Opcionales**: data-model.md (entidades), contracts/ (contratos de interfaz), research.md (decisiones), quickstart.md (escenarios de prueba)
   - **SI EXISTE**: Cargá `.specify/memory/constitution.md` para conocer los principios del proyecto y las restricciones de gobernanza
   - Nota: No todos los proyectos tienen todos los documentos. Generá las tareas en base a lo que esté disponible.

3. **Ejecutar el flujo de generación de tareas**:
   - Cargá plan.md y extraé el stack técnico, las bibliotecas y la estructura del proyecto
   - Cargá spec.md y extraé las historias de usuario con sus prioridades (P1, P2, P3, etc.)
   - Si existe data-model.md: extraé las entidades y asignalas a las historias de usuario
   - Si existe contracts/: asigná los contratos de interfaz a las historias de usuario
   - Si existe research.md: extraé las decisiones para las tareas de preparación
   - Generá las tareas organizadas por historia de usuario (ver Reglas de generación de tareas más abajo)
   - Generá un grafo de dependencias que muestre el orden de finalización de las historias de usuario
   - Creá ejemplos de ejecución en paralelo por historia de usuario
   - Validá que las tareas estén completas (cada historia de usuario tiene todas las tareas necesarias y se puede probar de forma independiente)

4. **Generar tasks.md**: Usá TASKS_TEMPLATE_CONTENT (de la salida JSON de arriba) como estructura. Por compatibilidad con scripts de preparación más viejos que omiten TASKS_TEMPLATE_CONTENT, leé TASKS_TEMPLATE en su lugar. Completalo con:
   - El nombre correcto de la funcionalidad, tomado de plan.md
   - Fase 1: tareas de preparación (inicialización del proyecto)
   - Fase 2: tareas de fundamentos (prerrequisitos bloqueantes para todas las historias de usuario)
   - Fase 3+: una fase por historia de usuario (en el orden de prioridad de spec.md)
   - Cada fase incluye: objetivo de la historia, criterios de prueba independiente, pruebas (si se pidieron) y tareas de implementación
   - Fase final: pulido y aspectos transversales
   - Todas las tareas deben seguir el formato estricto de checklist (ver Reglas de generación de tareas más abajo)
   - Rutas de archivo claras para cada tarea
   - Sección de dependencias que muestre el orden de finalización de las historias
   - Ejemplos de ejecución en paralelo por historia
   - Sección de estrategia de implementación (primero el MVP, entrega incremental)

## Hooks posteriores a la ejecución (obligatorios)

**DEBES completar esta sección antes de informar la finalización al usuario.**

Verificá si existe `.specify/extensions.yml` en la raíz del proyecto.
- Si no existe, o no hay hooks registrados bajo `hooks.after_tasks`, pasá directo al Informe de finalización.
- Si existe, leelo y buscá las entradas bajo la clave `hooks.after_tasks`.
- Si el YAML no se puede parsear o no es válido, no lo omitas en silencio: avisale al usuario que no se pudo leer `.specify/extensions.yml` (incluí el error del parser) y que no se verificó ningún hook, incluidos los obligatorios (`optional: false`) registrados ahí, y luego pasá al Informe de finalización.
- Descartá los hooks cuyo campo `enabled` sea explícitamente `false`. Los hooks sin campo `enabled` se consideran habilitados por defecto.
- Para cada hook restante, **no** intentes interpretar ni evaluar las expresiones del campo `condition`:
  - Si el hook no tiene campo `condition`, o es nulo/vacío, tratá el hook como ejecutable
  - Si el hook define un `condition` no vacío, omití el hook y dejá la evaluación de la condición a la implementación de HookExecutor
- Al armar las invocaciones de comandos a partir de los nombres de comando de los hooks, reemplazá los puntos (`.`) por guiones (`-`). Por ejemplo, `speckit.git.commit` → `/speckit-git-commit`.
- Para cada hook ejecutable, emití lo siguiente según su indicador `optional`:
  - **Hook obligatorio** (`optional: false`): **DEBES emitir `EXECUTE_COMMAND:` para cada hook obligatorio**:
    ```
    ## Hooks de extensión

    **Hook automático**: {extension}
    Ejecutando: `/{command}`
    EXECUTE_COMMAND: {command}
    ```
    Después de emitir el bloque anterior DEBES invocar realmente el hook y esperar a que termine antes de continuar. Ejecutalo de la misma forma en que ejecutarías el comando vos mismo en este agente/sesión (la invocación puede diferir del id literal `{command}` mostrado arriba; por ejemplo, un agente en modo skills lo ejecuta como `/skill:speckit-...` o `$speckit-...`). Emitir el bloque por sí solo no ejecuta el hook.
  - **Hook opcional** (`optional: true`):
    ```
    ## Hooks de extensión

    **Hook opcional**: {extension}
    Comando: `/{command}`
    Descripción: {description}

    Prompt: {prompt}
    Para ejecutarlo: `/{command}`
    ```


## Informe de finalización

Mostrá la ruta del tasks.md generado y un resumen:
- Cantidad total de tareas
- Cantidad de tareas por historia de usuario
- Oportunidades de paralelismo identificadas
- Criterios de prueba independiente de cada historia
- Alcance de MVP sugerido (normalmente solo la historia de usuario 1)
- Validación de formato: Confirmá que TODAS las tareas siguen el formato de checklist (casilla, ID, etiquetas, rutas de archivo)

Contexto para la generación de tareas: $ARGUMENTS

El tasks.md debe poder ejecutarse de inmediato: cada tarea debe ser lo bastante específica como para que un LLM la complete sin contexto adicional.

## Reglas de generación de tareas

**CRÍTICO**: Las tareas DEBEN organizarse por historia de usuario para permitir la implementación y las pruebas independientes.

**Las pruebas son OPCIONALES**: Generá tareas de prueba solo si la especificación de la funcionalidad las pide de forma explícita o si el usuario solicita un enfoque TDD.

### Formato de checklist (OBLIGATORIO)

Toda tarea DEBE seguir estrictamente este formato:

```text
- [ ] [IDTarea] [P?] [Historia?] Descripción con la ruta del archivo
```

**Componentes del formato**:

1. **Casilla**: SIEMPRE empezar con `- [ ]` (casilla de markdown)
2. **ID de tarea**: Número secuencial (T001, T002, T003...) en orden de ejecución
3. **Marcador [P]**: Incluirlo SOLO si la tarea es paralelizable (archivos distintos, sin dependencias de tareas incompletas)
4. **Etiqueta [Historia]**: OBLIGATORIA solo para las tareas de las fases de historias de usuario
   - Formato: [US1], [US2], [US3], etc. (corresponde a las historias de usuario de spec.md)
   - Fase de preparación: SIN etiqueta de historia
   - Fase de fundamentos: SIN etiqueta de historia
   - Fases de historias de usuario: DEBEN tener etiqueta de historia
   - Fase de pulido: SIN etiqueta de historia
5. **Descripción**: Una acción clara con la ruta exacta del archivo

**Ejemplos**:

- ✅ CORRECTO: `- [ ] T001 Crear la estructura del proyecto según el plan de implementación`
- ✅ CORRECTO: `- [ ] T005 [P] Implementar el middleware de autenticación en src/middleware/auth.py`
- ✅ CORRECTO: `- [ ] T012 [P] [US1] Crear el modelo User en src/models/user.py`
- ✅ CORRECTO: `- [ ] T014 [US1] Implementar UserService en src/services/user_service.py`
- ❌ INCORRECTO: `- [ ] Crear el modelo User` (falta el ID y la etiqueta de historia)
- ❌ INCORRECTO: `T001 [US1] Crear el modelo` (falta la casilla)
- ❌ INCORRECTO: `- [ ] [US1] Crear el modelo User` (falta el ID de tarea)
- ❌ INCORRECTO: `- [ ] T001 [US1] Crear el modelo` (falta la ruta del archivo)

### Organización de las tareas

1. **A partir de las historias de usuario (spec.md)**: ORGANIZACIÓN PRINCIPAL:
   - Cada historia de usuario (P1, P2, P3...) tiene su propia fase
   - Asigná todos los componentes relacionados a su historia:
     - Los modelos que necesita esa historia
     - Los servicios que necesita esa historia
     - Las interfaces/UI que necesita esa historia
     - Si se pidieron pruebas: las pruebas específicas de esa historia
   - Marcá las dependencias entre historias (la mayoría de las historias deberían ser independientes)

2. **A partir de los contratos**:
   - Asigná cada contrato de interfaz → a la historia de usuario a la que sirve
   - Si se pidieron pruebas: cada contrato de interfaz → una tarea de prueba de contrato [P] antes de la implementación, en la fase de esa historia

3. **A partir del modelo de datos**:
   - Asigná cada entidad a la(s) historia(s) de usuario que la necesitan
   - Si una entidad sirve a varias historias: ponela en la primera historia o en la fase de preparación
   - Relaciones → tareas de la capa de servicios en la fase de la historia que corresponda
   - Por cada campo con restricciones en data-model.md (longitud máxima, nulable/obligatorio, valores de enum, reglas de validación), citá la restricción textualmente en la descripción de la tarea para que no quede a discreción del momento de la implementación

4. **A partir de la preparación/infraestructura**:
   - Infraestructura compartida → fase de preparación (Fase 1)
   - Tareas de fundamentos/bloqueantes → fase de fundamentos (Fase 2)
   - Preparación específica de una historia → dentro de la fase de esa historia

### Estructura de las fases

- **Fase 1**: Preparación (inicialización del proyecto)
- **Fase 2**: Fundamentos (prerrequisitos bloqueantes: DEBEN completarse antes de las historias de usuario)
- **Fase 3+**: Historias de usuario en orden de prioridad (P1, P2, P3...)
  - Dentro de cada historia: Pruebas (si se pidieron) → Modelos → Servicios → Endpoints → Integración
  - Cada fase debe ser un incremento completo y probable de forma independiente
- **Fase final**: Pulido y aspectos transversales

## Terminado cuando

- [ ] tasks.md generado con todas las fases, IDs de tarea y rutas de archivo
- [ ] Los hooks de extensión se despacharon u omitieron según las reglas de Hooks posteriores a la ejecución (obligatorios) de arriba
- [ ] Se informó la finalización al usuario con la cantidad de tareas, el desglose por historia y el alcance de MVP
