---
name: "speckit-specify"
description: "Crea o actualiza la especificación de la funcionalidad a partir de una descripción en lenguaje natural."
argument-hint: "Describí la funcionalidad que querés especificar"
compatibility: "Requiere la estructura de proyecto de spec-kit con el directorio .specify/"
metadata:
  author: "github-spec-kit"
  source: "templates/commands/specify.md"
user-invocable: true
disable-model-invocation: false
---


## Entrada del usuario

```text
$ARGUMENTS
```

**DEBES** considerar la entrada del usuario antes de continuar (si no está vacía).

## Verificaciones previas a la ejecución

**Buscar hooks de extensión (antes de la especificación)**:
- Verificá si existe `.specify/extensions.yml` en la raíz del proyecto.
- Si existe, leelo y buscá las entradas bajo la clave `hooks.before_specify`
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

El texto que el usuario escribió después de `/speckit-specify` en el mensaje que lo disparó **es** la descripción de la funcionalidad. Asumí que siempre lo tenés disponible en esta conversación, aunque `$ARGUMENTS` aparezca literalmente más abajo. No le pidas al usuario que lo repita, salvo que haya enviado el comando vacío.

Dada esa descripción de la funcionalidad, hacé lo siguiente:

1. **Generá un nombre corto y conciso** (2-4 palabras) para la funcionalidad:
   - Analizá la descripción de la funcionalidad y extraé las palabras clave más significativas
   - Creá un nombre corto de 2-4 palabras que capture la esencia de la funcionalidad
   - Usá el formato acción-sustantivo cuando sea posible (p. ej., "add-user-auth", "fix-payment-bug")
   - Conservá los términos técnicos y siglas (OAuth2, API, JWT, etc.)
   - Mantenelo conciso pero lo bastante descriptivo para entender la funcionalidad de un vistazo
   - Ejemplos:
     - "Quiero agregar autenticación de usuarios" → "user-auth"
     - "Implementar la integración con OAuth2 para la API" → "oauth2-api-integration"
     - "Crear un panel de análisis" → "analytics-dashboard"
     - "Corregir el bug de timeout en el procesamiento de pagos" → "fix-payment-timeout"

2. **Creación de la rama** (opcional, mediante hook):

   Si un hook `before_specify` se ejecutó con éxito en las Verificaciones previas a la ejecución de arriba, habrá creado/cambiado a una rama de git y mostrado un JSON con `BRANCH_NAME` y `FEATURE_NUM`. Tomá nota de estos valores como referencia, pero el nombre de la rama **no** dicta el nombre del directorio de la spec.

   Si el usuario proporcionó explícitamente `GIT_BRANCH_NAME`, pasalo al hook para que el script de la rama use el valor exacto como nombre de la rama (salteando toda la generación de prefijos/sufijos).

3. **Creá el directorio de la spec de la funcionalidad**:

   Las specs viven bajo el directorio `specs/` por defecto, salvo que el usuario proporcione explícitamente `SPECIFY_FEATURE_DIRECTORY`.

   **Orden de resolución de `SPECIFY_FEATURE_DIRECTORY`**:
   1. Si el usuario proporcionó explícitamente `SPECIFY_FEATURE_DIRECTORY` (p. ej., mediante variable de entorno, argumento o configuración), usalo tal cual
   2. De lo contrario, generalo automáticamente bajo `specs/`:
      - Revisá `.specify/init-options.json` para ver `feature_numbering` (preferido) o `branch_numbering` (obsoleto, solo para migración; se eliminará en una versión futura)
      - Si es `"timestamp"`: el prefijo es `AAAAMMDD-HHMMSS` (marca de tiempo actual)
      - Si es `"sequential"` o está ausente: el prefijo es `NNN` (el próximo número de 3 dígitos disponible tras escanear los directorios existentes en `specs/`)
      - Armá el nombre del directorio: `<prefijo>-<nombre-corto>` (p. ej., `003-user-auth` o `20260319-143022-user-auth`)
      - Asigná `SPECIFY_FEATURE_DIRECTORY` a `specs/<nombre-del-directorio>`
      - Si se usó `branch_numbering` (y faltaba `feature_numbering`), emití una advertencia de una línea: "⚠️ `branch_numbering` en init-options.json está obsoleto. Renombralo a `feature_numbering`."

   **Creá el directorio y el archivo de la spec**:
   - `mkdir -p SPECIFY_FEATURE_DIRECTORY`
   - Resolvé el `spec-template` activo mediante la pila de resolución de presets/plantillas de Spec Kit (equivalente a `specify preset resolve spec-template`)
   - Copiá el archivo `spec-template` resuelto a `SPECIFY_FEATURE_DIRECTORY/spec.md` como punto de partida
   - Asigná `SPEC_FILE` a `SPECIFY_FEATURE_DIRECTORY/spec.md`
   - Persistí la ruta resuelta en `.specify/feature.json`:
     ```json
     {
       "feature_directory": "<directorio de la funcionalidad resuelto>"
     }
     ```
     Escribí el valor real de la ruta del directorio resuelta (por ejemplo, `specs/003-user-auth`), no la cadena literal `SPECIFY_FEATURE_DIRECTORY`.
     Esto permite que los comandos posteriores (`/speckit-plan`, `/speckit-tasks`, etc.) ubiquen el directorio de la funcionalidad sin depender de las convenciones de nombres de la rama de git.

   **IMPORTANTE**:
   - Solo debés crear una funcionalidad por cada invocación de `/speckit-specify`
   - El nombre del directorio de la spec y el nombre de la rama de git son independientes: pueden coincidir, pero eso lo decide el usuario
   - El directorio y el archivo de la spec siempre los crea este comando, nunca el hook

