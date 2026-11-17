"""Normalizador de diagnosticos (specs/008-etiquetas-diagnosticos). Textos 100% sinteticos,
escritos para esta spec: ninguno copiado de una planilla real."""
import pytest

from src.diagnosticos import cargar_vocabulario, etiquetar, normalizar_texto

V = cargar_vocabulario()


def test_normalizar_texto_minusculas_tildes_y_espacios():
    assert normalizar_texto("  Patrón   Bronquial.") == "patron bronquial"
    assert normalizar_texto("S/P") == "s/p"


def test_normal_por_abreviatura_o_control():
    for texto in ("s/p", "s/alt", "sin alteraciones", "control", "n", "normal"):
        r = etiquetar(texto, V)
        assert r.positivas == {"NORMAL"} and r.sano is True and not r.revisar, texto


def test_hallazgo_toracico_positivo_es_no_sano():
    r = etiquetar("patron bronquial", V)
    assert "PATRON_BRONQUIAL" in r.positivas
    assert r.sano is False


def test_diagnosticos_multiples_en_un_mismo_texto():
    r = etiquetar("patron bronquial y patron vascular", V)
    assert r.positivas == {"PATRON_BRONQUIAL", "PATRON_VASCULAR"}
    assert r.sano is False


def test_negacion_no_cuenta_como_positivo():
    r = etiquetar("sin signos de metastasis", V)
    assert "MASA_NODULO_METASTASIS" not in r.positivas
    assert "MASA_NODULO_METASTASIS" in r.negadas


def test_negacion_como_unico_contenido_va_a_revisar_no_a_normal():
    r = etiquetar("no se observan signos de metastasis", V)
    assert r.positivas == set()
    assert r.revisar and r.sano is None


def test_negacion_con_otro_hallazgo_positivo_en_el_mismo_texto():
    r = etiquetar("sin signos de metastasis, patron bronquial", V)
    assert r.positivas == {"PATRON_BRONQUIAL"}
    assert "MASA_NODULO_METASTASIS" in r.negadas
    assert r.sano is False


def test_hallazgo_no_toracico_no_es_sano_ni_no_sano():
    r = etiquetar("fractura", V)
    assert r.positivas == {"HALLAZGO_NO_TORACICO"}
    assert r.sano is None


def test_texto_vacio_va_a_revisar():
    for texto in ("", "   ", None):
        r = etiquetar(texto, V)
        assert r.revisar and r.sano is None


def test_combinacion_ambigua_normal_mas_hallazgo_va_a_revisar():
    r = etiquetar("s/p patron bronquial", V)
    assert r.revisar
    assert r.sano is None


def test_texto_sin_terminologia_reconocible_es_ruido():
    r = etiquetar("asdf qwerty zzz", V)
    assert r.positivas == set() and r.ruido and r.sano is None


def test_errata_conocida_se_corrige_antes_de_buscar():
    r = etiquetar("nuemotorax", V)
    assert "NEUMOTORAX" in r.positivas


def test_etiqueta_desconocida_fuera_del_vocabulario_no_rompe():
    r = etiquetar("blablablamedico", V)
    assert r.ruido


@pytest.mark.parametrize("texto", ["metastasis", "neumotorax", "cardiomegalia"])
def test_cada_positivo_simple_da_no_sano(texto):
    assert etiquetar(texto, V).sano is False
