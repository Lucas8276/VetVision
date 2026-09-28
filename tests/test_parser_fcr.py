from src.parser_fcr import parsear_metadata_fcr


def test_parsear_metadata_fcr(tmp_path):
    contenido = (
        "ID del paciente: 12345\n"
        "Nombre del menú de exposición: CERVICAL LAT CANINO\n"
        "Modalidad: CR\n"
    )
    txt_path = tmp_path / "paciente_12345.txt"
    txt_path.write_text(contenido, encoding="utf-8")

    resultado = parsear_metadata_fcr(txt_path)

    assert resultado["id_paciente"] == "12345"
    assert resultado["region"] == "CERVICAL"
    assert resultado["vista"] == "LAT"
    assert resultado["especie"] == "CANINO"
    assert resultado["modalidad"] == "CR"


def test_parsear_metadata_fcr_region_desconocida(tmp_path):
    contenido = "ID del paciente: 999\nNombre del menú de exposición: RARO LAT FELINO\n"
    txt_path = tmp_path / "paciente_999.txt"
    txt_path.write_text(contenido, encoding="utf-8")

    resultado = parsear_metadata_fcr(txt_path)

    assert resultado["region"] == "DESCONOCIDA"
    assert resultado["especie"] == "FELINO"


def _escribir_txt(tmp_path, nombre, region_anatomica, menu_exposicion):
    contenido = (
        f"ID del paciente: 1\n"
        f"Región anatómica: {region_anatomica}\n"
        f"Nombre del menú de exposición: {menu_exposicion}\n"
    )
    txt_path = tmp_path / nombre
    txt_path.write_text(contenido, encoding="utf-8")
    return txt_path


def test_region_chest_se_normaliza_a_torax(tmp_path):
    # menu sin la palabra "TORAX" a proposito, para probar que la normalizacion viene
    # del tag directo (FR-005), no del fallback de menu de exposicion
    txt_path = _escribir_txt(tmp_path, "p1.txt", "CHEST", "ESOFAGO CANINO")
    assert parsear_metadata_fcr(txt_path)["region"] == "TORAX"


def test_region_neck_se_normaliza_a_cervical(tmp_path):
    txt_path = _escribir_txt(tmp_path, "p2.txt", "NECK", "GARGANTA LAT CANINO")
    assert parsear_metadata_fcr(txt_path)["region"] == "CERVICAL"


def test_region_head_se_normaliza_a_craneo(tmp_path):
    txt_path = _escribir_txt(tmp_path, "p3.txt", "HEAD", "EXAMEN VD/DV FELINO")
    assert parsear_metadata_fcr(txt_path)["region"] == "CRANEO"


def test_region_up_exm_se_normaliza_a_extremidades(tmp_path):
    txt_path = _escribir_txt(tmp_path, "p4.txt", "UP_EXM", "MIEMBRO ANTERIOR LAT CANINO")
    assert parsear_metadata_fcr(txt_path)["region"] == "EXTREMIDADES"


def test_region_low_exm_se_normaliza_a_extremidades(tmp_path):
    txt_path = _escribir_txt(tmp_path, "p5.txt", "LOW_EXM", "MIEMBRO POSTERIOR LAT CANINO")
    assert parsear_metadata_fcr(txt_path)["region"] == "EXTREMIDADES"


def test_vista_combinada_vd_dv_se_reconoce(tmp_path):
    txt_path = _escribir_txt(tmp_path, "p6.txt", "HEAD", "CRANEO VD/DV FELINO")
    assert parsear_metadata_fcr(txt_path)["vista"] == "VD/DV"


def test_menu_sin_vista_devuelve_none_sin_excepcion(tmp_path):
    txt_path = _escribir_txt(tmp_path, "p7.txt", "CHEST", "ESOFAGO CANINO")
    assert parsear_metadata_fcr(txt_path)["vista"] is None


def test_id_paciente_con_guion_se_preserva_completo(tmp_path):
    contenido = "ID del paciente: 999-1\nNombre del menú de exposición: PELVIS VD CANINO\n"
    txt_path = tmp_path / "p8.txt"
    txt_path.write_text(contenido, encoding="utf-8")
    assert parsear_metadata_fcr(txt_path)["id_paciente"] == "999-1"
