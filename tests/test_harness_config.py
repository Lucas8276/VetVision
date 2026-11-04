import json
import subprocess
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parent.parent


def _workflow():
    return yaml.safe_load((RAIZ / ".github" / "workflows" / "verificar.yml").read_text(encoding="utf-8"))


def test_ci_dispara_en_push_y_pull_request_con_permisos_minimos():
    wf = _workflow()
    disparadores = wf.get("on", wf.get(True))  # PyYAML lee 'on' como True
    assert "push" in disparadores and "pull_request" in disparadores
    assert wf["permissions"] == {"contents": "read"}


def test_ci_ejecuta_el_harness_con_torch_cpu():
    texto = (RAIZ / ".github" / "workflows" / "verificar.yml").read_text(encoding="utf-8")
    assert "python -m harness" in texto
    assert "download.pytorch.org/whl/cpu" in texto


def test_requirements_ci_es_minimo():
    reqs = (RAIZ / "requirements-ci.txt").read_text(encoding="utf-8")
    for pesado in ("dvc", "mlflow", "flask"):
        assert pesado not in reqs


def test_settings_conserva_ask_y_declara_hooks():
    cfg = json.loads((RAIZ / ".claude" / "settings.json").read_text(encoding="utf-8"))
    ask = cfg["permissions"]["ask"]
    for tool in ("Bash", "PowerShell"):
        for verbo in ("commit", "push"):
            assert f"{tool}(git {verbo} *)" in ask and f"{tool}(git * {verbo} *)" in ask
    assert not any("commit" in a and "push" in a for a in ask)  # dos confirmaciones separadas
    assert "PreToolUse" in cfg["hooks"] and "PostToolUse" in cfg["hooks"]


def _ignorado(ruta):
    return subprocess.run(["git", "check-ignore", "-q", ruta], cwd=RAIZ).returncode == 0


def test_claude_compartido_se_versiona_y_lo_personal_no():
    assert not _ignorado(".claude/settings.json")
    assert not _ignorado(".claude/skills/speckit-plan/SKILL.md")
    assert _ignorado(".claude/settings.local.json")
