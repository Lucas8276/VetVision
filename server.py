"""
Servidor local minimo que conecta la demo visual ("VetVision Demo.dc.html")
con el modelo real de Etapa 0. Corre por separado del HTML - dejalo corriendo
en una terminal mientras abris el HTML en el navegador.

Uso: python server.py
Expone: POST /clasificar  (multipart, campo "imagen") -> {label, confidence, confidences}

Reusa la misma logica de src/preprocessing.py y src/model.py que ya se valido
en ENTRENAMIENTOS.md - no reimplementa nada en JS, para no arriesgar un
resultado distinto al que se midio (balanced_accuracy=92.45%).
"""

import tempfile
from pathlib import Path

import torch
import torchxrayvision as xrv
from flask import Flask, jsonify, request
from flask_cors import CORS

from src.dataset import ETIQUETAS_A_IDX
from src.model import build_model_etapa0
from src.preprocessing import normalizar_jpg_veterinario

MODEL_PATH = "models/etapa0_region.pt"

app = Flask(__name__)
CORS(app)  # el HTML puede abrirse como archivo local o en otro puerto - necesita CORS

_modelo = build_model_etapa0(num_classes=len(ETIQUETAS_A_IDX))
_modelo.load_state_dict(torch.load(MODEL_PATH, map_location="cpu"))
_modelo.eval()
_idx_a_etiqueta = {v: k for k, v in ETIQUETAS_A_IDX.items()}


@app.post("/clasificar")
def clasificar():
    archivo = request.files.get("imagen")
    if archivo is None:
        return jsonify({"error": "falta el campo 'imagen'"}), 400

    sufijo = Path(archivo.filename or "imagen.jpg").suffix or ".jpg"
    with tempfile.NamedTemporaryFile(suffix=sufijo, delete=False) as tmp:
        archivo.save(tmp.name)
        tmp_path = tmp.name

    try:
        img = normalizar_jpg_veterinario(tmp_path)
    except Exception as e:
        return jsonify({"error": f"no se pudo leer la imagen: {e}"}), 400
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    img = xrv.utils.normalize(img, maxval=255, reshape=True)
    x = torch.from_numpy(img).float().unsqueeze(0)

    with torch.no_grad():
        logits = _modelo(x)
        probs = torch.softmax(logits, dim=1)[0]

    idx = int(probs.argmax())
    etiqueta = _idx_a_etiqueta[idx]
    return jsonify(
        {
            "label": etiqueta,
            "confidence": float(probs[idx]) * 100,
            "confidences": {_idx_a_etiqueta[i]: float(probs[i]) * 100 for i in range(len(probs))},
        }
    )


@app.get("/salud")
def salud():
    return jsonify({"ok": True})


if __name__ == "__main__":
    print("Servidor de VetVision Etapa 0 en http://127.0.0.1:5001")
    print("Dejalo corriendo y abri 'VetVision Demo.dc.html' en el navegador.")
    app.run(port=5001)
