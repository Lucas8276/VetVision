"""Harness de verificacion automatica (spec 003).

Unidad comun de resultado: todas las verificaciones informan con `Resultado`.
"""
from dataclasses import dataclass

ESTADOS = ("ok", "falla", "pendiente", "sin_verificacion")


@dataclass
class Resultado:
    verificacion: str
    estado: str
    ubicacion: str = ""
    regla: str = ""
    esperado: str = ""
    obtenido: str = ""
    mensaje: str = ""

    def __post_init__(self):
        if self.estado not in ESTADOS:
            raise ValueError(f"estado invalido: {self.estado!r}")

    def formatear(self):
        """ESTADO  verificacion  ubicacion  [regla]  mensaje (sin valores detectados)."""
        msg = self.mensaje
        if self.estado == "falla" and self.esperado != "" and self.obtenido != "":
            msg = f"{msg} (spec: {self.esperado}; codigo: {self.obtenido})".strip()
        partes = [self.estado.upper(), self.verificacion, self.ubicacion]
        if self.regla:
            partes.append(f"[{self.regla}]")
        partes.append(msg)
        return "  ".join(p for p in partes if p)


def resumen(resultados):
    cuentas = {e: 0 for e in ESTADOS}
    for r in resultados:
        cuentas[r.estado] += 1
    return cuentas


def formatear_resumen(resultados):
    c = resumen(resultados)
    return "RESUMEN  " + "  ".join(f"{e}={c[e]}" for e in ESTADOS)


def codigo_de_salida(resultados):
    """Solo `falla` produce codigo 1. El codigo 2 (error interno) lo da __main__."""
    return 1 if any(r.estado == "falla" for r in resultados) else 0
