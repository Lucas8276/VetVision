"""Verificacion del documento de entrega (specs/005-harness-v2, incremento 1).

El contenido del documento es privado y no se versiona; aca vive solo el verificador. Cada regla
informa con `Resultado`: regla, archivo y linea. Nunca se repite el dato detectado (FR-010).

Dos tipos de hallazgo (FR-011):
- trabajo por hacer -> `pendiente` en modo normal, `falla` en modo entrega;
- defecto -> `falla` siempre.
"""
import re
from pathlib import Path

import yaml

from harness import Resultado
from harness import guardia

RAIZ = Path(__file__).resolve().parent.parent
DIR_POR_DEFECTO = RAIZ / "docs" / "privado" / "documento"
ARCHIVOS_DE_DATOS = ("normativa", "hechos", "fuentes", "estado-sync", "declaracion-uso-ia")

_RE_PENDIENTE = re.compile(r"\[(PENDIENTE|A completar|Completar)\b")
_RE_HECHO = re.compile(r"\{\{hecho:([A-Za-z0-9_]+)\}\}")
_RE_CITA = re.compile(r"\[@([A-Za-z0-9_]+)\]")


def _cargar(directorio, nombre):
    """Contenido de <nombre>.yaml, o None si el archivo no existe."""
    ruta = Path(directorio) / f"{nombre}.yaml"
    if not ruta.exists():
        return None
    with open(ruta, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _capitulos(directorio):
    """{nombre: [lineas]} de los capitulos Markdown, en orden de nombre."""
    return {p.name: p.read_text(encoding="utf-8", errors="replace").splitlines()
            for p in sorted(Path(directorio).glob("*.md"))}


class _Informe:
    """Acumula resultados y agrega un `ok` por regla sin hallazgos."""

    def __init__(self, entrega):
        self.entrega = entrega
        self.resultados = []
        self._con_hallazgo = set()

    def defecto(self, regla, ubicacion, mensaje):
        self._agregar(regla, "falla", ubicacion, mensaje)

    def por_hacer(self, regla, ubicacion, mensaje):
        self._agregar(regla, "falla" if self.entrega else "pendiente", ubicacion, mensaje)

    def _agregar(self, regla, estado, ubicacion, mensaje):
        self._con_hallazgo.add(regla.split("/")[0])
        self.resultados.append(Resultado("documento", estado, ubicacion, regla=regla, mensaje=mensaje))

    def cerrar(self, reglas):
        for regla in reglas:
            if regla not in self._con_hallazgo:
                self.resultados.append(Resultado("documento", "ok", regla=regla, mensaje="sin hallazgos"))
        return self.resultados


def _estructura(inf, caps, normativa):
    for sec in (normativa or {}).get("secciones_obligatorias", []):
        nombre, minimo = sec["archivo"], int(sec.get("palabras_minimas", 0))
        if nombre not in caps:
            inf.defecto("D-ESTRUCTURA", nombre, "falta una seccion obligatoria")
        elif sum(len(l.split()) for l in caps[nombre]) < minimo:
            inf.por_hacer("D-ESTRUCTURA", nombre, f"seccion con menos de {minimo} palabras: todavia es una plantilla")


def _pendientes(inf, caps):
    for nombre, lineas in caps.items():
        for n, linea in enumerate(lineas, 1):
            for _ in _RE_PENDIENTE.finditer(linea):
                inf.por_hacer("D-PENDIENTE", f"{nombre}:{n}", "marcador pendiente: resolverlo o dejar escrito el motivo")


def _valor_en_fuente(raiz, hecho):
    """None si el valor figura en su archivo fuente; si no, el motivo."""
    fuente = str(hecho.get("fuente") or "").split("#", 1)[0].strip()
    if not fuente or not hecho.get("verificado_en"):
        return "al hecho le falta `fuente` o `verificado_en`"
    ruta = Path(raiz) / fuente
    if not ruta.is_file():
        return "el archivo fuente del hecho no existe en el repositorio"
    texto = ruta.read_text(encoding="utf-8", errors="replace")
    buscado = str(hecho.get("valor_en_fuente") or hecho.get("valor") or "")
    if not buscado or (buscado not in texto and buscado.replace(",", ".") not in texto):
        return "el valor del hecho ya no figura en su archivo fuente: volver a verificarlo"
    return None


def _hechos(inf, caps, datos, raiz):
    if datos is None:
        inf.defecto("D-HECHO", "hechos.yaml", "falta hechos.yaml: sin registro de hechos no se puede respaldar ningun numero")
        return
    hechos = {str(h.get("clave")): h for h in datos.get("hechos", [])}
    for clave, hecho in hechos.items():
        motivo = _valor_en_fuente(raiz, hecho)
        if motivo:
            inf.defecto("D-HECHO", f"hechos.yaml:{clave}", motivo)
    for nombre, lineas in caps.items():
        for n, linea in enumerate(lineas, 1):
            for m in _RE_HECHO.finditer(linea):
                if m.group(1) not in hechos:
                    inf.defecto("D-HECHO", f"{nombre}:{n}", "se usa un hecho que no esta en hechos.yaml")


def _citas(inf, caps, datos, normativa):
    usadas = [(nombre, n, m.group(1)) for nombre, lineas in caps.items()
              for n, linea in enumerate(lineas, 1) for m in _RE_CITA.finditer(linea)]
    if datos is None:
        if usadas:
            inf.defecto("D-CITA", "fuentes.yaml", "falta fuentes.yaml: sin lista de fuentes no se puede citar")
        return
    fuentes = {str(f.get("clave")): f for f in datos.get("fuentes", [])}
    politica = (normativa or {}).get("citas", {})
    minimos = {str(k): int(v) for k, v in (politica.get("anio_minimo_por_tema") or {}).items()}
    for nombre, n, clave in usadas:
        ubic, f = f"{nombre}:{n}", fuentes.get(clave)
        if f is None:
            inf.defecto("D-CITA", ubic, "se cita una fuente que no esta en fuentes.yaml")
            continue
        if f.get("verificada") is not True:
            inf.defecto("D-CITA", ubic, "se cita una fuente sin verificar")
        if politica.get("acceso_libre_obligatorio") and f.get("acceso_libre") is not True:
            inf.defecto("D-CITA", ubic, "se cita una fuente que no es de lectura libre")
        minimo = minimos.get(str(f.get("tema")))
        if minimo and not f.get("clasico") and (not isinstance(f.get("anio"), int) or f["anio"] < minimo):
            inf.defecto("D-CITA", ubic, f"la fuente es anterior a {minimo}, el minimo de su tema")


def _datos_personales(inf, caps):
    ficticios = guardia.cargar_ficticios()
    for nombre, lineas in caps.items():
        for n, linea in enumerate(lineas, 1):
            for regla in guardia.revisar_linea(linea, "", ficticios):
                inf.defecto(f"D-DATOS/{regla}", f"{nombre}:{n}",
                            "dato sensible detectado (valor omitido); quitarlo o reemplazarlo por uno ficticio")


def _limite(inf, caps, normativa):
    descargo = (normativa or {}).get("descargo", {})
    frases = [f.lower() for f in descargo.get("frases", [])]
    for nombre in descargo.get("archivos", []):
        texto = " ".join(caps.get(nombre, [])).lower()
        if nombre in caps and frases and not any(f in texto for f in frases):
            inf.por_hacer("D-LIMITE", nombre, "falta el descargo de que el sistema no reemplaza al veterinario")


def _revision_e_ia(inf, normativa, sync, declaracion):
    secciones = (sync or {}).get("secciones", {}) or {}
    declarados = {str(r.get("apartado")) for r in (declaracion or {}).get("registros", []) or []}
    obligatorias = [s["archivo"] for s in (normativa or {}).get("secciones_obligatorias", [])]
    for nombre in sorted(set(obligatorias) | set(secciones)):
        s = secciones.get(nombre) or {}
        if s.get("estado") == "final":
            if not s.get("revisor") or not s.get("fecha"):
                inf.defecto("D-REVISION", nombre, "seccion marcada final sin revisor humano o sin fecha")
        elif nombre in obligatorias:
            inf.por_hacer("D-REVISION", nombre, "seccion todavia sin revision humana registrada")
        if s.get("asistencia_ia") is True and nombre not in declarados:
            inf.defecto("D-IA", nombre, "seccion con asistencia de IA que no figura en declaracion-uso-ia.yaml")


REGLAS = ("D-ESTRUCTURA", "D-PENDIENTE", "D-HECHO", "D-CITA", "D-DATOS", "D-LIMITE", "D-REVISION", "D-IA")


def validar_documento(directorio=DIR_POR_DEFECTO, raiz=RAIZ, entrega=False, por_defecto=False):
    """Lista de `Resultado` del documento. `por_defecto=True`: si el directorio no existe no es un
    error (en CI no hay documento privado); si se pidio un directorio explicito, si lo es."""
    directorio = Path(directorio)
    if not directorio.is_dir():
        if por_defecto:
            return [Resultado("documento", "sin_verificacion",
                              mensaje="no existe el directorio privado del documento; nada que verificar")]
        raise FileNotFoundError(f"no existe el directorio del documento: {directorio}")
    d = {n: _cargar(directorio, n) for n in ARCHIVOS_DE_DATOS}
    caps = _capitulos(directorio)
    inf = _Informe(entrega)
    _estructura(inf, caps, d["normativa"])
    _pendientes(inf, caps)
    _hechos(inf, caps, d["hechos"], raiz)
    _citas(inf, caps, d["fuentes"], d["normativa"])
    _datos_personales(inf, caps)
    _limite(inf, caps, d["normativa"])
    _revision_e_ia(inf, d["normativa"], d["estado-sync"], d["declaracion-uso-ia"])
    return inf.cerrar(REGLAS)


def resumen_documento(directorio=DIR_POR_DEFECTO, raiz=RAIZ):
    """Una sola linea para `python -m harness` (todo): informa sin bloquear el trabajo en el codigo."""
    res = validar_documento(directorio, raiz=raiz, por_defecto=True)
    if len(res) == 1 and res[0].estado == "sin_verificacion":
        return res
    nf = sum(r.estado == "falla" for r in res)
    np_ = sum(r.estado == "pendiente" for r in res)
    if nf == 0 and np_ == 0:
        return [Resultado("documento", "ok", mensaje="documento sin hallazgos")]
    return [Resultado("documento", "pendiente",
                      mensaje=f"{nf} falla{'' if nf == 1 else 's'}, {np_} pendiente{'' if np_ == 1 else 's'}; "
                              f"detalle: python -m harness documento")]
