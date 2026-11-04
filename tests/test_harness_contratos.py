import pytest

from harness.contratos import cargar_specs, con_cambio, validar_contratos


@pytest.fixture(scope="module")
def specs():
    return cargar_specs()


def _fallas(res):
    return [r for r in res if r.estado == "falla"]


@pytest.mark.contratos
def test_repo_real_cumple_los_contratos(specs):
    assert _fallas(validar_contratos(specs)) == []


@pytest.mark.parametrize("ruta,valor,campo,esperado,obtenido", [
    (["model-tensor", "input", "canales"], 3, "canales", "3", "1"),
    (["model-tensor", "export", "opset"], 17, "opset", "17", "18"),
])
def test_deriva_reintroducida_se_detecta(specs, ruta, valor, campo, esperado, obtenido):
    malo = con_cambio(specs, ruta, valor)
    fallas = _fallas(validar_contratos(malo))
    assert len(fallas) == 1
    assert campo in fallas[0].ubicacion
    assert (fallas[0].esperado, fallas[0].obtenido) == (esperado, obtenido)


def test_vista_faltante_en_el_contrato_se_detecta(specs):
    malo = con_cambio(specs, ["data-contract", "proyecciones_admitidas"], ["LAT", "VD", "DV"])
    fallas = _fallas(validar_contratos(malo))
    assert [f.ubicacion for f in fallas] == ["data-contract › proyecciones_admitidas"]


def test_secciones_pendientes_y_campos_sin_verificador_no_fallan(specs):
    res = validar_contratos(specs)
    pendientes = [r.ubicacion for r in res if r.estado == "pendiente"]
    assert "model-tensor › etapas › etapa_1_triaje" in pendientes
    assert "model-tensor › etapas › etapa_2_diagnostico" in pendientes
    sin = [r.ubicacion for r in res if r.estado == "sin_verificacion"]
    assert "data-contract › resolucion_minima_px" in sin
