"""Particion entrenamiento/validacion por paciente (specs/007-evaluacion-modelo, incremento 1).

Por que existe: partir al azar por imagen deja placas de un mismo paciente en entrenamiento y en
validacion a la vez, y la metrica termina midiendo memoria de pacientes ya vistos. Aca todas las
placas de un paciente quedan del mismo lado.

Los identificadores nunca salen de este modulo en claro: se convierten en un hash (FR-004).
"""
import hashlib
import re

from sklearn.model_selection import StratifiedGroupKFold

PARTICION_POR_DEFECTO = "paciente"
PARTICIONES_VALIDAS = ("paciente", "imagen")

_SUFIJO_NUMERICO = re.compile(r"^(.+?)-\d+$")


def grupo_paciente(id_paciente):
    """Grupo (hash de 16 caracteres) al que pertenece un estudio, o None si no hay identificador.

    Se normaliza (sin espacios, en mayusculas) y se quita el sufijo numerico posterior al guion:
    no sabemos si ese sufijo distingue visitas o animales de una misma ficha, y agrupar de mas
    nunca produce fuga (agrupar de menos, si).
    """
    if id_paciente is None:
        return None
    valor = re.sub(r"\s+", "", str(id_paciente)).upper()
    if not valor:
        return None
    m = _SUFIJO_NUMERICO.match(valor)
    base = m.group(1) if m else valor
    return hashlib.sha256(base.encode("utf-8")).hexdigest()[:16]


def particion_por_grupos(etiquetas, grupos, val_split=0.2, seed=42):
    """Devuelve (indices_train, indices_val) sin grupos compartidos y con clases balanceadas.

    Usa un pliegue de StratifiedGroupKFold: con val_split=0.2 son 5 pliegues y la validacion es
    uno de ellos (aprox. 20 %). Un estudio sin grupo (None) forma su propio grupo.
    """
    n = len(etiquetas)
    if n != len(grupos):
        raise ValueError("etiquetas y grupos deben tener el mismo largo")
    grupos = [g if g is not None else f"__sin_id_{i}" for i, g in enumerate(grupos)]
    n_pliegues = max(2, round(1 / val_split))
    pliegues = StratifiedGroupKFold(n_splits=n_pliegues, shuffle=True, random_state=seed)
    train, val = next(pliegues.split([0] * n, list(etiquetas), grupos))
    return sorted(int(i) for i in train), sorted(int(i) for i in val)


def huella_particion(indices):
    """Hash corto de un conjunto de indices: identifica una particion sin exponer ningun dato."""
    texto = ",".join(str(i) for i in sorted(indices))
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()[:12]
