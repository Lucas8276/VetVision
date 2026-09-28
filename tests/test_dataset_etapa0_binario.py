import cv2
import numpy as np

from src.dataset import ETIQUETAS_A_IDX, VetVisionEtapa0Dataset, region_a_etiqueta_binaria


def test_region_torax_es_torax():
    assert region_a_etiqueta_binaria("TORAX") == "TORAX"


def test_regiones_no_torax_son_no_torax():
    for region in ("CERVICAL", "ABDOMEN", "PELVIS", "EXTREMIDADES", "CRANEO"):
        assert region_a_etiqueta_binaria(region) == "NO_TORAX"


def test_region_desconocida_es_none():
    assert region_a_etiqueta_binaria("DESCONOCIDA") is None


def _escribir_estudio(carpeta, nombre, region, menu):
    contenido = (
        f"ID del paciente: 1\n"
        f"Región anatómica: {region}\n"
        f"Nombre del menú de exposición: {menu}\n"
    )
    (carpeta / f"{nombre}.txt").write_text(contenido, encoding="utf-8")
    (carpeta / f"{nombre}.jpg").write_bytes(b"contenido-jpg-irrelevante-para-listar-samples")


def test_vetvision_etapa0_dataset_excluye_desconocida_y_cuenta(tmp_path):
    _escribir_estudio(tmp_path, "e1", "TORAX", "TORAX VD CANINO")
    _escribir_estudio(tmp_path, "e2", "CHEST", "ESOFAGO CANINO")
    _escribir_estudio(tmp_path, "e3", "PELVIS", "PELVIS VD CANINO")
    _escribir_estudio(tmp_path, "e4", "RARO", "RARO SIN REGION CANINO")

    dataset = VetVisionEtapa0Dataset(tmp_path)

    assert len(dataset) == 3
    assert dataset.n_excluidos_desconocida == 1

    etiquetas = sorted(label for _, label in dataset.samples)
    assert etiquetas == sorted([ETIQUETAS_A_IDX["TORAX"], ETIQUETAS_A_IDX["TORAX"], ETIQUETAS_A_IDX["NO_TORAX"]])


def test_no_empareja_jpg_de_otro_paciente_por_coincidencia_de_prefijo(tmp_path):
    """Regresion: FCR1.txt no debe terminar emparejado con FCR10.jpg o
    FCR100.jpg solo porque el nombre empieza igual. Antes de la correccion,
    _encontrar_jpg_pesado usaba glob(f"{stem}*.jpg") (coincidencia de
    prefijo); ahora usa lookup por stem exacto."""
    _escribir_estudio(tmp_path, "FCR1", "TORAX", "TORAX VD CANINO")
    # jpg de otro estudio que arranca con el mismo prefijo, sin su propio .txt
    (tmp_path / "FCR10.jpg").write_bytes(b"jpg-de-otro-paciente")
    (tmp_path / "FCR100.jpg").write_bytes(b"jpg-de-otro-paciente-mas")

    dataset = VetVisionEtapa0Dataset(tmp_path)

    assert len(dataset) == 1
    jpg_path, _ = dataset.samples[0]
    assert jpg_path.name == "FCR1.jpg"


def test_getitem_devuelve_1_canal_en_rango_torchxrayvision(tmp_path):
    """Regresion: el backbone de TorchXRayVision (src/model.py) espera 1
    canal (no 3/RGB) y un rango ~[-1024, 1024] (no [0,1] ni imagenet_mean_std).
    Sin esto, el forward pass del modelo falla con un RuntimeError de shape."""
    _escribir_estudio(tmp_path, "e1", "TORAX", "TORAX VD CANINO")
    imagen_sintetica = np.random.randint(0, 256, (300, 300), dtype=np.uint8)
    cv2.imwrite(str(tmp_path / "e1.jpg"), imagen_sintetica)  # sobreescribe el placeholder

    dataset = VetVisionEtapa0Dataset(tmp_path)
    tensor, _ = dataset[0]

    assert tensor.shape == (1, 512, 512)
    assert tensor.min() >= -1024.0
    assert tensor.max() <= 1024.0
