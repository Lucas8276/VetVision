import pytest

from harness import Resultado, codigo_de_salida, formatear_resumen, resumen
from harness.__main__ import main


def test_estado_invalido_se_rechaza():
    with pytest.raises(ValueError):
        Resultado("contratos", "quizas")


def test_formatear_incluye_estado_ubicacion_regla_y_mensaje():
    r = Resultado("guardia", "falla", "a.py:3", regla="R-X", mensaje="corregir")
    assert r.formatear() == "FALLA  guardia  a.py:3  [R-X]  corregir"


def test_falla_de_contrato_muestra_esperado_y_obtenido():
    r = Resultado("contratos", "falla", "c › campo", esperado="3", obtenido="1", mensaje="x")
    assert "spec: 3" in r.formatear() and "codigo: 1" in r.formatear()


def test_resumen_cuenta_los_cuatro_estados():
    rs = [Resultado("t", e) for e in ("ok", "ok", "falla", "pendiente", "sin_verificacion")]
    assert resumen(rs) == {"ok": 2, "falla": 1, "pendiente": 1, "sin_verificacion": 1}
    assert formatear_resumen(rs) == "RESUMEN  ok=2  falla=1  pendiente=1  sin_verificacion=1"


@pytest.mark.parametrize("estado,esperado", [
    ("ok", 0), ("pendiente", 0), ("sin_verificacion", 0), ("falla", 1)])
def test_solo_falla_produce_codigo_1(estado, esperado):
    assert codigo_de_salida([Resultado("t", estado)]) == esperado


def test_subcomando_desconocido_devuelve_2():
    assert main(["nada"]) == 2


def test_excepcion_interna_devuelve_2_nunca_0(monkeypatch):
    import harness.__main__ as m

    def explota(*a, **k):
        raise RuntimeError("boom")

    monkeypatch.setattr(m, "correr", explota)
    assert main(["guardia"]) == 2
