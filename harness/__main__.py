"""python -m harness [contratos | guardia | todo | hook <pre-commit|post-edit>]

Codigos de salida: 0 sin fallas, 1 al menos una falla, 2 error interno del harness
(nunca se interpreta como "paso").
"""
import argparse
import subprocess
import sys
import traceback
from pathlib import Path

from harness import Resultado, codigo_de_salida, formatear_resumen

RAIZ = Path(__file__).resolve().parent.parent


def _imprimir(resultados):
    for r in resultados:
        print(r.formatear())
    print(formatear_resumen(resultados))


def _tests():
    p = subprocess.run([sys.executable, "-m", "pytest", "-q", "-m", "not contratos"], cwd=RAIZ)
    if p.returncode == 0:
        return [Resultado("tests", "ok", mensaje="pytest sin fallas")]
    return [Resultado("tests", "falla", mensaje=f"pytest termino con codigo {p.returncode}")]


def _aviso_hooks():
    p = subprocess.run(["git", "config", "--local", "core.hooksPath"], cwd=RAIZ,
                       capture_output=True, text=True)
    if p.stdout.strip() != ".githooks":
        print("AVISO: los hooks de git no estan activos; correr: python scripts/instalar_hooks.py",
              file=sys.stderr)


def correr(comando, preparados=False, archivos=None, rapido=False):
    from harness import contratos, guardia

    if comando == "contratos":
        return contratos.validar_contratos()
    if comando == "guardia":
        if archivos:
            return guardia.guardia("archivos", archivos)
        return guardia.guardia("preparados" if preparados else "arbol")
    # todo
    res = []
    if rapido:
        res.append(Resultado("contratos", "sin_verificacion", mensaje="omitido por --rapido (construye el modelo)"))
    else:
        res += contratos.validar_contratos()
    res += guardia.guardia("arbol")
    res += _tests()
    _aviso_hooks()
    return res


def hook(evento):
    """Hook del asistente: JSON por stdin; 0 continuar, 2 bloquear/avisar por stderr."""
    import json
    import re

    try:
        datos = json.load(sys.stdin)
    except Exception:
        return 0
    entrada = datos.get("tool_input") or {}
    from harness import guardia

    if evento == "pre-commit":
        cmd = entrada.get("command", "")
        if not re.search(r"\bgit\b[^\n;&|]*\bcommit\b", cmd):
            return 0
        res = guardia.guardia("preparados")
    elif evento == "post-edit":
        ruta = (entrada.get("file_path") or "").replace("\\", "/")
        if not re.search(r"/(src|specs|tests)/", ruta):
            return 0
        res = guardia.guardia("archivos", [ruta])
        if re.search(r"/(src|specs)/", ruta):
            from harness import contratos
            res += contratos.validar_contratos()
    else:
        print(f"hook desconocido: {evento}", file=sys.stderr)
        return 2
    fallas = [r for r in res if r.estado == "falla"]
    for r in fallas:
        print(r.formatear(), file=sys.stderr)
    return 2 if fallas else 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="harness")
    ap.add_argument("comando", nargs="?", default="todo", choices=["contratos", "guardia", "todo", "hook"])
    ap.add_argument("evento", nargs="?")
    ap.add_argument("--preparados", action="store_true")
    ap.add_argument("--archivos", nargs="+")
    ap.add_argument("--rapido", action="store_true")
    try:
        args = ap.parse_args(argv)
    except SystemExit as e:
        return 2 if e.code else 0
    try:
        if args.comando == "hook":
            return hook(args.evento or "")
        res = correr(args.comando, args.preparados, args.archivos, args.rapido)
        _imprimir(res)
        return codigo_de_salida(res)
    except Exception:
        traceback.print_exc()
        return 2


if __name__ == "__main__":
    sys.exit(main())
