import io
import json
import subprocess
import sys

from harness import lanzar
from harness.__main__ import hook

CAMPO = "Nombre del " + "paciente: "


def _stdin(monkeypatch, datos):
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(datos)))


def test_pre_commit_ignora_comandos_que_no_son_commit(monkeypatch):
    _stdin(monkeypatch, {"tool_input": {"command": "git status"}})
    assert hook("pre-commit") == 0


def test_pre_commit_bloquea_con_dato_preparado(tmp_path, monkeypatch, capsys):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    (tmp_path / "a.txt").write_text(CAMPO + "Fulano Zutano\n", encoding="utf-8")
    subprocess.run(["git", "add", "a.txt"], cwd=tmp_path, check=True)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("harness.guardia.RAIZ", tmp_path)
    import harness.guardia as g

    orig = g.guardia
    monkeypatch.setattr(g, "guardia", lambda modo="arbol", archivos=None, cwd=tmp_path: orig(modo, archivos, cwd))
    _stdin(monkeypatch, {"tool_input": {"command": "git commit -m x"}})
    assert hook("pre-commit") == 2
    assert "Fulano" not in capsys.readouterr().err


def test_post_edit_ignora_rutas_ajenas(monkeypatch):
    _stdin(monkeypatch, {"tool_input": {"file_path": "C:/otro/lugar/x.py"}})
    assert hook("post-edit") == 0


def test_entrada_invalida_no_bloquea(monkeypatch):
    monkeypatch.setattr(sys, "stdin", io.StringIO("no es json"))
    assert hook("pre-commit") == 0


def test_lanzador_ubica_un_python_existente(tmp_path):
    assert lanzar.python_del_venv(tmp_path) == sys.executable
    py = tmp_path / "venv" / "Scripts" / "python.exe"
    py.parent.mkdir(parents=True)
    py.write_text("")
    assert lanzar.python_del_venv(tmp_path) == str(py)
