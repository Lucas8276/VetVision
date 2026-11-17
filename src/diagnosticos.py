"""Normalizador deterministico de diagnosticos transcriptos (specs/008-etiquetas-diagnosticos).

Convierte un texto libre (con abreviaturas, erratas y negaciones) en etiquetas, usando SOLO el
vocabulario versionado en specs/diagnosticos_vocabulario.yaml. Nada se adivina: lo ambiguo queda
marcado `revisar` para que lo resuelva una persona. No lee ni conoce ningun dato de paciente.
"""
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parent.parent
RUTA_VOCABULARIO_POR_DEFECTO = RAIZ / "specs" / "diagnosticos_vocabulario.yaml"

_NORMAL = "NORMAL"
_SEPARADOR = re.compile(r"[,;]|(?:\by\b)")


def cargar_vocabulario(ruta=RUTA_VOCABULARIO_POR_DEFECTO):
    with open(ruta, encoding="utf-8") as f:
        return yaml.safe_load(f)


def normalizar_texto(texto):
    """minusculas, sin tildes, espacios y puntuacion final colapsados. No toca '/' (de 's/p')."""
    if not texto:
        return ""
    t = unicodedata.normalize("NFD", texto.strip().lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    t = re.sub(r"\s+", " ", t)
    return t.strip(" .;:")


def _corregir_erratas(texto, vocabulario):
    for errata, correcta in (vocabulario.get("erratas") or {}).items():
        texto = re.sub(rf"\b{re.escape(errata)}\b", correcta, texto)
    return texto


def _expandir_abreviaturas(texto, vocabulario):
    """FR-002: las abreviaturas conocidas se expanden a su forma completa antes de buscar
    terminos (ademas de poder figurar como termino directo en `terminos`)."""
    for abreviatura, completa in (vocabulario.get("abreviaturas") or {}).items():
        texto = re.sub(rf"\b{re.escape(abreviatura)}\b", completa, texto)
    return texto


@dataclass
class ResultadoEtiquetado:
    positivas: set = field(default_factory=set)
    negadas: set = field(default_factory=set)
    revisar: str = ""
    ruido: bool = False
    sano: object = field(default=None, init=False)

    def __post_init__(self, vocabulario=None):
        vocabulario = vocabulario if vocabulario is not None else cargar_vocabulario()
        etiquetas_vocab = vocabulario.get("etiquetas") or {}
        if self.revisar or self.ruido:
            self.sano = None
        elif self.positivas == {_NORMAL}:
            self.sano = True
        elif any(etiquetas_vocab.get(e, {}).get("torax") for e in self.positivas):
            self.sano = False
        else:
            self.sano = None


def etiquetar(texto, vocabulario=None):
    """Etiqueta un texto de diagnostico ya transcripto. Nunca lanza excepcion por texto invalido:
    un texto vacio o irreconocible queda en `revisar` o `ruido`, no se adivina."""
    vocabulario = vocabulario if vocabulario is not None else cargar_vocabulario()
    terminos = vocabulario.get("terminos") or {}
    negaciones = sorted((vocabulario.get("negaciones") or []), key=len, reverse=True)

    normalizado = normalizar_texto(texto)
    if not normalizado:
        return ResultadoEtiquetado(revisar="texto vacio")
    normalizado = _corregir_erratas(normalizado, vocabulario)
    normalizado = _expandir_abreviaturas(normalizado, vocabulario)

    # Zonas negadas: desde el final de cada disparador hasta el siguiente separador (o el final).
    zonas_negadas = []
    for negador in negaciones:
        desde = 0
        while True:
            idx = normalizado.find(negador, desde)
            if idx == -1:
                break
            fin_disparador = idx + len(negador)
            siguiente_sep = _SEPARADOR.search(normalizado, fin_disparador)
            zonas_negadas.append((fin_disparador, siguiente_sep.start() if siguiente_sep else len(normalizado)))
            desde = fin_disparador

    def negada(posicion):
        return any(a <= posicion < b for a, b in zonas_negadas)

    positivas, negadas, reconocido = set(), set(), False
    for termino, etiquetas in terminos.items():
        if not termino:
            continue
        for coincidencia in re.finditer(rf"\b{re.escape(termino)}\b", normalizado):
            reconocido = True
            (negadas if negada(coincidencia.start()) else positivas).update(etiquetas)

    if not reconocido:
        return ResultadoEtiquetado(ruido=True)
    # NORMAL junto con otro hallazgo en el mismo texto es ambiguo (no se sabe si el hallazgo es
    # nuevo o el "normal"/"s/p" se refiere a otra parte del cuerpo): queda para revision humana.
    if _NORMAL in positivas and len(positivas) > 1:
        return ResultadoEtiquetado(revisar="NORMAL combinado con otro hallazgo en el mismo texto")
    if not positivas and negadas:
        return ResultadoEtiquetado(
            negadas=negadas, revisar="solo hay negaciones: no equivale a un control de rutina")
    return ResultadoEtiquetado(positivas=positivas, negadas=negadas)
