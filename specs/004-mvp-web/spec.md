# Feature Specification: MVP web de VetVision AI

**Feature Branch**: `004-mvp-web`
**Created**: 2026-11-17
**Status**: Draft (versión abreviada; a revisar por el equipo antes de implementar)
**Input**: el documento del proyecto compromete un MVP con carga de radiografía, ejecución del modelo,
borrador de hallazgos con nivel de confianza y descargo, validación / corrección / descarte por el
veterinario y consulta de los estudios procesados. Hoy existe una demo de una sola pantalla
(`server.py` + `VetVision Demo.dc.html`) que solo devuelve TÓRAX / NO TÓRAX y no guarda nada.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Cargar una radiografía y recibir un borrador (Priority: P1)

Como veterinario, cargo una radiografía de tórax de un perro y en segundos veo un borrador: qué región
detectó el sistema, qué hallazgos propone, con qué nivel de confianza, y la advertencia de que no es un
diagnóstico.

**Why this priority**: es la entrada de todo el flujo; sin esto no hay nada que validar ni consultar.

**Independent Test**: cargar una imagen sintética válida y verificar que se crea un estudio con su
borrador; cargar archivos inválidos y verificar cada rechazo.

**Acceptance Scenarios**:

1. **Given** un JPG o PNG válido, **When** lo cargo, **Then** se crea un estudio y veo el borrador con
   la región detectada, la lista de hallazgos con su nivel de confianza y el descargo.
2. **Given** un archivo que no es una imagen, está corrupto o supera el tamaño máximo, **When** lo
   cargo, **Then** no se crea ningún estudio y veo, junto al campo, qué falló y cómo resolverlo.
3. **Given** una imagen que la puerta de región clasifica como "no tórax", **When** veo el borrador,
   **Then** el sistema me avisa y me deja continuar igual: la puerta se equivoca en parte de las placas
   de tórax (sensibilidad medida: 88,3 %), así que avisa pero no bloquea.
4. **Given** que no hay un modelo de hallazgos disponible, **When** veo el borrador, **Then** el sistema
   lo dice con claridad y puedo cargar hallazgos a mano.

### User Story 2 - Validar, corregir o descartar cada hallazgo (Priority: P1)

Como veterinario matriculado, reviso cada hallazgo propuesto y lo valido, lo corrijo o lo descarto;
también puedo agregar uno que el sistema no propuso. Recién cuando resolví todos, cierro el informe.

**Why this priority**: es lo que hace del sistema un apoyo y no un reemplazo del criterio profesional.

**Independent Test**: sobre un estudio con hallazgos, aplicar las tres acciones, cerrar el informe,
reabrir el estudio y comprobar que todo quedó guardado.

**Acceptance Scenarios**:

1. **Given** un hallazgo pendiente, **When** lo valido, corrijo (cambio de tipo o comentario) o
   descarto, **Then** su estado cambia, se guarda con fecha y hora, y lo veo igual al reabrir.
2. **Given** hallazgos todavía pendientes, **When** intento cerrar el informe, **Then** el sistema no lo
   permite y me señala cuáles faltan.
3. **Given** un informe cerrado, **When** lo abro, **Then** veo qué propuso el sistema y qué decidió el
   veterinario, por separado.

### User Story 3 - Consultar los estudios procesados (Priority: P1)

Como veterinario, veo el listado de estudios con su fecha, resultado y estado, filtro por estado y abro
cualquiera.

**Independent Test**: con varios estudios en distintos estados, el listado los muestra ordenados por
fecha, el filtro funciona y cada fila abre su detalle.

### User Story 4 - Ver dónde miró el modelo (Priority: P2)

Como veterinario, puedo superponer a la radiografía un mapa de calor de la zona que más pesó en la
predicción, para decidir si confío en ella.

### Edge Cases

- Dos cargas de la misma imagen: se crean dos estudios y el segundo avisa que es un duplicado.
- El modelo no está en disco o falla al cargar: la aplicación arranca, lo informa y sigue sirviendo el
  listado; la carga explica por qué no puede procesar.
- Confianza baja: el hallazgo se muestra igual, marcado como "confianza baja".
- Especie distinta de canino: se permite, con el aviso de que queda fuera del alcance evaluado.
- Cierre del navegador a mitad de la validación: lo ya decidido quedó guardado.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema DEBE aceptar una imagen JPG o PNG por estudio y validar el contenido (no la
  extensión): tipo real, que se pueda decodificar, tamaño máximo y dimensiones mínimas configurables.
- **FR-002**: El sistema DEBE ejecutar siempre la puerta de región (Etapa 0) y mostrar su resultado
  como aviso, nunca como bloqueo.
- **FR-003**: El sistema DEBE obtener los hallazgos de los modelos registrados como disponibles. Agregar
  un modelo nuevo (Etapa 1, Etapa 2) NO DEBE requerir cambios en la interfaz ni en el almacenamiento.
