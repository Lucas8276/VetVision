---
name: "speckit-checklist"
description: "Genera un checklist personalizado para la funcionalidad actual a partir de los requisitos del usuario."
argument-hint: "Dominio o área de enfoque del checklist"
compatibility: "Requiere la estructura de proyecto de spec-kit con el directorio .specify/"
metadata:
  author: "github-spec-kit"
  source: "templates/commands/checklist.md"
user-invocable: true
disable-model-invocation: false
---


## Propósito del checklist: "Pruebas unitarias para el español"

**CONCEPTO CRÍTICO**: Los checklists son **PRUEBAS UNITARIAS PARA LA REDACCIÓN DE REQUISITOS**: validan la calidad, la claridad y la completitud de los requisitos de un dominio dado.

**NO sirven para verificar/probar**:

- ❌ NO "Verificar que el botón responde correctamente al clic"
- ❌ NO "Probar que el manejo de errores funciona"
- ❌ NO "Confirmar que la API devuelve 200"
- ❌ NO revisar si el código/la implementación coincide con la spec

**SÍ sirven para validar la calidad de los requisitos**:

- ✅ "¿Están definidos los requisitos de jerarquía visual para todos los tipos de tarjeta?" (completitud)
- ✅ "¿Está 'visualización destacada' cuantificada con tamaños/posiciones específicos?" (claridad)
- ✅ "¿Son consistentes los requisitos del estado hover en todos los elementos interactivos?" (consistencia)
- ✅ "¿Están definidos los requisitos de accesibilidad para la navegación por teclado?" (cobertura)
- ✅ "¿Define la spec qué ocurre cuando falla la carga de la imagen del logo?" (casos límite)

**Metáfora**: Si tu spec es código escrito en español, el checklist es su suite de pruebas unitarias. Estás probando si los requisitos están bien escritos, completos, sin ambigüedades y listos para implementar, NO si la implementación funciona.

**Responsabilidad y ciclo de vida de las casillas**:

- Los checklists personalizados generados por este comando son artefactos de revisión de la calidad de los requisitos, a cargo de quien revisa.
- `[x]` significa que quien revisa determinó que se cumple el criterio de calidad del requisito.
- `[x]` NO significa que el trabajo de implementación esté terminado.
- Este comando genera o agrega ítems al checklist; NO DEBE marcar los ítems generados con `[x]`.
- Un agente puede ayudar a evaluar ítems solo cuando quien revisa se lo pida explícitamente.
- `checklists/requirements.md` es un checklist integrado y aparte de calidad de la spec, mantenido por `/speckit-specify` y `/speckit-clarify`; no consideres que esa excepción aplique a los checklists personalizados generados acá.

## Entrada del usuario

```text
$ARGUMENTS
```

**DEBES** considerar la entrada del usuario antes de continuar (si no está vacía).

## Verificaciones previas a la ejecución

