from pathlib import Path

import torch
import torchxrayvision as xrv
from torch.utils.data import Dataset

from src.parser_fcr import parsear_metadata_fcr
from src.particion import grupo_paciente
from src.preprocessing import normalizar_jpg_veterinario

ETIQUETAS_A_IDX = {"NO_TORAX": 0, "TORAX": 1}

_REGIONES_NO_TORAX = {"CERVICAL", "ABDOMEN", "PELVIS", "EXTREMIDADES", "CRANEO"}


def region_a_etiqueta_binaria(region: str):
    """FR-002/FR-003. "TORAX" -> "TORAX"; cualquier otra region valida conocida
    -> "NO_TORAX"; "DESCONOCIDA" (o cualquier valor no reconocido) -> None, que
    el llamador interpreta como "excluir este estudio del dataset"."""
    if region == "TORAX":
        return "TORAX"
    if region in _REGIONES_NO_TORAX:
        return "NO_TORAX"
    return None


class VetVisionEtapa0Dataset(Dataset):
    """
    Dataset de PyTorch para Etapa 0 (clasificación binaria TORAX/NO_TORAX).
    Usa metadata automática del .txt, sin depender de la anotación clínica
    todavía pendiente. Asume que cada paciente tiene un .txt y un jpg pesado
    con el mismo stem (ajustar _encontrar_jpg_pesado si limpiar_datos_fcr.py
    usa otra convención de nombres). Los estudios cuya región es
    "DESCONOCIDA" se excluyen explícitamente (ver n_excluidos_desconocida),
    nunca se fuerzan a una de las dos clases.
    """

    def __init__(self, data_dir, transform=None):
        self.data_dir = Path(data_dir)
        self.transform = transform
        self.samples = []
        # Grupo de paciente (hash) de cada muestra, alineado con samples: lo usa la particion
        # por paciente de src/particion.py. Nunca el identificador en claro (007, FR-004).
        self.grupos = []
        self.n_excluidos_desconocida = 0

        # Se indexan los .jpg una sola vez (por stem exacto), en vez de hacer
        # un glob por cada .txt: con miles de estudios, un glob por archivo es
        # cuasi-cuadratico y ademas glob(f"{stem}*.jpg") matchea por PREFIJO,
        # no por nombre exacto (ej. "FCR1" matchea "FCR1.jpg" pero tambien
        # "FCR10.jpg", "FCR100.jpg", ...) - podia emparejar la metadata de un
        # paciente con la imagen de otro. Ver tests/test_dataset_etapa0_binario.py.
        self._jpgs_por_stem = {p.stem: p for p in self.data_dir.glob("*.jpg")}

        for txt_path in sorted(self.data_dir.glob("*.txt")):
            metadata = parsear_metadata_fcr(txt_path)
            region = metadata["region"]
            etiqueta = region_a_etiqueta_binaria(region)
            if etiqueta is None:
                self.n_excluidos_desconocida += 1
                continue

            jpg_path = self._encontrar_jpg_pesado(txt_path)
            if jpg_path is None:
                continue

            self.samples.append((jpg_path, ETIQUETAS_A_IDX[etiqueta]))
            self.grupos.append(grupo_paciente(metadata["id_paciente"]))

    def _encontrar_jpg_pesado(self, txt_path):
        candidato_pesado = self._jpgs_por_stem.get(txt_path.stem + "_pesado")
        if candidato_pesado is not None:
            return candidato_pesado
        return self._jpgs_por_stem.get(txt_path.stem)

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        jpg_path, label = self.samples[idx]
        img = normalizar_jpg_veterinario(jpg_path)  # 2D uint8, escala de grises
        if self.transform:
            img = self.transform(image=img)["image"]
        # El backbone de TorchXRayVision espera 1 canal, rango ~[-1024, 1024]
        # (no 3 canales ni [0,1]/imagenet_mean_std) - ver research.md Decision 6.
        img = xrv.utils.normalize(img, maxval=255, reshape=True)
        img = torch.from_numpy(img).float()
        return img, label
