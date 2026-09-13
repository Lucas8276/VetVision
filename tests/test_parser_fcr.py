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
