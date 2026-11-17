"""Tests de app/validacion.py: cada caso de entrada invalida del FR-001 (spec 004, SC-003).

Todas las imagenes son sinteticas (numpy); no se usa ningun archivo real.
"""
import cv2
import numpy as np
import pytest

from app.config import cargar_configuracion
from app.validacion import ErrorValidacion, validar_imagen
from ayudas_app import jpg_sintetico, png_sintetico

MAX = 25 * 1024 * 1024
MIN_LADO = 256


def _error(contenido, max_bytes=MAX, min_lado_px=MIN_LADO):
    with pytest.raises(ErrorValidacion) as info:
        validar_imagen(contenido, max_bytes=max_bytes, min_lado_px=min_lado_px)
    # SC-003: el mensaje tiene que decir que hacer, no solo que fallo.
    assert len(info.value.mensaje) > 20
    return info.value


def test_jpg_valido_se_acepta():
    imagen = validar_imagen(jpg_sintetico(600, 500), max_bytes=MAX, min_lado_px=MIN_LADO)
    assert (imagen.formato, imagen.ancho, imagen.alto) == ("jpg", 600, 500)


def test_png_valido_se_acepta():
    imagen = validar_imagen(png_sintetico(300, 400), max_bytes=MAX, min_lado_px=MIN_LADO)
    assert (imagen.formato, imagen.ancho, imagen.alto) == ("png", 300, 400)


def test_la_extension_no_importa_solo_el_contenido():
    # validar_imagen ni siquiera recibe el nombre: no puede dejarse engañar por la extension.
    assert validar_imagen(png_sintetico(), max_bytes=MAX, min_lado_px=MIN_LADO).formato == "png"


def test_archivo_vacio():
    assert _error(b"").codigo == "archivo_vacio"


def test_archivo_que_no_es_imagen():
    assert _error(b"esto es un texto, no una radiografia" * 10).codigo == "tipo_no_soportado"


def test_pdf_renombrado_a_jpg():
    assert _error(b"%PDF-1.7\n" + b"0" * 500).codigo == "tipo_no_soportado"


def test_formato_de_imagen_no_admitido():
    ok, datos = cv2.imencode(".bmp", np.zeros((300, 300), dtype=np.uint8))
    assert ok
    assert _error(datos.tobytes()).codigo == "tipo_no_soportado"


def test_jpg_con_firma_valida_pero_contenido_roto():
    assert _error(b"\xff\xd8\xff\xe0" + b"\x00" * 2000 + b"\xff\xd9").codigo == "imagen_corrupta"


def test_jpg_truncado():
    completo = jpg_sintetico()
    assert _error(completo[: len(completo) // 2]).codigo == "imagen_corrupta"


def test_png_truncado():
    completo = png_sintetico()
    assert _error(completo[: len(completo) // 2]).codigo == "imagen_corrupta"


def test_archivo_que_supera_el_tamano_maximo():
    contenido = jpg_sintetico()
    error = _error(contenido, max_bytes=len(contenido) - 1)
    assert error.codigo == "archivo_muy_grande"


def test_imagen_mas_chica_que_el_minimo():
    error = _error(jpg_sintetico(ancho=400, alto=100))
    assert error.codigo == "imagen_muy_chica"
    assert "256" in error.mensaje


def test_png_de_16_bits_se_rechaza():
    # El modelo se entreno con imagenes de 8 bits; una de 16 bits daria un resultado sin sentido.
    ok, datos = cv2.imencode(".png", np.full((300, 300), 2000, dtype=np.uint16))
    assert ok
    assert _error(datos.tobytes()).codigo == "profundidad_no_soportada"


def test_configuracion_por_defecto(tmp_path):
    configuracion = cargar_configuracion({})
    assert configuracion.max_bytes == 25 * 1024 * 1024
    assert configuracion.min_lado_px == 256
    assert configuracion.ruta_base.name == "vetvision.db"
    assert configuracion.dir_imagenes.name == "imagenes"


def test_configuracion_por_variables_de_entorno(tmp_path):
    configuracion = cargar_configuracion({
        "VETVISION_DIR_DATOS": str(tmp_path),
        "VETVISION_MAX_MB": "2",
        "VETVISION_MIN_LADO_PX": "100",
    })
    assert configuracion.dir_datos == tmp_path
    assert configuracion.max_bytes == 2 * 1024 * 1024
    assert configuracion.min_lado_px == 100
