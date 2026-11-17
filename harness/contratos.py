"""Valida los contratos specs/*.spec.yaml contra el codigo real.

Un campo del contrato sin verificador se informa `sin_verificacion`; una seccion
con `estado: pendiente` se informa `pendiente`. Solo una divergencia es `falla`.
"""
import copy
import tempfile
from pathlib import Path

import yaml

from harness import Resultado

RAIZ = Path(__file__).resolve().parent.parent
SPECS_DIR = RAIZ / "specs"
NOMBRES = ("model-tensor", "ground-truth-annotation", "data-contract")
SEP = " › "
_PENDIENTE = object()


def cargar_specs(specs_dir=SPECS_DIR):
    specs = {}
    for nombre in NOMBRES:
        with open(Path(specs_dir) / f"{nombre}.spec.yaml", encoding="utf-8") as f:
            specs[nombre] = yaml.safe_load(f)
    return specs


def _hojas(nodo, ruta):
    """Genera (ruta, valor) por hoja; una lista es una hoja; seccion pendiente = una sola."""
    if isinstance(nodo, dict):
        if nodo.get("estado") == "pendiente":
            yield ruta, _PENDIENTE
            return
        for k, v in nodo.items():
            if k == "estado":
                continue
            yield from _hojas(v, ruta + [str(k)])
    else:
        yield ruta, nodo


class _Codigo:
    """Valores reales del codigo; el modelo se construye una sola vez (sin pesos)."""

    def __init__(self):
        self._modelo = None
        self._forma = None

    def modelo(self):
        if self._modelo is None:
            from src.model import DenseNetEtapa0

            self._modelo = DenseNetEtapa0(num_classes=2, weights=None)
        return self._modelo

    def canales(self):
        return self.modelo().features.conv0.in_channels

    def n_salidas(self):
        return self.modelo().classifier.out_features

    def clases_etapa0(self):
        from src.dataset import ETIQUETAS_A_IDX

        return list(ETIQUETAS_A_IDX)

    def umbral(self):
        from src.evaluate import UMBRAL_PROMOCION_ACC

        return UMBRAL_PROMOCION_ACC

    def particion(self):
        from src.particion import PARTICION_POR_DEFECTO

        return PARTICION_POR_DEFECTO

    def opset(self):
        import inspect

        from src.export_onnx import exportar_onnx

        return inspect.signature(exportar_onnx).parameters["opset"].default

    def vistas(self):
        from src.parser_fcr import VISTAS_VALIDAS

        return sorted(VISTAS_VALIDAS)

    def especies(self):
        from src.parser_fcr import ESPECIES_VALIDAS

        return sorted(ESPECIES_VALIDAS)

    def forma_entrada(self):
        """Forma que devuelve Dataset.__getitem__ sobre una imagen sintetica."""
        if self._forma is None:
            import cv2
            import numpy as np

            from src.dataset import VetVisionEtapa0Dataset

            with tempfile.TemporaryDirectory() as d:
                cv2.imwrite(str(Path(d) / "X.jpg"), np.full((600, 700), 128, np.uint8))
                (Path(d) / "X.txt").write_text(
                    "Región anatómica: CHEST\n", encoding="utf-8")
                ds = VetVisionEtapa0Dataset(d)
                if len(ds) == 0:
                    raise RuntimeError("dataset sintetico vacio")
                self._forma = list(ds[0][0].shape)
        return self._forma


def _verificadores(c):
    """ruta (tupla) -> (funcion que da el valor real, modo de comparacion)."""
    return {
        ("model-tensor", "input", "canales"): (c.canales, "eq"),
        ("model-tensor", "input", "size"): (lambda: c.forma_entrada()[1:], "eq"),
        ("model-tensor", "etapas", "etapa_0_torax", "input_shape"): (c.forma_entrada, "eq"),
        ("model-tensor", "etapas", "etapa_0_torax", "output_shape"): (lambda: [c.n_salidas()], "eq"),
        ("model-tensor", "etapas", "etapa_0_torax", "umbral_promocion_balanced_accuracy"): (c.umbral, "eq"),
        ("model-tensor", "etapas", "etapa_0_torax", "particion_validacion"): (c.particion, "eq"),
        ("model-tensor", "export", "opset"): (c.opset, "eq"),
        ("ground-truth-annotation", "etapa_0_torax", "clases"): (c.clases_etapa0, "conjunto"),
        ("data-contract", "proyecciones_admitidas"): (c.vistas, "conjunto"),
        ("data-contract", "especies_admitidas"): (c.especies, "conjunto"),
    }


def _comparar(esperado, obtenido, modo):
    if modo == "conjunto":
        return sorted(map(str, esperado)) == sorted(map(str, obtenido))
    return esperado == obtenido


def validar_contratos(specs=None):
    specs = specs if specs is not None else cargar_specs()
    verifs = _verificadores(_Codigo())
    resultados = []
    for nombre, spec in specs.items():
        for ruta, valor in _hojas(spec, []):
            ubic = SEP.join([nombre] + ruta)
            if valor is _PENDIENTE:
                resultados.append(Resultado(
                    "contratos", "pendiente", ubic,
                    mensaje="seccion marcada estado: pendiente en el spec"))
                continue
            clave = tuple([nombre] + ruta)
            if clave not in verifs:
                resultados.append(Resultado(
                    "contratos", "sin_verificacion", ubic,
                    mensaje="campo sin verificador registrado"))
                continue
            obtener, modo = verifs[clave]
            try:
                obtenido = obtener()
            except Exception as e:  # no se pudo consultar el codigo: falla real
                resultados.append(Resultado(
                    "contratos", "falla", ubic, esperado=str(valor),
                    obtenido=f"error {type(e).__name__}: {e}",
                    mensaje="no se pudo obtener el valor del codigo."))
                continue
            if _comparar(valor, obtenido, modo):
                resultados.append(Resultado("contratos", "ok", ubic))
            else:
                resultados.append(Resultado(
                    "contratos", "falla", ubic, esperado=str(valor), obtenido=str(obtenido),
                    mensaje="el codigo no coincide con el spec; corregir el codigo (o el spec primero)."))
    return resultados


def con_cambio(specs, ruta, valor):
    """Copia de `specs` con una hoja cambiada (para tests de deriva)."""
    nuevo = copy.deepcopy(specs)
    nodo = nuevo
    for k in ruta[:-1]:
        nodo = nodo[k]
    nodo[ruta[-1]] = valor
    return nuevo