4. Cargá el archivo `spec-template` activo resuelto para entender las secciones requeridas.

5. **SI EXISTE**: Cargá `.specify/memory/constitution.md` para conocer los principios del proyecto y las restricciones de gobernanza.

6. Seguí este flujo de ejecución:
    1. Parseá la descripción del usuario a partir de los argumentos
       Si está vacía: ERROR "No se proporcionó una descripción de la funcionalidad"
    2. Extraé los conceptos clave de la descripción
       Identificá: actores, acciones, datos, restricciones
    3. Para los aspectos poco claros:
       - Hacé suposiciones fundadas basadas en el contexto y en los estándares de la industria
       - Marcá con [NEEDS CLARIFICATION: pregunta específica] solo si:
         - La decisión impacta de forma significativa el alcance de la funcionalidad o la experiencia del usuario
         - Existen varias interpretaciones razonables con implicancias distintas
         - No existe un valor por defecto razonable
       - **LÍMITE: máximo 3 marcadores [NEEDS CLARIFICATION] en total**
       - Priorizá las aclaraciones por impacto: alcance > seguridad/privacidad > experiencia de usuario > detalles técnicos
    4. Completá la sección Escenarios de usuario y pruebas
       Si no hay un flujo de usuario claro: ERROR "No se pueden determinar los escenarios de usuario"
    5. Generá los Requisitos funcionales
       Cada requisito debe ser verificable
       Usá valores por defecto razonables para los detalles no especificados (documentá los supuestos en la sección Supuestos)
    6. Definí los Criterios de éxito
       Creá resultados medibles e independientes de la tecnología
       Incluí tanto métricas cuantitativas (tiempo, rendimiento, volumen) como medidas cualitativas (satisfacción del usuario, finalización de tareas)
       Cada criterio debe poder verificarse sin detalles de implementación
    7. Identificá las Entidades clave (si hay datos involucrados)
    8. Devolvé: ÉXITO (spec lista para planificar)

7. Escribí la especificación en SPEC_FILE usando la estructura de la plantilla, reemplazando los marcadores de posición con detalles concretos derivados de la descripción de la funcionalidad (los argumentos) y preservando el orden de las secciones y los encabezados.

