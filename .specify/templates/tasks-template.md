---

description: "Plantilla de lista de tareas para la implementación de una funcionalidad"
---

# Tareas: [NOMBRE DE LA FUNCIONALIDAD]

**Entrada**: Documentos de diseño en `/specs/[###-nombre-de-la-funcionalidad]/`

**Prerrequisitos**: plan.md (obligatorio), spec.md (obligatorio para las historias de usuario), research.md, data-model.md, contracts/

**Pruebas**: Los ejemplos de abajo incluyen tareas de prueba. Las pruebas son OPCIONALES: incluilas solo si la especificación de la funcionalidad las pide de forma explícita.

**Organización**: Las tareas se agrupan por historia de usuario para permitir implementar y probar cada historia de forma independiente.

## Formato: `[ID] [P?] [Historia] Descripción`

- **[P]**: Se puede ejecutar en paralelo (archivos distintos, sin dependencias)
- **[Historia]**: A qué historia de usuario pertenece la tarea (ej.: US1, US2, US3)
- Incluir las rutas exactas de los archivos en las descripciones

## Convenciones de rutas

- **Proyecto único**: `src/`, `tests/` en la raíz del repositorio
- **Aplicación web**: `backend/src/`, `frontend/src/`
- **Móvil**: `api/src/`, `ios/src/` o `android/src/`
- Las rutas de abajo asumen un proyecto único: ajustalas según la estructura de plan.md

<!--
  ============================================================================
  IMPORTANTE: Las tareas de abajo son TAREAS DE EJEMPLO, solo con fines ilustrativos.

  El comando /speckit-tasks DEBE reemplazarlas por tareas reales basadas en:
  - Las historias de usuario de spec.md (con sus prioridades P1, P2, P3...)
  - Los requisitos de la funcionalidad en plan.md
  - Las entidades de data-model.md
  - Los endpoints de contracts/

  Las tareas DEBEN organizarse por historia de usuario para que cada historia pueda:
  - Implementarse de forma independiente
  - Probarse de forma independiente
  - Entregarse como un incremento de MVP

  NO conserves estas tareas de ejemplo en el archivo tasks.md generado.
  ============================================================================
-->

## Fase 1: Preparación (infraestructura compartida)

**Propósito**: Inicialización del proyecto y estructura básica

- [ ] T001 Crear la estructura del proyecto según el plan de implementación
- [ ] T002 Inicializar el proyecto de [lenguaje] con las dependencias de [framework]
- [ ] T003 [P] Configurar las herramientas de lint y formato

---

## Fase 2: Fundamentos (prerrequisitos bloqueantes)

**Propósito**: Infraestructura central que DEBE estar completa antes de poder implementar CUALQUIER historia de usuario

**⚠️ CRÍTICO**: No se puede empezar ninguna historia de usuario hasta completar esta fase

Ejemplos de tareas de fundamentos (ajustalas según tu proyecto):

- [ ] T004 Configurar el esquema de base de datos y el framework de migraciones
- [ ] T005 [P] Implementar el framework de autenticación/autorización
- [ ] T006 [P] Configurar el enrutamiento de la API y la estructura de middleware
- [ ] T007 Crear los modelos/entidades base de los que dependen todas las historias
- [ ] T008 Configurar el manejo de errores y la infraestructura de logging
- [ ] T009 Configurar la gestión de la configuración del entorno

**Punto de control**: Fundamentos listos: ya se puede empezar a implementar las historias de usuario en paralelo

---

## Fase 3: Historia de usuario 1 - [Título] (Prioridad: P1) 🎯 MVP

**Objetivo**: [Descripción breve de lo que entrega esta historia]

**Prueba independiente**: [Cómo verificar que esta historia funciona por sí sola]

### Pruebas de la historia de usuario 1 (OPCIONAL: solo si se pidieron pruebas) ⚠️

> **NOTA: Escribí estas pruebas PRIMERO y asegurate de que FALLEN antes de implementar**

