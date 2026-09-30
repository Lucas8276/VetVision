# Feature Specification: Extracción de metadata e imagen desde estudios FCR PRIMA

**Feature Branch**: `001-fcr-metadata-extraction`

**Created**: 2026-09-28

**Status**: Draft

**Input**: User description: "El pipeline de extraccion FCR PRIMA (.ddo -> .txt, .hq -> .png 16-bit) ya esta
implementado y funcionando en produccion sobre ~8000 estudios reales (limpiar_datos_fcr.py +
src/parser_fcr.py). Esta especificacion documenta el comportamiento ya existente como contrato
formal, incluyendo los casos reales ya descubiertos que el codigo actual maneja mal (region en
ingles/codigos de equipo en vez de espanol, vista combinada VD/DV, menus sin vista, IDs con guion)
para que queden como requisitos explicitos y no como bugs silenciosos."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Leer metadata de un estudio sin el software oficial de Fuji (Priority: P1)

Como responsable de armar el dataset de entrenamiento, cuando tengo un estudio radiológico crudo
del equipo FCR PRIMA y no tengo disponible DDOView (porque `MSCOMCTL.OCX` no está instalado o la
máquina está offline), necesito poder leer igual toda la metadata del paciente/estudio (ID,
nombre, sexo, fecha, región anatómica, menú de exposición, modalidad, institución) sin depender de
ningún software de Windows.

**Why this priority**: sin esto no existe dataset — es el problema original que bloqueaba todo el
proyecto antes de que se resolviera por ingeniería inversa.

**Independent Test**: tomar un `.ddo` cualquiera del pool real, correr la extracción, y verificar
que el `.txt` resultante tiene los 8 campos esperados con valores no vacíos (salvo que el campo
realmente falte en el `.ddo` de origen).

**Acceptance Scenarios**:

1. **Given** un archivo `.ddo` válido de un estudio real, **When** se ejecuta la extracción,
   **Then** se genera un `.txt` con ID paciente, nombre, sexo, fecha de exposición (formato
   DD.MM.YYYY), región anatómica, nombre del menú de exposición, modalidad e institución.
2. **Given** un `.ddo` cuyo recorrido de tags incluye una secuencia anidada de largo indefinido,
   **When** se parsea, **Then** el parser distingue correctamente el tag de cierre de secuencia
   `(FFFE,E0DD)` del tag de cierre de ítem `(FFFE,E00D)` y no desincroniza la lectura de offsets
   del resto del archivo.

---

### User Story 2 - Obtener la imagen de mayor calidad disponible sin pérdida (Priority: P1)

Como responsable del dataset, necesito que la imagen de mayor resolución y profundidad de bits
capturada por el equipo (el `.hq`, JPEG-Lossless) quede disponible en un formato estándar y
abrible (PNG de 16 bits), sin pasar por el software de Fuji ni perder información del sensor.

**Why this priority**: el `.hq` es la fuente de imagen de mayor fidelidad disponible — más que el
`.jpg` que exporta el sistema — y sin decodificarlo esa calidad se pierde por completo.

**Independent Test**: tomar un `.hq` real, decodificarlo, y verificar que el `.png` resultante es
de 16 bits, con las mismas dimensiones que reporta el equipo, y que los valores de píxel no fueron
reescalados a 0-255.

**Acceptance Scenarios**:

1. **Given** un `.hq` válido (JPEG-Lossless, marcador SOF3), **When** se decodifica, **Then** se
   obtiene un `.png` de 16 bits que conserva los valores de píxel originales sin normalizar.
2. **Given** un `.hq` que falla al decodificar (corrupto o formato inesperado), **When** se
   procesa el lote, **Then** ese estudio se enruta a revisión manual con el motivo del error
   registrado, y el resto del lote sigue procesándose sin interrumpirse.

---

### User Story 3 - Clasificar correctamente metadata que llega en formatos no anticipados (Priority: P2)

Como responsable del dataset, necesito que los campos de metadata realmente observados en
producción (que no siempre vienen en el formato que se asumió al principio) se interpreten
correctamente, para no perder o mal-etiquetar silenciosamente la mayoría de los estudios reales.

