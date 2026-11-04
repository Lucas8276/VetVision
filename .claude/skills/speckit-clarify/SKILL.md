---
name: "speckit-clarify"
description: "Identifica las áreas subespecificadas de la spec de la funcionalidad actual haciendo hasta 5 preguntas de aclaración muy puntuales, y vuelca las respuestas en la spec."
argument-hint: "Áreas opcionales a aclarar en la spec"
compatibility: "Requiere la estructura de proyecto de spec-kit con el directorio .specify/"
metadata:
  author: "github-spec-kit"
  source: "templates/commands/clarify.md"
user-invocable: true
disable-model-invocation: false
---


## Entrada del usuario

```text
$ARGUMENTS
```

**DEBES** considerar la entrada del usuario antes de continuar (si no está vacía).

## Verificaciones previas a la ejecución

**Buscar hooks de extensión (antes de la aclaración)**:
- Verificá si existe `.specify/extensions.yml` en la raíz del proyecto.
- Si existe, leelo y buscá las entradas bajo la clave `hooks.before_clarify`
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

Objetivo: Detectar y reducir la ambigüedad o los puntos de decisión faltantes en la especificación de la funcionalidad activa, y registrar las aclaraciones directamente en el archivo de la spec.

Nota: Se espera que este flujo de aclaración se ejecute (y se complete) ANTES de invocar `/speckit-plan`. Si el usuario indica explícitamente que se saltea la aclaración (p. ej., un spike exploratorio), podés continuar, pero debés advertir que aumenta el riesgo de retrabajo posterior.

Pasos de ejecución:

1. Ejecutá `.specify/scripts/powershell/check-prerequisites.ps1 -Json -PathsOnly` desde la raíz del repositorio **una sola vez** (modo combinado `--json --paths-only` / `-Json -PathsOnly`). Parseá los campos mínimos del JSON:
   - `FEATURE_DIR`
   - `FEATURE_SPEC`
   - (Opcionalmente capturá `IMPL_PLAN`, `TASKS` para flujos encadenados futuros.)
   - Si falla el parseo del JSON, abortá e indicale al usuario que vuelva a ejecutar `/speckit-specify` o que verifique el entorno de la rama de la funcionalidad.
   - Para las comillas simples en los argumentos, como "I'm Groot", usá la sintaxis de escape: p. ej. 'I'\''m Groot' (o comillas dobles si es posible: "I'm Groot").

2. **SI EXISTE**: Cargá `.specify/memory/constitution.md` para conocer los principios del proyecto y las restricciones de gobernanza.

3. Cargá el archivo de la spec actual. Realizá un escaneo estructurado de ambigüedad y cobertura usando esta taxonomía. Por cada categoría, marcá el estado: Claro / Parcial / Faltante. Producí un mapa de cobertura interno que se use para priorizar (no muestres el mapa crudo salvo que no vaya a hacerse ninguna pregunta).

   Alcance funcional y comportamiento:
   - Objetivos centrales del usuario y criterios de éxito
   - Declaraciones explícitas de qué queda fuera del alcance
   - Diferenciación de roles de usuario / personas

   Dominio y modelo de datos:
   - Entidades, atributos, relaciones
   - Reglas de identidad y unicidad
   - Ciclo de vida / transiciones de estado
   - Supuestos de volumen / escala de los datos

   Interacción y flujo de UX:
   - Recorridos / secuencias críticas del usuario
   - Estados de error / vacío / carga
   - Notas de accesibilidad o localización

   Atributos de calidad no funcionales:
   - Rendimiento (objetivos de latencia, throughput)
   - Escalabilidad (horizontal/vertical, límites)
   - Confiabilidad y disponibilidad (tiempo de actividad, expectativas de recuperación)
   - Observabilidad (señales de logging, métricas, trazas)
   - Seguridad y privacidad (autenticación/autorización, protección de datos, supuestos de amenazas)
   - Restricciones de cumplimiento / regulatorias (si las hay)

   Integración y dependencias externas:
   - Servicios/APIs externos y sus modos de falla
   - Formatos de importación/exportación de datos
   - Supuestos de protocolo/versionado

   Casos límite y manejo de fallas:
   - Escenarios negativos
   - Limitación de tasa / throttling
   - Resolución de conflictos (p. ej., ediciones concurrentes)

   Restricciones y compromisos:
   - Restricciones técnicas (lenguaje, almacenamiento, alojamiento)
   - Compromisos explícitos o alternativas descartadas

   Terminología y consistencia:
   - Términos canónicos del glosario
   - Sinónimos a evitar / términos obsoletos

   Señales de finalización:
   - Verificabilidad de los criterios de aceptación
   - Indicadores medibles al estilo de Definición de Terminado

   Varios / marcadores de posición:
   - Marcadores TODO / decisiones sin resolver
   - Adjetivos ambiguos ("robusto", "intuitivo") sin cuantificar

   Por cada categoría con estado Parcial o Faltante, agregá una oportunidad de pregunta candidata, salvo que:
   - La aclaración no cambie de forma material la estrategia de implementación o de validación
   - La información sea mejor diferirla a la fase de planificación (anotalo internamente)

