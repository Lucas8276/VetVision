# Feature Specification: Clasificador de Etapa 0 — Tórax vs. No-Tórax

**Feature Branch**: `002-etapa0-torax-clasificador`

**Created**: 2026-09-28

**Status**: Draft

**Input**: User description: "Clasificador de Etapa 0: torax vs no-torax. El objetivo real del
proyecto (diagnostico de Etapa 2) es exclusivamente sobre radiografias de torax, asi que en vez de
clasificar entre las 6 regiones anatomicas (CERVICAL/TORAX/ABDOMEN/PELVIS/EXTREMIDADES/CRANEO),
Etapa 0 debe ser binaria: TORAX vs NO_TORAX. No se agrega una etapa previa de 'es radiografia
valida o no' porque las imagenes no-radiografia son un caso raro/anecdotico en el pool, ya
filtrado procedimentalmente por limpiar_datos_fcr.py (cola REVISAR), no justifica un clasificador
de ML aparte. Esta etapa es la unica que no depende de la anotacion clinica pendiente: el label
(region, ya corregido por la feature 001-fcr-metadata-extraction) sale automaticamente del .txt de
cada estudio, asi que se puede entrenar ya mismo con los ~8000 estudios reales disponibles, sin
esperar a la Dra. Repetto ni al sistema Veter."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Etiquetar automáticamente cada estudio como tórax o no-tórax (Priority: P1)

Como responsable de armar el dataset de entrenamiento, necesito que cada estudio ya extraído
(feature 001) quede etiquetado automáticamente como `TORAX` o `NO_TORAX` a partir de su región
anatómica ya conocida, sin depender de ninguna anotación clínica, para poder usarlo de inmediato
como dataset de entrenamiento.

**Why this priority**: sin un dataset etiquetado no hay nada que entrenar — y esta etapa es la
única que no está bloqueada por la anotación clínica pendiente.

**Independent Test**: tomar una muestra de estudios con distintas regiones ya conocidas (`TORAX`,
`CERVICAL`, `ABDOMEN`, `PELVIS`, `EXTREMIDADES`, `CRANEO`, `DESCONOCIDA`) y verificar que cada uno
recibe la etiqueta correcta o queda explícitamente excluido.

**Acceptance Scenarios**:

1. **Given** un estudio cuya región es `TORAX`, **When** se etiqueta, **Then** queda `TORAX`.
2. **Given** un estudio cuya región es `CERVICAL`, `ABDOMEN`, `PELVIS`, `EXTREMIDADES` o `CRANEO`,
   **When** se etiqueta, **Then** queda `NO_TORAX`.
3. **Given** un estudio cuya región es `"DESCONOCIDA"` (no resuelta por la feature 001), **When**
   se arma el dataset, **Then** ese estudio queda excluido del conjunto de entrenamiento/evaluación
   — nunca se le asigna `TORAX` ni `NO_TORAX` a ciegas — y el motivo de exclusión queda registrado.

---

### User Story 2 - Entrenar un modelo con desempeño medible (Priority: P1)

Como responsable del proyecto, necesito entrenar un modelo sobre el dataset etiquetado
automáticamente y conocer su desempeño real antes de decidir si está listo para usarse, para no
promover a producción un modelo que no distingue bien tórax de no-tórax.

**Why this priority**: sin una medición objetiva no hay forma de saber si el modelo sirve — y el
desbalance de clases (si lo hay) puede esconder un mal desempeño detrás de una exactitud alta
engañosa.

**Independent Test**: entrenar sobre un lote real, evaluar sobre un conjunto separado que el
modelo no vio durante el entrenamiento, y confirmar que se reportan métricas que no se inflan con
desbalance de clases.

**Acceptance Scenarios**:

1. **Given** un dataset etiquetado por la Historia 1, **When** se entrena el modelo, **Then** se
   produce un modelo evaluable sobre datos que no participaron del entrenamiento.
2. **Given** un modelo ya entrenado, **When** se evalúa, **Then** se reportan al menos exactitud
   balanceada y F1 (no solo exactitud simple).
3. **Given** el desempeño medido, **When** se compara contra el umbral mínimo definido, **Then**
   el sistema indica explícitamente si el modelo es promovible a uso en el pipeline o no.

---

### User Story 3 - Clasificar un estudio nuevo automáticamente (Priority: P2)

Como responsable del pipeline, necesito poder aplicar el modelo ya entrenado sobre un estudio
nuevo y obtener una decisión `TORAX`/`NO_TORAX`, para filtrar automáticamente qué estudios avanzan
hacia la Etapa 1/2 (que son exclusivamente de tórax) sin gastar anotación clínica en los que no lo
son.

**Why this priority**: es el punto donde el modelo entrega valor real al flujo, pero solo tiene
sentido una vez que las Historias 1 y 2 garantizan que el modelo es confiable.

**Independent Test**: tomar un estudio nuevo (no usado en entrenamiento ni evaluación) y confirmar
que se obtiene una decisión `TORAX`/`NO_TORAX`, no un score interno sin interpretar.

**Acceptance Scenarios**:

