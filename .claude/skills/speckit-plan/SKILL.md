---
name: "speckit-plan"
description: "Ejecuta el flujo de planificación de la implementación usando la plantilla de plan para generar los artefactos de diseño."
argument-hint: "Orientación opcional para la fase de planificación"
compatibility: "Requiere la estructura de proyecto de spec-kit con el directorio .specify/"
metadata:
  author: "github-spec-kit"
  source: "templates/commands/plan.md"
user-invocable: true
disable-model-invocation: false
---


## Entrada del usuario

```text
$ARGUMENTS
```

**DEBES** considerar la entrada del usuario antes de continuar (si no está vacía).

## Verificaciones previas a la ejecución

**Buscar hooks de extensión (antes de planificar)**:
- Verificá si existe `.specify/extensions.yml` en la raíz del proyecto.
- Si existe, leelo y buscá las entradas bajo la clave `hooks.before_plan`
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

1. **Preparación**: Ejecutá `.specify/scripts/powershell/setup-plan.ps1 -Json` desde la raíz del repositorio y parseá el JSON para obtener FEATURE_SPEC, IMPL_PLAN, FEATURE_DIR y BRANCH. Para las comillas simples en los argumentos, como "I'm Groot", usá la sintaxis de escape: p. ej. 'I'\''m Groot' (o comillas dobles si es posible: "I'm Groot").

2. **Cargar el contexto**: Leé FEATURE_SPEC y `.specify/memory/constitution.md`. Cargá la plantilla IMPL_PLAN (ya copiada).

3. **Ejecutar el flujo del plan**: Seguí la estructura de la plantilla IMPL_PLAN para:
   - Completar el Contexto técnico (marcá las incógnitas como "NEEDS CLARIFICATION")
   - Completar la sección de Verificación contra la constitution a partir de la constitution
   - Evaluar las puertas (ERROR si hay violaciones sin justificar)
   - Fase 0: Generar research.md (resolver todos los NEEDS CLARIFICATION)
   - Fase 1: Generar data-model.md, contracts/ y quickstart.md
   - Volver a evaluar la Verificación contra la constitution después del diseño

## Hooks posteriores a la ejecución (obligatorios)

**DEBES completar esta sección antes de informar la finalización al usuario.**

Verificá si existe `.specify/extensions.yml` en la raíz del proyecto.
- Si no existe, o no hay hooks registrados bajo `hooks.after_plan`, pasá directo al Informe de finalización.
- Si existe, leelo y buscá las entradas bajo la clave `hooks.after_plan`.
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

El comando termina después del diseño de la Fase 1. Informá la rama, la ruta de IMPL_PLAN y los artefactos generados.

## Fases

### Fase 0: Esquema e investigación

1. **Extraer las incógnitas del Contexto técnico** de arriba:
   - Por cada NEEDS CLARIFICATION → una tarea de investigación
   - Por cada dependencia → una tarea de mejores prácticas
   - Por cada integración → una tarea de patrones

2. **Generar y despachar agentes de investigación**:

   ```text
   Por cada incógnita del Contexto técnico:
     Tarea: "Investigar {incógnita} para {contexto de la funcionalidad}"
   Por cada elección de tecnología:
     Tarea: "Buscar mejores prácticas de {tecnología} en {dominio}"
   ```

3. **Consolidar los hallazgos** en `research.md` con este formato:
   - Decisión: [qué se eligió]
   - Justificación: [por qué se eligió]
   - Alternativas consideradas: [qué más se evaluó]

**Salida**: research.md con todos los NEEDS CLARIFICATION resueltos

### Fase 1: Diseño y contratos

**Prerrequisitos:** `research.md` completo

1. **Extraer las entidades de la spec de la funcionalidad** → `data-model.md`:
   - Nombre de la entidad, campos, relaciones
   - Reglas de validación derivadas de los requisitos
   - Transiciones de estado, si corresponde

2. **Definir los contratos de interfaz** (si el proyecto tiene interfaces externas) → `/contracts/`:
   - Identificar qué interfaces expone el proyecto a los usuarios o a otros sistemas
   - Documentar el formato de contrato apropiado para el tipo de proyecto
   - Ejemplos: APIs públicas para bibliotecas, esquemas de comandos para herramientas de CLI, endpoints para servicios web, gramáticas para parsers, contratos de UI para aplicaciones
   - Omitir si el proyecto es puramente interno (scripts de build, herramientas de un solo uso, etc.)

3. **Crear la guía de validación rápida** → `quickstart.md`:
   - Documentar escenarios de validación ejecutables que prueben que la funcionalidad anda de punta a punta
   - Incluir prerrequisitos, comandos de preparación, comandos de prueba/ejecución y resultados esperados
   - Usar enlaces o referencias a los contratos y a los detalles del modelo de datos en lugar de duplicarlos
   - No incluir código de implementación completo, cuerpos de modelos/servicios/controladores, migraciones ni suites de pruebas completas
   - Mantener este artefacto como una guía de validación/ejecución; los detalles de implementación van en `tasks.md` y en la fase de implementación

**Salida**: data-model.md, /contracts/*, quickstart.md

## Reglas clave

- Usá rutas absolutas para las operaciones del sistema de archivos; usá rutas relativas al proyecto para las referencias en la documentación
- ERROR ante fallas en las puertas o aclaraciones sin resolver

## Terminado cuando

- [ ] Se ejecutó el flujo del plan y se generaron los artefactos de diseño
- [ ] Los hooks de extensión se despacharon u omitieron según las reglas de Hooks posteriores a la ejecución (obligatorios) de arriba
- [ ] Se informó la finalización al usuario con la rama, la ruta del plan y los artefactos generados
