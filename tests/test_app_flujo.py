"""Test de extremo a extremo del MVP (spec 004, SC-004 y SC-005).

Flujo: carga -> validar / corregir / descartar -> cerrar -> reabrir -> listado. Corre con un modelo
falso y una base temporal: pasa en CI sin datos reales ni pesos.
"""
import logging
import sqlite3

from ayudas_app import NOMBRE_ORIGINAL, ModeloFalso, crear_cliente, jpg_sintetico, subir

COMENTARIO = "texto libre del veterinario que no debe ir a los registros"


def _modelos():
    return [
        ModeloFalso(),
        ModeloFalso(nombre="hallazgos_a", papel="hallazgos", etiqueta="cardiomegalia",
                    confianza=0.93),
        ModeloFalso(nombre="hallazgos_b", papel="hallazgos", etiqueta="patron_alveolar",
                    confianza=0.75),
        ModeloFalso(nombre="hallazgos_c", papel="hallazgos", etiqueta="neumotorax",
                    confianza=0.40),
    ]


def _recorrer_flujo(cliente):
    estudio = subir(cliente).json()
    codigo = estudio["codigo"]
    a, b, c = (h["id"] for h in estudio["hallazgos"])
    assert [h["nivel"] for h in estudio["hallazgos"]] == ["alta", "media", "baja"]

    # Con pendientes no se puede cerrar, y el mensaje dice cuales faltan (historia 2, escenario 2).
    rechazo = cliente.post(f"/api/estudios/{codigo}/cerrar")
    assert rechazo.status_code == 409
    assert rechazo.json()["codigo"] == "hallazgos_pendientes"
    assert "Cardiomegalia" in rechazo.json()["mensaje"]

    base = f"/api/estudios/{codigo}/hallazgos"
    assert cliente.patch(f"{base}/{a}", json={"accion": "validar"}).status_code == 200
    assert cliente.patch(f"{base}/{b}", json={
        "accion": "corregir", "tipo": "patron_intersticial", "comentario": COMENTARIO,
    }).status_code == 200
    parcial = cliente.patch(f"{base}/{c}", json={"accion": "descartar"}).json()
    assert parcial["pendientes"] == 0 and parcial["puede_cerrarse"] is True
    assert cliente.post(base, json={"tipo": "efusion_pleural"}).status_code == 201

    cerrado = cliente.post(f"/api/estudios/{codigo}/cerrar")
    assert cerrado.status_code == 200
    assert cerrado.json()["estado"] == "validado"
    return codigo, (a, b, c)


def test_flujo_completo(tmp_path):
    cliente, configuracion = crear_cliente(tmp_path, modelos=_modelos())
    codigo, (a, b, c) = _recorrer_flujo(cliente)

    # "Reabrir": una aplicacion nueva sobre la misma base (como cerrar y volver a levantar).
    otro_cliente, _ = crear_cliente(tmp_path, modelos=_modelos())
    reabierto = otro_cliente.get(f"/api/estudios/{codigo}").json()
    assert reabierto["estado"] == "validado"
    assert reabierto["fecha_cierre"]
    assert "No es un diagnóstico definitivo" in reabierto["descargo"]
    por_id = {h["id"]: h for h in reabierto["hallazgos"]}
    assert por_id[a]["estado"] == "validado"
    # Lo que propuso el sistema y lo que decidio el veterinario quedan por separado.
    assert por_id[b]["estado"] == "corregido"
    assert por_id[b]["tipo_propuesto"] == "patron_alveolar"
    assert por_id[b]["tipo"] == "patron_intersticial"
    assert por_id[b]["comentario"] == COMENTARIO
    assert por_id[c]["estado"] == "descartado"
    manual = next(h for h in reabierto["hallazgos"] if h["origen"] == "manual")
    assert manual["tipo"] == "efusion_pleural"
    assert all(h["fecha_decision"] for h in reabierto["hallazgos"])

    # Un informe cerrado ya no se modifica.
    intento = otro_cliente.patch(f"/api/estudios/{codigo}/hallazgos/{a}",
                                 json={"accion": "descartar"})
    assert intento.status_code == 409
    assert intento.json()["codigo"] == "estudio_cerrado"

    # Listado: el nuevo borrador aparece arriba; el filtro por estado funciona.
    borrador = subir(otro_cliente, jpg_sintetico(semilla=5)).json()["codigo"]
    listado = otro_cliente.get("/api/estudios").json()
    assert [e["codigo"] for e in listado["estudios"]] == [borrador, codigo]
    assert "No es un diagnóstico definitivo" in listado["descargo"]
    fila = listado["estudios"][1]
    assert fila["estado"] == "validado"
    assert fila["cantidad_hallazgos"] == 4
    assert fila["region"]["etiqueta"] == "TORAX"
    validados = otro_cliente.get("/api/estudios", params={"estado": "validado"}).json()
    assert [e["codigo"] for e in validados["estudios"]] == [codigo]
    borradores = otro_cliente.get("/api/estudios", params={"estado": "borrador"}).json()
    assert [e["codigo"] for e in borradores["estudios"]] == [borrador]


def test_ni_los_registros_ni_la_base_guardan_el_nombre_original(tmp_path, caplog):
    """SC-005 / FR-010: despues del flujo no queda rastro del nombre de archivo ni del comentario
    en los registros, ni del nombre de archivo en la base o en la carpeta de imagenes."""
    cliente, configuracion = crear_cliente(tmp_path, modelos=_modelos())
    with caplog.at_level(logging.DEBUG):
        codigo, _ = _recorrer_flujo(cliente)
        subir(cliente, b"no soy una imagen" * 20)  # un rechazo tambien deja registro

    registros = caplog.text
    assert codigo in registros  # hay registros, y hablan del estudio por su codigo
    assert "estudio_creado" in registros and "carga_rechazada" in registros
    prohibidos = [NOMBRE_ORIGINAL, "PACIENTE", "PRUEBA", "0000-1"]
    for texto in prohibidos + [COMENTARIO]:
        assert texto not in registros

    # La base: ni en los bytes del archivo ni en ningun valor de ninguna tabla.
    crudo = configuracion.ruta_base.read_bytes()
    with sqlite3.connect(configuracion.ruta_base) as conexion:
        valores = []
        for (tabla,) in conexion.execute("SELECT name FROM sqlite_master WHERE type='table'"):
            for fila in conexion.execute(f"SELECT * FROM {tabla}"):
                valores.extend(str(valor) for valor in fila)
    assert valores
    for texto in prohibidos:
        assert texto.encode() not in crudo
        assert not any(texto in valor for valor in valores)

    # La carpeta de imagenes: solo archivos nombrados con el codigo del estudio.
    nombres = [ruta.name for ruta in configuracion.dir_imagenes.iterdir()]
    assert nombres and all(nombre.startswith("EST-") for nombre in nombres)
