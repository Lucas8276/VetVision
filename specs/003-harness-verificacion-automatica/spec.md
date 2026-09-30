# Feature Specification: Harness de verificación automática

**Feature Branch**: `003-harness-verificacion-automatica`

**Created**: 2026-09-30

**Status**: Draft

**Input**: User description: "Harness de verificación automática para el proyecto VetVision, para
que la disciplina SDD deje de depender de la memoria de las personas y pase a ser exigida por el
sistema. Regla de fondo del equipo: los specs son la fuente de verdad; si el código no se alinea
con el spec, el código está mal; primero se especifica y después se codea. Incluye: validación de
los contratos `specs/*.spec.yaml` contra el código, CI en push y pull request, hooks del asistente
de código compartidos, versionado de la configuración `.claude`, memoria compartida del proyecto
en un documento versionado (repo público: sin datos personales), y una guardia automática contra
datos personales de pacientes/dueños (ya hubo una filtración real en el repositorio público)."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Detectar cuando el código se desvía del spec (Priority: P1)

Como integrante del equipo, cuando cambio código (o un spec) y el resultado deja de coincidir con
lo que dicen los contratos de `specs/*.spec.yaml`, necesito que el sistema me lo marque como un
**fallo**, indicando qué campo del contrato no coincide, qué dice el spec y qué hace el código —
para no enterarme semanas después, cuando alguien intente correr el pipeline de punta a punta.

**Why this priority**: es la regla central del equipo ("si el código no se alinea al spec, el
código está mal"). Hoy los contratos son solo documentación: ya hubo deriva real (el spec decía
entrada RGB de 3 canales y el backbone exige 1; el spec decía opset 17 y la exportación real da
18) y solo se descubrió por accidente al correr todo por primera vez.

**Independent Test**: reintroducir a propósito cada deriva conocida (ej. declarar 3 canales en el
contrato, o cambiar una clase de salida en el código) y confirmar que la verificación falla
nombrando el campo exacto; revertir y confirmar que pasa.

**Acceptance Scenarios**:

1. **Given** un contrato que declara una entrada de 3 canales y un código cuyo modelo espera 1
   canal, **When** se corre la verificación, **Then** falla e informa el campo, el valor del spec
   (3) y el valor del código (1).
2. **Given** un contrato cuyas clases de salida de una etapa coinciden con las del código,
   **When** se corre la verificación, **Then** esa etapa pasa sin ruido.
3. **Given** un contrato que describe una etapa todavía no implementada en el código (ej. triaje
   y diagnóstico, bloqueadas por anotación clínica), **When** se corre la verificación, **Then**
   esa sección se informa explícitamente como "pendiente / no implementada" — ni pasa en silencio
   ni rompe la verificación.
4. **Given** una divergencia detectada, **When** el resultado se muestra, **Then** es un fallo
   (no una advertencia ignorable) y el mensaje permite corregirlo sin investigar más.

---

### User Story 2 - Verificación automática al subir cambios (Priority: P1)

Como integrante del equipo, cada vez que subo cambios al repositorio (directo o por pull request)
necesito que se ejecuten solas las verificaciones (tests, contratos, guardia de datos personales)
y que un fallo deje claro que el cambio no está bien, para no depender de que alguien se acuerde
de correrlas a mano.

**Why this priority**: sin esto, las reglas del equipo se cumplen solo si alguien se acuerda. Hoy
no hay ninguna verificación automática y todo se validó manualmente.

**Independent Test**: subir un cambio deliberadamente roto (un test que falla, o una deriva de
contrato) y confirmar que queda marcado como fallido; subir uno correcto y confirmar que pasa.

**Acceptance Scenarios**:

1. **Given** un cambio con un test roto, **When** se sube al repositorio, **Then** la verificación
   automática lo marca como fallido y el motivo es visible sin abrir logs internos.