**Buscar hooks de extensión (antes de generar el checklist)**:
- Verificá si existe `.specify/extensions.yml` en la raíz del proyecto.
- Si existe, leelo y buscá las entradas bajo la clave `hooks.before_checklist`
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

    Esperá el resultado del comando del hook antes de continuar con el Pasos de ejecución.
    ```
    Después de emitir el bloque anterior DEBES invocar realmente el hook y esperar a que termine antes de continuar. Ejecutalo de la misma forma en que ejecutarías el comando vos mismo en este agente/sesión (la invocación puede diferir del id literal `{command}` mostrado arriba; por ejemplo, un agente en modo skills lo ejecuta como `/skill:speckit-...` o `$speckit-...`). Emitir el bloque por sí solo no ejecuta el hook.
- Si no hay hooks registrados o no existe `.specify/extensions.yml`, omití este paso en silencio


## Pasos de ejecución

1. **Preparación**: Ejecutá `.specify/scripts/powershell/check-prerequisites.ps1 -Json -Template checklist-template` desde la raíz del repositorio y parseá el JSON para obtener FEATURE_DIR, la lista AVAILABLE_DOCS y TEMPLATE_CONTENT.
   - Todas las rutas de archivo deben ser absolutas.
   - Para las comillas simples en los argumentos, como "I'm Groot", usá la sintaxis de escape: p. ej. 'I'\''m Groot' (o comillas dobles si es posible: "I'm Groot").

2. **SI EXISTE**: Cargá `.specify/memory/constitution.md` para conocer los principios del proyecto y las restricciones de gobernanza.

3. **Aclarar la intención (dinámico)**: Derivá hasta TRES preguntas contextuales iniciales de aclaración (sin catálogo prearmado). DEBEN:
   - Generarse a partir de la redacción del usuario + las señales extraídas de la spec/plan/tareas
   - Preguntar solo por información que cambie de forma material el contenido del checklist
   - Omitirse individualmente si ya no hay ambigüedad en `$ARGUMENTS`
   - Preferir la precisión sobre la amplitud

   Algoritmo de generación:
   1. Extraé señales: palabras clave del dominio de la funcionalidad (p. ej., auth, latencia, UX, API), indicadores de riesgo ("crítico", "debe", "cumplimiento"), pistas de partes interesadas ("QA", "revisión", "equipo de seguridad") y entregables explícitos ("a11y", "rollback", "contratos").
   2. Agrupá las señales en áreas de enfoque candidatas (máx. 4) ordenadas por relevancia.
   3. Identificá la audiencia y el momento probables (autor, revisor, QA, lanzamiento) si no son explícitos.
   4. Detectá las dimensiones faltantes: amplitud del alcance, profundidad/rigor, énfasis en riesgos, límites de exclusión, criterios de aceptación medibles.
   5. Formulá las preguntas eligiendo entre estos arquetipos:
      - Refinamiento del alcance (p. ej., "¿Debe incluir los puntos de integración con X e Y o limitarse a la corrección del módulo local?")
      - Priorización de riesgos (p. ej., "¿Cuáles de estas áreas de riesgo potencial deberían recibir controles de puerta obligatorios?")
      - Calibración de la profundidad (p. ej., "¿Es una lista liviana de sanidad previa al commit o una puerta formal de lanzamiento?")
      - Encuadre de la audiencia (p. ej., "¿Lo usará solo el autor o los pares durante la revisión del PR?")
      - Exclusión de límites (p. ej., "¿Deberíamos excluir explícitamente los ítems de ajuste de rendimiento en esta ronda?")
      - Brecha de clase de escenario (p. ej., "No se detectan flujos de recuperación: ¿están dentro del alcance los caminos de rollback / falla parcial?")

   Reglas de formato de las preguntas:
   - Si presentás opciones, generá una tabla compacta con las columnas: Opción | Candidato | Por qué importa
   - Limitá a un máximo de opciones A–E; omití la tabla si una respuesta de formato libre es más clara
   - Nunca le pidas al usuario que repita lo que ya dijo
   - Evitá categorías especulativas (sin inventar). Si hay dudas, preguntá explícitamente: "Confirmá si X pertenece al alcance."

   Valores por defecto cuando la interacción es imposible:
   - Profundidad: Estándar
   - Audiencia: Revisor (PR) si está relacionado con código; Autor en caso contrario
   - Enfoque: Los 2 principales grupos de relevancia

   Mostrá las preguntas (rotuladas P1/P2/P3). Después de las respuestas: si ≥2 clases de escenario (Alternativo / Excepción / Recuperación / dominio No funcional) siguen sin quedar claras, PODÉS hacer hasta DOS seguimientos más puntuales (P4/P5), cada uno con una justificación de una línea (p. ej., "Riesgo de camino de recuperación sin resolver"). No superes cinco preguntas en total. Omití la escalada si el usuario rechaza explícitamente más preguntas.

4. **Comprender el pedido del usuario**: Combiná `$ARGUMENTS` + las respuestas de aclaración:
   - Derivá el tema del checklist (p. ej., seguridad, revisión, despliegue, UX)
   - Consolidá los ítems imprescindibles que el usuario mencionó explícitamente
   - Asigná las elecciones de enfoque al andamiaje de categorías
   - Inferí cualquier contexto faltante a partir de la spec/plan/tareas (NO inventes)

5. **Cargar el contexto de la funcionalidad**: Leé desde FEATURE_DIR:
   - spec.md: Requisitos y alcance de la funcionalidad
   - plan.md (si existe): Detalles técnicos, dependencias
   - tasks.md (si existe): Tareas de implementación

   **Estrategia de carga de contexto**:
   - Cargá solo las porciones necesarias relevantes para las áreas de enfoque activas (evitá volcar archivos completos)
   - Preferí resumir las secciones largas en viñetas concisas de escenarios/requisitos
   - Usá divulgación progresiva: agregá recuperaciones posteriores solo si detectás brechas
   - Si los documentos fuente son grandes, generá ítems de resumen intermedios en lugar de incrustar el texto crudo

6. **Generar el checklist**: Usá TEMPLATE_CONTENT como plantilla estructural y creá "Pruebas unitarias para requisitos":
   - Creá el directorio `FEATURE_DIR/checklists/` si no existe
   - Generá un nombre de archivo de checklist único:
     - Usá un nombre corto y descriptivo basado en el dominio (p. ej., `ux.md`, `api.md`, `security.md`)
     - Formato: `[dominio].md`
   - Comportamiento al manejar el archivo:
     - Si el archivo NO existe: Creá un archivo nuevo y numerá los ítems desde CHK001
     - Si el archivo existe: Agregá los ítems nuevos al archivo existente, continuando desde el último ID CHK (p. ej., si el último ítem es CHK015, empezá los nuevos en CHK016)
   - Nunca borres ni reemplaces el contenido existente del checklist: siempre conservalo y agregá
   - Dejá cada ítem recién generado sin marcar (`[ ]`); el estado de las casillas le pertenece a quien revisa

   **PRINCIPIO CENTRAL - Probar los requisitos, no la implementación**:
   Cada ítem del checklist DEBE evaluar los REQUISITOS EN SÍ MISMOS en cuanto a:
   - **Completitud**: ¿Están presentes todos los requisitos necesarios?
   - **Claridad**: ¿Son los requisitos inequívocos y específicos?
   - **Consistencia**: ¿Están alineados los requisitos entre sí?
   - **Medibilidad**: ¿Se pueden verificar los requisitos de forma objetiva?
   - **Cobertura**: ¿Están abordados todos los escenarios/casos límite?

   **Estructura de categorías**: Agrupá los ítems por dimensiones de calidad de los requisitos:
   - **Completitud de los requisitos** (¿Están documentados todos los requisitos necesarios?)
   - **Claridad de los requisitos** (¿Son específicos y sin ambigüedades?)
   - **Consistencia de los requisitos** (¿Se alinean sin conflictos?)
   - **Calidad de los criterios de aceptación** (¿Son medibles los criterios de éxito?)
   - **Cobertura de escenarios** (¿Están abordados todos los flujos/casos?)
   - **Cobertura de casos límite** (¿Están definidas las condiciones de borde?)
   - **Requisitos no funcionales** (Rendimiento, Seguridad, Accesibilidad, etc.: ¿están especificados?)
   - **Dependencias y supuestos** (¿Están documentados y validados?)
   - **Ambigüedades y conflictos** (¿Qué necesita aclaración?)

   **CÓMO REDACTAR LOS ÍTEMS DEL CHECKLIST: "Pruebas unitarias para el español"**:

   ❌ **INCORRECTO** (probar la implementación):
   - "Verificar que la página de inicio muestre 3 tarjetas de episodios"
   - "Probar que los estados hover funcionen en escritorio"
   - "Confirmar que el clic en el logo navegue al inicio"

   ✅ **CORRECTO** (probar la calidad de los requisitos):
   - "¿Están especificados la cantidad exacta y la disposición de los episodios destacados?" [Completitud]
   - "¿Está 'visualización destacada' cuantificada con tamaños/posiciones específicos?" [Claridad]
   - "¿Son consistentes los requisitos del estado hover en todos los elementos interactivos?" [Consistencia]
   - "¿Están definidos los requisitos de navegación por teclado para toda la UI interactiva?" [Cobertura]
   - "¿Está especificado el comportamiento alternativo cuando falla la carga de la imagen del logo?" [Casos límite]
   - "¿Están definidos los estados de carga para los datos asíncronos de episodios?" [Completitud]
   - "¿Define la spec la jerarquía visual para los elementos de UI en competencia?" [Claridad]

   **ESTRUCTURA DEL ÍTEM**:
   Cada ítem debe seguir este patrón:
   - Formato de pregunta sobre la calidad del requisito
   - Concentrarse en lo que está ESCRITO (o no escrito) en la spec/plan
   - Incluir la dimensión de calidad entre corchetes [Completitud/Claridad/Consistencia/etc.]
   - Referenciar la sección de la spec `[Spec §X.Y]` al verificar requisitos existentes
   - Usar el marcador `[Brecha]` al verificar requisitos faltantes

   **EJEMPLOS POR DIMENSIÓN DE CALIDAD**:

   Completitud:
   - "¿Están definidos los requisitos de manejo de errores para todos los modos de falla de la API? [Brecha]"
   - "¿Están especificados los requisitos de accesibilidad para todos los elementos interactivos? [Completitud]"
   - "¿Están definidos los requisitos de puntos de quiebre móviles para los diseños responsivos? [Brecha]"

   Claridad:
   - "¿Está 'carga rápida' cuantificada con umbrales de tiempo específicos? [Claridad, Spec §NFR-2]"
   - "¿Están definidos explícitamente los criterios de selección de 'episodios relacionados'? [Claridad, Spec §FR-5]"
   - "¿Está 'destacado' definido con propiedades visuales medibles? [Ambigüedad, Spec §FR-4]"

   Consistencia:
   - "¿Se alinean los requisitos de navegación en todas las páginas? [Consistencia, Spec §FR-10]"
   - "¿Son consistentes los requisitos del componente tarjeta entre la página de inicio y la de detalle? [Consistencia]"

   Cobertura:
   - "¿Están definidos los requisitos para escenarios de estado cero (sin episodios)? [Cobertura, Caso límite]"
   - "¿Se abordan los escenarios de interacción concurrente de usuarios? [Cobertura, Brecha]"
   - "¿Están especificados los requisitos para fallas parciales en la carga de datos? [Cobertura, Flujo de excepción]"

   Medibilidad:
   - "¿Son medibles/verificables los requisitos de jerarquía visual? [Criterios de aceptación, Spec §FR-1]"
   - "¿Se puede verificar de forma objetiva el 'peso visual equilibrado'? [Medibilidad, Spec §FR-2]"

   **Clasificación y cobertura de escenarios** (enfoque en la calidad de los requisitos):
   - Verificá si existen requisitos para: escenarios Principal, Alternativo, Excepción/Error, Recuperación, No funcional
   - Por cada clase de escenario, preguntá: "¿Son completos, claros y consistentes los requisitos de [tipo de escenario]?"
   - Si falta una clase de escenario: "¿Los requisitos de [tipo de escenario] están excluidos a propósito o faltan? [Brecha]"
   - Incluí resiliencia/rollback cuando haya mutación de estado: "¿Están definidos los requisitos de rollback para las fallas de migración? [Brecha]"

   **Requisitos de trazabilidad**:
   - MÍNIMO: ≥80 % de los ítems DEBEN incluir al menos una referencia de trazabilidad
   - Cada ítem debería referenciar: la sección de la spec `[Spec §X.Y]`, o usar los marcadores: `[Brecha]`, `[Ambigüedad]`, `[Conflicto]`, `[Supuesto]`
   - Si no existe un sistema de IDs: "¿Está establecido un esquema de IDs de requisitos y criterios de aceptación? [Trazabilidad]"

   **Detectar y resolver problemas** (problemas de calidad de los requisitos):
   Hacé preguntas sobre los requisitos en sí:
   - Ambigüedades: "¿Está el término 'rápido' cuantificado con métricas específicas? [Ambigüedad, Spec §NFR-1]"
   - Conflictos: "¿Entran en conflicto los requisitos de navegación entre §FR-10 y §FR-10a? [Conflicto]"
   - Supuestos: "¿Está validado el supuesto de una 'API de podcasts siempre disponible'? [Supuesto]"
   - Dependencias: "¿Están documentados los requisitos de la API externa de podcasts? [Dependencia, Brecha]"
   - Definiciones faltantes: "¿Está 'jerarquía visual' definida con criterios medibles? [Brecha]"

   **Consolidación del contenido**:
   - Tope blando: si los ítems candidatos en bruto > 40, priorizá por riesgo/impacto
   - Unificá los casi duplicados que verifican el mismo aspecto de un requisito
   - Si hay >5 casos límite de bajo impacto, creá un único ítem: "¿Están abordados en los requisitos los casos límite X, Y, Z? [Cobertura]"

   **🚫 ABSOLUTAMENTE PROHIBIDO**: Esto lo convierte en una prueba de implementación, no de requisitos:
   - ❌ Cualquier ítem que empiece con "Verificar", "Probar", "Confirmar", "Comprobar" + comportamiento de la implementación
   - ❌ Referencias a la ejecución de código, acciones del usuario, comportamiento del sistema
   - ❌ "Se muestra correctamente", "funciona bien", "funciona como se espera"
   - ❌ "Clic", "navegar", "renderizar", "cargar", "ejecutar"
   - ❌ Casos de prueba, planes de prueba, procedimientos de QA
   - ❌ Detalles de implementación (frameworks, APIs, algoritmos)

   **✅ PATRONES REQUERIDOS**: Estos prueban la calidad de los requisitos:
   - ✅ "¿Están definidos/especificados/documentados los [tipo de requisito] para [escenario]?"
   - ✅ "¿Está [término vago] cuantificado/aclarado con criterios específicos?"
   - ✅ "¿Son consistentes los requisitos entre [sección A] y [sección B]?"
   - ✅ "¿Se puede medir/verificar [requisito] de forma objetiva?"
   - ✅ "¿Están abordados en los requisitos los [casos límite/escenarios]?"
   - ✅ "¿Define la spec [aspecto faltante]?"

7. **Referencia de estructura**: Generá el checklist siguiendo la plantilla canónica de `.specify/templates/checklist-template.md` para el título, la sección de metadatos, los encabezados de categoría, la nota de responsabilidad, la sección de notas y el formato de los IDs. Si la plantilla no está disponible, usá: título H1, líneas de metadatos de propósito/creación, una nota de responsabilidad que explique que `[x]` significa la aprobación de quien revisa sobre la calidad de los requisitos, secciones de categoría `##` con líneas `- [ ] CHK### <ítem de requisito>` con IDs que se incrementan globalmente desde CHK001, y notas que indiquen que `/speckit-implement` lee el estado del checklist pero no modifica los marcadores.

