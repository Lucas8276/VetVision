"""Las muestras 'filtradas' se arman concatenando fragmentos en tiempo de ejecucion, asi este
archivo no coincide con las reglas y no se marca a si mismo (research D5)."""
import subprocess

from harness import guardia
from harness.__main__ import main

# Fragmentos: nada de esto es un dato real.
NOM = "FULANO" + "^" + "ZUTANO"
CAMPO = "Nombre del " + "paciente: "
CAMPO_ID = "ID del " + "paciente: "


def reglas(linea, ruta="x.txt"):
    return guardia.revisar_linea(linea, ruta, guardia.cargar_ficticios())


def test_campo_paciente_no_aprobado_se_marca():
    assert "R-CAMPO-PACIENTE" in reglas(CAMPO + "Fulano Zutano")


def test_campo_paciente_ficticio_y_plantilla_pasan():
    assert reglas(CAMPO + "PACIENTE PRUEBA") == []
    assert reglas(CAMPO + "{nombre}") == []
    assert reglas('f"' + CAMPO + '{get_tag(t)}\\n"') == []


def test_nombre_dicom():
    assert "R-NOMBRE-DICOM" in reglas("PN: " + NOM)
    assert reglas("PN: PACIENTE^PRUEBA") == []


def test_id_paciente_campo_y_suelto():
    assert "R-ID-PACIENTE" in reglas(CAMPO_ID + "4821-7")
    assert "R-ID-PACIENTE" in reglas("paciente " + "4821" + "-7" + " ingreso")
    assert reglas(CAMPO_ID + "0000-1") == []


def test_no_se_confunden_fechas_versiones_ni_ids_de_requisito():
    assert reglas("creado 2026-09-30, version 1.2.0, FR-018, SC-002, utf-8") == []


def test_archivos_crudos_por_ruta():
    for ruta in ("a/b.ddo", "x.hq", "data/raw/a.txt", "data/processed/x", "FCR12.jpg",
                 "mlflow.db", "models/m.pt", "m.onnx"):
        assert guardia.revisar_ruta(ruta) == "R-ARCHIVO-CRUDO", ruta
    assert guardia.revisar_ruta("src/model.py") is None


def test_secretos():
    assert "R-SECRETO" in reglas("k=" + "AK" + "IA" + "A" * 16)
    assert "R-SECRETO" in reglas("-----BEGIN " + "RSA PRIVATE KEY-----")
    assert "R-SECRETO" in reglas("token " + "ghp" + "_" + "a" * 36)


def test_contacto_solo_en_docs_memoria():
    texto = "escribir a " + "alguien" + "@" + "ejemplo.com"
    assert "R-CONTACTO" in reglas(texto, "docs/MEMORIA.md")
    assert "R-CONTACTO" not in reglas(texto, "otro.md")


def _repo(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, check=True)


def test_preparados_revisa_solo_lo_agregado_y_no_repite_el_valor(tmp_path, capsys):
    _repo(tmp_path)
    (tmp_path / "sucio.txt").write_text(CAMPO + "Fulano Zutano\n", encoding="utf-8")
    (tmp_path / "limpio.txt").write_text("nada\n", encoding="utf-8")
    (tmp_path / "suelto.txt").write_text(CAMPO + "Otro Nombre\n", encoding="utf-8")  # sin preparar
    subprocess.run(["git", "add", "sucio.txt", "limpio.txt"], cwd=tmp_path, check=True)
    res = guardia.guardia("preparados", cwd=tmp_path)
    assert [r.ubicacion for r in res if r.estado == "falla"] == ["sucio.txt:1"]
    salida = "\n".join(r.formatear() for r in res)
    assert "Fulano" not in salida and "Zutano" not in salida


def test_preparados_limpio_es_ok(tmp_path):
    _repo(tmp_path)
    (tmp_path / "a.txt").write_text("hola\n", encoding="utf-8")
    subprocess.run(["git", "add", "a.txt"], cwd=tmp_path, check=True)
    assert [r.estado for r in guardia.guardia("preparados", cwd=tmp_path)] == ["ok"]


def test_cli_archivos_devuelve_1_y_no_imprime_el_valor(tmp_path, capsys):
    f = tmp_path / "m.txt"
    f.write_text(CAMPO + "Fulano Zutano\n", encoding="utf-8")
    assert main(["guardia", "--archivos", str(f)]) == 1
    out = capsys.readouterr()
    assert "Fulano" not in out.out + out.err


def test_repo_real_no_tiene_hallazgos():
    assert [r for r in guardia.guardia("arbol") if r.estado == "falla"] == []
