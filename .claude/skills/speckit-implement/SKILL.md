---
name: "speckit-implement"
description: "Ejecuta el plan de implementación procesando y ejecutando todas las tareas definidas en tasks.md"
argument-hint: "Orientación opcional de implementación o filtro de tareas"
compatibility: "Requiere la estructura de proyecto de spec-kit con el directorio .specify/"
metadata:
  author: "github-spec-kit"
  source: "templates/commands/implement.md"
user-invocable: true
disable-model-invocation: false
---


## Entrada del usuario

```text
$ARGUMENTS
```

**DEBES** considerar la entrada del usuario antes de continuar (si no está vacía).

## Verificaciones previas a la ejecución

**Buscar hooks de extensión (antes de implementar)**:
- Verificá si existe `.specify/extensions.yml` en la raíz del proyecto.
- Si existe, leelo y buscá las entradas bajo la clave `hooks.before_implement`
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

2. **Verificar el estado de los checklists** (si existe FEATURE_DIR/checklists/):
   - Tratá los marcadores de los checklists como una puerta de solo lectura: escaneá el estado de las casillas, informá el estado y preguntá antes de continuar cuando haga falta; NO modifiques los archivos de checklist ni sus marcadores
   - `checklists/requirements.md` es el checklist integrado de calidad de la spec, mantenido por `/speckit-specify` y `/speckit-clarify`; los checklists personalizados generados por `/speckit-checklist` son artefactos de revisión de la calidad de los requisitos, a cargo de quien revisa
   - En los checklists personalizados, `[x]` significa que quien revisa determinó que se cumple el criterio de calidad del requisito; NO significa que el trabajo de implementación esté terminado
   - Escaneá todos los archivos de checklist del directorio checklists/
   - Por cada checklist, contá:
     - Ítems totales: todas las líneas que coincidan con `- [ ]` o `- [X]` o `- [x]`
     - Ítems marcados: líneas que coincidan con `- [X]` o `- [x]`
     - Ítems sin marcar: líneas que coincidan con `- [ ]`
   - Creá una tabla de estado:

     ```text
     | Checklist | Total | Marcados | Sin marcar | Estado |
     |-----------|-------|----------|------------|--------|
     | ux.md     | 12    | 12       | 0          | ✓ OK   |
     | test.md   | 8     | 5        | 3          | ✗ FALLA |
     | security.md | 6   | 6        | 0          | ✓ OK   |
     ```

   - Calculá el estado general:
     - **OK**: todos los checklists tienen 0 ítems sin marcar
     - **FALLA**: uno o más checklists tienen ítems sin marcar

   - **Si algún checklist tiene ítems sin marcar**:
     - Mostrá la tabla con la cantidad de ítems sin marcar
     - **DETENETE** y preguntá: "Algunos checklists tienen ítems sin marcar. ¿Querés continuar con la implementación de todos modos? (sí/no)"
     - Esperá la respuesta del usuario antes de continuar
     - Si el usuario dice "no", "esperá" o "pará", detené la ejecución
     - Si el usuario dice "sí", "adelante" o "continuá", pasá al paso 3

   - **Si todos los checklists están marcados**:
     - Mostrá la tabla indicando que todos los checklists se aprobaron
     - Pasá automáticamente al paso 3

3. Cargá y analizá el contexto de implementación:
   - **OBLIGATORIO**: Leé tasks.md para obtener la lista completa de tareas y el plan de ejecución
   - **OBLIGATORIO**: Leé plan.md para conocer el stack técnico, la arquitectura y la estructura de archivos
   - **SI EXISTE**: Leé data-model.md para las entidades y relaciones
   - **SI EXISTE**: Leé contracts/ para las especificaciones de API y los requisitos de pruebas
   - **SI EXISTE**: Leé research.md para las decisiones técnicas y las restricciones
   - **SI EXISTE**: Leé .specify/memory/constitution.md para las restricciones de gobernanza
   - **SI EXISTE**: Leé quickstart.md para los escenarios de integración