8. **Informe**: Mostrá la ruta completa del archivo de checklist, la cantidad de ítems, y resumí si la ejecución creó un archivo nuevo o agregó a uno existente. Resumí:
   - Áreas de enfoque seleccionadas
   - Nivel de profundidad
   - Actor/momento
   - Cualquier ítem imprescindible especificado explícitamente por el usuario que se haya incorporado

**Importante**: Cada invocación del comando `/speckit-checklist` usa un nombre de archivo de checklist corto y descriptivo y, o bien crea un archivo nuevo, o bien agrega a uno existente. Esto permite:

- Varios checklists de distintos tipos (p. ej., `ux.md`, `test.md`, `security.md`)
- Nombres de archivo simples y fáciles de recordar que indican el propósito del checklist
- Identificación y navegación sencillas en la carpeta `checklists/`

Para evitar el desorden, usá tipos descriptivos y limpiá los checklists obsoletos cuando terminés.

## Tipos de checklist de ejemplo e ítems de muestra

**Calidad de los requisitos de UX:** `ux.md`

Ítems de muestra (prueban los requisitos, NO la implementación):

- "¿Están definidos los requisitos de jerarquía visual con criterios medibles? [Claridad, Spec §FR-1]"
- "¿Están especificados de forma explícita la cantidad y la posición de los elementos de UI? [Completitud, Spec §FR-1]"
- "¿Están definidos de forma consistente los requisitos de estados de interacción (hover, focus, active)? [Consistencia]"
- "¿Están especificados los requisitos de accesibilidad para todos los elementos interactivos? [Cobertura, Brecha]"
- "¿Está definido el comportamiento alternativo cuando fallan las imágenes al cargar? [Caso límite, Brecha]"
- "¿Se puede medir de forma objetiva la 'visualización destacada'? [Medibilidad, Spec §FR-4]"