2. **Given** un cambio correcto, **When** se sube, **Then** todas las verificaciones pasan.
3. **Given** que el dataset real nunca está en el repositorio, **When** corren las verificaciones
   automáticas, **Then** funcionan igual (usan datos sintéticos) y no fallan por falta de datos.
4. **Given** un integrante que quiere verificar antes de subir, **When** corre las verificaciones
   en su máquina, **Then** obtiene el mismo veredicto que obtendría la verificación automática.

---

### User Story 3 - Guardia contra datos personales (Priority: P1)

Como responsable del proyecto, necesito que el sistema detecte automáticamente nombres, IDs y
archivos de pacientes o dueños reales **antes** de que lleguen al repositorio, porque el
repositorio es público y ya ocurrió una filtración real (nombres e IDs reales en documentación,
specs y tests, que siguen en el historial de git).

**Why this priority**: es una obligación legal/ética con los datos del Hospital de Clínicas y ya
falló una vez sin que nadie lo notara; el Principio IV de la constitution existía pero no había
nada que lo hiciera cumplir.

**Independent Test**: intentar agregar (a) un archivo de datos crudos de paciente, (b) un texto
con un campo de nombre de paciente con un valor no aprobado, (c) un ID con formato de paciente
real; confirmar que los tres se bloquean. Confirmar que los valores ficticios aprobados
(ej. `PACIENTE^PRUEBA`) NO se bloquean.

**Acceptance Scenarios**:

1. **Given** un archivo de datos crudos del equipo de rayos X o una imagen del dataset, **When**
   se intenta incluir en un cambio, **Then** se bloquea con un mensaje que explica por qué.
2. **Given** un texto (doc, spec o test) con un campo de nombre de paciente cuyo valor no está en
   la lista de valores ficticios aprobados, **When** se verifica, **Then** falla indicando
   archivo y línea.
3. **Given** patrones de secretos (claves, tokens), **When** aparecen en un cambio, **Then** se
   bloquean.
4. **Given** el estado actual del repositorio ya saneado, **When** corre la guardia, **Then**
   pasa limpia (sin falsos positivos sobre los datos ficticios ya reemplazados).
5. **Given** la guardia misma, **When** se revisa su contenido, **Then** no contiene nombres ni
   IDs reales (no puede convertirse en una nueva filtración).

---

### User Story 4 - Configuración del asistente compartida y hooks del proyecto (Priority: P2)

Como integrante del equipo, quiero que al clonar el repositorio ya tenga los mismos comandos del
flujo SDD (`/speckit-*`) y las mismas reglas automáticas en mi asistente de código que tiene mi
compañero, sin instalar nada extra, para que ambos trabajemos con la misma disciplina.

**Why this priority**: hoy `.claude/` está ignorado por git, por eso Lucas no recibe los comandos.
La auditoría hecha confirmó que solo contiene 10 archivos de instrucciones del flujo SDD, sin
claves ni secretos, así que es seguro compartirlo. Es P2 porque depende de que existan las
verificaciones de las historias 1–3 para que los hooks tengan qué ejecutar.

**Independent Test**: clonar el repositorio en una carpeta limpia y confirmar que los comandos
`/speckit-*` están disponibles y que los hooks se activan; confirmar que un archivo de
configuración personal/local sigue sin subirse.

**Acceptance Scenarios**:

1. **Given** un clon limpio del repositorio, **When** el integrante abre el proyecto en su
   asistente, **Then** los comandos del flujo SDD están disponibles sin pasos de instalación.
2. **Given** que se editó código fuente, **When** termina la edición, **Then** se ejecutan
   automáticamente las verificaciones relevantes y el resultado es visible.
3. **Given** un intento de agregar al commit archivos de datos crudos o secretos, **When** el
   asistente intenta hacerlo, **Then** se bloquea antes de que ocurra.
4. **Given** archivos locales o con permisos personales de un integrante, **When** se hace un
   commit, **Then** permanecen ignorados y no se suben.
