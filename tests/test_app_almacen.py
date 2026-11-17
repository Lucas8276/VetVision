"""Tests de app/almacen.py: persistencia en SQLite e imagenes en disco (spec 004, FR-006 a FR-011)."""
import sqlite3

import pytest

from app.almacen import VERSION_ESQUEMA, Almacen
from app.errores import ErrorApp
from ayudas_app import jpg_sintetico


@pytest.fixture
def almacen(tmp_path):
    return Almacen(tmp_path / "datos" / "vetvision.db", tmp_path / "datos" / "imagenes")


def _crear(almacen, contenido=None, hallazgos=None, especie="canino"):
    contenido = contenido if contenido is not None else jpg_sintetico()
    codigo = almacen.nuevo_codigo()
    almacen.guardar_imagen(codigo, contenido, "jpg")
    return almacen.crear_estudio(
        codigo=codigo,
        especie=especie,
        formato="jpg",
        contenido=contenido,
        ancho=600,
        alto=500,
        region={"etiqueta": "TORAX", "confianza": 0.95, "nivel": "alta"},
        modelos=[{"nombre": "puerta_falsa", "huella_sha256": "f" * 64, "tiempo_ms": 12.5}],
        hallazgos=hallazgos or [],
    )


HALLAZGO_MODELO = {"tipo": "cardiomegalia", "modelo": "hallazgos_falso", "confianza": 0.6,
                   "nivel": "baja"}


