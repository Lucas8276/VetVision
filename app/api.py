"""API y servidor de la interfaz del MVP (spec 004). FastAPI, contrato OpenAPI 3.1.

Principio de diseño (FR-003): los modelos se consultan solo a traves de `RegistroModelos`. Sumar
un modelo de hallazgos no cambia ni esta API ni la base ni la interfaz: solo se agrega una entrada
al registro.
"""
import logging
import tempfile
from pathlib import Path
from typing import Literal, Optional

from fastapi import FastAPI, File, Form, Query, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.almacen import Almacen
from app.config import Configuracion
from app.errores import ErrorApp
from app.modelos_ia import RegistroModelos, medir_prediccion, nivel_de_confianza
from app.validacion import validar_imagen

log = logging.getLogger("vetvision.app")

DESCARGO = ("Borrador de apoyo. No es un diagnóstico definitivo ni reemplaza el criterio del "
            "veterinario matriculado.")

# Catalogo cerrado de hallazgos que el veterinario puede elegir a mano. Un modelo puede proponer
# un tipo fuera de este catalogo (por ejemplo "no_sano" de la Etapa 1): se muestra igual, con una
# etiqueta derivada de su nombre (ver `_etiqueta_de_tipo`).
CATALOGO_HALLAZGOS = {
    "patron_alveolar": "Patrón alveolar",
    "patron_bronquial": "Patrón bronquial",
    "patron_vascular": "Patrón vascular",
    "patron_intersticial": "Patrón intersticial",
    "efusion_pleural": "Efusión pleural",
    "neumotorax": "Neumotórax",
    "cardiomegalia": "Cardiomegalia",
    "masa_nodulo": "Masa o nódulo",
    "sin_hallazgos": "Sin hallazgos",
    "otro": "Otro",
}
ESPECIES_ADMITIDAS = {"canino", "felino"}
ESTADOS_ADMITIDOS = {"borrador", "validado"}

ESTADOS_HTTP = {
    "archivo_vacio": 422, "tipo_no_soportado": 422, "imagen_corrupta": 422,
    "profundidad_no_soportada": 422, "imagen_muy_chica": 422, "archivo_muy_grande": 413,
    "especie_invalida": 422, "tipo_invalido": 422, "accion_invalida": 422,
    "filtro_invalido": 422, "correccion_sin_cambios": 422, "solicitud_invalida": 422,
    "estudio_no_encontrado": 404, "hallazgo_no_encontrado": 404,
    "hallazgos_pendientes": 409, "informe_vacio": 409, "estudio_cerrado": 409,
    "modelo_no_disponible": 503,
}

STATIC_DIR = Path(__file__).resolve().parent / "static"


def _etiqueta_de_tipo(tipo):
    return CATALOGO_HALLAZGOS.get(tipo) or tipo.replace("_", " ").strip().capitalize()


def _hallazgo_publico(h):
    return {
        "id": h["id"], "origen": h["origen"], "modelo": h["modelo"], "tipo": h["tipo"],
        "tipo_etiqueta": _etiqueta_de_tipo(h["tipo"]), "tipo_propuesto": h["tipo_propuesto"],
        "confianza": h["confianza"], "nivel": h["nivel"], "estado": h["estado"],
        "comentario": h["comentario"], "fecha_decision": h["fecha_decision"],
    }


def _calcular_avisos(estudio, registro):
    avisos = []
    etiqueta_region = estudio["region"].get("etiqueta")
    if etiqueta_region and etiqueta_region != "TORAX":
        avisos.append({
            "codigo": "region_no_torax",
            "mensaje": "La puerta de región indica que esta imagen podría no ser de tórax. El "
                       "modelo se equivoca en parte de los casos: revisá la imagen antes de "
                       "continuar; podés hacerlo igual.",
        })
    if estudio["especie"] == "felino":
        avisos.append({
            "codigo": "especie_fuera_de_alcance",
            "mensaje": "La especie felina queda fuera del alcance evaluado del modelo: interpretá "
                       "el resultado con cautela.",
        })
    if not registro.disponibles("hallazgos"):
        avisos.append({
            "codigo": "sin_modelo_hallazgos",
            "mensaje": "Todavía no hay un modelo de hallazgos evaluado: podés cargarlos a mano.",
        })
    if estudio.get("duplicado_de"):
        avisos.append({
            "codigo": "duplicado",
            "mensaje": f"Esta imagen ya se cargó antes en el estudio {estudio['duplicado_de']}.",
        })
    return avisos


