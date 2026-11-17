# Feature Specification: Etiquetas a partir de los diagnósticos transcriptos

**Feature Branch**: `008-etiquetas-diagnosticos`
**Created**: 2026-11-17
**Status**: Draft (versión abreviada)
**Input**: los diagnósticos se transcriben a mano desde registros en papel: texto libre, con
abreviaturas, erratas, negaciones y ruido. Hay que convertirlos en etiquetas de forma determinista
y cruzarlos con las placas del dataset, sin etiquetar nada "por intuición".

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Normalizar un texto de diagnóstico a etiquetas (Priority: P1)

Como equipo, le paso al normalizador un texto transcripto y obtengo un resultado explícito: qué
etiquetas positivas encontró, cuáles negó, y si hay que mandarlo a revisión humana en vez de
etiquetarlo solo.

**Independent Test**: sobre una lista de textos sintéticos (nunca copiados de la planilla real),
cada regla de esta spec tiene al menos un caso que la dispara.

**Acceptance Scenarios**:

1. **Given** `"s/p"`, `"s/alt"`, `"sin alteraciones"`, `"control"` o `"n"` sueltos, **When** se
   normaliza, **Then** el resultado es `NORMAL` y `sano = True`.
2. **Given** un texto con un hallazgo torácico positivo (por ejemplo `"patron bronquial"`),
   **When** se normaliza, **Then** `sano = False` y la etiqueta correspondiente queda en el
   conjunto positivo.
3. **Given** una negación (`"sin signos de metástasis"`, `"no se observa efusión"`), **When** se
   normaliza, **Then** la etiqueta negada NO entra al conjunto positivo, y si es lo único que dice
   el texto el resultado queda en `REVISAR` (no en `NORMAL`): negar un hallazgo específico no es lo
   mismo que un estudio de rutina.
4. **Given** varios hallazgos en un mismo texto (`"patrón bronquial y vascular"`), **When** se
   normaliza, **Then** las dos etiquetas quedan en el conjunto positivo.
5. **Given** un hallazgo no torácico (fractura, cuerpo extraño), **When** se normaliza, **Then** la
   etiqueta es `HALLAZGO_NO_TORACICO` y `sano` queda en `None` (ni sano ni no sano: decisión
   pendiente del equipo, ver Assumptions).
6. **Given** un texto vacío, con errata o abreviatura conocida, o con una combinación ambigua
   (por ejemplo `"s/p"` seguido de un hallazgo), **When** se normaliza, **Then** el resultado queda
   en `REVISAR` con un motivo, nunca se adivina.
7. **Given** un texto que es puramente ruido (sin terminología médica reconocible), **When** se
   normaliza, **Then** la etiqueta es `RUIDO` y se excluye del etiquetado.

### User Story 2 - Vincular cada fila de la planilla con su placa (Priority: P1)

Como equipo, cruzo cada fila transcripta con el estudio real del dataset por identificador y año,
y separo lo ambiguo para revisión en vez de adivinar a qué fecha corresponde.

**Independent Test**: sobre datos privados, cada fila queda clasificada en una de cuatro
categorías (única, ambigua, sin placa, sin observación), nunca sin clasificar.

### Edge Cases

- Identificador con sufijo numérico: se agrupa igual que en `src/particion.py::grupo_paciente`.
- Un identificador con estudios de tórax en más de una fecha dentro del mismo período: `AMBIGUA`,
  no se etiqueta.
- Observación con texto que no es terminología médica (nombre propio, fragmento sin sentido):
  `RUIDO`, nunca se escribe en un archivo versionado.

## Requirements *(mandatory)*

- **FR-001**: `normalizar_texto` DEBE pasar a minúsculas, quitar tildes y normalizar espacios y
  puntuación, antes de cualquier otra regla.
- **FR-002**: `etiquetar` DEBE reconocer abreviaturas y erratas frecuentes definidas en
  `specs/diagnosticos_vocabulario.yaml`, nunca hardcodeadas en el código.
- **FR-003**: `etiquetar` DEBE detectar negación sobre la etiqueta que sigue inmediatamente a un
  disparador de negación (`"sin signos de"`, `"no se observa"`, `"no se observan"`, `"sin
  evidencia de"`, `"descartar"`), y esa etiqueta NO DEBE contar como positiva.
- **FR-004**: `etiquetar` DEBE devolver, para cada texto: el conjunto de etiquetas positivas, el
  conjunto de etiquetas negadas, una bandera `revisar` con motivo cuando corresponda, y `sano`
  (`True`, `False` o `None`) según la regla: solo `NORMAL` → `True`; al menos una etiqueta torácica
  positiva → `False`; solo `HALLAZGO_NO_TORACICO`, `RUIDO` o `REVISAR` → `None`.
- **FR-005**: El vocabulario (`specs/diagnosticos_vocabulario.yaml`) DEBE ser una lista cerrada de
  etiquetas, versionada y sin ningún dato de paciente.
- **FR-006**: Ningún identificador, nombre ni fecha de estudio individual DEBE escribirse en un
  archivo versionado, en un test ni en un mensaje: los tests usan textos sintéticos escritos para
  esta spec, nunca copiados de una planilla real.
- **FR-007**: El cruce fila↔placa DEBE vincular por identificador normalizado (mismo criterio de
  agrupación que `grupo_paciente`) y por año/período de la planilla contra la fecha del estudio, y
  DEBE clasificar cada fila en exactamente una de: `UNICA`, `AMBIGUA`, `SIN_PLACA`,
  `SIN_OBSERVACION`.

## Success Criteria *(mandatory)*

- **SC-001**: Cada regla de las historias 1 tiene un test con una entrada sintética que la dispara.
- **SC-002**: El vocabulario cubre al menos el 70 % de las observaciones no vacías de la muestra
  real (medido en privado, informado en agregado en `docs/privado/etiquetas/resumen_etiquetas.md`).
- **SC-003**: El resumen agregado entrega una tabla de cantidad por etiqueta y por paciente, y un
  veredicto de viabilidad de la Etapa 1 y de cada grupo de la Etapa 2, con la incertidumbre
  esperable según el tamaño de muestra (sin afirmar una métrica que no se calculó).

## Assumptions

- `control` y `N` se etiquetan `NORMAL` por definición del equipo (2026-11-16): son estudios de
  rutina, no indican una patología. Queda a confirmar con la radióloga colaboradora.
- Un hallazgo no torácico en una placa de tórax no se etiqueta `NO_SANO` del tórax ni `NORMAL`:
  queda en `HALLAZGO_NO_TORACICO` hasta que el equipo decida si cuenta como `NO_SANO` a los fines
  de la Etapa 1.
- Negar un hallazgo específico ("sin signos de metástasis") no equivale a un estudio de control:
  por eso no se etiqueta `NORMAL`, sino `REVISAR`, salvo que el equipo decida lo contrario.
