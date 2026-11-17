"""Verificacion del documento (specs/005-harness-v2, incremento 1). Documentos 100 % sinteticos."""
import yaml

from harness import documento
from harness.__main__ import main

DESCARGO = "El sistema es una herramienta de apoyo y no reemplaza el criterio del veterinario."
CUERPO = " ".join(["palabra"] * 30)


def _doc(tmp_path, capitulos=None, **datos):
    """Arma un documento valido minimo en tmp_path/doc y un 'repo' en tmp_path. Devuelve (dir, raiz)."""
    tmp_path.mkdir(parents=True, exist_ok=True)
    d = tmp_path / "doc"
    d.mkdir()
    (tmp_path / "RESULTADOS.md").write_text("balanced accuracy: 92,45 %\n", encoding="utf-8")
    caps = {
        "01-intro.md": f"# Intro\n\n{DESCARGO} {CUERPO}\nLa exactitud fue {{{{hecho:bal_acc}}}} % [@fuente2025].\n",
        "02-cierre.md": f"# Cierre\n\n{CUERPO}\n",
    }
    caps.update(capitulos or {})
    for nombre, texto in caps.items():
        (d / nombre).write_text(texto, encoding="utf-8")
    base = {
        "normativa": {
            "secciones_obligatorias": [{"archivo": "01-intro.md", "palabras_minimas": 20},
                                       {"archivo": "02-cierre.md", "palabras_minimas": 20}],
            "descargo": {"frases": ["no reemplaza"], "archivos": ["01-intro.md"]},
            "citas": {"acceso_libre_obligatorio": True, "anio_minimo_por_tema": {1: 2025}},
        },
        "hechos": {"hechos": [{"clave": "bal_acc", "valor": "92,45", "unidad": "%",
                               "fuente": "RESULTADOS.md#resultado", "verificado_en": "2026-11-17"}]},
        "fuentes": {"fuentes": [{"clave": "fuente2025", "anio": 2025, "tema": 1, "verificada": True,
                                 "acceso_libre": True}]},
        "estado-sync": {"secciones": {
            "01-intro.md": {"estado": "final", "revisor": "Revisor Uno", "fecha": "2026-11-17", "asistencia_ia": True},
            "02-cierre.md": {"estado": "final", "revisor": "Revisor Dos", "fecha": "2026-11-17", "asistencia_ia": False}}},
        "declaracion-uso-ia": {"registros": [{"apartado": "01-intro.md", "herramienta": "asistente",
                                              "fecha": "2026-11-17", "tipo_de_ayuda": "redaccion"}]},
    }
    base.update(datos)
    for nombre, contenido in base.items():
        if contenido is not None:
            (d / f"{nombre}.yaml").write_text(yaml.safe_dump(contenido, allow_unicode=True), encoding="utf-8")
    return d, tmp_path


def _reglas(res, estado):
    return sorted({r.regla for r in res if r.estado == estado})


def test_documento_valido_no_tiene_fallas_ni_pendientes(tmp_path):
    d, raiz = _doc(tmp_path)
    for entrega in (False, True):
        res = documento.validar_documento(d, raiz=raiz, entrega=entrega)
        assert _reglas(res, "falla") == [] and _reglas(res, "pendiente") == []
    assert main(["documento", "--dir", str(d), "--raiz", str(raiz), "--entrega"]) == 0


def test_pendiente_informa_en_modo_normal_y_bloquea_en_entrega(tmp_path):
    d, raiz = _doc(tmp_path, {"02-cierre.md": f"# Cierre\n\n{CUERPO}\n[PENDIENTE: falta un dato]\n[A completar: algo]\n"})
    normal = documento.validar_documento(d, raiz=raiz)
    assert _reglas(normal, "pendiente") == ["D-PENDIENTE"] and _reglas(normal, "falla") == []
    assert [r.ubicacion for r in normal if r.regla == "D-PENDIENTE"] == ["02-cierre.md:4", "02-cierre.md:5"]
    assert _reglas(documento.validar_documento(d, raiz=raiz, entrega=True), "falla") == ["D-PENDIENTE"]
    assert main(["documento", "--dir", str(d), "--raiz", str(raiz)]) == 0
    assert main(["documento", "--dir", str(d), "--raiz", str(raiz), "--entrega"]) == 1


def test_hecho_inexistente_o_sin_respaldo_en_su_fuente_falla(tmp_path):
    d, raiz = _doc(tmp_path, {"02-cierre.md": f"# Cierre\n\n{CUERPO} {{{{hecho:no_existe}}}}\n"})
    assert "D-HECHO" in _reglas(documento.validar_documento(d, raiz=raiz), "falla")

    d2, raiz2 = _doc(tmp_path / "b")
    (raiz2 / "RESULTADOS.md").write_text("balanced accuracy: 88,10 %\n", encoding="utf-8")  # el repo cambio
    assert "D-HECHO" in _reglas(documento.validar_documento(d2, raiz=raiz2), "falla")