5. **Given** que el asistente va a crear un commit, **When** intenta ejecutarlo, **Then** se pide
   una **primera confirmación explícita** del integrante, mostrando la lista exacta de archivos
   incluidos y un resumen de los cambios; sin esa confirmación no se crea el commit.
6. **Given** que el asistente va a subir commits al remoto, **When** intenta ejecutarlo, **Then**
   se pide una **segunda confirmación explícita**, distinta de la anterior, mostrando qué commits
   salen, hacia qué remoto y si el repositorio es público o privado; la confirmación del commit
   NO vale como confirmación de la subida.

---

### User Story 5 - Memoria compartida del proyecto (Priority: P2)

Como integrante del equipo, quiero que exista un documento versionado con el contexto del
proyecto (objetivos, decisiones, convenciones, lecciones aprendidas) que mi compañero y yo —y
nuestras sesiones con el asistente— compartamos, en lugar de que ese contexto viva en archivos
locales de una sola persona.

**Why this priority**: hoy Lucas no ve nada de ese contexto y cada sesión depende de quién la
abra. Se eligió un documento versionado (frente a una base de datos) por simplicidad: se revisa
en cada cambio, no requiere infraestructura y ambos lo reciben con un `git pull`.

**Independent Test**: confirmar que el documento existe, que un clon limpio lo tiene, que el
asistente lo carga al iniciar una sesión, y que la guardia rechaza contenido de las categorías
prohibidas.

**Acceptance Scenarios**:

1. **Given** un clon limpio, **When** se inicia una sesión con el asistente, **Then** el contexto
   compartido del proyecto se carga sin pasos manuales.
2. **Given** que el repositorio es público, **When** se agrega contenido al documento, **Then**
   se rechaza cualquier dato personal de pacientes/dueños, nombres de contactos externos,
   información de otros proyectos de los integrantes, o credenciales.
3. **Given** una decisión importante tomada en una sesión, **When** se registra, **Then** queda
   en el documento versionado y visible para el otro integrante en su próximo `git pull`.

---

### User Story 6 - Registrar la regla "spec primero" en la constitution (Priority: P3)

Como equipo, queremos que la regla "los specs son la fuente de verdad; si el código no coincide,
el código está mal; primero se especifica y después se codea" quede escrita en la constitution
como principio explícito, para que sea la referencia formal de las verificaciones automáticas.

**Why this priority**: es gobernanza; las verificaciones (historias 1–3) funcionan igual sin ella,
pero sin el texto la regla sigue siendo un acuerdo verbal.

**Independent Test**: leer la constitution y confirmar que enuncia la regla y que la versión del
documento se incrementó según su propia política de versionado.

**Acceptance Scenarios**:

1. **Given** la constitution actual, **When** se enmienda, **Then** incluye la regla, su
   justificación (casos reales de deriva) y el nuevo número de versión.

---

### Edge Cases

- ¿Qué pasa con un valor ficticio legítimo que parece un nombre real (ej. un nombre común usado en
  un test)? → solo se aceptan valores de la lista de valores ficticios aprobados; cualquier otro
  valor en un campo de nombre de paciente se marca, y la lista se amplía a propósito (con revisión).
- ¿Qué pasa si un campo del contrato aún no tiene verificación asociada? → se informa como "sin
  verificación asociada" para que la cobertura de contratos sea visible, no se ignora en silencio.
- ¿Qué pasa si se cambia un contrato **y** el código a la vez, de forma consistente? → pasa (el
  contrato es la fuente de verdad, pero el cambio es deliberado); la regla "primero el spec" se
  apoya además en la revisión del cambio, no solo en la verificación automática.
- ¿Qué pasa si la verificación automática no está disponible o tarda demasiado? → el integrante
  puede correr las mismas verificaciones localmente (historia 2, escenario 4); no se bloquea el
  trabajo, pero el cambio no se considera verificado.
- ¿Qué pasa con datos personales que ya están en el historial público? → fuera de alcance: la
  guardia protege hacia adelante; limpiar el historial es decisión del dueño del repositorio.
