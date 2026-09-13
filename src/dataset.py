from pathlib import Path

import torch
from torch.utils.data import Dataset

from src.parser_fcr import parsear_metadata_fcr, REGIONES_VALIDAS
from src.preprocessing import normalizar_jpg_veterinario

REGIONES_A_IDX = {region: i for i, region in enumerate(sorted(REGIONES_VALIDAS))}


class VetVisionEtapa0Dataset(Dataset):
    """
    Dataset de PyTorch para Etapa 0 (clasificación por región anatómica).
    Usa metadata automática del .txt, sin depender de la anotación clínica
    todavía pendiente. Asume que cada paciente tiene un .txt y un jpg pesado
    con el mismo stem (ajustar _encontrar_jpg_pesado si limpiar_datos_fcr.py
    usa otra convención de nombres).
    """

    def __init__(self, data_dir, transform=None):
        self.data_dir = Path(data_dir)
        self.transform = transform
        self.samples = []

        for txt_path in sorted(self.data_dir.glob("*.txt")):
            metadata = parsear_metadata_fcr(txt_path)
            region = metadata["region"]
            if region not in REGIONES_A_IDX:
                continue

            jpg_path = self._encontrar_jpg_pesado(txt_path)
            if jpg_path is None:
                continue

            self.samples.append((jpg_path, REGIONES_A_IDX[region]))

    def _encontrar_jpg_pesado(self, txt_path):
        candidato = txt_path.with_name(txt_path.stem + "_pesado.jpg")
        if candidato.exists():
            return candidato
        candidatos = list(txt_path.parent.glob(f"{txt_path.stem}*.jpg"))
        return candidatos[0] if candidatos else None

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        jpg_path, label = self.samples[idx]
        img = normalizar_jpg_veterinario(jpg_path)
        if self.transform:
            img = self.transform(image=img)["image"]
        else:
            img = torch.from_numpy(img).permute(2, 0, 1).float() / 255.0
        return img, label