def test_crea_la_base_con_version_de_esquema(almacen):
    with sqlite3.connect(almacen.ruta_base) as conexion:
        version = conexion.execute("SELECT version FROM version_esquema").fetchone()[0]
        tablas = {f[0] for f in conexion.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert version == VERSION_ESQUEMA
    assert {"estudio", "hallazgo", "version_esquema"} <= tablas


def test_el_codigo_es_generado_y_distinto_cada_vez(almacen):
    codigos = {almacen.nuevo_codigo() for _ in range(50)}
    assert len(codigos) == 50
    assert all(c.startswith("EST-") and len(c) == 12 for c in codigos)


def test_la_imagen_se_guarda_con_el_codigo_como_nombre(almacen):
    estudio = _crear(almacen)
    ruta = almacen.ruta_imagen(estudio["codigo"])
    assert ruta.name == estudio["codigo"] + ".jpg"
    assert ruta.read_bytes() == jpg_sintetico()


def test_el_estudio_persiste_entre_instancias(almacen):
    estudio = _crear(almacen, hallazgos=[HALLAZGO_MODELO])
    otro = Almacen(almacen.ruta_base, almacen.dir_imagenes)
    leido = otro.obtener_estudio(estudio["codigo"])
    assert leido["especie"] == "canino"
    assert leido["estado"] == "borrador"
    assert leido["region"] == {"etiqueta": "TORAX", "confianza": 0.95, "nivel": "alta"}
    assert leido["modelos"] == [{"nombre": "puerta_falsa", "huella_sha256": "f" * 64,
                                 "tiempo_ms": 12.5}]
    assert leido["tiempo_inferencia_ms"] == 12.5
    assert leido["fecha_carga"]
    hallazgo = leido["hallazgos"][0]
    assert hallazgo["origen"] == "modelo"
    assert hallazgo["estado"] == "pendiente"
    assert hallazgo["tipo"] == hallazgo["tipo_propuesto"] == "cardiomegalia"
    assert hallazgo["fecha_decision"] is None


def test_estudio_inexistente(almacen):
    with pytest.raises(ErrorApp) as info:
        almacen.obtener_estudio("EST-00000000")
    assert info.value.codigo == "estudio_no_encontrado"


def test_segunda_carga_de_la_misma_imagen_queda_marcada_como_duplicado(almacen):
    primero = _crear(almacen)
    segundo = _crear(almacen)
    distinto = _crear(almacen, contenido=jpg_sintetico(semilla=7))
    assert primero["duplicado_de"] is None
    assert segundo["duplicado_de"] == primero["codigo"]
    assert distinto["duplicado_de"] is None


def test_validar_corregir_y_descartar_guardan_estado_y_fecha(almacen):
    estudio = _crear(almacen, hallazgos=[HALLAZGO_MODELO, HALLAZGO_MODELO, HALLAZGO_MODELO])
    codigo = estudio["codigo"]
    a, b, c = (h["id"] for h in estudio["hallazgos"])

    almacen.decidir_hallazgo(codigo, a, "validar")
    almacen.decidir_hallazgo(codigo, b, "corregir", tipo="efusion_pleural", comentario="borde")
    almacen.decidir_hallazgo(codigo, c, "descartar")

    por_id = {h["id"]: h for h in almacen.obtener_estudio(codigo)["hallazgos"]}
    assert por_id[a]["estado"] == "validado"
    assert por_id[b]["estado"] == "corregido"
    assert por_id[b]["tipo"] == "efusion_pleural"
    assert por_id[b]["tipo_propuesto"] == "cardiomegalia"  # lo que propuso el sistema no se pisa
    assert por_id[b]["comentario"] == "borde"
    assert por_id[c]["estado"] == "descartado"
    assert all(por_id[i]["fecha_decision"] for i in (a, b, c))


def test_corregir_sin_cambiar_nada_se_rechaza(almacen):
    estudio = _crear(almacen, hallazgos=[HALLAZGO_MODELO])
    with pytest.raises(ErrorApp) as info:
        almacen.decidir_hallazgo(estudio["codigo"], estudio["hallazgos"][0]["id"], "corregir",
                                 tipo="cardiomegalia", comentario="  ")
    assert info.value.codigo == "correccion_sin_cambios"


def test_hallazgo_de_otro_estudio_no_se_puede_decidir(almacen):
    uno = _crear(almacen, hallazgos=[HALLAZGO_MODELO])
    otro = _crear(almacen, contenido=jpg_sintetico(semilla=3))
    with pytest.raises(ErrorApp) as info:
        almacen.decidir_hallazgo(otro["codigo"], uno["hallazgos"][0]["id"], "validar")
    assert info.value.codigo == "hallazgo_no_encontrado"


def test_hallazgo_manual_nace_validado(almacen):
    estudio = _crear(almacen)
    hallazgo = almacen.agregar_hallazgo_manual(estudio["codigo"], "neumotorax", "apical")
    assert hallazgo["origen"] == "manual"
    assert hallazgo["estado"] == "validado"
    assert hallazgo["tipo_propuesto"] is None
    assert hallazgo["confianza"] is None
    assert hallazgo["fecha_decision"]


def test_no_se_cierra_con_pendientes(almacen):
    estudio = _crear(almacen, hallazgos=[HALLAZGO_MODELO])
    with pytest.raises(ErrorApp) as info:
        almacen.cerrar_estudio(estudio["codigo"])
    assert info.value.codigo == "hallazgos_pendientes"
    assert almacen.obtener_estudio(estudio["codigo"])["estado"] == "borrador"


def test_no_se_cierra_un_informe_sin_ningun_hallazgo_vigente(almacen):
    estudio = _crear(almacen, hallazgos=[HALLAZGO_MODELO])
    almacen.decidir_hallazgo(estudio["codigo"], estudio["hallazgos"][0]["id"], "descartar")
    with pytest.raises(ErrorApp) as info:
        almacen.cerrar_estudio(estudio["codigo"])
    assert info.value.codigo == "informe_vacio"


def test_cerrar_y_despues_no_se_puede_modificar(almacen):
    estudio = _crear(almacen, hallazgos=[HALLAZGO_MODELO])
    codigo, id_hallazgo = estudio["codigo"], estudio["hallazgos"][0]["id"]
    almacen.decidir_hallazgo(codigo, id_hallazgo, "validar")
    cerrado = almacen.cerrar_estudio(codigo)
    assert cerrado["estado"] == "validado"
    assert cerrado["fecha_cierre"]
    for intento in (
        lambda: almacen.decidir_hallazgo(codigo, id_hallazgo, "descartar"),
        lambda: almacen.agregar_hallazgo_manual(codigo, "otro", ""),
        lambda: almacen.cerrar_estudio(codigo),
    ):
        with pytest.raises(ErrorApp) as info:
            intento()
        assert info.value.codigo == "estudio_cerrado"


def test_listado_ordenado_por_fecha_y_filtrado_por_estado(almacen):
    primero = _crear(almacen)
    segundo = _crear(almacen, contenido=jpg_sintetico(semilla=2), hallazgos=[HALLAZGO_MODELO])
    almacen.agregar_hallazgo_manual(primero["codigo"], "sin_hallazgos", "")
    almacen.cerrar_estudio(primero["codigo"])

    todos = almacen.listar_estudios()
    assert [e["codigo"] for e in todos] == [segundo["codigo"], primero["codigo"]]  # mas nuevo arriba
    assert todos[0]["cantidad_hallazgos"] == 1 and todos[0]["pendientes"] == 1
    assert [e["codigo"] for e in almacen.listar_estudios("validado")] == [primero["codigo"]]
    assert [e["codigo"] for e in almacen.listar_estudios("borrador")] == [segundo["codigo"]]
