# Research: Clasificador de Etapa 0 — Tórax vs. No-Tórax

## Decisión 1: Redefinir `VetVisionEtapa0Dataset` en vez de crear una clase paralela

**Decision**: `VetVisionEtapa0Dataset` pasa a derivar una etiqueta binaria (`TORAX`/`NO_TORAX`) en
vez de una de 6 regiones. No se crea `VetVisionToraxDataset` como clase separada.

**Rationale**: el spec (`spec.md`, Input) es explícito: "Etapa 0 debe ser binaria", no "agregar una
Etapa 0b". Mantener dos clases para el mismo concepto de Etapa 0 sería duplicar lógica de carga de
imagen sin ninguna necesidad real — nadie va a entrenar el clasificador de 6 regiones en paralelo.

**Alternatives considered**:
- *Clase nueva, dejar la vieja intacta "por si acaso"* — rechazado por el Principio V: no hay un
  caso de uso real para el clasificador de 6 regiones una vez que Etapa 0 se redefine.

## Decisión 2: `src/model.py` no se modifica

**Decision**: `build_model_etapa0(num_classes=2)` reemplaza a `num_classes=5` en la llamada desde
`train.py`/`evaluate.py`/`export_onnx.py` — ningún cambio en `model.py` mismo.

**Rationale**: `build_model_etapa0` y `DenseNetEtapa0` ya reciben `num_classes` como parámetro
genérico — el backbone preentrenado y el freeze no dependen del número de clases de salida, solo
la última capa lineal (`nn.Linear(in_features, num_classes)`), que ya se construye dinámicamente.

## Decisión 3: Métrica de evaluación — `balanced_accuracy_score` de scikit-learn

**Decision**: `src/evaluate.py` agrega `balanced_accuracy_score` (ya en `requirements.txt` vía
`scikit-learn`) y evalúa el umbral de promoción (`UMBRAL_PROMOCION_ACC`) contra esa métrica, no
contra accuracy simple.

**Rationale**: si el dataset real resulta desbalanceado (ver Assumptions del spec — no se conoce
la proporción exacta TORAX/NO_TORAX sobre los ~8000 estudios completos, solo sobre la muestra de
500 vista antes, que era ~49/51), una accuracy simple alta podría ocultar que el modelo casi
siempre predice la clase mayoritaria. `balanced_accuracy_score` promedia el recall por clase,
así que no se infla con desbalance.

**Alternatives considered**:
- *Solo F1* — rechazado: F1 estándar de scikit-learn es binario por defecto (asume una clase
  "positiva"), lo cual es razonable acá pero menos intuitivo como criterio único de promoción que
  una exactitud balanceada; se mantienen ambas métricas, balanced accuracy como criterio de
  promoción y F1 como métrica complementaria (igual que ya hacía `evaluate.py` con F1 macro antes).
- *Reescribir el umbral existente (0.85) tal cual* — rechazado: SC-002 del spec pide 90%, y el
  umbral anterior era para un problema de 6 clases (más difícil) — no hay razón para heredarlo sin
  revisar.

## Decisión 4: Qué se loguea a MLflow (Principio IV)

**Decision**: los params/metrics logueados a MLflow se limitan a: conteos (n_train, n_val,
n_excluidos_desconocida), hiperparámetros (epochs, batch_size, lr, freeze_backbone), y métricas
(train_loss, val_loss, val_acc, balanced_accuracy, f1). Nunca un ID de paciente, nombre, ni ruta de
archivo que contenga esos datos.

**Rationale**: Principio IV — MLflow corre local (sin remoto configurado todavía, ver
`.dvc/config`), pero sus runs son justamente el tipo de artefacto que alguien podría compartir sin
pensarlo dos veces (un screenshot, un link). Ningún run de esta feature debe poder identificar a un
paciente aunque se comparta fuera del equipo.

**Alternatives considered**:
- *Loguear la lista de estudios excluidos con su ID* — rechazado: el conteo alcanza para auditar
  (FR-003 solo pide reportar cuántos, no cuáles); loguear IDs sería innecesario y arriesgado.

## Decisión 5: Test de la función de etiquetado, no del entrenamiento

**Decision**: se testea `region_a_etiqueta_binaria()` (determinística) con casos sintéticos, no se
escribe un test que entrene un modelo real.

**Rationale**: entrenar un modelo real en un test de CI sería lento, no determinístico (pesos
aleatorios, orden de batches), y no aporta más certeza que ya dan SC-002/SC-003 medidos en la
corrida real — el Principio III (test-first) tampoco lo exige, ya que no aplica a este archivo (ver
Constitution Check del plan).