def test_hecho_acepta_valor_en_fuente_con_otro_formato(tmp_path):
    d, raiz = _doc(tmp_path / "c", hechos={"hechos": [{
        "clave": "bal_acc", "valor": "92,45", "valor_en_fuente": "92,45 %", "unidad": "%",
        "fuente": "RESULTADOS.md", "verificado_en": "2026-11-17"}]})
    assert _reglas(documento.validar_documento(d, raiz=raiz), "falla") == []


def _con_fuente(tmp_path, **cambios):
    f = {"clave": "fuente2025", "anio": 2025, "tema": 1, "verificada": True, "acceso_libre": True}
    f.update(cambios)
    return _doc(tmp_path, fuentes={"fuentes": [f]})


def test_cita_debe_existir_estar_verificada_ser_libre_y_reciente(tmp_path):
    casos = {"a": {"clave": "otra"}, "b": {"verificada": False}, "c": {"acceso_libre": False}, "d": {"anio": 2019}}
    for nombre, cambio in casos.items():
        d, raiz = _con_fuente(tmp_path / nombre, **cambio)
        assert "D-CITA" in _reglas(documento.validar_documento(d, raiz=raiz), "falla"), nombre
    d, raiz = _con_fuente(tmp_path / "e", anio=1982, clasico=True)  # un clasico no exige anio minimo
    assert "D-CITA" not in _reglas(documento.validar_documento(d, raiz=raiz), "falla")


def test_estructura_seccion_faltante_falla_y_corta_queda_pendiente(tmp_path):
    d, raiz = _doc(tmp_path, {"02-cierre.md": "# Cierre\n\nmuy corto\n"})
    res = documento.validar_documento(d, raiz=raiz)
    assert _reglas(res, "pendiente") == ["D-ESTRUCTURA"]
    (d / "02-cierre.md").unlink()
    assert "D-ESTRUCTURA" in _reglas(documento.validar_documento(d, raiz=raiz), "falla")


def test_revision_final_sin_revisor_falla_y_borrador_bloquea_la_entrega(tmp_path):
    sync = {"secciones": {
        "01-intro.md": {"estado": "final", "revisor": "", "fecha": "", "asistencia_ia": True},
        "02-cierre.md": {"estado": "borrador", "asistencia_ia": False}}}
    d, raiz = _doc(tmp_path, **{"estado-sync": sync})
    normal = documento.validar_documento(d, raiz=raiz)
    assert _reglas(normal, "falla") == ["D-REVISION"] and _reglas(normal, "pendiente") == ["D-REVISION"]
    entrega = [r for r in documento.validar_documento(d, raiz=raiz, entrega=True) if r.regla == "D-REVISION"]
    assert len(entrega) == 2 and all(r.estado == "falla" for r in entrega)


def test_asistencia_de_ia_sin_declarar_falla(tmp_path):
    d, raiz = _doc(tmp_path, **{"declaracion-uso-ia": {"registros": []}})
    assert _reglas(documento.validar_documento(d, raiz=raiz), "falla") == ["D-IA"]


def test_descargo_faltante_es_pendiente_y_bloquea_la_entrega(tmp_path):
    d, raiz = _doc(tmp_path, {"01-intro.md": f"# Intro\n\n{CUERPO} {{{{hecho:bal_acc}}}} [@fuente2025]\n"})
    assert _reglas(documento.validar_documento(d, raiz=raiz), "pendiente") == ["D-LIMITE"]
    assert _reglas(documento.validar_documento(d, raiz=raiz, entrega=True), "falla") == ["D-LIMITE"]


def test_datos_personales_fallan_sin_repetir_el_valor(tmp_path):
    valor = "Fulano " + "Zutano"
    linea = "Nombre del " + "paciente: " + valor
    d, raiz = _doc(tmp_path, {"02-cierre.md": f"# Cierre\n\n{CUERPO}\n{linea}\n"})
    res = [r for r in documento.validar_documento(d, raiz=raiz) if r.regla.startswith("D-DATOS")]
    assert len(res) == 1 and res[0].estado == "falla" and res[0].ubicacion == "02-cierre.md:4"
    assert valor not in res[0].formatear()


def test_archivo_de_datos_faltante_se_informa_y_no_rompe(tmp_path):
    d, raiz = _doc(tmp_path, hechos=None)
    res = documento.validar_documento(d, raiz=raiz)
    assert any(r.regla == "D-HECHO" and r.estado == "falla" and "hechos.yaml" in r.mensaje for r in res)
    assert any(r.regla == "D-CITA" and r.estado == "ok" for r in res)


def test_directorio_por_defecto_ausente_no_falla_y_explicito_ausente_es_error_de_uso(tmp_path):
    res = documento.validar_documento(tmp_path / "no_existe", raiz=tmp_path, por_defecto=True)
    assert [r.estado for r in res] == ["sin_verificacion"]
    assert main(["documento", "--dir", str(tmp_path / "no_existe")]) == 2


def test_resumen_para_todo_es_una_linea_que_no_bloquea(tmp_path):
    d, raiz = _doc(tmp_path, {"02-cierre.md": f"# Cierre\n\n{CUERPO} {{{{hecho:no_existe}}}}\n"})
    r = documento.resumen_documento(d, raiz=raiz)
    assert len(r) == 1 and r[0].estado == "pendiente" and "1 falla" in r[0].mensaje
