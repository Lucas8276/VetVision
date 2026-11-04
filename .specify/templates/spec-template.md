# Especificación de la funcionalidad: [NOMBRE DE LA FUNCIONALIDAD]

**Rama de la funcionalidad**: `[###-nombre-de-la-funcionalidad]`

**Creada**: [FECHA]

**Estado**: Borrador

**Entrada**: Descripción del usuario: "$ARGUMENTS"

## Escenarios de usuario y pruebas *(obligatorio)*

<!--
  IMPORTANTE: Las historias de usuario deben PRIORIZARSE como recorridos de usuario ordenados por importancia.
  Cada historia/recorrido debe ser PROBABLE DE FORMA INDEPENDIENTE: si se implementa solo UNA de ellas,
  debe seguir existiendo un MVP (Producto Mínimo Viable) que aporte valor.

  Asigná prioridades (P1, P2, P3, etc.) a cada historia, donde P1 es la más crítica.
  Pensá cada historia como una porción de funcionalidad autónoma que se puede:
  - Desarrollar de forma independiente
  - Probar de forma independiente
  - Desplegar de forma independiente
  - Demostrar a los usuarios de forma independiente
-->

### Historia de usuario 1 - [Título breve] (Prioridad: P1)

[Describí este recorrido de usuario en lenguaje simple]

**Por qué esta prioridad**: [Explicá el valor y por qué tiene este nivel de prioridad]

**Prueba independiente**: [Describí cómo se puede probar de forma independiente. Ej.: "Se puede probar por completo con [acción concreta] y entrega [valor concreto]"]

**Escenarios de aceptación**:

1. **Dado** [estado inicial], **Cuando** [acción], **Entonces** [resultado esperado]
2. **Dado** [estado inicial], **Cuando** [acción], **Entonces** [resultado esperado]

---

### Historia de usuario 2 - [Título breve] (Prioridad: P2)

[Describí este recorrido de usuario en lenguaje simple]

**Por qué esta prioridad**: [Explicá el valor y por qué tiene este nivel de prioridad]

**Prueba independiente**: [Describí cómo se puede probar de forma independiente]

**Escenarios de aceptación**:

1. **Dado** [estado inicial], **Cuando** [acción], **Entonces** [resultado esperado]

---

### Historia de usuario 3 - [Título breve] (Prioridad: P3)

[Describí este recorrido de usuario en lenguaje simple]

**Por qué esta prioridad**: [Explicá el valor y por qué tiene este nivel de prioridad]

**Prueba independiente**: [Describí cómo se puede probar de forma independiente]

**Escenarios de aceptación**:

1. **Dado** [estado inicial], **Cuando** [acción], **Entonces** [resultado esperado]

---

[Agregá más historias de usuario según haga falta, cada una con su prioridad]

### Casos límite

<!--
  ACCIÓN REQUERIDA: El contenido de esta sección son marcadores de posición.
  Completalos con los casos límite que correspondan.
-->

- ¿Qué pasa cuando [condición de borde]?
- ¿Cómo maneja el sistema [escenario de error]?

## Requisitos *(obligatorio)*

<!--
  ACCIÓN REQUERIDA: El contenido de esta sección son marcadores de posición.
  Completalos con los requisitos funcionales que correspondan.
-->

### Requisitos funcionales

- **FR-001**: El sistema DEBE [capacidad específica, ej.: "permitir a los usuarios crear cuentas"]
- **FR-002**: El sistema DEBE [capacidad específica, ej.: "validar direcciones de correo"]
- **FR-003**: Los usuarios DEBEN poder [interacción clave, ej.: "restablecer su contraseña"]
- **FR-004**: El sistema DEBE [requisito de datos, ej.: "conservar las preferencias del usuario"]
- **FR-005**: El sistema DEBE [comportamiento, ej.: "registrar todos los eventos de seguridad"]

*Ejemplo de cómo marcar requisitos poco claros (el marcador `[NEEDS CLARIFICATION: ...]` se mantiene en inglés porque los skills de spec-kit lo buscan literalmente):*

- **FR-006**: El sistema DEBE autenticar a los usuarios mediante [NEEDS CLARIFICATION: método de autenticación no especificado: ¿correo/contraseña, SSO, OAuth?]
- **FR-007**: El sistema DEBE conservar los datos del usuario durante [NEEDS CLARIFICATION: período de retención no especificado]

### Entidades clave *(incluir si la funcionalidad involucra datos)*

- **[Entidad 1]**: [Qué representa, atributos clave sin detalles de implementación]
- **[Entidad 2]**: [Qué representa, relaciones con otras entidades]

## Criterios de éxito *(obligatorio)*

<!--
  ACCIÓN REQUERIDA: Definí criterios de éxito medibles.
  Deben ser independientes de la tecnología y medibles.
-->

### Resultados medibles

- **SC-001**: [Métrica medible, ej.: "Los usuarios pueden completar la creación de una cuenta en menos de 2 minutos"]
- **SC-002**: [Métrica medible, ej.: "El sistema soporta 1000 usuarios concurrentes sin degradarse"]
- **SC-003**: [Métrica de satisfacción, ej.: "El 90 % de los usuarios completa la tarea principal al primer intento"]
- **SC-004**: [Métrica de negocio, ej.: "Reducir en un 50 % los tickets de soporte relacionados con [X]"]

## Supuestos

<!--
  ACCIÓN REQUERIDA: El contenido de esta sección son marcadores de posición.
  Completalos con los supuestos que correspondan, basados en valores por defecto razonables
  elegidos cuando la descripción de la funcionalidad no especificaba ciertos detalles.
-->

- [Supuesto sobre los usuarios objetivo, ej.: "Los usuarios tienen conexión a internet estable"]
- [Supuesto sobre los límites del alcance, ej.: "El soporte móvil queda fuera del alcance de la v1"]
- [Supuesto sobre datos/entorno, ej.: "Se reutilizará el sistema de autenticación existente"]
- [Dependencia de un sistema/servicio existente, ej.: "Requiere acceso a la API de perfiles de usuario existente"]
