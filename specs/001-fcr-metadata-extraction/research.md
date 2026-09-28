# Research: Extracción de metadata e imagen desde estudios FCR PRIMA

No quedaron `[NEEDS CLARIFICATION]` en el Technical Context del plan — todas las decisiones de
esta sección se resuelven con datos reales ya observados (Principio II de la constitution), no con
supuestos. Se documentan igual como decisiones formales porque cada una tiene una alternativa
descartada explícita.

## Decisión 1: Tabla de normalización de región anatómica

**Decision**: Antes de validar contra `REGIONES_VALIDAS`, mapear los códigos reales observados en
el tag `(0018,0015)` a su región canónica en español:

| Código real observado | Región canónica |
|---|---|
| `CHEST` | `TORAX` |
| `NECK` | `CERVICAL` |
| `HEAD` | `CRANEO` *(región nueva, ver Decisión 2)* |
| `UP_EXM` | `EXTREMIDADES` |
| `LOW_EXM` | `EXTREMIDADES` |
| `PELVIS`, `ABDOMEN` | sin cambio (ya coinciden) |

El fallback actual (buscar un token de región dentro del "Nombre del menú de exposición") se
mantiene como segundo intento, para menús como `"ESOFAGO CANINO"` donde el tag directo no alcanza
y no hay código de región reconocible tampoco — ese caso queda `"DESCONOCIDA"` legítimamente (no
es un bug, es información que el estudio no trae).

**Rationale**: la muestra real (500 estudios) mostró 247 `CHEST`, 56 `UP_EXM`, 45 `NECK`, 36
`HEAD`, 29 `LOW_EXM` contra apenas 56 `PELVIS` + 31 `ABDOMEN` que sí matcheaban — es decir, la
mayoría de los estudios reales fallaban la validación directa. Normalizar antes de validar resuelve
la mayor parte sin tocar el fallback existente.

**Alternatives considered**:
- *Ampliar `REGIONES_VALIDAS` para aceptar directamente los códigos en inglés* (sin tabla de
  normalización) — rechazado: mezclaría dos vocabularios (español para lo curado a mano,
  inglés/códigos para lo que viene del equipo) en el mismo campo de salida, complicando cualquier
  consumidor futuro (ej. `src/dataset.py`, specs de anotación) que tendría que conocer ambos.
- *Solo usar el fallback de menú de exposición y no tocar el tag directo* — rechazado: el menú de
  exposición no siempre trae la región (`"ESOFAGO CANINO"` no la trae), mientras que el tag directo
  casi siempre sí — descartar la fuente más confiable para depender de la menos confiable es peor.

## Decisión 2: Región `CRANEO` como categoría nueva

**Decision**: Agregar `CRANEO` a `REGIONES_VALIDAS` en `src/parser_fcr.py`.

**Rationale**: `HEAD` aparece 36 veces en una muestra de 500 (~7%) — volumen real, no un caso
aislado — y no es anatómica ni diagnósticamente equivalente a `CERVICAL` ni a ninguna otra
categoría existente. Clasificarlo como `"DESCONOCIDA"` o forzarlo dentro de `CERVICAL` perdería o
falsearía esos estudios.

**Consecuencia fuera de alcance de esta feature**: agregar una 6ª región cambia el espacio de
clases que consume `src/dataset.py`/`src/model.py` para la Etapa 0 (hoy 5 clases fijas) y el campo
`clases` de `specs/ground-truth-annotation.spec.yaml`. Esta feature solo produce el valor `region`
correcto; actualizar el entrenamiento/modelo de Etapa 0 para usar 6 clases es trabajo de otra
feature (Principio V — no se mezcla acá).

**Alternatives considered**:
- *Mapear `HEAD` a `CERVICAL`* — rechazado: anatómicamente incorrecto, un radiólogo no los trata
  como la misma región.
- *Dejar `HEAD` como `"DESCONOCIDA"` hasta que el modelo soporte 6 clases* — rechazado: viola el
  Principio II (el spec ya exige que los códigos reales conocidos no caigan en desconocido, ver
  SC-003) y descarta ~7% del dataset sin necesidad.

## Decisión 3: Vista combinada `VD/DV`

**Decision**: Agregar `"VD/DV"` como token válido y atómico en `VISTAS_VALIDAS`, sin partirlo en
dos vistas separadas.

**Rationale**: el campo `vista` hoy es un valor escalar consumido como tal; convertirlo en lista
rompería a cualquier consumidor actual sin necesidad. `"VD/DV"` como string ya es la representación
exacta que trae el equipo — no hay pérdida de información al aceptarlo tal cual.

**Alternatives considered**:
- *Partir `"VD/DV"` en dos entradas separadas (una fila por vista)* — rechazado: cambia el tipo del
  campo `vista` de escalar a colección, un cambio de contrato más grande que lo que este spec pide,
  y ningún requisito (FR-006) exige esa granularidad.

## Decisión 4: Vista ausente e ID con guion

**Decision**: Sin cambio de código — ya cumplen FR-007 y FR-008 tal como está el código hoy
(`next(..., None)` ya devuelve `None` explícito sin vista; `campos.get("ID del paciente")` ya
preserva el string completo, guiones incluidos). Se agregan solo tests de regresión que fijen este
comportamiento ya correcto.

**Rationale**: verificado leyendo `src/parser_fcr.py` línea por línea contra los requisitos — no
hay lógica que trunque o rechace estos casos.

## Decisión 5: Decodificación de `.hq` (JPEG-Lossless)

**Decision**: Mantener `pylibjpeg` + `pylibjpeg-libjpeg`, ya en uso en `limpiar_datos_fcr.py` y ya
declarados en `requirements.txt`.

**Rationale**: Pillow no decodifica JPEG-Lossless (marcador SOF3) nativamente; `pylibjpeg` ya está
probado en producción sobre el pool real de ~8000 estudios (98.2% de éxito observado).

**Alternatives considered**:
- *Escribir un decodificador JPEG-Lossless propio* — rechazado: alto riesgo de introducir errores
  sutiles de fidelidad en imágenes médicas, sin ningún beneficio sobre una librería ya validada.

## Decisión 6: Datos de fixtures para tests (Principio IV)

**Decision**: Los tests nuevos (`tests/test_ddo_parser.py`, extensión de
`tests/test_parser_fcr.py`) usan `.ddo`/`.txt` **sintéticos**, construidos a mano para reproducir
cada caso (tags DICOM-like armados con `struct.pack`, o texto plano para el caso de
`parser_fcr.py`) — nunca una copia de un archivo real de
`C:\Users\Usuario\Music\DatasetVetVision`.

**Rationale**: Principio IV (Patient Data Protection) — los `.txt` reales que vimos contienen
nombres de pacientes reales (ej. "BARRIOS LINO DANIEL"). Copiar un archivo real a `tests/fixtures/`
y commitearlo subiría datos de paciente identificables a git, violando la constitution
directamente.

**Alternatives considered**:
- *Anonymizar un archivo real y usarlo como fixture* — rechazado por innecesario: el valor de campo
  que importa para cada test (ej. `"Región anatómica:CHEST"`) es trivial de reproducir sintético,
  no hace falta partir de un archivo real ni el paso extra de anonimizarlo.