4. Generá (internamente) una cola priorizada de preguntas de aclaración candidatas (máximo 5). NO las muestres todas a la vez. Aplicá estas restricciones:
    - Máximo 5 preguntas en total en toda la sesión.
    - Cada pregunta debe poder responderse con UNA de estas formas:
       - Una selección corta de opción múltiple (2 a 5 opciones distintas y mutuamente excluyentes), O
       - Una respuesta de una palabra / frase corta (con restricción explícita: "Respondé en <=5 palabras").
    - Incluí solo preguntas cuyas respuestas impacten de forma material la arquitectura, el modelado de datos, la descomposición en tareas, el diseño de pruebas, el comportamiento de UX, la preparación operativa o la validación de cumplimiento.
    - Asegurá un balance de cobertura por categorías: intentá cubrir primero las categorías sin resolver de mayor impacto; evitá hacer dos preguntas de bajo impacto cuando un único área de alto impacto (p. ej., la postura de seguridad) sigue sin resolver.
    - Excluí las preguntas ya respondidas, las preferencias de estilo triviales o los detalles de ejecución a nivel de plan (salvo que bloqueen la corrección).
    - Favorecé las aclaraciones que reduzcan el riesgo de retrabajo posterior o eviten pruebas de aceptación desalineadas.
    - Si quedan más de 5 categorías sin resolver, elegí las 5 principales con la heurística (Impacto * Incertidumbre).

5. Bucle de preguntas secuencial (interactivo):
    - Presentá EXACTAMENTE UNA pregunta por vez.
    - **Calidad de redacción de las preguntas (aplica a toda pregunta, de opción múltiple o de respuesta corta):**
       - Empezá con `**Pregunta:**` seguido de una interrogación completa que termine con `?`. El texto de la pregunta antes del `?` debe tener sentido por sí solo.
       - NUNCA uses una etiqueta de tema, un encabezado de sección o un id de requisito como la pregunta en sí. Por ejemplo, `Matriz de dispositivos/entornos de aceptación (FR-023)` NO es válido: es una etiqueta, no una pregunta.
       - Después del `?`, el único sufijo permitido es un id de requisito/pregunta opcional entre paréntesis. Formato exacto: `**Pregunta:** <interrogación>?` o `**Pregunta:** <interrogación>? (FR-023)`. Nunca pongas el id antes del `?` y nunca uses el id (solo o con una etiqueta de tema) como el enunciado completo.
       - Inmediatamente después de la línea de la pregunta, agregá una oración en lenguaje llano de "Por qué importa" (qué está en juego para la aceptación o la entrega) antes de la recomendación/opciones.
       - Usá palabras cotidianas; incorporá jerga solo si la definís en la misma oración. Autoverificación: una persona que no conoce Spec Kit debe poder responder solo con la línea de la Pregunta. Se admite lo escueto; las etiquetas crípticas, no.
    - Para preguntas de opción múltiple:
       - **Analizá todas las opciones** y determiná la **opción más adecuada** en función de:
          - Las mejores prácticas para el tipo de proyecto
          - Los patrones comunes en implementaciones similares
          - La reducción de riesgos (seguridad, rendimiento, mantenibilidad)
          - La alineación con cualquier objetivo o restricción explícita del proyecto visible en la spec
       - Presentá tu **opción recomendada de forma destacada** al comienzo, con un razonamiento claro (1-2 oraciones que expliquen por qué es la mejor elección).
       - Formato: `**Recomendada:** Opción [X] - <razonamiento>`
       - Luego mostrá todas las opciones como una tabla Markdown:

       | Opción | Descripción |
       |--------|-------------|
       | A | <Descripción de la opción A> |
       | B | <Descripción de la opción B> |
       | C | <Descripción de la opción C> (agregá D/E según haga falta, hasta 5) |
       | Corta | Dar otra respuesta corta (<=5 palabras) (Incluir solo si corresponde una alternativa de formato libre) |

       - Después de la tabla, agregá: `Podés responder con la letra de la opción (p. ej., "A"), aceptar la recomendación diciendo "sí" o "recomendada", o dar tu propia respuesta corta.`
    - Para el estilo de respuesta corta (sin opciones discretas significativas):
       - Dá tu **respuesta sugerida** según las mejores prácticas y el contexto.
       - Formato: `**Sugerida:** <tu respuesta propuesta> - <breve razonamiento>`
       - Luego mostrá: `Formato: respuesta corta (<=5 palabras). Podés aceptar la sugerencia diciendo "sí" o "sugerida", o dar tu propia respuesta.`
    - Después de que el usuario responda:
       - Si el usuario responde "sí", "recomendada" o "sugerida", usá como respuesta tu recomendación/sugerencia anterior.
       - De lo contrario, validá que la respuesta corresponda a una opción o cumpla la restricción de <=5 palabras.
       - Si es ambigua, pedí una desambiguación rápida (sigue contando como la misma pregunta; no avances).
       - Una vez que sea satisfactoria, registrala en la memoria de trabajo (todavía no la escribas en disco) y pasá a la siguiente pregunta de la cola.
    - Dejá de hacer más preguntas cuando:
       - Todas las ambigüedades críticas se resolvieron antes de tiempo (los elementos restantes de la cola dejan de ser necesarios), O
       - El usuario indique que terminó ("listo", "bien", "no más"), O
       - Llegues a 5 preguntas hechas.
    - Nunca reveles por adelantado las preguntas futuras de la cola.
    - Si al comienzo no hay preguntas válidas, informá de inmediato que no hay ambigüedades críticas.