- **FR-004**: Cada hallazgo DEBE mostrar su tipo, su confianza numérica y un nivel (alta, media, baja)
  cuyos cortes salen de la calibración medida del modelo, no de un valor arbitrario.
- **FR-005**: El descargo de que el resultado es un borrador de apoyo y no un diagnóstico definitivo DEBE
  estar visible en el borrador, en el informe cerrado y en el listado.
- **FR-006**: El veterinario DEBE poder validar, corregir o descartar cada hallazgo, agregar hallazgos
  manuales y dejar un comentario; cada decisión se guarda con fecha y hora.
- **FR-007**: Un informe solo DEBE poder cerrarse cuando no quedan hallazgos pendientes.
- **FR-008**: El sistema DEBE listar los estudios con fecha de carga, resultado, estado y filtro por
  estado, y abrir el detalle de cada uno.
- **FR-009**: Los estudios, hallazgos y decisiones DEBEN persistir en una base local de un solo archivo,
  y las imágenes en una carpeta local; ambos fuera de git.
- **FR-010**: El sistema NO DEBE pedir ni guardar nombre del paciente ni del dueño. Cada estudio se
  identifica con un código generado. Los registros de la aplicación solo contienen códigos de estudio y
  eventos: nunca nombres de archivo originales ni texto libre.
- **FR-011**: Cada estudio DEBE guardar qué versión de cada modelo lo procesó (nombre y huella del
  archivo) y el tiempo de inferencia medido.
- **FR-012**: La API DEBE publicar su contrato en OpenAPI 3.1 y validar entradas y salidas con modelos
  tipados.
- **FR-013**: La inferencia DEBE usar el modelo exportado (ONNX) y existir un test de paridad contra el
  modelo original con una entrada sintética.
- **FR-014**: La aplicación DEBE levantarse con un solo comando documentado y escuchar solo en la
  máquina local.
- **FR-015**: La interfaz DEBE estar en español y cumplir: contraste de texto 4,5:1, uso completo con
  teclado y foco visible, etiquetas visibles en los campos, error junto al campo, indicador de carga
  mientras procesa, y funcionar desde 375 px de ancho.

### Key Entities

- **Estudio**: código, fecha de carga, especie declarada, imagen, estado (borrador / validado),
  modelos que lo procesaron, tiempo de inferencia.
- **Hallazgo**: tipo, origen (modelo o manual), confianza, nivel, estado (pendiente / validado /
  corregido / descartado), comentario, fecha de la decisión.

## Success Criteria *(mandatory)*

- **SC-001**: Un usuario que nunca vio la aplicación completa el flujo carga → validación → cierre →
  consulta sin ayuda (se comprueba con el otro integrante del equipo y se anota el resultado).
- **SC-002**: El 95 % de las inferencias tarda menos de 2 s por imagen en la máquina de referencia,
  medido de punta a punta y registrado con el hardware usado.
- **SC-003**: El 100 % de los casos de entrada inválida de FR-001 tiene test y devuelve un mensaje
  accionable.
- **SC-004**: Hay un test de extremo a extremo del flujo completo y pasa en CI sin datos reales ni pesos
  del modelo.
- **SC-005**: Una búsqueda en los registros y en la base después de la prueba de extremo a extremo no
  encuentra nombres de archivo originales ni datos de pacientes.
- **SC-006**: La lista de verificación de accesibilidad y usabilidad de FR-015 queda completa y guardada
  junto al spec.

## Decisiones de diseño (con su por qué)

- **FastAPI + ONNX Runtime + SQLite, interfaz servida por el mismo proceso.** Un solo comando, sin
  segundo servidor. FastAPI genera el contrato OpenAPI 3.1 y valida con modelos tipados, y ONNX Runtime
  usa la exportación que ya existe: es lo que el documento del proyecto declara y hoy no está construido.
- **La puerta de región avisa y no bloquea.** Con la sensibilidad medida dejaría afuera una de cada
  nueve placas de tórax.
- **Hallazgos desde un registro de modelos.** El MVP funciona hoy con la Etapa 0 y carga manual, y suma
  la Etapa 1 cuando esté evaluada, sin rehacer la aplicación.
- **Identidad visual de la demo actual** (fondo oscuro, acento turquesa): el fondo oscuro es el habitual
  para leer radiografías. Las reglas de accesibilidad y usabilidad se toman de una lista de verificación
  externa; no se adopta un estilo "amigable de mascotas" porque resta seriedad a una herramienta clínica.

## Fuera de alcance

Usuarios con perfiles e inicio de sesión, historial por paciente, integración con sistemas de gestión
de clínicas, despliegue en la nube, carga de archivos DICOM y estimación del índice cardíaco vertebral.

## Assumptions

- Un solo usuario por vez, en la máquina local.
- La especie la declara el veterinario al cargar; el sistema no la infiere.
- `server.py` y la demo actual se retiran cuando el MVP cubra su función.
