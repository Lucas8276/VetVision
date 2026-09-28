import cv2
import numpy as np

def normalizar_jpg_veterinario(jpg_path, apply_clahe=True, size=512):
    """
    Normaliza el jpg 'pesado' (fuente principal de entrenamiento).
    Ya NO se asume 16-bit: se trabaja directo sobre 8-bit.

    Devuelve un array 2D (escala de grises, uint8), NO RGB: el backbone de
    TorchXRayVision (src/model.py) espera 1 solo canal de entrada, no 3 - ver
    specs/002-etapa0-torax-clasificador/research.md, Decision 6. La conversion
    a rango [-1024, 1024] que ese backbone espera se aplica en src/dataset.py
    (xrv.utils.normalize), no aca.
    """
    img = cv2.imread(str(jpg_path), cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise ValueError(f"No se pudo leer la imagen: {jpg_path}")

    if apply_clahe:
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        img = clahe.apply(img)

    img = cv2.resize(img, (size, size), interpolation=cv2.INTER_AREA)
    return img
