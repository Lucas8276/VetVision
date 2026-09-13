import argparse
from pathlib import Path

import mlflow
import torch
from torch import nn, optim
from torch.utils.data import DataLoader, random_split

from src.dataset import VetVisionEtapa0Dataset, REGIONES_A_IDX
from src.model import build_model_etapa0


def train(data_dir, epochs=15, batch_size=8, lr=1e-4, val_split=0.2, freeze_backbone=True):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    dataset = VetVisionEtapa0Dataset(data_dir)
    n_val = int(len(dataset) * val_split)
    n_train = len(dataset) - n_val
    train_ds, val_ds = random_split(dataset, [n_train, n_val])

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size)

    model = build_model_etapa0(num_classes=len(REGIONES_A_IDX), freeze_backbone=freeze_backbone).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(filter(lambda p: p.requires_grad, model.parameters()), lr=lr)

    mlflow.set_experiment("sadrv-vetvision-etapa0")
    with mlflow.start_run():
        mlflow.log_params({
            "epochs": epochs,
            "batch_size": batch_size,
            "lr": lr,
            "freeze_backbone": freeze_backbone,
            "n_train": n_train,
            "n_val": n_val,
        })

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
            correct, val_loss = 0, 0.0
            with torch.no_grad():
                for imgs, labels in val_loader:
                    imgs, labels = imgs.to(device), labels.to(device)
                    outputs = model(imgs)
                    loss = criterion(outputs, labels)
                    val_loss += loss.item() * imgs.size(0)
                    correct += (outputs.argmax(1) == labels).sum().item()
            val_loss /= max(n_val, 1)
            val_acc = correct / max(n_val, 1)

            mlflow.log_metrics(
                {"train_loss": train_loss, "val_loss": val_loss, "val_acc": val_acc}, step=epoch
            )
            print(
                f"epoch {epoch + 1}/{epochs} - train_loss {train_loss:.4f} "
                f"- val_loss {val_loss:.4f} - val_acc {val_acc:.4f}"
            )

        Path("models").mkdir(exist_ok=True)
        model_path = "models/etapa0_region.pt"
        torch.save(model.state_dict(), model_path)
        mlflow.log_artifact(model_path)

    return model


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default="data/processed")
    parser.add_argument("--epochs", type=int, default=15)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--lr", type=float, default=1e-4)
    args = parser.parse_args()
    train(args.data_dir, epochs=args.epochs, batch_size=args.batch_size, lr=args.lr)
