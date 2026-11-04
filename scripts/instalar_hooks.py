"""Activa los hooks de git versionados (.githooks) en ESTE clon. Idempotente; solo config local."""
import subprocess
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def instalar():
    subprocess.run(["git", "config", "--local", "core.hooksPath", ".githooks"], cwd=RAIZ, check=True)
    print("core.hooksPath=.githooks configurado en este clon (config local).")


if __name__ == "__main__":
    instalar()