def _estudio_publico(estudio, registro):
    region = dict(estudio["region"])
    region["es_torax"] = region.get("etiqueta") == "TORAX"
    hallazgos = [_hallazgo_publico(h) for h in estudio["hallazgos"]]
    pendientes = sum(1 for h in hallazgos if h["estado"] == "pendiente")
    return {
        "codigo": estudio["codigo"], "especie": estudio["especie"], "formato": estudio["formato"],
        "estado": estudio["estado"], "duplicado_de": estudio["duplicado_de"], "region": region,
        "modelos": estudio["modelos"], "tiempo_inferencia_ms": estudio["tiempo_inferencia_ms"],
        "fecha_carga": estudio["fecha_carga"], "fecha_cierre": estudio["fecha_cierre"],
        "hallazgos": hallazgos, "pendientes": pendientes,
        "puede_cerrarse": pendientes == 0 and estudio["estado"] == "borrador",
        "descargo": DESCARGO, "avisos": _calcular_avisos(estudio, registro),
    }


class DecisionEntrada(BaseModel):
    accion: Literal["validar", "corregir", "descartar"]
    tipo: Optional[str] = None
    comentario: Optional[str] = None


class HallazgoManualEntrada(BaseModel):
    tipo: str
    comentario: Optional[str] = None


def crear_app(configuracion: Configuracion, registro: RegistroModelos) -> FastAPI:
    """Construye la aplicacion completa (API + interfaz) sobre una configuracion y un registro de
    modelos dados. Cada test crea la suya con una base temporal y modelos falsos."""
    almacen = Almacen(configuracion.ruta_base, configuracion.dir_imagenes)
    app = FastAPI(
        title="VetVision AI - MVP",
        version="0.1.0",
        description="Borrador de apoyo para la lectura de radiografías de tórax caninas. No "
                    "reemplaza el criterio del veterinario matriculado.",
    )

    @app.exception_handler(ErrorApp)
    async def _manejar_error_app(_request, exc: ErrorApp):
        return JSONResponse(status_code=ESTADOS_HTTP.get(exc.codigo, 400),
                            content={"codigo": exc.codigo, "mensaje": exc.mensaje})

    @app.exception_handler(RequestValidationError)
    async def _manejar_error_validacion(_request, _exc):
        return JSONResponse(
            status_code=422,
            content={"codigo": "solicitud_invalida",
                     "mensaje": "La solicitud no es válida: revisá los campos enviados."})

    @app.get("/api/salud")
    def salud():
        return {
            "estado": "ok",
            "hay_modelo_region": bool(registro.disponibles("region")),
            "hay_modelo_hallazgos": bool(registro.disponibles("hallazgos")),
            "modelos": registro.estado(),
            "tipos_hallazgo": [{"id": k, "etiqueta": v} for k, v in CATALOGO_HALLAZGOS.items()],
            "descargo": DESCARGO,
        }

    @app.post("/api/estudios", status_code=201)
    async def cargar_estudio(imagen: UploadFile = File(...), especie: str = Form(...)):
        especie = especie.strip().lower()
        if especie not in ESPECIES_ADMITIDAS:
            raise ErrorApp("especie_invalida",
                           f"Especie no admitida: '{especie}'. Usá 'canino' o 'felino'.")
        modelos_region = registro.disponibles("region")
        if not modelos_region:
            log.info("carga_rechazada codigo=modelo_no_disponible")
            raise ErrorApp("modelo_no_disponible",
                           "No hay un modelo de región disponible en este momento: avisá al "
                           "equipo técnico; el listado de estudios sigue funcionando.")
        contenido = await imagen.read()
        try:
            info = validar_imagen(contenido, configuracion.max_bytes, configuracion.min_lado_px)
        except ErrorApp as error:
            log.info("carga_rechazada codigo=%s", error.codigo)
            raise

        with tempfile.NamedTemporaryFile(suffix="." + info.formato, delete=False) as tmp:
            tmp.write(contenido)
            ruta_tmp = Path(tmp.name)
        try:
            modelos_usados, region_resultado, hallazgos = _inferir(modelos_region[0], registro, ruta_tmp)
        finally:
            ruta_tmp.unlink(missing_ok=True)

        codigo = almacen.nuevo_codigo()
        almacen.guardar_imagen(codigo, contenido, info.formato)
        estudio = almacen.crear_estudio(
            codigo=codigo, especie=especie, formato=info.formato, contenido=contenido,
            ancho=info.ancho, alto=info.alto, region=region_resultado, modelos=modelos_usados,
            hallazgos=hallazgos)
        log.info("estudio_creado codigo=%s", codigo)
        return _estudio_publico(estudio, registro)

    @app.get("/api/estudios")
    def listar_estudios(estado: Optional[str] = Query(None)):
        if estado is not None and estado not in ESTADOS_ADMITIDOS:
            raise ErrorApp("filtro_invalido",
                           f"Estado de filtro no admitido: '{estado}'. Usá 'borrador' o 'validado'.")
        return {"estudios": almacen.listar_estudios(estado), "descargo": DESCARGO}

    @app.get("/api/estudios/{codigo}")
    def obtener_estudio(codigo: str):
        return _estudio_publico(almacen.obtener_estudio(codigo), registro)

    @app.get("/api/estudios/{codigo}/imagen")
    def imagen_estudio(codigo: str):
        estudio = almacen.obtener_estudio(codigo)
        ruta = configuracion.dir_imagenes / f"{codigo}.{estudio['formato']}"
        tipo_mime = "image/jpeg" if estudio["formato"] == "jpg" else "image/png"
        return Response(content=ruta.read_bytes(), media_type=tipo_mime)

    @app.post("/api/estudios/{codigo}/hallazgos", status_code=201)
    def agregar_hallazgo(codigo: str, entrada: HallazgoManualEntrada):
        if entrada.tipo not in CATALOGO_HALLAZGOS:
            raise ErrorApp("tipo_invalido",
                           f"Tipo de hallazgo no reconocido: '{entrada.tipo}'. Elegí uno de la "
                           "lista disponible.")
        almacen.agregar_hallazgo_manual(codigo, entrada.tipo, entrada.comentario)
        return _estudio_publico(almacen.obtener_estudio(codigo), registro)

    @app.patch("/api/estudios/{codigo}/hallazgos/{id_hallazgo}")
    def decidir_hallazgo(codigo: str, id_hallazgo: int, entrada: DecisionEntrada):
        if entrada.accion == "corregir" and entrada.tipo and entrada.tipo not in CATALOGO_HALLAZGOS:
            raise ErrorApp("tipo_invalido",
                           f"Tipo de hallazgo no reconocido: '{entrada.tipo}'.")
        almacen.decidir_hallazgo(codigo, id_hallazgo, entrada.accion, tipo=entrada.tipo,
                                 comentario=entrada.comentario)
        return _estudio_publico(almacen.obtener_estudio(codigo), registro)

    @app.post("/api/estudios/{codigo}/cerrar")
    def cerrar_estudio(codigo: str):
        estudio = almacen.cerrar_estudio(codigo)
        log.info("estudio_cerrado codigo=%s", codigo)
        return _estudio_publico(estudio, registro)

    @app.get("/", include_in_schema=False)
    def pagina_principal():
        return FileResponse(STATIC_DIR / "index.html")

    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    return app


