# Contracts: interfaces internas — Etapa 0 binaria

## `src/dataset.py` (modificado)

```python
ETIQUETAS_A_IDX: dict[str, int]  # {"NO_TORAX": 0, "TORAX": 1} — reemplaza REGIONES_A_IDX

def region_a_etiqueta_binaria(region: str) -> str | None:
    """FR-002/FR-003. "TORAX" -> "TORAX"; cualquier otra region valida conocida
    -> "NO_TORAX"; "DESCONOCIDA" (o cualquier valor no reconocido) -> None,
    que el llamador interpreta como "excluir este estudio"."""

class VetVisionEtapa0Dataset(Dataset):
    n_excluidos_desconocida: int  # NUEVO, expuesto tras __init__

    def __init__(self, data_dir, transform=None):
        """Igual que hoy, pero usa region_a_etiqueta_binaria() en vez de
        REGIONES_A_IDX para decidir la etiqueta de cada estudio; incrementa
        n_excluidos_desconocida en vez de simplemente `continue` cuando
        region_a_etiqueta_binaria() devuelve None."""
```

## `src/evaluate.py` (modificado)

```python
UMBRAL_PROMOCION_ACC = 0.90  # antes 0.85 — ver research.md Decision 3

def evaluate(data_dir, model_path, batch_size=8) -> dict:
    """Retorna {"accuracy": float, "balanced_accuracy": float, "f1_macro": float,
    "promovible": bool}. `promovible` ahora se calcula contra balanced_accuracy,
    no contra accuracy simple."""
```

## `src/train.py` (modificado, sin cambio de firma pública)

`train()` sigue con la misma firma; internamente, después de construir el
`VetVisionEtapa0Dataset`, debe loguear a MLflow `dataset.n_excluidos_desconocida`
como param (ver `research.md` Decisión 4 — nunca loguear IDs de estudios
individuales, solo el conteo).

## `src/model.py`, `src/export_onnx.py`

Sin cambios de firma — `build_model_etapa0(num_classes)` ya es genérico; ambos
archivos pasan a invocarse con `num_classes=len(ETIQUETAS_A_IDX)` (2) en vez de
`len(REGIONES_A_IDX)` (6), vía el import actualizado desde `src/dataset.py`.
