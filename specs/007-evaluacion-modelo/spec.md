# Feature Specification: Evaluación del modelo — incremento 1: partición por paciente

**Feature Branch**: `007-evaluacion-modelo`
**Created**: 2026-11-17
**Status**: Draft (versión abreviada; el protocolo completo de evaluación se agrega como incremento 2
antes de entrenar la Etapa 1)
**Input**: hallazgo del 2026-11-17: la partición de la Corrida 3 se hizo al azar por imagen y 1473 de
las 1603 imágenes de validación (91,9 %) pertenecen a un paciente que también tiene imágenes en
entrenamiento. La métrica informada puede estar inflada.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Medir la Etapa 0 sin fuga entre pacientes (Priority: P1)

Como equipo que va a defender una métrica, necesitamos que ninguna placa de un mismo paciente quede a
la vez en entrenamiento y en validación, para que el número informado mida generalización a pacientes
nuevos y no memoria de pacientes ya vistos.

**Why this priority**: es la mayor amenaza a la validez del único resultado medido del proyecto.

**Independent Test**: sobre un dataset sintético con pacientes repetidos, la partición no deja ningún
grupo en los dos lados; sobre el dataset real, la cantidad de pacientes compartidos entre entrenamiento
y validación es 0.

**Acceptance Scenarios**:

1. **Given** estudios de varios pacientes, algunos con varias placas, **When** se arma la partición,
   **Then** todas las placas de un mismo paciente quedan del mismo lado.
2. **Given** la misma semilla, **When** se arma la partición dos veces, **Then** el resultado es idéntico.
3. **Given** un modelo ya entrenado con la partición anterior, **When** se entrena la corrida nueva,
   **Then** el checkpoint anterior y sus índices de validación no se sobrescriben.

### Edge Cases

- Identificador con sufijo (`0000-1`): no sabemos todavía si el sufijo distingue visitas o animales de
  una misma ficha. Se agrupa por la parte anterior al guion: es la opción conservadora (agrupar de más
  nunca produce fuga; agrupar de menos, sí).
- Estudio sin identificador: forma su propio grupo.
- Identificador escrito con distinta capitalización o espacios: se normaliza antes de agrupar.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema DEBE derivar de cada estudio un grupo de paciente a partir del identificador
  de la metadata, normalizado y sin el sufijo posterior al guion.
- **FR-002**: El sistema DEBE partir entrenamiento y validación de modo que ningún grupo aparezca en
  ambos lados, manteniendo una proporción de clases parecida en cada lado (partición estratificada por
  grupos), con semilla fija.
- **FR-003**: La partición por paciente DEBE ser el comportamiento por defecto del entrenamiento; la
  partición por imagen queda disponible solo para reproducir corridas anteriores.
- **FR-004**: Los identificadores de paciente NO DEBEN escribirse en registros, métricas, artefactos ni
  archivos: en memoria se manejan como hash. Solo se guardan conteos y la huella de la partición.
- **FR-005**: El entrenamiento DEBE permitir elegir la ruta del checkpoint de salida, y los índices de
  validación DEBEN guardarse junto a él con la convención que ya usa `src/evaluate.py`.
- **FR-006**: `specs/model-tensor.spec.yaml` DEBE declarar la partición de validación de la Etapa 0 y
  el harness DEBE verificarla contra el código.

### Protocolo congelado para la Corrida 4 (no se toca después de lanzar)

- Mismos datos, modelo e hiperparámetros que la Corrida 3 (`ENTRENAMIENTOS.md`): 15 épocas, batch 8,
  `lr` 1e-4, `denseblock4` + `norm5` descongelados, factor 0,1 para el backbone, semilla 42. **Lo único
  que cambia es la partición.**
- Validación: un pliegue de una partición estratificada por grupos en 5 (aprox. 20 %).
- Métrica principal: balanced accuracy sobre la validación, con IC 95 % por bootstrap. Umbral de
  promoción sin cambios: 0,90.
- Se informa el resultado **aunque sea peor** que el de la Corrida 3, junto a la comparación.
- Se guarda el mejor checkpoint por `val_balanced_acc`, igual que antes. Limitación conocida y
  declarada: elegir la mejor época mirando la validación vuelve optimista esa misma métrica; un
  conjunto de prueba separado queda para el incremento 2.

## Success Criteria *(mandatory)*

- **SC-001**: 0 grupos de paciente compartidos entre entrenamiento y validación en el dataset real.
- **SC-002**: La fracción de validación queda entre 15 % y 25 % de las imágenes y las dos clases están
  presentes en ambos lados.
- **SC-003**: La Corrida 4 queda registrada en `ENTRENAMIENTOS.md` con duración real, métricas con
  intervalo y la comparación con la Corrida 3.
- **SC-004**: `python -m harness` en verde, con el campo nuevo del contrato en `ok`.

## Assumptions

- El identificador de la metadata identifica al paciente (o a su ficha). Si el equipo confirma que el
  sufijo distingue animales distintos, la agrupación sigue siendo válida, solo más conservadora.
- No se agrupa por nombre del animal: los nombres comunes se repiten entre animales distintos.
