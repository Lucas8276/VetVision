# Data Model: Clasificador de Etapa 0 — Tórax vs. No-Tórax

## Entidad: Estudio etiquetado (input del dataset de entrenamiento)

Construida a partir de la metadata estructurada que ya produce
`src/parser_fcr.py::parsear_metadata_fcr` (feature 001).

| Campo | Origen | Valores | Regla |
|---|---|---|---|
| `region` | `parsear_metadata_fcr()["region"]` | `{TORAX, CERVICAL, ABDOMEN, PELVIS, EXTREMIDADES, CRANEO, DESCONOCIDA}` | sin cambio, ya corregido por feature 001 |
| `etiqueta` | derivado de `region` | `{TORAX, NO_TORAX, None}` | `TORAX` si `region=="TORAX"`; `NO_TORAX` si `region` es cualquier otra región válida conocida; `None` (excluido) si `region=="DESCONOCIDA"` (FR-002, FR-003) |
| `imagen` | jpg "pesado" encontrado por `_encontrar_jpg_pesado` | path | sin cambio; si no se encuentra, el estudio se excluye igual que hoy (comportamiento ya existente, no modificado por esta feature) |

## Entidad: Dataset de entrenamiento (`VetVisionEtapa0Dataset`, modificado)

| Atributo | Tipo | Notas |
|---|---|---|
| `samples` | `list[(Path, int)]` | igual que hoy, pero el índice ahora viene de `ETIQUETAS_A_IDX` (2 clases), no de `REGIONES_A_IDX` (6) |
| `n_excluidos_desconocida` | `int` | NUEVO — cuenta los estudios saltados por `region == "DESCONOCIDA"` (FR-003); expuesto para que `train.py` lo loguee |

`ETIQUETAS_A_IDX = {"NO_TORAX": 0, "TORAX": 1}` — reemplaza a `REGIONES_A_IDX` como el mapping que
consume `src/model.py::build_model_etapa0(num_classes=len(ETIQUETAS_A_IDX))`.

## Entidad: Resultado de evaluación (`src/evaluate.py`, modificado)

| Campo | Tipo | Notas |
|---|---|---|
| `accuracy` | float | ya existía |
| `balanced_accuracy` | float | NUEVO — `sklearn.metrics.balanced_accuracy_score` |
| `f1_macro` | float | ya existía (nombre sin cambio) |
| `promovible` | bool | ahora se calcula contra `balanced_accuracy >= UMBRAL_PROMOCION_ACC` (0.90), no contra `accuracy` |

## Transición: de metadata a etiqueta

```
region (de parsear_metadata_fcr)
   │
   ├─ "TORAX" ──────────────────────────► etiqueta = TORAX
   ├─ "CERVICAL"/"ABDOMEN"/"PELVIS"/
   │  "EXTREMIDADES"/"CRANEO" ──────────► etiqueta = NO_TORAX
   └─ "DESCONOCIDA" ────────────────────► etiqueta = None (excluido del dataset,
                                            n_excluidos_desconocida += 1)
```