def _inferir(modelo_region, registro, ruta_imagen):
    """Corre la puerta de región y, si hay, el o los modelos de hallazgos. Devuelve
    (modelos_usados, region_resultado, hallazgos) listos para `Almacen.crear_estudio`."""
    modelos_usados, hallazgos = [], []

    prediccion, ms = medir_prediccion(modelo_region, ruta_imagen)
    modelos_usados.append({"nombre": modelo_region.nombre, "huella_sha256": modelo_region.huella,
                           "tiempo_ms": round(ms, 3)})
    region_resultado = {"etiqueta": prediccion.etiqueta, "confianza": prediccion.confianza,
                        "nivel": nivel_de_confianza(prediccion.confianza)}

    for modelo_h in registro.disponibles("hallazgos"):
        prediccion_h, ms_h = medir_prediccion(modelo_h, ruta_imagen)
        modelos_usados.append({"nombre": modelo_h.nombre, "huella_sha256": modelo_h.huella,
                               "tiempo_ms": round(ms_h, 3)})
        mapa = getattr(modelo_h, "hallazgo_por_clase", {}) or {}
        tipo = mapa.get(prediccion_h.etiqueta, prediccion_h.etiqueta.lower())
        hallazgos.append({"modelo": modelo_h.nombre, "tipo": tipo,
                          "confianza": prediccion_h.confianza,
                          "nivel": nivel_de_confianza(prediccion_h.confianza)})
    return modelos_usados, region_resultado, hallazgos
