import argparse
import json
from pathlib import Path

import copy

import mlflow
import torch
from sklearn.metrics import balanced_accuracy_score
from torch import nn, optim
from torch.utils.data import DataLoader, random_split

from src.dataset import VetVisionEtapa0Dataset, ETIQUETAS_A_IDX
from src.model import build_model_etapa0


def train(data_dir, epochs=15, batch_size=8, lr=1e-4, val_split=0.2, freeze_backbone=True, seed=42,
          unfreeze_layers=None, backbone_lr_factor=0.1):
    """unfreeze_layers: ver DenseNetEtapa0. backbone_lr_factor: los parametros
    del backbone que queden entrenables usan lr * backbone_lr_factor (mas
    bajo que la cabeza nueva), para no destruir los pesos preentrenados de
    un salto - practica estandar de fine-tuning parcial."""
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    dataset = VetVisionEtapa0Dataset(data_dir)
    n_val = int(len(dataset) * val_split)
    n_train = len(dataset) - n_val
    generator = torch.Generator().manual_seed(seed)
    train_ds, val_ds = random_split(dataset, [n_train, n_val], generator=generator)

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size)

    model = build_model_etapa0(
        num_classes=len(ETIQUETAS_A_IDX), freeze_backbone=freeze_backbone, unfreeze_layers=unfreeze_layers
    ).to(device)
    criterion = nn.CrossEntropyLoss()

    backbone_params = [p for p in model.features.parameters() if p.requires_grad]
    param_groups = [{"params": model.classifier.parameters(), "lr": lr}]
    if backbone_params:
        param_groups.append({"params": backbone_params, "lr": lr * backbone_lr_factor})
    optimizer = optim.Adam(param_groups)

    mlflow.set_experiment("sadrv-vetvision-etapa0")
    with mlflow.start_run():
        mlflow.log_params({
            "epochs": epochs,
            "batch_size": batch_size,
            "lr": lr,
            "freeze_backbone": freeze_backbone,
            "unfreeze_layers": ",".join(unfreeze_layers) if unfreeze_layers else "",
            "backbone_lr_factor": backbone_lr_factor if backbone_params else None,
            "n_train": n_train,
            "n_val": n_val,
            # conteo, nunca IDs de estudios individuales (Principio IV)
            "n_excluidos_desconocida": dataset.n_excluidos_desconocida,
        })

        best_balanced_acc = -1.0
        best_epoch = -1
        best_state_dict = None

        for epoch in range(epochs):
            model.train()
            train_loss = 0.0
            for imgs, labels in train_loader:
                imgs, labels = imgs.to(device), labels.to(device)
                optimizer.zero_grad()
                outputs = model(imgs)
                loss = criterion(outputs, labels)
                loss.backward()
                optimizer.step()
                train_loss += loss.item() * imgs.size(0)
            train_loss /= max(n_train, 1)

            model.eval()
            val_loss = 0.0
            y_true, y_pred = [], []
            with torch.no_grad():
                for imgs, labels in val_loader:
                    imgs, labels = imgs.to(device), labels.to(device)
                    outputs = model(imgs)
                    loss = criterion(outputs, labels)
                    val_loss += loss.item() * imgs.size(0)
                    y_pred.extend(outputs.argmax(1).cpu().tolist())
                    y_true.extend(labels.tolist())
            val_loss /= max(n_val, 1)
            val_acc = sum(int(p == t) for p, t in zip(y_pred, y_true)) / max(n_val, 1)
            val_balanced_acc = balanced_accuracy_score(y_true, y_pred) if y_true else 0.0

            # Se guarda el estado del mejor epoch (por balanced_accuracy, la
            # misma metrica que usa evaluate.py para decidir "promovible"),
            # no el ultimo - sin esto, si el modelo empieza a sobreajustar
            # hacia el final, terminariamos guardando un checkpoint peor que
            # uno de una epoca anterior sin darnos cuenta.
            if val_balanced_acc > best_balanced_acc:
                best_balanced_acc = val_balanced_acc
                best_epoch = epoch + 1
                best_state_dict = copy.deepcopy(model.state_dict())

            mlflow.log_metrics(
                {
                    "train_loss": train_loss,
                    "val_loss": val_loss,
                    "val_acc": val_acc,
                    "val_balanced_acc": val_balanced_acc,
                },
                step=epoch,
            )
            print(
                f"epoch {epoch + 1}/{epochs} - train_loss {train_loss:.4f} "
                f"- val_loss {val_loss:.4f} - val_acc {val_acc:.4f} "
                f"- val_balanced_acc {val_balanced_acc:.4f}",
                flush=True,  # sin esto, el progreso no se ve en vivo cuando stdout
                             # esta redirigido a un archivo (no es una terminal)
            )

        mlflow.log_metrics({"best_epoch": best_epoch, "best_val_balanced_acc": best_balanced_acc})
        print(
            f"mejor epoch: {best_epoch}/{epochs} (val_balanced_acc {best_balanced_acc:.4f}) "
            f"- guardando ese checkpoint, no el ultimo",
            flush=True,
        )

        Path("models").mkdir(exist_ok=True)
        model_path = "models/etapa0_region.pt"
        torch.save(best_state_dict, model_path)
        mlflow.log_artifact(model_path)

        # Persistir que imagenes quedaron en validacion (no en el split de
        # entrenamiento), para que evaluate.py pueda medir sobre un held-out
        # real en vez de sobre el dataset completo (que incluiria imagenes ya
        # vistas en entrenamiento e infla la metrica). Ver evaluate.py.
        val_indices_path = "models/etapa0_region_val_indices.json"
        with open(val_indices_path, "w", encoding="utf-8") as f:
            json.dump(list(val_ds.indices), f)
        mlflow.log_artifact(val_indices_path)

        model.load_state_dict(best_state_dict)  # el objeto devuelto debe coincidir con lo guardado

    return model


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default="data/processed")
    parser.add_argument("--epochs", type=int, default=15)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--unfreeze-layers", default="",
                         help="Nombres de submodulos de features a descongelar, separados por coma "
                              "(ej. 'denseblock4,norm5'). Vacio = backbone 100% congelado (default).")
    parser.add_argument("--backbone-lr-factor", type=float, default=0.1)
    args = parser.parse_args()
    unfreeze_layers = [s for s in args.unfreeze_layers.split(",") if s]
    train(
        args.data_dir, epochs=args.epochs, batch_size=args.batch_size, lr=args.lr, seed=args.seed,
        unfreeze_layers=unfreeze_layers, backbone_lr_factor=args.backbone_lr_factor,
    )
