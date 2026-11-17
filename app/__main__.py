"""`python -m app` levanta el MVP en http://127.0.0.1:8000 (solo local), con un solo comando.

Ver specs/004-mvp-web/quickstart.md para los pasos de instalacion y prueba manual.
"""
import logging

import uvicorn

from app.api import crear_app
from app.config import cargar_configuracion
from app.modelos_ia import RegistroModelos


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    configuracion = cargar_configuracion()
    registro = RegistroModelos.desde_definiciones()
    for fila in registro.estado():
        if not fila["disponible"]:
            logging.getLogger("vetvision.app").warning(
                "modelo_no_disponible nombre=%s motivo=%s: la aplicación sigue funcionando",
                fila["nombre"], fila.get("motivo"))
    app = crear_app(configuracion, registro)
    print("VetVision AI - MVP en http://127.0.0.1:8000 (Ctrl+C para detener)")
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")


if __name__ == "__main__":
    main()