1. **Given** un estudio nuevo con su imagen ya extraída, **When** se aplica el modelo, **Then** se
   obtiene una decisión `TORAX` o `NO_TORAX`, no una probabilidad cruda sin umbral aplicado.

---

### Edge Cases

- ¿Qué pasa con un estudio cuya región es `"DESCONOCIDA"`? → excluido del dataset de
  entrenamiento/evaluación, nunca forzado a una de las dos clases (ver Historia 1, Escenario 3).
- ¿Qué pasa si a un estudio le falta la imagen fuente (jpg pesado no encontrado)? → excluido del
  dataset, sin interrumpir el armado del resto del dataset ni el entrenamiento.
- ¿Qué pasa si el dataset real resulta desbalanceado (mucho más `NO_TORAX` que `TORAX`, o
  viceversa)? → las métricas de evaluación (SC-002) deben seguir siendo informativas igual
  (exactitud balanceada / F1, no solo exactitud simple).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema DEBE derivar la etiqueta `TORAX`/`NO_TORAX` de cada estudio a partir del
  campo `region` ya extraído por la feature 001-fcr-metadata-extraction, sin requerir anotación
  clínica adicional.
- **FR-002**: El sistema DEBE mapear `region == "TORAX"` a la etiqueta `TORAX`, y cualquier otra
  región válida conocida (`CERVICAL`, `ABDOMEN`, `PELVIS`, `EXTREMIDADES`, `CRANEO`) a la etiqueta
  `NO_TORAX`.
- **FR-003**: El sistema DEBE excluir del dataset de entrenamiento/evaluación los estudios cuya
  región sea `"DESCONOCIDA"`, y DEBE reportar cuántos estudios quedaron excluidos por esta razón.
- **FR-004**: El sistema DEBE entrenar un modelo de clasificación binaria sobre las imágenes
  disponibles y las etiquetas derivadas.
- **FR-005**: El sistema DEBE medir el desempeño del modelo entrenado con al menos exactitud
  balanceada y F1.
- **FR-006**: El sistema DEBE definir un umbral de desempeño mínimo por debajo del cual el modelo
  NO se considera listo para uso en el pipeline.
- **FR-007**: El sistema DEBE poder aplicar el modelo entrenado sobre un estudio nuevo y devolver
  una decisión `TORAX`/`NO_TORAX` explícita, no solo un score interno.
- **FR-008**: Esta etapa NO DEBE requerir anotación clínica de triaje sano/no-sano ni de
  diagnóstico (Principio V de la constitution) — debe poder completarse solo con los ~8000
  estudios ya extraídos.

### Key Entities

- **Estudio etiquetado**: un estudio (de la feature 001) más su etiqueta derivada
  (`TORAX` / `NO_TORAX` / excluido, con motivo si aplica).
- **Modelo Etapa 0 (binario)**: el clasificador entrenado sobre el dataset etiquetado.
- **Resultado de evaluación**: exactitud balanceada, F1, y la decisión de promoción (listo / no
  listo) de una corrida de entrenamiento dada.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: El 100% de los estudios con región conocida (distinta de `"DESCONOCIDA"`) quedan
  etiquetados automáticamente como `TORAX` o `NO_TORAX` sin intervención manual.
- **SC-002**: El modelo entrenado alcanza al menos 90% de exactitud balanceada sobre un conjunto
  de evaluación que no participó del entrenamiento.
- **SC-003**: 0 estudios del dataset de entrenamiento de esta etapa requieren anotación clínica
  manual (triaje o diagnóstico) para poder usarse.
- **SC-004**: Un estudio nuevo recibe una decisión `TORAX`/`NO_TORAX` interpretable sin necesidad
  de que una persona interprete manualmente un score interno.

## Assumptions

- El dataset de entrenamiento/evaluación de esta etapa es el conjunto de estudios ya extraídos por
  la feature 001-fcr-metadata-extraction, con su campo `region` ya corregido.
- Se usa la misma fuente de imagen que ya usa el pipeline de Etapa 0 actual (el jpg "pesado",
  8 bits) — cambiar la fuente de imagen a la `.png` de 16 bits queda fuera de alcance de esta
  feature.
- El mecanismo exacto de separación entre datos de entrenamiento y de evaluación (proporción,
  aleatoriedad, estratificación) es una decisión técnica que se resuelve en `/speckit-plan`, no en
  este spec.
- El umbral de 90% de exactitud balanceada (SC-002) es un valor por defecto razonable para una
  tarea de clasificación anatómica binaria (más simple que diagnóstico de patología) — no es un
  compromiso clínico definitivo, se puede ajustar después de la primera corrida real.
- Fuera de alcance de esta feature: Etapa 1 (triaje sano/no-sano) y Etapa 2 (diagnóstico) —
  siguen bloqueadas por la anotación clínica pendiente (Dra. Repetto / sistema Veter).
- Fuera de alcance: una etapa previa de "es radiografía válida o no" — evaluada y descartada
  explícitamente (caso raro/anecdótico en el pool, ya filtrado procedimentalmente por
  `limpiar_datos_fcr.py`).
