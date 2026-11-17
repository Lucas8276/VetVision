"""Validacion de la radiografia cargada, por CONTENIDO, no por extension (spec 004, FR-001).

La extension del archivo no se usa para nada: se detecta el formato real por la firma de bytes y
se decodifica de verdad con OpenCV. Cada caso de entrada invalida tiene un codigo estable y un
mensaje que dice que hacer (SC-003), nunca solo "fallo".
"""
import cv2
import numpy as np

from app.errores import ErrorApp

_FIRMAS = (
    (b"\xff\xd8\xff", "jpg"),
    (b"\x89PNG\r\n\x1a\n", "png"),
)


class ErrorValidacion(ErrorApp):
    pass


class Imagen:
    """Resultado de una validacion exitosa: formato real y dimensiones."""

    __slots__ = ("formato", "ancho", "alto")

    def __init__(self, formato, ancho, alto):
        self.formato = formato
        self.ancho = ancho
        self.alto = alto


def _detectar_formato(contenido):
    for firma, formato in _FIRMAS:
        if contenido[: len(firma)] == firma:
            return formato
    return None


def validar_imagen(contenido, max_bytes, min_lado_px):
    if not contenido:
        raise ErrorValidacion(
            "archivo_vacio", "El archivo está vacío. Elegí una radiografía en formato JPG o PNG.")
    if len(contenido) > max_bytes:
        raise ErrorValidacion(
            "archivo_muy_grande",
            f"El archivo supera el tamaño máximo permitido ({max_bytes / (1024 * 1024):.0f} MB). "
            "Reducí el tamaño de la imagen e intentá cargarla de nuevo.")
    formato = _detectar_formato(contenido)
    if formato is None:
        raise ErrorValidacion(
            "tipo_no_soportado",
            "El archivo no tiene un formato de imagen admitido. Cargá una radiografía en JPG o PNG.")
    decodificada = cv2.imdecode(np.frombuffer(contenido, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
    if decodificada is None:
        raise ErrorValidacion(
            "imagen_corrupta",
            "El archivo parece una imagen pero no se pudo leer su contenido: puede estar dañado o "
            "incompleto. Volvé a exportarlo desde el equipo de origen y cargalo de nuevo.")
    if decodificada.dtype != np.uint8:
        raise ErrorValidacion(
            "profundidad_no_soportada",
            "La imagen tiene una profundidad de color no admitida (se espera 8 bits por canal). "
            "Exportala en 8 bits e intentá de nuevo.")
    alto, ancho = decodificada.shape[:2]
    if min(ancho, alto) < min_lado_px:
        raise ErrorValidacion(
            "imagen_muy_chica",
            f"La imagen es demasiado chica ({ancho}x{alto} px): el lado menor debe tener al menos "
            f"{min_lado_px} px. Cargá una radiografía de mayor resolución.")
    return Imagen(formato, ancho, alto)