- [ ] T010 [P] [US1] Prueba de contrato para [endpoint] en tests/contract/test_[nombre].py
- [ ] T011 [P] [US1] Prueba de integración para [recorrido de usuario] en tests/integration/test_[nombre].py

### Implementación de la historia de usuario 1

- [ ] T012 [P] [US1] Crear el modelo [Entidad1] en src/models/[entidad1].py
- [ ] T013 [P] [US1] Crear el modelo [Entidad2] en src/models/[entidad2].py
- [ ] T014 [US1] Implementar [Servicio] en src/services/[servicio].py (depende de T012, T013)
- [ ] T015 [US1] Implementar [endpoint/funcionalidad] en src/[ubicación]/[archivo].py
- [ ] T016 [US1] Agregar validación y manejo de errores
- [ ] T017 [US1] Agregar logging para las operaciones de la historia de usuario 1

**Punto de control**: En este punto, la historia de usuario 1 debe ser totalmente funcional y probable de forma independiente

---

## Fase 4: Historia de usuario 2 - [Título] (Prioridad: P2)

**Objetivo**: [Descripción breve de lo que entrega esta historia]

**Prueba independiente**: [Cómo verificar que esta historia funciona por sí sola]

### Pruebas de la historia de usuario 2 (OPCIONAL: solo si se pidieron pruebas) ⚠️

- [ ] T018 [P] [US2] Prueba de contrato para [endpoint] en tests/contract/test_[nombre].py
- [ ] T019 [P] [US2] Prueba de integración para [recorrido de usuario] en tests/integration/test_[nombre].py

### Implementación de la historia de usuario 2

- [ ] T020 [P] [US2] Crear el modelo [Entidad] en src/models/[entidad].py
- [ ] T021 [US2] Implementar [Servicio] en src/services/[servicio].py
- [ ] T022 [US2] Implementar [endpoint/funcionalidad] en src/[ubicación]/[archivo].py
- [ ] T023 [US2] Integrar con los componentes de la historia de usuario 1 (si hace falta)

**Punto de control**: En este punto, las historias de usuario 1 Y 2 deben funcionar de forma independiente

---

## Fase 5: Historia de usuario 3 - [Título] (Prioridad: P3)

**Objetivo**: [Descripción breve de lo que entrega esta historia]

**Prueba independiente**: [Cómo verificar que esta historia funciona por sí sola]

### Pruebas de la historia de usuario 3 (OPCIONAL: solo si se pidieron pruebas) ⚠️

- [ ] T024 [P] [US3] Prueba de contrato para [endpoint] en tests/contract/test_[nombre].py
- [ ] T025 [P] [US3] Prueba de integración para [recorrido de usuario] en tests/integration/test_[nombre].py

### Implementación de la historia de usuario 3

- [ ] T026 [P] [US3] Crear el modelo [Entidad] en src/models/[entidad].py
- [ ] T027 [US3] Implementar [Servicio] en src/services/[servicio].py
- [ ] T028 [US3] Implementar [endpoint/funcionalidad] en src/[ubicación]/[archivo].py

**Punto de control**: Todas las historias de usuario deben funcionar ahora de forma independiente

---

[Agregá más fases de historias de usuario según haga falta, siguiendo el mismo patrón]

---

## Fase N: Pulido y aspectos transversales

**Propósito**: Mejoras que afectan a varias historias de usuario

- [ ] TXXX [P] Actualizaciones de documentación en docs/
- [ ] TXXX Limpieza y refactorización del código
- [ ] TXXX Optimización de rendimiento en todas las historias
- [ ] TXXX [P] Pruebas unitarias adicionales (si se piden) en tests/unit/
- [ ] TXXX Refuerzo de seguridad
- [ ] TXXX Ejecutar la validación de quickstart.md

---

## Dependencias y orden de ejecución

### Dependencias entre fases

- **Preparación (Fase 1)**: Sin dependencias: se puede empezar de inmediato
- **Fundamentos (Fase 2)**: Depende de completar la Preparación: BLOQUEA todas las historias de usuario
- **Historias de usuario (Fase 3+)**: Todas dependen de completar la fase de Fundamentos
  - Luego las historias pueden avanzar en paralelo (si hay personas disponibles)
  - O en secuencia, por orden de prioridad (P1 → P2 → P3)