**Calidad de los requisitos de API:** `api.md`

Ítems de muestra:

- "¿Están especificados los formatos de respuesta de error para todos los escenarios de falla? [Completitud]"
- "¿Están cuantificados los requisitos de limitación de tasa con umbrales específicos? [Claridad]"
- "¿Son consistentes los requisitos de autenticación en todos los endpoints? [Consistencia]"
- "¿Están definidos los requisitos de reintento/timeout para las dependencias externas? [Cobertura, Brecha]"
- "¿Está documentada en los requisitos la estrategia de versionado? [Brecha]"

**Calidad de los requisitos de rendimiento:** `performance.md`

Ítems de muestra:

- "¿Están cuantificados los requisitos de rendimiento con métricas específicas? [Claridad]"
- "¿Están definidos los objetivos de rendimiento para todos los recorridos críticos del usuario? [Cobertura]"
- "¿Están especificados los requisitos de rendimiento bajo distintas condiciones de carga? [Completitud]"
- "¿Se pueden medir de forma objetiva los requisitos de rendimiento? [Medibilidad]"
- "¿Están definidos los requisitos de degradación para escenarios de carga alta? [Caso límite, Brecha]"

**Calidad de los requisitos de seguridad:** `security.md`

Ítems de muestra:

- "¿Están especificados los requisitos de autenticación para todos los recursos protegidos? [Cobertura]"
- "¿Están definidos los requisitos de protección de datos para la información sensible? [Completitud]"
- "¿Está documentado el modelo de amenazas y alineados los requisitos con él? [Trazabilidad]"
- "¿Son consistentes los requisitos de seguridad con las obligaciones de cumplimiento? [Consistencia]"
- "¿Están definidos los requisitos de respuesta ante fallas/brechas de seguridad? [Brecha, Flujo de excepción]"