**Why this priority**: hoy la mayoría de los registros reales caen en un valor de "desconocido"
para región anatómica porque el validador solo reconoce nombres en español, cuando el equipo
entrega códigos en inglés — esto degrada directamente los datos de entrenamiento de la Etapa 0 sin
que nadie lo note en los logs.

**Independent Test**: correr el parser sobre una muestra de `.txt` reales que incluya cada uno de
los casos conocidos (región en inglés/código de equipo, vista combinada, menú sin vista, ID con
guion) y verificar que ninguno cae en un valor "desconocido" que debería estar mapeado.

**Acceptance Scenarios**:

1. **Given** un `.txt` cuya "Región anatómica" es `CHEST`, `NECK`, `HEAD`, `UP_EXM` o `LOW_EXM`,
   **When** se parsea, **Then** el sistema lo clasifica en su región válida correspondiente
   (`TORAX`, `CERVICAL`, `CRANEO`/región equivalente, `EXTREMIDADES`) en vez de `"DESCONOCIDA"`.
2. **Given** un menú de exposición con vista combinada (`"CRANEO VD/DV FELINO"`), **When** se
   parsea, **Then** el sistema extrae una vista válida en vez de devolver `None`.
3. **Given** un menú de exposición sin ningún token de vista (`"ESOFAGO CANINO"`), **When** se
   parsea, **Then** el sistema devuelve explícitamente "vista ausente" sin lanzar error ni asumir
   un valor incorrecto.
4. **Given** un ID de paciente con guion (`"123-4"`, `"456-7"`), **When** se parsea, **Then** el
   valor se conserva completo, sin truncar ni rechazar el registro.

---

### Edge Cases

- ¿Qué pasa cuando el `.ddo` no tiene un tag esperado (ej. institución vacía)? → el campo queda
  vacío en el `.txt`, no se inventa un valor ni se aborta la extracción del resto de los campos.
- ¿Qué pasa cuando dos archivos de entrada generarían el mismo nombre de salida? → se genera un
  sufijo único (`_1`, `_2`, ...) en vez de sobrescribir silenciosamente.
- ¿Qué pasa con un archivo cuya extensión no es ninguna de las 8 esperadas por estudio? → se
  enruta a revisión manual con el motivo "extensión no reconocida", no se descarta ni se conserva
  por defecto.
- ¿Qué pasa con un `.jpg` de tamaño límite (ni claramente grande ni claramente miniatura, y sin el
  sufijo `s` de miniatura)? → se enruta a revisión manual en vez de adivinar la clasificación.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema DEBE extraer del `.ddo` binario, sin depender de DDOView ni de
  `MSCOMCTL.OCX`, los campos: ID paciente, nombre del paciente, sexo, fecha de exposición, región
  anatómica, nombre del menú de exposición, modalidad e institución.
- **FR-002**: El sistema DEBE distinguir correctamente el tag `(FFFE,E0DD)` (fin de secuencia) del
  tag `(FFFE,E00D)` (fin de ítem) al recorrer secuencias de largo indefinido, de forma que un
  recorrido nunca desincronice los offsets de lectura del resto del archivo. Este comportamiento
  DEBE estar cubierto por una prueba automatizada de regresión.
- **FR-003**: El sistema DEBE escribir un `.txt` de metadata por cada `.ddo` procesado, con
  formato de fecha DD.MM.YYYY.
- **FR-004**: El sistema DEBE decodificar cada `.hq` (JPEG-Lossless) a un `.png` de 16 bits que
  conserve los valores de píxel originales sin reescalarlos a 0-255.
- **FR-005**: El sistema DEBE clasificar como región anatómica válida, además de los nombres en
  español ya reconocidos, los códigos realmente observados en producción: `CHEST`, `NECK`,
  `HEAD`, `UP_EXM`, `LOW_EXM` (mapeados a su región equivalente), en vez de asignarles
  `"DESCONOCIDA"`.
- **FR-006**: El sistema DEBE reconocer una vista combinada (ej. `"VD/DV"`) como una vista válida,
  no como un token no reconocido.