6. Integración después de CADA respuesta aceptada (enfoque de actualización incremental):
    - Mantené en memoria una representación de la spec (cargada una vez al comienzo) junto con el contenido crudo del archivo.
    - Para la primera respuesta integrada de esta sesión:
       - Asegurá que exista una sección `## Aclaraciones` (si falta, creala justo después de la sección contextual/de resumen de más alto nivel según la plantilla de spec).
       - Debajo, creá (si no está presente) un subencabezado `### Sesión AAAA-MM-DD` con la fecha de hoy.
    - Agregá una línea de viñeta inmediatamente después de la aceptación: `- P: <pregunta> → R: <respuesta final>`.
    - Luego aplicá de inmediato la aclaración en la(s) sección(es) más apropiada(s):
       - Ambigüedad funcional → Actualizá o agregá una viñeta en Requisitos funcionales.
       - Interacción de usuario / distinción de actores → Actualizá Historias de usuario o el subapartado de Actores (si existe) con el rol, la restricción o el escenario aclarado.
       - Forma de los datos / entidades → Actualizá el Modelo de datos (agregá campos, tipos, relaciones) preservando el orden; anotá brevemente las restricciones agregadas.
       - Restricción no funcional → Agregá/modificá criterios medibles en Criterios de éxito > Resultados medibles (convertí el adjetivo vago en una métrica o un objetivo explícito).
       - Caso límite / flujo negativo → Agregá una viñeta nueva en Casos límite / Manejo de errores (o creá ese subapartado si la plantilla prevé un marcador para él).
       - Conflicto de terminología → Normalizá el término en toda la spec; conservá el original solo si es necesario, agregando una única vez `(antes denominado "X")`.
    - Si la aclaración invalida una afirmación ambigua anterior, reemplazá esa afirmación en lugar de duplicarla; no dejes texto obsoleto que se contradiga.
    - Guardá el archivo de la spec DESPUÉS de cada integración para minimizar el riesgo de perder contexto (sobrescritura atómica).
    - Preservá el formato: no reordenes secciones no relacionadas; mantené intacta la jerarquía de encabezados.
    - Mantené cada aclaración insertada mínima y verificable (evitá desviaciones narrativas).

7. Validación (se realiza después de CADA escritura más una pasada final):
   - La sesión de Aclaraciones contiene exactamente una viñeta por respuesta aceptada (sin duplicados).
   - El total de preguntas hechas (aceptadas) es ≤ 5.
   - Las secciones actualizadas no contienen marcadores de posición vagos que la nueva respuesta debía resolver.
   - No queda ninguna afirmación anterior contradictoria (revisá que se hayan quitado las opciones alternativas que ahora son inválidas).
   - La estructura Markdown es válida; los únicos encabezados nuevos permitidos son: `## Aclaraciones`, `### Sesión AAAA-MM-DD`.
   - Consistencia terminológica: se usa el mismo término canónico en todas las secciones actualizadas.

8. Escribí la spec actualizada de vuelta en `FEATURE_SPEC`.