- ¿Qué pasa con archivos binarios grandes o imágenes? → se bloquean por tipo/ubicación (no se
  inspecciona su contenido).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema DEBE validar automáticamente los contratos de `specs/*.spec.yaml`
  (model-tensor, ground-truth-annotation, data-contract) contra el código real, cubriendo como
  mínimo: canales y forma de entrada del modelo, clases de salida de cada etapa implementada,
  umbral de promoción, regiones/vistas/especies admitidas y formato/versión de exportación.
- **FR-002**: Una divergencia entre contrato y código DEBE ser un fallo (no una advertencia) e
  informar el campo del contrato, el valor del spec y el valor del código.
- **FR-003**: Las secciones de un contrato que describen etapas todavía no implementadas DEBEN
  informarse como "pendientes", sin pasar en silencio ni provocar fallo.
- **FR-004**: Los campos de un contrato sin verificación asociada DEBEN quedar visibles en el
  reporte como "sin verificación", para que la cobertura sea auditable.
- **FR-005**: Al subir cambios al repositorio (directo y por pull request) DEBEN ejecutarse
  automáticamente los tests, la validación de contratos y la guardia de datos personales, y un
  fallo DEBE marcar el cambio como no aceptable.
- **FR-006**: Todas las verificaciones automáticas DEBEN poder ejecutarse sin el dataset real
  (que nunca está en el repositorio), usando datos sintéticos.
- **FR-007**: Cualquier integrante DEBE poder ejecutar las mismas verificaciones localmente con un
  único comando, obteniendo el mismo veredicto que la verificación automática.
- **FR-008**: La guardia DEBE bloquear archivos de datos crudos de pacientes (formatos del equipo
  de rayos X y archivos de imagen del dataset).
- **FR-009**: La guardia DEBE marcar, con archivo y línea, cualquier campo de nombre o ID de
  paciente cuyo valor no esté en la lista de valores ficticios aprobados.
- **FR-010**: La guardia DEBE bloquear patrones de secretos (claves, tokens, credenciales).
- **FR-011**: La guardia NO DEBE contener nombres ni IDs reales de personas (ni siquiera como
  lista de "valores prohibidos"); DEBE funcionar por patrones estructurales y lista de valores
  ficticios aprobados.
- **FR-012**: La guardia DEBE pasar limpia sobre el estado actual del repositorio ya saneado.
- **FR-013**: La configuración compartida del asistente (comandos del flujo SDD y reglas del
  proyecto) DEBE estar versionada en el repositorio y disponible en un clon limpio sin pasos de
  instalación; los archivos locales o personales DEBEN seguir ignorados.
- **FR-014**: Las reglas automáticas del asistente a nivel de proyecto DEBEN ejecutar las
  verificaciones tras editar código fuente y DEBEN bloquear que se agreguen al commit archivos de
  datos crudos o secretos.
- **FR-015**: DEBE existir un documento versionado de memoria compartida del proyecto que el
  asistente cargue al iniciar sesión en cualquier clon.
- **FR-016**: El documento de memoria compartida NO DEBE contener datos personales de
  pacientes/dueños, nombres de contactos externos, información de otros proyectos de los
  integrantes, ni credenciales; la guardia DEBE revisarlo como cualquier otro archivo.
- **FR-017**: La constitution DEBE enunciar la regla "los specs son la fuente de verdad; si el
  código no coincide, el código está mal; primero se especifica y después se codea", con su
  justificación y el incremento de versión correspondiente.
- **FR-018**: Todo fallo de verificación DEBE informar un mensaje accionable (qué archivo, línea o
  campo, y qué se esperaba).
- **FR-019**: Antes de crear cualquier commit, el sistema DEBE exigir una confirmación explícita
  del integrante que muestre la lista exacta de archivos incluidos y un resumen de cambios. Esta
  regla la hace cumplir el propio entorno del asistente (no depende de que el asistente se
  acuerde) y aplica a cualquier integrante.
