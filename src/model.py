import torch
import torch.nn as nn
import torchxrayvision as xrv


class DenseNetEtapa0(nn.Module):
    """
    Clasificador binario TORAX/NO_TORAX. Backbone DenseNet-121 pre-entrenado
    en tórax humano (TorchXRayVision), transfer learning con head nuevo.
    """

    def __init__(self, num_classes, weights="densenet121-res224-all", freeze_backbone=True,
                 unfreeze_layers=None):
        """unfreeze_layers: nombres de submódulos de self.features que quedan
        entrenables aunque freeze_backbone=True (ej. ["denseblock4", "norm5"]
        para fine-tuning parcial del ultimo bloque - las capas mas tempranas
        capturan features genericas que conviene no tocar con poco dato; ver
        ENTRENAMIENTOS.md Corrida 2, donde el backbone 100% congelado se
        estanco en ~85%)."""
        super().__init__()
        base = xrv.models.DenseNet(weights=weights)
        self.features = base.features
        in_features = base.classifier.in_features

        unfreeze_layers = unfreeze_layers or []
        if freeze_backbone:
            for name, p in self.features.named_parameters():
                p.requires_grad = any(name.startswith(capa) for capa in unfreeze_layers)

        self.pool = nn.AdaptiveAvgPool2d(1)
        self.classifier = nn.Linear(in_features, num_classes)

    def forward(self, x):
        x = self.features(x)
        x = torch.relu(x)
        x = self.pool(x).flatten(1)
        return self.classifier(x)


def build_model_etapa0(num_classes=5, freeze_backbone=True, unfreeze_layers=None):
    return DenseNetEtapa0(
        num_classes=num_classes, freeze_backbone=freeze_backbone, unfreeze_layers=unfreeze_layers
    )
