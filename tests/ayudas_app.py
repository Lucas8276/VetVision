"""Ayudas compartidas por los tests del MVP web (tests/test_app_*.py).

Por que existe: los tests del MVP no pueden usar radiografias reales ni los pesos del modelo
(repositorio publico, y CI no tiene `models/`). Aca se generan imagenes sinteticas con numpy y se
define un modelo falso que devuelve una prediccion fija, para inyectarlo en la aplicacion.
"""
import cv2
import numpy as np
from fastapi.testclient import TestClient

from app.api import crear_app
from app.config import Configuracion
from app.modelos_ia import Prediccion, RegistroModelos

# Nombre de archivo ficticio con forma de dato personal: sirve para comprobar que nunca se guarda.
NOMBRE_ORIGINAL = "PACIENTE^PRUEBA_0000-1.jpg"


def imagen_sintetica(ancho=600, alto=500, semilla=0):
    """Matriz 2D uint8 con ruido: alcanza para ejercitar validacion y preprocesamiento."""
    generador = np.random.default_rng(semilla)
    return generador.integers(0, 256, size=(alto, ancho), dtype=np.uint8)


def jpg_sintetico(ancho=600, alto=500, semilla=0):
    ok, datos = cv2.imencode(".jpg", imagen_sintetica(ancho, alto, semilla))
    assert ok
    return datos.tobytes()


def png_sintetico(ancho=600, alto=500, semilla=0):
    ok, datos = cv2.imencode(".png", imagen_sintetica(ancho, alto, semilla))
    assert ok
    return datos.tobytes()


class ModeloFalso:
    """Reemplaza a un modelo ONNX: misma interfaz (nombre, papel, huella, predecir)."""

    def __init__(self, nombre="puerta_falsa", papel="region", etiqueta="TORAX", confianza=0.95,
                 hallazgo_por_clase=None):
        self.nombre = nombre
        self.papel = papel
        self.huella = "f" * 64
        self.etiqueta = etiqueta
        self.confianza = confianza
        self.hallazgo_por_clase = hallazgo_por_clase or {}
        self.llamadas = 0

    def predecir(self, ruta_imagen):
        self.llamadas += 1
        return Prediccion(
            etiqueta=self.etiqueta,
            confianza=self.confianza,
            probabilidades={self.etiqueta: self.confianza},
        )


def crear_cliente(tmp_path, modelos=None, no_disponibles=None, max_bytes=25 * 1024 * 1024,
                  min_lado_px=256):
    """Aplicacion completa con base temporal y modelos falsos. Devuelve (cliente, configuracion)."""
    configuracion = Configuracion(dir_datos=tmp_path / "app", max_bytes=max_bytes,
                                  min_lado_px=min_lado_px)
    if modelos is None:
        modelos = [ModeloFalso()]
    registro = RegistroModelos(modelos=modelos, no_disponibles=no_disponibles or [])
    return TestClient(crear_app(configuracion, registro)), configuracion


def subir(cliente, contenido=None, especie="canino", nombre=NOMBRE_ORIGINAL):
    if contenido is None:
        contenido = jpg_sintetico()
    return cliente.post(
        "/api/estudios",
        files={"imagen": (nombre, contenido, "application/octet-stream")},
        data={"especie": especie},
    )
