"""Guardia contra datos personales, archivos crudos y secretos (solo biblioteca estandar).

Reglas estructurales + lista de valores FICTICIOS aprobados (`valores_ficticios.txt`).
El reporte NUNCA contiene el valor detectado: los logs de CI de un repo publico son publicos.
"""
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from harness import Resultado

RAIZ = Path(__file__).resolve().parent.parent
FICTICIOS = Path(__file__).resolve().parent / "valores_ficticios.txt"

EXT_CRUDAS = {".ddo", ".hq", ".dsp", ".std", ".edk", ".edr", ".db", ".pt", ".onnx"}
RUTAS_CRUDAS = ("data/raw/", "data/processed/")
_FCR = re.compile(r"(^|/)FCR\d+\.[A-Za-z0-9]+$")

_MAY = "A-ZÁÉÍÓÚÑ"
# Los patrones se arman por partes para que este archivo no se marque a si mismo.
_RE_CAMPO_PACIENTE = re.compile(r"Nombre del paciente\s*:[ \t]*([^\s`].*?)\s*$", re.I)
_RE_NOMBRE_DICOM = re.compile(rf"(?<![\w^])([{_MAY}]{{3,}}\^[{_MAY}]{{2,}}(?:\^[{_MAY}]+)*)(?![\w^])")
_RE_CAMPO_ID = re.compile(r"ID del paciente\s*:[ \t]*([^\s`]\S*)", re.I)
_RE_ID_SUELTO = re.compile(r"(?<![\w.\-/])(\d{3,4}-\d)(?![\w\-])")
_RE_SECRETO = [
    re.compile("AK" + r"IA[0-9A-Z]{16}"),
    re.compile(r"gh[pousr]" + r"_[A-Za-z0-9]{30,}"),
    re.compile("-----BEGIN [A-Z ]*" + "PRIVATE KEY-----"),
    re.compile(r"(?i)(password|passwd|api[_-]?key|secret[_-]?key)\s*[=:]\s*['\"]?[A-Za-z0-9/+_\-]{16,}"),
]
_RE_CONTACTO = [
    re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"),
    re.compile(r"(?<!\d)(?:\+?\d[\d ()\-]{7,}\d)(?!\d)"),
    re.compile(r"\b(?:Dra?|Dr|Lic|Ing|Sr|Sra)\.\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+"),
]
ARCHIVO_CONTACTO = "docs/MEMORIA.md"


@dataclass
class Hallazgo:
    ruta: str
    linea: int
    regla: str


def cargar_ficticios(ruta=FICTICIOS):
    valores = set()
    if Path(ruta).exists():
        for lin in Path(ruta).read_text(encoding="utf-8").splitlines():
            lin = lin.split("#", 1)[0].strip()
            if lin:
                valores.add(lin.lower())
    return valores


def _aprobado(valor, ficticios):
    # Un literal de codigo cierra con comilla (y quiza "\n" antes): el valor es lo previo.
    v = valor.strip().split('"')[0].split("\\n")[0]
    v = v.strip("'`").strip().lower()
    # "{...}" = interpolacion/plantilla de codigo, no un valor real
    return v in ficticios or v.startswith("{")


def revisar_ruta(ruta):
    """Reglas que dependen solo de la ruta (R-ARCHIVO-CRUDO)."""
    p = ruta.replace("\\", "/")
    if PurePosixPath(p).suffix.lower() in EXT_CRUDAS or p.startswith(RUTAS_CRUDAS) or _FCR.search(p):
        return "R-ARCHIVO-CRUDO"
    return None


def revisar_linea(texto, ruta="", ficticios=None):
    """Devuelve la lista de ids de regla que dispara una linea (sin valores)."""
    ficticios = cargar_ficticios() if ficticios is None else ficticios
    reglas = []
    m = _RE_CAMPO_PACIENTE.search(texto)
    if m and not _aprobado(m.group(1), ficticios):
        reglas.append("R-CAMPO-PACIENTE")
    if any(not _aprobado(m.group(1), ficticios) for m in _RE_NOMBRE_DICOM.finditer(texto)):
        reglas.append("R-NOMBRE-DICOM")
    m = _RE_CAMPO_ID.search(texto)
    id_malo = bool(m and not _aprobado(m.group(1), ficticios))
    id_malo = id_malo or any(not _aprobado(x.group(1), ficticios) for x in _RE_ID_SUELTO.finditer(texto))
    if id_malo:
        reglas.append("R-ID-PACIENTE")
    if any(r.search(texto) for r in _RE_SECRETO):
        reglas.append("R-SECRETO")
    if ruta.replace("\\", "/") == ARCHIVO_CONTACTO and any(r.search(texto) for r in _RE_CONTACTO):
        reglas.append("R-CONTACTO")
    return reglas


