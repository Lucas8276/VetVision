"""Registro de modelos de IA disponibles (spec 004, FR-002, FR-003, FR-011, FR-013).

Agregar un modelo nuevo (por ejemplo la Etapa 1) es agregar una entrada a DEFINICIONES: la API, la
base y la interfaz no cambian. Si el archivo del modelo no esta en disco, la aplicacion arranca
igual y lo informa (no es un error fatal).

El preprocesamiento (`preparar_entrada`) es EXACTAMENTE el de entrenamiento
(`src/preprocessing.py` + `xrv.utils.normalize(img, maxval=255, reshape=True)`), replicado sin
importar `torchxrayvision` para que arrancar la aplicacion sea liviano; `normalizar_rango_xrv` se
compara contra la funcion original en los tests cuando la biblioteca esta instalada.
"""
import time
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Dict, List

import numpy as np

RAIZ = Path(__file__).resolve().parent.parent

# Mismo orden que ETIQUETAS_A_IDX en src/dataset.py: {"NO_TORAX": 0, "TORAX": 1}.
DEFINICIONES = {
    "etapa0_region": {
        "papel": "region",
        "ruta": "models/etapa0_region.onnx",
        "clases": ["NO_TORAX", "TORAX"],
    },
}

# Cortes de nivel de confianza, tomados de la calibracion medida de la Etapa 0 (docs/MEMORIA.md,
# Estado 2026-11-17): por debajo de 0,70 el acierto observado ronda el 60-70%.
UMBRAL_ALTA = 0.90
UMBRAL_MEDIA = 0.70


def nivel_de_confianza(confianza):
    if confianza >= UMBRAL_ALTA:
        return "alta"
    if confianza >= UMBRAL_MEDIA:
        return "media"
    return "baja"


@dataclass
class Prediccion:
    etiqueta: str
    confianza: float
    probabilidades: Dict[str, float]


def huella_sha256(rutas):
    """Hash combinado del contenido de uno o mas archivos (identifica la version de un modelo)."""
    h = sha256()
    for ruta in sorted(str(r) for r in rutas):
        h.update(Path(ruta).read_bytes())
    return h.hexdigest()


def normalizar_rango_xrv(imagen):
    """Replica xrv.utils.normalize(img, maxval=255, reshape=True): a [-1024, 1024], canal primero."""
    normalizada = (2 * (imagen.astype(np.float32) / 255.0) - 1.0) * 1024.0
    return normalizada[None, :, :]


def preparar_entrada(ruta_imagen):
    """Imagen -> tensor (1, 1, 512, 512) float32, igual que en entrenamiento (src/dataset.py)."""
    from src.preprocessing import normalizar_jpg_veterinario

    imagen = normalizar_jpg_veterinario(ruta_imagen)
    entrada = normalizar_rango_xrv(imagen)
    return entrada[None, :, :, :].astype(np.float32)


def _softmax(logits):
    logits = logits - np.max(logits)
    exp = np.exp(logits)
    return exp / exp.sum()


class ModeloOnnx:
    """Modelo de inferencia real via ONNX Runtime. `papel`: "region" u "hallazgos"."""

    def __init__(self, nombre, papel, ruta, clases, hallazgo_por_clase=None):
        self.nombre = nombre
        self.papel = papel
        self.ruta = Path(ruta)
        self.clases = list(clases)
        self.hallazgo_por_clase = hallazgo_por_clase or {}
        self.huella = huella_sha256([self.ruta])
        self._sesion = None

    def _cargar(self):
        if self._sesion is None:
            import onnxruntime as ort

            self._sesion = ort.InferenceSession(str(self.ruta), providers=["CPUExecutionProvider"])
        return self._sesion

    def predecir(self, ruta_imagen):
        sesion = self._cargar()
        entrada = preparar_entrada(ruta_imagen)
        salida = sesion.run(None, {sesion.get_inputs()[0].name: entrada})[0][0]
        probabilidades = _softmax(salida)
        idx = int(np.argmax(probabilidades))
        return Prediccion(
            etiqueta=self.clases[idx],
            confianza=float(probabilidades[idx]),
            probabilidades={c: float(p) for c, p in zip(self.clases, probabilidades)},
        )


class RegistroModelos:
    """Modelos disponibles por papel, mas el motivo de los que no se pudieron cargar."""

    def __init__(self, modelos, no_disponibles=None):
        self.modelos: List = list(modelos)
        self.no_disponibles: List[dict] = list(no_disponibles or [])

    def disponibles(self, papel):
        return [m for m in self.modelos if m.papel == papel]

    def estado(self):
        filas = [{"nombre": m.nombre, "papel": m.papel, "disponible": True} for m in self.modelos]
        filas += [
            {"nombre": d["nombre"], "papel": d["papel"], "disponible": False,
             "motivo": d.get("motivo")}
            for d in self.no_disponibles
        ]
        return filas

    @classmethod
    def desde_definiciones(cls, definiciones=None, raiz=RAIZ):
        definiciones = definiciones if definiciones is not None else DEFINICIONES
        modelos, no_disponibles = [], []
        for nombre, d in definiciones.items():
            ruta = Path(raiz) / d["ruta"]
            if ruta.is_file():
                modelos.append(ModeloOnnx(nombre=nombre, papel=d["papel"], ruta=ruta,
                                          clases=d["clases"],
                                          hallazgo_por_clase=d.get("hallazgo_por_clase")))
            else:
                no_disponibles.append(
                    {"nombre": nombre, "papel": d["papel"], "motivo": "archivo_no_encontrado"})
        return cls(modelos=modelos, no_disponibles=no_disponibles)


def medir_prediccion(modelo, ruta_imagen):
    """Ejecuta `modelo.predecir` y devuelve (Prediccion, tiempo_ms): el tiempo se mide aca, igual
    para un modelo real o uno falso de test, para no duplicar esa logica en cada modelo."""
    inicio = time.perf_counter()
    prediccion = modelo.predecir(ruta_imagen)
    return prediccion, (time.perf_counter() - inicio) * 1000