9. **Volver a validar el checklist de calidad de la spec** (si existe):
   - Verificá si existe `FEATURE_DIR/checklists/requirements.md`.
   - Si NO existe, omití este paso en silencio.
   - Si existe:
     1. Leé el archivo de checklist.
     2. Identificá todas las líneas de casillas de lista de tareas de GitHub, es decir las que coincidan con `- [ ]`, `- [x]` o `- [X]` (sin distinguir mayúsculas, tolerando espacios iniciales en ítems anidados) fuera de bloques de código. Ignorá cualquier otro contenido (encabezados, notas, viñetas sin casilla, metadatos).
     3. Por cada línea con casilla, registrá su estado actual del marcador (marcada o sin marcar) y el texto del ítem en una lista de instantánea previa.
     4. Reevaluá cada ítem con casilla contra la spec **actualizada** (la versión recién guardada en el paso 7).
     5. Por cada ítem con casilla, actualizalo solo si el estado marcada/sin marcar realmente cambia:
        - Si el ítem ahora cumple y estaba sin marcar: cambiá `[ ]` por `[x]`.
        - Si el ítem ahora no cumple y estaba marcado: cambiá `[x]`/`[X]` por `[ ]`.
        - Si el estado no cambió: dejá el marcador como está (conservá las mayúsculas/minúsculas existentes para evitar diffs cosméticos).
     6. Guardá el archivo de checklist actualizado. **Cambiá únicamente la parte del marcador `[ ]`/`[x]` de las líneas con casilla cuyo estado cambió.** Todo el resto del contenido del archivo (encabezados, metadatos, notas, orden de líneas, espacios en blanco) debe permanecer sin cambios para evitar diffs ruidosos.
     7. Compará la instantánea previa con el estado actual para calcular tres listas para el Informe de finalización:
        - **Nuevos que cumplen**: ítems que pasaron de sin marcar a marcados.
        - **Regresiones**: ítems que pasaron de marcados a sin marcar.
        - **Siguen sin marcar**: ítems que continúan sin marcar.
     8. Registrá los conteos de aprobados antes/después como ítems con casilla marcados/total (p. ej., "12/16 → 15/16 ítems aprobados").

Reglas de comportamiento:

- Si no se encuentran ambigüedades significativas (o todas las preguntas potenciales serían de bajo impacto), respondé: "No se detectaron ambigüedades críticas que justifiquen una aclaración formal." y sugerí continuar.
- Si falta el archivo de la spec, indicale al usuario que ejecute primero `/speckit-specify` (no crees una spec nueva acá).
- Nunca superes las 5 preguntas hechas en total (los reintentos de aclaración de una misma pregunta no cuentan como preguntas nuevas).
- Evitá preguntas especulativas sobre el stack tecnológico, salvo que su ausencia bloquee la claridad funcional.
- Respetá las señales de terminación anticipada del usuario ("pará", "listo", "seguí").
- Si no se hicieron preguntas por cobertura completa, mostrá un resumen de cobertura compacto (todas las categorías Claras) y luego sugerí avanzar.
- Si se alcanzó la cuota y quedan categorías de alto impacto sin resolver, marcalas explícitamente como Diferidas con su justificación.

Contexto para la priorización: $ARGUMENTS

## Hooks posteriores a la ejecución (obligatorios)

**DEBES completar esta sección antes de informar la finalización al usuario.**

Verificá si existe `.specify/extensions.yml` en la raíz del proyecto.
- Si no existe, o no hay hooks registrados bajo `hooks.after_clarify`, pasá directo al Informe de finalización.
- Si existe, leelo y buscá las entradas bajo la clave `hooks.after_clarify`.
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

Informá la finalización (después de que termine el bucle de preguntas o de una terminación anticipada):
- Cantidad de preguntas hechas y respondidas.
- Ruta de la spec actualizada.
- Secciones modificadas (listá los nombres).
- Estado del checklist de calidad de la spec (si se revalidó `FEATURE_DIR/checklists/requirements.md`): mostrá los conteos de aprobados antes/después (p. ej., "Checklist de calidad de la spec: 12/16 → 15/16 ítems aprobados") y listá los ítems que cambiaron de estado, tanto los recién marcados (sin marcar → marcado) como las regresiones (marcado → sin marcar). Si algún ítem sigue sin marcar, listalo como un área que requiere atención.
- Tabla de resumen de cobertura que liste cada categoría de la taxonomía con su Estado: Resuelta (estaba Parcial/Faltante y se abordó), Diferida (excede la cuota de preguntas o es más apropiada para la planificación), Clara (ya era suficiente), Pendiente (sigue Parcial/Faltante pero de bajo impacto).
- Si quedan categorías Pendientes o Diferidas, recomendá si conviene pasar a `/speckit-plan` o volver a ejecutar `/speckit-clarify` más adelante, después del plan.
- Comando sugerido a continuación.

## Terminado cuando

- [ ] Se identificaron las ambigüedades de la spec y se integraron las aclaraciones en el archivo de la spec
- [ ] El checklist de calidad de la spec se revalidó contra la spec actualizada (si existe `FEATURE_DIR/checklists/requirements.md`)
- [ ] Los hooks de extensión se despacharon u omitieron según las reglas de Hooks posteriores a la ejecución (obligatorios) de arriba
- [ ] Se informó la finalización al usuario con las preguntas respondidas, las secciones modificadas, el estado del checklist y el resumen de cobertura
