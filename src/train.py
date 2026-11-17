import argparse
import json
from pathlib import Path

import copy

import mlflow
import torch
from sklearn.metrics import balanced_accuracy_score
from torch import nn, optim
from torch.utils.data import DataLoader, Subset, random_split

from src.dataset import VetVisionEtapa0Dataset, ETIQUETAS_A_IDX
from src.model import build_model_etapa0
from src.particion import PARTICION_POR_DEFECTO, PARTICIONES_VALIDAS, huella_particion, particion_por_grupos


def train(data_dir, epochs=15, batch_size=8, lr=1e-4, val_split=0.2, freeze_backbone=True, seed=42,
          unfreeze_layers=None, backbone_lr_factor=0.1, split=PARTICION_POR_DEFECTO,
          model_path="models/etapa0_region.pt", sobrescribir=False):
    """unfreeze_layers: ver DenseNetEtapa0. backbone_lr_factor: los parametros
    del backbone que queden entrenables usan lr * backbone_lr_factor (mas
    bajo que la cabeza nueva), para no destruir los pesos preentrenados de
    un salto - practica estandar de fine-tuning parcial.

    split: "paciente" (por defecto) deja todas las placas de un mismo paciente del mismo lado
    (specs/007-evaluacion-modelo); "imagen" es la particion al azar por imagen de las corridas
    1 a 3, que mezcla pacientes entre entrenamiento y validacion y solo se conserva para
    reproducirlas. model_path: donde se guarda el mejor checkpoint; no se pisa uno existente
    salvo sobrescribir=True."""
    if split not in PARTICIONES_VALIDAS:
        raise ValueError(f"split debe ser uno de {PARTICIONES_VALIDAS}")
    model_path = Path(model_path)
    val_indices_path = model_path.with_name(model_path.stem + "_val_indices.json")
    if model_path.exists() and not sobrescribir:
        raise FileExistsError(
            f"{model_path} ya existe: elegir otro --model-path o pasar --sobrescribir "
            f"(asi no se pierde el checkpoint de una corrida anterior).")
    torch.manual_seed(seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    dataset = VetVisionEtapa0Dataset(data_dir)
    if split == "paciente":
        etiquetas = [etiqueta for _, etiqueta in dataset.samples]
        idx_train, idx_val = particion_por_grupos(etiquetas, dataset.grupos, val_split=val_split, seed=seed)
        train_ds, val_ds = Subset(dataset, idx_train), Subset(dataset, idx_val)
    else:
        n_val = int(len(dataset) * val_split)
        generator = torch.Generator().manual_seed(seed)
        train_ds, val_ds = random_split(dataset, [len(dataset) - n_val, n_val], generator=generator)
    n_train, n_val = len(train_ds), len(val_ds)
    grupos_train = {dataset.grupos[i] for i in train_ds.indices}
    grupos_val = {dataset.grupos[i] for i in val_ds.indices}
    n_grupos_compartidos = len((grupos_train & grupos_val) - {None})
    print(f"particion '{split}': {n_train} train / {n_val} val - grupos de paciente compartidos: "
          f"{n_grupos_compartidos}", flush=True)

    # Los indices de validacion se guardan ANTES de entrenar: si la corrida se interrumpe, el
    # mejor checkpoint parcial igual se puede evaluar sobre el held-out correcto.
    model_path.parent.mkdir(parents=True, exist_ok=True)
    with open(val_indices_path, "w", encoding="utf-8") as f:
        json.dump([int(i) for i in val_ds.indices], f)

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
            "split": split,
            "seed": seed,
            "n_grupos_train": len(grupos_train),
            "n_grupos_val": len(grupos_val),
            "n_grupos_compartidos": n_grupos_compartidos,
            "huella_particion_val": huella_particion(val_ds.indices),
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
                # Se escribe a disco en cada mejora: una interrupcion no pierde lo ya entrenado.
                torch.save(best_state_dict, model_path)

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

        torch.save(best_state_dict, model_path)
        mlflow.log_artifact(str(model_path))

        # Persistir que imagenes quedaron en validacion (no en el split de
        # entrenamiento), para que evaluate.py pueda medir sobre un held-out
        # real en vez de sobre el dataset completo (que incluiria imagenes ya
        # vistas en entrenamiento e infla la metrica). Ver evaluate.py.
        mlflow.log_artifact(str(val_indices_path))

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
    parser.add_argument("--split", choices=PARTICIONES_VALIDAS, default=PARTICION_POR_DEFECTO,
                        help="paciente (por defecto): ninguna placa de un paciente queda en train y val a "
                             "la vez. imagen: particion al azar por imagen de las corridas 1 a 3.")
    parser.add_argument("--model-path", default="models/etapa0_region.pt")
    parser.add_argument("--sobrescribir", action="store_true",
                        help="Permite pisar un checkpoint existente en --model-path.")
    args = parser.parse_args()
    unfreeze_layers = [s for s in args.unfreeze_layers.split(",") if s]
    train(
        args.data_dir, epochs=args.epochs, batch_size=args.batch_size, lr=args.lr, seed=args.seed,
        unfreeze_layers=unfreeze_layers, backbone_lr_factor=args.backbone_lr_factor,
        split=args.split, model_path=args.model_path, sobrescribir=args.sobrescribir,
    )
