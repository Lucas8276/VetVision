"""Particion entrenamiento/validacion por paciente (specs/007-evaluacion-modelo, incremento 1)."""
import cv2
import numpy as np

from src.dataset import VetVisionEtapa0Dataset
from src.particion import PARTICION_POR_DEFECTO, grupo_paciente, huella_particion, particion_por_grupos

# Identificadores ficticios; el sufijo distinto se arma por partes para no parecer un ID real.
ID_A = "123-4"
ID_A_OTRO_SUFIJO = "123" + "-" + "9"
ID_B = "456-7"


def test_grupo_ignora_sufijo_espacios_y_mayusculas():
    assert grupo_paciente(ID_A) == grupo_paciente(ID_A_OTRO_SUFIJO)
    assert grupo_paciente(ID_A) == grupo_paciente("  " + ID_A + " ")
    assert grupo_paciente("abc") == grupo_paciente(" ABC ")
    assert grupo_paciente(ID_A) != grupo_paciente(ID_B)


def test_grupo_sin_identificador_es_none():
    assert grupo_paciente(None) is None
    assert grupo_paciente("   ") is None


def test_grupo_es_un_hash_no_el_identificador():
    g = grupo_paciente(ID_A)
    assert g != "123" and len(g) == 16 and all(c in "0123456789abcdef" for c in g)


def _datos_sinteticos(n_grupos=60, seed=0):
    rng = np.random.default_rng(seed)
    grupos, etiquetas = [], []
    for g in range(n_grupos):
        for _ in range(int(rng.integers(1, 7))):  # entre 1 y 6 placas por paciente
            grupos.append(f"g{g}")
            etiquetas.append(int(rng.integers(0, 2)))
    return etiquetas, grupos


def test_particion_no_comparte_grupos_y_respeta_proporcion():
    etiquetas, grupos = _datos_sinteticos()
    train, val = particion_por_grupos(etiquetas, grupos, val_split=0.2, seed=42)
    assert sorted(train + val) == list(range(len(etiquetas)))
    assert not ({grupos[i] for i in train} & {grupos[i] for i in val})
    assert 0.15 <= len(val) / len(etiquetas) <= 0.25
    assert {etiquetas[i] for i in train} == {0, 1} == {etiquetas[i] for i in val}


def test_particion_es_determinista_y_depende_de_la_semilla():
    etiquetas, grupos = _datos_sinteticos()
    a = particion_por_grupos(etiquetas, grupos, seed=42)
    assert a == particion_por_grupos(etiquetas, grupos, seed=42)
    assert a[1] != particion_por_grupos(etiquetas, grupos, seed=7)[1]
    assert huella_particion(a[1]) == huella_particion(list(reversed(a[1])))
    assert huella_particion(a[1]) != huella_particion(a[0])


def test_sin_identificador_cada_estudio_es_su_propio_grupo():
    etiquetas = [0, 1] * 20
    train, val = particion_por_grupos(etiquetas, [None] * 40, seed=42)
    assert len(val) == 8 and len(train) == 32


def test_particion_por_defecto_es_por_paciente():
    assert PARTICION_POR_DEFECTO == "paciente"


def test_dataset_expone_grupos_alineados_con_samples(tmp_path):
    for nombre, pid in (("FCR1", ID_A), ("FCR2", ID_A_OTRO_SUFIJO), ("FCR3", ID_B)):
        cv2.imwrite(str(tmp_path / f"{nombre}.jpg"), np.full((64, 64), 128, np.uint8))
        (tmp_path / f"{nombre}.txt").write_text(
            f"ID del paciente: {pid}\nRegión anatómica: CHEST\n", encoding="utf-8")
    ds = VetVisionEtapa0Dataset(tmp_path)
    assert len(ds.grupos) == len(ds.samples) == 3
    assert ds.grupos[0] == ds.grupos[1] != ds.grupos[2]