- **Pulido (fase final)**: Depende de que estén completas todas las historias de usuario deseadas

### Dependencias entre historias de usuario

- **Historia de usuario 1 (P1)**: Puede empezar después de Fundamentos (Fase 2); no depende de otras historias
- **Historia de usuario 2 (P2)**: Puede empezar después de Fundamentos (Fase 2); puede integrarse con US1 pero debe ser probable de forma independiente
- **Historia de usuario 3 (P3)**: Puede empezar después de Fundamentos (Fase 2); puede integrarse con US1/US2 pero debe ser probable de forma independiente

### Dentro de cada historia de usuario

- Las pruebas (si se incluyen) DEBEN escribirse y FALLAR antes de implementar
- Modelos antes que servicios
- Servicios antes que endpoints
- Implementación central antes que integración
- Completar la historia antes de pasar a la siguiente prioridad

### Oportunidades de paralelismo

- Todas las tareas de Preparación marcadas [P] pueden ejecutarse en paralelo
- Todas las tareas de Fundamentos marcadas [P] pueden ejecutarse en paralelo (dentro de la Fase 2)
- Una vez completada la fase de Fundamentos, todas las historias de usuario pueden empezar en paralelo (si la capacidad del equipo lo permite)
- Todas las pruebas de una historia de usuario marcadas [P] pueden ejecutarse en paralelo
- Los modelos dentro de una historia marcados [P] pueden ejecutarse en paralelo
- Distintas historias de usuario pueden ser trabajadas en paralelo por distintos integrantes del equipo

---

## Ejemplo de paralelismo: historia de usuario 1

```bash
# Lanzar juntas todas las pruebas de la historia de usuario 1 (si se pidieron pruebas):
Task: "Prueba de contrato para [endpoint] en tests/contract/test_[nombre].py"
Task: "Prueba de integración para [recorrido de usuario] en tests/integration/test_[nombre].py"

# Lanzar juntos todos los modelos de la historia de usuario 1:
Task: "Crear el modelo [Entidad1] en src/models/[entidad1].py"
Task: "Crear el modelo [Entidad2] en src/models/[entidad2].py"
```

---

## Estrategia de implementación

### Primero el MVP (solo la historia de usuario 1)

1. Completar la Fase 1: Preparación
2. Completar la Fase 2: Fundamentos (CRÍTICO: bloquea todas las historias)
3. Completar la Fase 3: Historia de usuario 1
4. **DETENERSE y VALIDAR**: probar la historia de usuario 1 de forma independiente
5. Desplegar/mostrar si está lista

### Entrega incremental

1. Completar Preparación + Fundamentos → Base lista
2. Agregar la historia de usuario 1 → Probar de forma independiente → Desplegar/mostrar (¡MVP!)
3. Agregar la historia de usuario 2 → Probar de forma independiente → Desplegar/mostrar
4. Agregar la historia de usuario 3 → Probar de forma independiente → Desplegar/mostrar
5. Cada historia aporta valor sin romper las anteriores

### Estrategia de equipo en paralelo

Con varios desarrolladores:

1. El equipo completa juntos Preparación + Fundamentos
2. Una vez terminados los Fundamentos:
   - Desarrollador A: historia de usuario 1
   - Desarrollador B: historia de usuario 2
   - Desarrollador C: historia de usuario 3
3. Las historias se completan e integran de forma independiente

---

## Notas

- Tareas [P] = archivos distintos, sin dependencias
- La etiqueta [Historia] asocia la tarea a una historia de usuario específica para la trazabilidad
- Cada historia de usuario debe poder completarse y probarse de forma independiente
- Verificá que las pruebas fallen antes de implementar
- Hacé commit después de cada tarea o grupo lógico
- Detenete en cualquier punto de control para validar la historia de forma independiente
- Evitá: tareas vagas, conflictos por editar el mismo archivo, dependencias entre historias que rompan la independencia
