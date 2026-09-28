# Quickstart: validar la feature 002-etapa0-torax-clasificador

## Prerrequisitos

```bash
venv\Scripts\activate
pip install -r requirements.txt
```

Necesita `data/processed/` poblado con pares `.txt`+jpg (salida de la feature 001 aplicada al
dataset real, con `--confirmar`). Si no está poblado todavía, este quickstart no se puede correr
de punta a punta — avisar antes de reportar la feature como validada.

## 1. Test de la función de etiquetado (FR-002, FR-003)

```bash
pytest tests/test_dataset_etapa0_binario.py -v
```

**Esperado**: pasan los casos `TORAX→TORAX`, cada región no-tórax `→NO_TORAX`, y
`DESCONOCIDA→None`.

## 2. Entrenar (Historia 2)

```bash
python -m src.train --data-dir data/processed --epochs 15 --batch-size 8 --lr 1e-4
```

**Esperado**: el log de MLflow (`mlflow ui`, experimento `sadrv-vetvision-etapa0`) muestra un
párametro `n_excluidos_desconocida` (SC-001 — solo estudios con región conocida entrenan) y
ninguna columna con nombre/ID de paciente (Principio IV).

## 3. Evaluar (Historia 2, SC-002)

```bash
python -m src.evaluate --data-dir data/processed --model-path models/etapa0_region.pt
```

**Esperado**: imprime `accuracy`, `balanced_accuracy`, `f1_macro` y `promovible` — `promovible`
debe ser `True` solo si `balanced_accuracy >= 0.90`.

## 4. Clasificar un estudio nuevo (Historia 3)

```bash
python -c "
import torch
from src.model import build_model_etapa0
from src.dataset import ETIQUETAS_A_IDX
from src.preprocessing import normalizar_jpg_veterinario

modelo = build_model_etapa0(num_classes=len(ETIQUETAS_A_IDX))
modelo.load_state_dict(torch.load('models/etapa0_region.pt', map_location='cpu'))
modelo.eval()

img = normalizar_jpg_veterinario('data/processed/ALGUN_ESTUDIO.jpg')
x = torch.from_numpy(img).permute(2, 0, 1).float().unsqueeze(0) / 255.0
with torch.no_grad():
    idx = modelo(x).argmax(1).item()
etiqueta = {v: k for k, v in ETIQUETAS_A_IDX.items()}[idx]
print(etiqueta)
"
```

**Esperado**: imprime `TORAX` o `NO_TORAX`, no un tensor/score crudo (FR-007).