4. **Verificación de la preparación del proyecto**:
   - **OBLIGATORIO**: Creá/verificá los archivos de ignore según la configuración real del proyecto:

   **Lógica de detección y creación**:
   - Verificá si el siguiente comando tiene éxito para determinar si el repositorio es un repo de git (si lo es, creá/verificá .gitignore):

     ```sh
     git rev-parse --git-dir 2>/dev/null
     ```

   - Si existe Dockerfile* o hay Docker en plan.md → creá/verificá .dockerignore
   - Si existe .eslintrc* → creá/verificá .eslintignore
   - Si existe eslint.config.* → asegurá que las entradas `ignores` de la configuración cubran los patrones requeridos
   - Si existe .prettierrc* → creá/verificá .prettierignore
   - Si existe .npmrc o package.json → creá/verificá .npmignore (si se va a publicar)
   - Si existen archivos de terraform (*.tf) → creá/verificá .terraformignore
   - Si hace falta .helmignore (hay charts de helm) → creá/verificá .helmignore

   **Si el archivo de ignore ya existe**: Verificá que contenga los patrones esenciales y agregá solo los patrones críticos que falten
   **Si el archivo de ignore no existe**: Crealo con el conjunto completo de patrones para la tecnología detectada

   **Patrones comunes por tecnología** (según el stack técnico de plan.md):
   - **Node.js/JavaScript/TypeScript**: `node_modules/`, `dist/`, `build/`, `*.log`, `.env*`
   - **Python**: `__pycache__/`, `*.pyc`, `.venv/`, `venv/`, `dist/`, `*.egg-info/`
   - **Java**: `target/`, `*.class`, `*.jar`, `.gradle/`, `build/`
   - **C#/.NET**: `bin/`, `obj/`, `*.user`, `*.suo`, `packages/`
   - **Go**: `*.exe`, `*.test`, `vendor/`, `*.out`
   - **Ruby**: `.bundle/`, `log/`, `tmp/`, `*.gem`, `vendor/bundle/`
   - **PHP**: `vendor/`, `*.log`, `*.cache`, `*.env`
   - **Rust**: `target/`, `debug/`, `release/`, `*.rs.bk`, `*.rlib`, `*.prof*`, `.idea/`, `*.log`, `.env*`
   - **Kotlin**: `build/`, `out/`, `.gradle/`, `.idea/`, `*.class`, `*.jar`, `*.iml`, `*.log`, `.env*`
   - **C++**: `build/`, `bin/`, `obj/`, `out/`, `*.o`, `*.so`, `*.a`, `*.exe`, `*.dll`, `.idea/`, `*.log`, `.env*`
   - **C**: `build/`, `bin/`, `obj/`, `out/`, `*.o`, `*.a`, `*.so`, `*.exe`, `*.dll`, `autom4te.cache/`, `config.status`, `config.log`, `.idea/`, `*.log`, `.env*`
   - **Swift**: `.build/`, `DerivedData/`, `*.swiftpm/`, `Packages/`
   - **R**: `.Rproj.user/`, `.Rhistory`, `.RData`, `.Ruserdata`, `*.Rproj`, `packrat/`, `renv/`
   - **Universales**: `.DS_Store`, `Thumbs.db`, `*.tmp`, `*.swp`, `.vscode/`, `.idea/`

   **Patrones específicos de herramientas**:
   - **Docker**: `node_modules/`, `.git/`, `Dockerfile*`, `.dockerignore`, `*.log*`, `.env*`, `coverage/`
   - **ESLint**: `node_modules/`, `dist/`, `build/`, `coverage/`, `*.min.js`
   - **Prettier**: `node_modules/`, `dist/`, `build/`, `coverage/`, `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`
   - **Terraform**: `.terraform/`, `*.tfstate*`, `*.tfvars`, `.terraform.lock.hcl`
   - **Kubernetes/k8s**: `*.secret.yaml`, `secrets/`, `.kube/`, `kubeconfig*`, `*.key`, `*.crt`

5. Parseá la estructura de tasks.md y extraé:
   - **Fases de tareas**: Preparación, Pruebas, Núcleo, Integración, Pulido
   - **Dependencias entre tareas**: reglas de ejecución secuencial vs. paralela
   - **Detalles de las tareas**: ID, descripción, rutas de archivo, marcadores de paralelismo [P]
   - **Flujo de ejecución**: orden y requisitos de dependencia

6. Ejecutá la implementación siguiendo el plan de tareas:
   - **Ejecución fase por fase**: completá cada fase antes de pasar a la siguiente
   - **Respetá las dependencias**: ejecutá las tareas secuenciales en orden; las tareas paralelas [P] pueden ejecutarse juntas
   - **Seguí el enfoque TDD**: ejecutá las tareas de prueba antes de las tareas de implementación que les corresponden
   - **Coordinación por archivo**: las tareas que afectan los mismos archivos deben ejecutarse en secuencia
   - **Puntos de validación**: verificá que cada fase esté completa antes de continuar

7. Reglas de ejecución de la implementación:
   - **Primero la preparación**: inicializá la estructura del proyecto, las dependencias y la configuración
   - **Pruebas antes que el código**: si hace falta escribir pruebas para contratos, entidades y escenarios de integración
   - **Desarrollo central**: implementá modelos, servicios, comandos de CLI, endpoints
   - **Trabajo de integración**: conexiones a bases de datos, middleware, logging, servicios externos
   - **Pulido y validación**: pruebas unitarias, optimización de rendimiento, documentación

8. Seguimiento del progreso y manejo de errores:
   - Informá el progreso después de cada tarea completada
   - Detené la ejecución si falla cualquier tarea no paralela
   - En las tareas paralelas [P], continuá con las que tuvieron éxito e informá las que fallaron
   - Dá mensajes de error claros, con contexto para depurar
   - Sugerí los próximos pasos si la implementación no puede continuar
   - **IMPORTANTE** En las tareas completadas, asegurate de marcarlas como [X] en el archivo de tareas.

9. Validación de la finalización:
   - Verificá que todas las tareas requeridas estén completas
   - Comprobá que las funcionalidades implementadas coincidan con la especificación original
   - Validá que las pruebas pasen y que la cobertura cumpla los requisitos
   - Confirmá que la implementación sigue el plan técnico

Nota: Este comando asume que existe en tasks.md un desglose completo de tareas. Si las tareas están incompletas o faltan, sugerí ejecutar primero `/speckit-tasks` para regenerar la lista de tareas.

## Hooks posteriores a la ejecución (obligatorios)

**DEBES completar esta sección antes de informar la finalización al usuario.**

Verificá si existe `.specify/extensions.yml` en la raíz del proyecto.
- Si no existe, o no hay hooks registrados bajo `hooks.after_implement`, pasá directo al Informe de finalización.
- Si existe, leelo y buscá las entradas bajo la clave `hooks.after_implement`.
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

Informá el estado final con un resumen del trabajo completado.

## Terminado cuando

- [ ] Todas las tareas de tasks.md están completas y marcadas con `[X]`
- [ ] La implementación se validó contra la especificación, el plan y la cobertura de pruebas
- [ ] Los hooks de extensión se despacharon u omitieron según las reglas de Hooks posteriores a la ejecución (obligatorios) de arriba
- [ ] Se informó la finalización al usuario con un resumen del trabajo completado
