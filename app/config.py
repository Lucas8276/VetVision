"""Configuracion del MVP (spec 004, FR-001 y FR-009): rutas de datos y limites de carga.

Todo tiene un valor por defecto razonable y se puede ajustar por variable de entorno, sin tocar
codigo. Los datos (base e imagenes) viven fuera de git: `data/app/` esta en `.gitignore`.
"""
import os
from dataclasses import dataclass, field
from pathlib import Path

MAX_MB_POR_DEFECTO = 25
MIN_LADO_PX_POR_DEFECTO = 256
DIR_DATOS_POR_DEFECTO = "data/app"


@dataclass
class Configuracion:
    dir_datos: Path
    max_bytes: int = field(default=MAX_MB_POR_DEFECTO * 1024 * 1024)
    min_lado_px: int = MIN_LADO_PX_POR_DEFECTO

    def __post_init__(self):
        self.dir_datos = Path(self.dir_datos)

    @property
    def ruta_base(self):
        return self.dir_datos / "vetvision.db"

    @property
    def dir_imagenes(self):
        return self.dir_datos / "imagenes"


def cargar_configuracion(entorno=None):
    """`entorno`: un diccionario (los tests pasan uno aislado) o None para usar las variables reales."""
    origen = entorno if entorno is not None else os.environ
    dir_datos = origen.get("VETVISION_DIR_DATOS", DIR_DATOS_POR_DEFECTO)
    max_mb = float(origen.get("VETVISION_MAX_MB", MAX_MB_POR_DEFECTO))
    min_lado = int(origen.get("VETVISION_MIN_LADO_PX", MIN_LADO_PX_POR_DEFECTO))
    return Configuracion(dir_datos=Path(dir_datos), max_bytes=int(max_mb * 1024 * 1024),
                         min_lado_px=min_lado)