8. **Validación de calidad de la especificación**: Después de escribir la spec inicial, validala contra criterios de calidad:

   a. **Crear el checklist de calidad de la spec**: Generá un archivo de checklist en `SPECIFY_FEATURE_DIRECTORY/checklists/requirements.md` usando la estructura de la plantilla de checklist con estos ítems de validación:

      ```markdown
      # Checklist de calidad de la especificación: [NOMBRE DE LA FUNCIONALIDAD]

      **Propósito**: Validar la completitud y la calidad de la especificación antes de pasar a la planificación
      **Creado**: [FECHA]
      **Funcionalidad**: [Enlace a spec.md]

      ## Calidad del contenido

      - [ ] Sin detalles de implementación (lenguajes, frameworks, APIs)
      - [ ] Centrada en el valor para el usuario y las necesidades del negocio
      - [ ] Escrita para partes interesadas no técnicas
      - [ ] Todas las secciones obligatorias completas

      ## Completitud de los requisitos

      - [ ] No quedan marcadores [NEEDS CLARIFICATION]
      - [ ] Los requisitos son verificables y no ambiguos
      - [ ] Los criterios de éxito son medibles
      - [ ] Los criterios de éxito son independientes de la tecnología (sin detalles de implementación)
      - [ ] Todos los escenarios de aceptación están definidos
      - [ ] Los casos límite están identificados
      - [ ] El alcance está claramente acotado
      - [ ] Las dependencias y los supuestos están identificados

      ## Preparación de la funcionalidad

      - [ ] Todos los requisitos funcionales tienen criterios de aceptación claros
      - [ ] Los escenarios de usuario cubren los flujos principales
      - [ ] La funcionalidad cumple los resultados medibles definidos en los Criterios de éxito
      - [ ] No se filtran detalles de implementación en la especificación

      ## Notas

      - Los ítems marcados como incompletos requieren actualizar la spec antes de `/speckit-clarify` o `/speckit-plan`
      ```

   b. **Ejecutar la verificación de validación**: Revisá la spec contra cada ítem del checklist:
      - Por cada ítem, determiná si cumple o no
      - Documentá los problemas específicos encontrados (citá las secciones relevantes de la spec)

   c. **Manejar los resultados de la validación**:

      - **Si todos los ítems cumplen**: Marcá el checklist como completo y pasá a la sección Hooks posteriores a la ejecución (obligatorios)

      - **Si fallan ítems (excluyendo [NEEDS CLARIFICATION])**:
        1. Listá los ítems que fallan y los problemas específicos
        2. Actualizá la spec para abordar cada problema
        3. Volvé a ejecutar la validación hasta que todos los ítems cumplan (máximo 3 iteraciones)
        4. Si después de 3 iteraciones todavía falla, documentá los problemas restantes en las notas del checklist y advertile al usuario

      - **Si quedan marcadores [NEEDS CLARIFICATION]**:
        1. Extraé todos los marcadores [NEEDS CLARIFICATION: ...] de la spec
        2. **CONTROL DE LÍMITE**: Si existen más de 3 marcadores, conservá solo los 3 más críticos (por impacto en alcance/seguridad/UX) y hacé suposiciones fundadas para el resto
        3. Por cada aclaración necesaria (máximo 3), presentale las opciones al usuario con este formato:

           ```markdown
           ## Pregunta [N]: [Tema]

           **Contexto**: [Citar la sección relevante de la spec]

           **Qué necesitamos saber**: [Pregunta específica del marcador NEEDS CLARIFICATION]

           **Respuestas sugeridas**:

           | Opción | Respuesta | Implicancias |
           |--------|-----------|--------------|
           | A      | [Primera respuesta sugerida] | [Qué significa esto para la funcionalidad] |
           | B      | [Segunda respuesta sugerida] | [Qué significa esto para la funcionalidad] |
           | C      | [Tercera respuesta sugerida] | [Qué significa esto para la funcionalidad] |
           | Otra   | Dar tu propia respuesta | [Explicar cómo ingresar una respuesta personalizada] |

           **Tu elección**: _[Esperar la respuesta del usuario]_
           ```

        4. **CRÍTICO - Formato de tablas**: Asegurate de que las tablas markdown estén bien formateadas:
           - Usá un espaciado consistente con las barras verticales alineadas
           - Cada celda debe tener espacios alrededor del contenido: `| Contenido |` y no `|Contenido|`
           - El separador del encabezado debe tener al menos 3 guiones: `|--------|`
           - Probá que la tabla se renderice correctamente en la vista previa de markdown
        5. Numerá las preguntas de forma secuencial (P1, P2, P3; máximo 3 en total)
        6. Presentá todas las preguntas juntas antes de esperar las respuestas
        7. Esperá a que el usuario responda con sus elecciones para todas las preguntas (p. ej., "P1: A, P2: Otra - [detalles], P3: B")
        8. Actualizá la spec reemplazando cada marcador [NEEDS CLARIFICATION] por la respuesta elegida o provista por el usuario
        9. Volvé a ejecutar la validación una vez resueltas todas las aclaraciones

   d. **Actualizar el checklist**: Después de cada iteración de validación, actualizá el archivo de checklist con el estado actual de cumple/no cumple

## Hooks posteriores a la ejecución (obligatorios)

**DEBES completar esta sección antes de informar la finalización al usuario.**

Verificá si existe `.specify/extensions.yml` en la raíz del proyecto.
- Si no existe, o no hay hooks registrados bajo `hooks.after_specify`, pasá directo al Informe de finalización.
- Si existe, leelo y buscá las entradas bajo la clave `hooks.after_specify`.
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