- **FR-020**: Antes de subir commits a un remoto, el sistema DEBE exigir una segunda confirmación
  explícita, independiente de la del commit, que muestre los commits que salen, el remoto y la
  visibilidad (público/privado) del repositorio. Una confirmación no sustituye a la otra.

### Key Entities

- **Contrato**: cada archivo `specs/*.spec.yaml`; declara valores que el código debe cumplir.
- **Verificación**: chequeo automático con veredicto (pasa / falla / pendiente / sin verificación)
  y mensaje accionable.
- **Regla de contenido prohibido**: patrón estructural o categoría de archivo que no puede
  entrar al repositorio (datos crudos de pacientes, secretos, datos personales).
- **Lista de valores ficticios aprobados**: conjunto explícito de valores de ejemplo permitidos en
  campos de nombre/ID de paciente.
- **Documento de memoria compartida**: contexto versionado del proyecto, sujeto a la política de
  contenido.
- **Configuración compartida del asistente**: comandos y reglas automáticas versionados; distinta
  de la configuración local/personal, que no se comparte.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: El 100% de las derivas de contrato conocidas (canales 3 vs 1, versión de exportación
  17 vs 18) se detectan cuando se reintroducen a propósito.
- **SC-002**: Un cambio con una deriva o un test roto se marca como fallido automáticamente en
  menos de 10 minutos desde que se sube.
- **SC-003**: El 100% de un conjunto de casos de filtración de prueba (archivo de datos crudos,
  nombre de paciente no aprobado, ID de paciente, secreto) se bloquea, y 0 falsos positivos sobre
  el repositorio saneado actual.
- **SC-004**: Un integrante que clona el repositorio tiene los comandos del flujo SDD y las
  reglas automáticas disponibles con 0 pasos manuales de instalación.
- **SC-005**: El documento de memoria compartida tiene 0 elementos de las categorías prohibidas
  (verificado por la guardia) y ambos integrantes lo cargan en el 100% de sus sesiones.
- **SC-006**: El veredicto de las verificaciones en la máquina de un integrante coincide con el de
  la verificación automática en el 100% de los casos probados.
- **SC-007**: Ningún dato personal real vuelve a llegar al repositorio en el período posterior a
  la puesta en marcha (0 incidentes detectados en revisión).
- **SC-008**: El 100% de los commits y de las subidas al remoto realizados por el asistente pasan
  por su confirmación explícita correspondiente (0 commits o subidas sin confirmación previa).

## Assumptions

- El repositorio está alojado en GitHub, por lo que la verificación automática usa la
  automatización integrada de esa plataforma; es público y ambos integrantes tienen acceso de
  escritura.
- La detección de datos personales es heurística (patrones estructurales + lista de valores
  ficticios aprobados): reduce mucho el riesgo pero no puede garantizar el 100% frente a datos
  personales que no sigan un patrón reconocible. Por eso el documento de memoria y la revisión de
  cambios siguen siendo parte de la defensa.
- Los datos personales ya presentes en el historial de git (commits anteriores) quedan **fuera de
  alcance**: reescribir el historial público, o volver privado el repositorio mientras tanto, es
  decisión del dueño del repositorio. En el árbol de trabajo actual ya fueron reemplazados por
  datos ficticios.
- La demo web (`server.py`, página HTML) se construyó sin pasar por SDD; retro-especificarla es
  una feature aparte y no forma parte de esta.
- Entrenar o mejorar el modelo queda fuera de alcance.
- El equipo es de dos personas trabajando en Windows; la verificación automática puede correr en
  otro sistema operativo, por lo que las verificaciones no deben depender de rutas específicas de
  una máquina.
- El contexto compartido se guarda como documento versionado (no como base de datos) por
  simplicidad; si en el futuro crece demasiado, puede reevaluarse.
- Las verificaciones de contrato solo cubren lo que existe en el código; las etapas 1 y 2 (triaje y
  diagnóstico) siguen bloqueadas por la anotación clínica y se informan como pendientes.