- **FR-007**: El sistema DEBE tolerar un menú de exposición sin ningún token de vista reconocible,
  devolviendo un valor explícito de "ausente" en vez de fallar o inferir incorrectamente.
- **FR-008**: El sistema DEBE aceptar identificadores de paciente que contengan caracteres además
  de dígitos (ej. un guion), preservando el valor completo.
- **FR-009**: Cuando la decodificación de un `.hq` falla, el sistema DEBE enrutar ese estudio a una
  cola de revisión manual con el motivo de la falla registrado, y DEBE continuar procesando el
  resto del lote sin interrumpirse.
- **FR-010**: El sistema DEBE producir, por cada corrida sobre un lote, un reporte que registre
  para cada archivo de entrada: la acción tomada (conservar / sobrante / revisar) y el motivo.
- **FR-011**: El sistema DEBE evitar sobrescribir un archivo de salida existente, generando un
  sufijo único cuando el nombre de destino ya está ocupado.

### Key Entities

- **Estudio radiológico**: conjunto de archivos que comparten el mismo nombre base
  (`.ddo`, `.hq`, `.dsp`, `.std`, `.edk`, `.edr`, jpg grande, jpg chico), producido por el equipo
  FCR PRIMA para una exposición de un paciente.
- **Registro de metadata (`.txt`)**: campos estructurados legibles derivados del `.ddo` de un
  estudio (identidad del paciente, datos clínicos básicos y de captura).
- **Imagen de alta calidad (`.png` 16-bit)**: imagen decodificada desde el `.hq` de un estudio, sin
  pérdida y sin normalizar.
- **Reporte de clasificación**: registro, por corrida de extracción sobre un lote de estudios, de
  qué se hizo con cada archivo de entrada y por qué.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: El 100% de los `.ddo` de un lote procesado generan su `.txt` de metadata
  correspondiente sin intervención manual (línea base ya observada: 8158/8158 en el dataset de
  referencia).
- **SC-002**: Al menos el 98% de los `.hq` de un lote procesado se decodifican exitosamente a
  `.png` sin intervención manual (línea base ya observada: 8015/8158 ≈ 98.2%); el resto queda
  identificable en la cola de revisión con motivo registrado, no se pierde silenciosamente.
- **SC-003**: 0% de los registros cuya región anatómica es uno de los códigos reales conocidos
  (`CHEST`, `NECK`, `HEAD`, `UP_EXM`, `LOW_EXM`, además de los nombres en español) quedan
  clasificados como región desconocida.
- **SC-004**: Una corrida repetida del parser sobre el caso de regresión conocido (secuencia
  anidada con tag de cierre `(FFFE,E0DD)`) produce el mismo resultado correcto en el 100% de las
  ejecuciones, verificable por una prueba automatizada sin inspección manual del archivo.
- **SC-005**: Una persona revisando la cola de "revisar" puede identificar el motivo de cada
  archivo marcado leyendo únicamente el reporte, sin necesidad de abrir el archivo original.

## Assumptions

- El formato binario del `.ddo` (variante no estándar de DICOM propia de Fuji) es consistente a
  través de los ~8000+ estudios del dataset — todos provienen del mismo equipo FCR PRIMA.
- "Producción" en este spec significa que este pipeline ya corre sobre datos reales del Hospital
  de Clínicas F.C.V. y sus salidas (`.txt`/`.png`/`.jpg`) son las que se usan hoy para preparar el
  dataset de entrenamiento — no es un pipeline aspiracional a futuro.
- La especie y la vista se derivan únicamente del texto libre de "Nombre del menú de exposición",
  no de un tag DICOM estructurado separado — consistente con la implementación actual.
- La anonimización de datos de paciente (remover nombre/ID original antes de subir a la nube) es
  una responsabilidad separada, ya cubierta por el Principio IV de la constitution y por
  `specs/data-contract.spec.yaml` — no se duplica en este spec.
- Fuera de alcance de este spec: arquitectura del modelo, entrenamiento de las Etapas 1/2, y el
  proceso de anonimización/subida a la nube en sí (solo se referencian como dependencia).