Informá la finalización al usuario con:
- `SPECIFY_FEATURE_DIRECTORY`: la ruta del directorio de la funcionalidad
- `SPEC_FILE`: la ruta del archivo de la spec
- Resumen de los resultados del checklist
- Preparación para la siguiente fase (`/speckit-clarify` o `/speckit-plan`)

**NOTA:** La creación de la rama la maneja el hook `before_specify` (extensión de git). La creación del directorio y del archivo de la spec siempre la maneja este comando central.

## Guía rápida

- Concentrate en **QUÉ** necesitan los usuarios y **POR QUÉ**.
- Evitá el CÓMO implementarlo (sin stack tecnológico, APIs ni estructura de código).
- Escrita para partes interesadas del negocio, no para desarrolladores.
- NO crees ningún checklist embebido en la spec. Eso corresponde a otro comando.

### Requisitos de las secciones

- **Secciones obligatorias**: Deben completarse en toda funcionalidad
- **Secciones opcionales**: Incluílas solo cuando sean relevantes para la funcionalidad
- Cuando una sección no aplique, eliminala por completo (no la dejes como "N/A")

### Para la generación con IA

Al crear esta spec a partir de un pedido del usuario:

1. **Hacé suposiciones fundadas**: Usá el contexto, los estándares de la industria y los patrones comunes para completar los vacíos
2. **Documentá los supuestos**: Registrá los valores por defecto razonables en la sección Supuestos
3. **Limitá las aclaraciones**: Máximo 3 marcadores [NEEDS CLARIFICATION]; usalos solo para decisiones críticas que:
   - Impactan de forma significativa el alcance de la funcionalidad o la experiencia del usuario
   - Tienen varias interpretaciones razonables con implicancias distintas
   - No tienen ningún valor por defecto razonable
4. **Priorizá las aclaraciones**: alcance > seguridad/privacidad > experiencia de usuario > detalles técnicos
5. **Pensá como un tester**: Todo requisito vago debería fallar el ítem del checklist "verificable y no ambiguo"
6. **Áreas comunes que necesitan aclaración** (solo si no existe un valor por defecto razonable):
   - Alcance y límites de la funcionalidad (incluir/excluir casos de uso específicos)
   - Tipos de usuario y permisos (si son posibles varias interpretaciones en conflicto)
   - Requisitos de seguridad/cumplimiento (cuando son significativos legal o financieramente)

**Ejemplos de valores por defecto razonables** (no preguntes sobre esto):

- Retención de datos: prácticas estándar de la industria para el dominio
- Objetivos de rendimiento: expectativas estándar de aplicaciones web/móviles, salvo que se especifique otra cosa
- Manejo de errores: mensajes amigables para el usuario con alternativas apropiadas
- Método de autenticación: basado en sesión estándar u OAuth2 para aplicaciones web
- Patrones de integración: usar los patrones apropiados al proyecto (REST/GraphQL para servicios web, llamadas a funciones para bibliotecas, argumentos de CLI para herramientas, etc.)

### Pautas para los criterios de éxito

Los criterios de éxito deben ser:

1. **Medibles**: Incluir métricas específicas (tiempo, porcentaje, cantidad, tasa)
2. **Independientes de la tecnología**: Sin mencionar frameworks, lenguajes, bases de datos ni herramientas
3. **Centrados en el usuario**: Describir los resultados desde la perspectiva del usuario/negocio, no de las partes internas del sistema
4. **Verificables**: Que se puedan probar/validar sin conocer los detalles de implementación

**Buenos ejemplos**:

- "Los usuarios pueden completar la compra en menos de 3 minutos"
- "El sistema soporta 10.000 usuarios concurrentes"
- "El 95 % de las búsquedas devuelve resultados en menos de 1 segundo"
- "La tasa de finalización de tareas mejora un 40 %"

**Malos ejemplos** (centrados en la implementación):

- "El tiempo de respuesta de la API es menor a 200 ms" (demasiado técnico; usar "Los usuarios ven los resultados al instante")
- "La base de datos soporta 1000 TPS" (detalle de implementación; usar una métrica orientada al usuario)
- "Los componentes de React se renderizan de forma eficiente" (específico de un framework)
- "La tasa de aciertos de la caché Redis supera el 80 %" (específico de una tecnología)

## Terminado cuando

- [ ] La especificación se escribió en `SPEC_FILE` y se validó contra el checklist de calidad
- [ ] Los hooks de extensión se despacharon u omitieron según las reglas de Hooks posteriores a la ejecución (obligatorios) de arriba
- [ ] Se informó la finalización al usuario con el directorio de la funcionalidad, la ruta del archivo de la spec y los resultados del checklist