def _leer_texto(ruta):
    try:
        datos = Path(ruta).read_bytes()
    except OSError:
        return None
    if b"\x00" in datos[:8192]:
        return None
    return datos.decode("utf-8", errors="replace")


def revisar_archivo(ruta, base=RAIZ, ficticios=None, lineas=None):
    """Hallazgos de un archivo. `lineas`: conjunto de n° de linea a revisar (None = todas)."""
    rel = str(ruta).replace("\\", "/")
    hallazgos = []
    regla = revisar_ruta(rel)
    if regla:
        hallazgos.append(Hallazgo(rel, 0, regla))
        return hallazgos
    texto = _leer_texto(Path(base) / ruta)
    if texto is None:
        return hallazgos
    for n, lin in enumerate(texto.splitlines(), 1):
        if lineas is not None and n not in lineas:
            continue
        for r in revisar_linea(lin, rel, ficticios):
            hallazgos.append(Hallazgo(rel, n, r))
    return hallazgos


def _git(args, cwd):
    return subprocess.run(
        ["git", "-c", "core.quotepath=off", *args], cwd=cwd, capture_output=True,
        text=True, encoding="utf-8", errors="replace", check=True).stdout


def archivos_rastreados(cwd=RAIZ):
    return [l for l in _git(["ls-files"], cwd).splitlines() if l]


def lineas_preparadas(cwd=RAIZ):
    """{ruta: set(n° de lineas agregadas)} del indice; archivos nuevos/modificados."""
    salida = _git(["diff", "--cached", "-U0", "--diff-filter=ACMR", "--no-color"], cwd)
    por_archivo, actual = {}, None
    for lin in salida.splitlines():
        if lin.startswith("+++ b/"):
            actual = lin[6:]
            por_archivo.setdefault(actual, set())
        elif lin.startswith("@@") and actual is not None:
            m = re.search(r"\+(\d+)(?:,(\d+))?", lin)
            ini, n = int(m.group(1)), int(m.group(2) or 1)
            por_archivo[actual].update(range(ini, ini + n))
    for ruta in _git(["diff", "--cached", "--name-only", "--diff-filter=ACMR"], cwd).splitlines():
        por_archivo.setdefault(ruta, set())  # p.ej. binarios: solo regla de ruta
    return por_archivo


def a_resultados(hallazgos):
    return [Resultado("guardia", "falla", f"{h.ruta}:{h.linea}" if h.linea else h.ruta,
                      regla=h.regla,
                      mensaje="dato sensible o archivo crudo detectado (valor omitido); "
                              "reemplazar por un valor ficticio o quitar el archivo")
            for h in hallazgos]


def guardia(modo="arbol", archivos=None, cwd=RAIZ):
    """modo: 'arbol' | 'preparados' | 'archivos'. Devuelve lista de Resultado."""
    ficticios = cargar_ficticios()
    hallazgos = []
    if modo == "preparados":
        for ruta, lineas in lineas_preparadas(cwd).items():
            hallazgos += revisar_archivo(ruta, cwd, ficticios, lineas or None)
    elif modo == "archivos":
        for ruta in archivos or []:
            rel = Path(ruta)
            try:
                rel = rel.resolve().relative_to(Path(cwd).resolve())
            except ValueError:
                pass
            hallazgos += revisar_archivo(rel.as_posix(), cwd, ficticios)
    else:
        for ruta in archivos_rastreados(cwd):
            hallazgos += revisar_archivo(ruta, cwd, ficticios)
    res = a_resultados(hallazgos)
    return res or [Resultado("guardia", "ok", mensaje=f"modo {modo}: sin hallazgos")]


