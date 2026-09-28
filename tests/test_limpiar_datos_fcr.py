import csv

import numpy as np
import pytest
from PIL import Image

import limpiar_datos_fcr as ldf


def test_decodificar_y_guardar_hq_preserva_16_bits_sin_normalizar(tmp_path, monkeypatch):
    """FR-004: el .png generado debe conservar los valores de pixel originales
    (16 bits), sin reescalarlos a 0-255."""
    array_simulado = np.array([[0, 100, 2700], [50, 65535, 12]], dtype=np.uint16)
    monkeypatch.setattr(ldf, "decode_jpeg_lossless", lambda data: array_simulado)

    hq_path = tmp_path / "FCR1.hq"
    hq_path.write_bytes(b"contenido-hq-irrelevante-porque-decode-esta-mockeado")
    carpeta_destino = tmp_path / "conservados"
    carpeta_destino.mkdir()

    destino_png = ldf.decodificar_y_guardar_hq(hq_path, carpeta_destino)

    with Image.open(destino_png) as img:
        assert img.mode == "I;16"
        resultado = np.array(img)
    assert np.array_equal(resultado, array_simulado)


def test_hq_que_falla_al_decodificar_va_a_revisar_y_no_interrumpe_el_lote(tmp_path, monkeypatch):
    """FR-009: si un .hq falla al decodificar, ese estudio va a REVISAR con el
    motivo registrado, y el resto del lote se sigue procesando."""

    def decode_que_falla(data):
        raise ValueError("archivo .hq corrupto de prueba")

    monkeypatch.setattr(ldf, "decode_jpeg_lossless", decode_que_falla)

    origen = tmp_path / "origen"
    origen.mkdir()
    (origen / "FCR1.hq").write_bytes(b"hq-corrupto")
    (origen / "FCR2.jpg").write_bytes(b"x" * (ldf.UMBRAL_JPG_GRANDE + 1))

    dir_conservados = tmp_path / "CONSERVADOS"
    dir_sobrantes = tmp_path / "SOBRANTES"
    dir_revisar = tmp_path / "REVISAR"
    reporte = tmp_path / "reporte.csv"

    ldf.procesar(
        str(origen), str(dir_conservados), str(dir_sobrantes), str(dir_revisar),
        str(reporte), confirmar=True,
    )

    with open(reporte, encoding="utf-8") as f:
        filas = {row["ruta_original"].split("\\")[-1].split("/")[-1]: row for row in csv.DictReader(f)}

    assert filas["FCR1.hq"]["accion"] == "REVISAR"
    assert "error al decodificar hq" in filas["FCR1.hq"]["motivo"]
    assert (dir_revisar / "FCR1.hq").exists()

    assert filas["FCR2.jpg"]["accion"] == "CONSERVAR"
    assert (dir_conservados / "FCR2.jpg").exists()
