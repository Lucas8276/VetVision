import torch
import torch.nn as nn
import torchxrayvision as xrv


class DenseNetEtapa0(nn.Module):
    """
    Clasificador de región anatómica. Backbone DenseNet-121 pre-entrenado
    en tórax humano (TorchXRayVision), transfer learning con head nuevo.
    """

    def __init__(self, num_classes, weights="densenet121-res224-all", freeze_backbone=True):
        super().__init__()
        base = xrv.models.DenseNet(weights=weights)
        self.features = base.features
        in_features = base.classifier.in_features

        if freeze_backbone:
            for p in self.features.parameters():
                p.requires_grad = False

        self.pool = nn.AdaptiveAvgPool2d(1)
        self.classifier = nn.Linear(in_features, num_classes)

    def forward(self, x):
        x = self.features(x)
        x = torch.relu(x)
        x = self.pool(x).flatten(1)
        return self.classifier(x)


def build_model_etapa0(num_classes=5, freeze_backbone=True):
    return DenseNetEtapa0(num_classes=num_classes, freeze_backbone=freeze_backbone)
