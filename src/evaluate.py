import argparse
import json
from pathlib import Path

import torch
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score
from torch.utils.data import DataLoader, Subset

from src.dataset import VetVisionEtapa0Dataset, ETIQUETAS_A_IDX
from src.model import build_model_etapa0

UMBRAL_PROMOCION_ACC = 0.90  # sobre balanced_accuracy, no accuracy simple (ver research.md
                              # de la feature 002-etapa0-torax-clasificador, Decision 3)


def evaluate(data_dir, model_path, batch_size=8, val_indices_path=None):
    """Si val_indices_path existe (por defecto, el que genera src.train junto
    al checkpoint), evalua solo sobre ese held-out real. Si no existe, evalua
    sobre TODO data_dir - lo cual, si data_dir es el mismo usado para
    entrenar, infla la metrica porque incluye imagenes ya vistas. Se avisa
    explicitamente en ese caso."""
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    dataset = VetVisionEtapa0Dataset(data_dir)

    if val_indices_path is None:
        val_indices_path = str(Path(model_path).with_name(
            Path(model_path).stem + "_val_indices.json"
        ))

    if Path(val_indices_path).exists():
        with open(val_indices_path, encoding="utf-8") as f:
            indices = json.load(f)
        dataset = Subset(dataset, indices)
        print(f"Evaluando sobre held-out real: {len(dataset)} imagenes (de {val_indices_path})")
    else:
        print(
            f"AVISO: no se encontro {val_indices_path} - evaluando sobre TODO "
            f"data_dir ({len(dataset)} imagenes). Si data_dir es el mismo usado "
            f"para entrenar, esta metrica esta inflada (incluye imagenes ya vistas)."
        )

    loader = DataLoader(dataset, batch_size=batch_size)

    model = build_model_etapa0(num_classes=len(ETIQUETAS_A_IDX))
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.to(device).eval()

    y_true, y_pred = [], []
    with torch.no_grad():
        for imgs, labels in loader:
            imgs = imgs.to(device)
            outputs = model(imgs)
            y_pred.extend(outputs.argmax(1).cpu().tolist())
            y_true.extend(labels.tolist())

    acc = accuracy_score(y_true, y_pred)
    balanced_acc = balanced_accuracy_score(y_true, y_pred)
    f1 = f1_score(y_true, y_pred, average="macro")

    print(f"accuracy: {acc:.4f} - balanced_accuracy: {balanced_acc:.4f} - f1_macro: {f1:.4f}")
    promovible = balanced_acc >= UMBRAL_PROMOCION_ACC
    print(f"promovible a producción: {promovible} (umbral balanced_accuracy: {UMBRAL_PROMOCION_ACC})")
    return {
        "accuracy": acc,
        "balanced_accuracy": balanced_acc,
        "f1_macro": f1,
        "promovible": promovible,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default="data/processed")
    parser.add_argument("--model-path", default="models/etapa0_region.pt")
    parser.add_argument("--val-indices-path", default=None)
    args = parser.parse_args()
    evaluate(args.data_dir, args.model_path, val_indices_path=args.val_indices_path)
