"""Lanzador (solo biblioteca estandar): ubica el Python del venv y ejecuta `python -m harness`."""
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def python_del_venv(raiz=RAIZ):
    for rel in ("venv/Scripts/python.exe", "venv/bin/python"):
        p = Path(raiz) / rel
        if p.exists():
            return str(p)
    return sys.executable


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    return subprocess.run([python_del_venv(), "-m", "harness", *argv], cwd=RAIZ).returncode


if __name__ == "__main__":
    sys.exit(main())
