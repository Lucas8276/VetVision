import argparse

import torch
from sklearn.metrics import accuracy_score, f1_score
from torch.utils.data import DataLoader

from src.dataset import VetVisionEtapa0Dataset, REGIONES_A_IDX
from src.model import build_model_etapa0

UMBRAL_PROMOCION_ACC = 0.85


def evaluate(data_dir, model_path, batch_size=8):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    dataset = VetVisionEtapa0Dataset(data_dir)
    loader = DataLoader(dataset, batch_size=batch_size)

    model = build_model_etapa0(num_classes=len(REGIONES_A_IDX))
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
    f1 = f1_score(y_true, y_pred, average="macro")

    print(f"accuracy: {acc:.4f} - f1_macro: {f1:.4f}")
    promovible = acc >= UMBRAL_PROMOCION_ACC
    print(f"promovible a producción: {promovible} (umbral: {UMBRAL_PROMOCION_ACC})")
    return {"accuracy": acc, "f1_macro": f1, "promovible": promovible}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default="data/processed")
    parser.add_argument("--model-path", default="models/etapa0_region.pt")
    args = parser.parse_args()
    evaluate(args.data_dir, args.model_path)