## Antiejemplos: qué NO hacer

**❌ INCORRECTO: estos prueban la implementación, no los requisitos:**

```markdown
- [ ] CHK001 - Verificar que la página de inicio muestre 3 tarjetas de episodios [Spec §FR-001]
- [ ] CHK002 - Probar que los estados hover funcionen correctamente en escritorio [Spec §FR-003]
- [ ] CHK003 - Confirmar que el clic en el logo navegue a la página de inicio [Spec §FR-010]
- [ ] CHK004 - Comprobar que la sección de episodios relacionados muestre de 3 a 5 ítems [Spec §FR-005]
```

**✅ CORRECTO: estos prueban la calidad de los requisitos:**

```markdown
- [ ] CHK001 - ¿Están especificados de forma explícita la cantidad y la disposición de los episodios destacados? [Completitud, Spec §FR-001]
- [ ] CHK002 - ¿Están definidos de forma consistente los requisitos del estado hover para todos los elementos interactivos? [Consistencia, Spec §FR-003]
- [ ] CHK003 - ¿Son claros los requisitos de navegación para todos los elementos de marca en los que se puede hacer clic? [Claridad, Spec §FR-010]
- [ ] CHK004 - ¿Están documentados los criterios de selección de los episodios relacionados? [Brecha, Spec §FR-005]
- [ ] CHK005 - ¿Están definidos los requisitos de los estados de carga para los datos asíncronos de episodios? [Brecha]
- [ ] CHK006 - ¿Se pueden medir de forma objetiva los requisitos de "jerarquía visual"? [Medibilidad, Spec §FR-001]
```

**Diferencias clave:**

- Incorrecto: Prueba si el sistema funciona correctamente
- Correcto: Prueba si los requisitos están bien escritos
- Incorrecto: Verificación del comportamiento
- Correcto: Validación de la calidad de los requisitos
- Incorrecto: "¿Hace X?"
- Correcto: "¿Está X claramente especificado?"

## Verificaciones posteriores a la ejecución

**Buscar hooks de extensión (después de generar el checklist)**:
Verificá si existe `.specify/extensions.yml` en la raíz del proyecto.
- Si existe, leelo y buscá las entradas bajo la clave `hooks.after_checklist`
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

