import struct

from src.ddo_parser import (
    fecha_dicom_a_puntos,
    generar_txt_desde_ddo,
    get_tag,
    parse_ddo_bytes,
)

ITEM = (0xFFFE, 0xE000)
SEQ_DELIM_CORRECTO = (0xFFFE, 0xE0DD)


def _elemento(group, elem, vr, value: bytes) -> bytes:
    return struct.pack("<HH", group, elem) + vr.encode("ascii") + struct.pack("<I", len(value)) + value


def _ddo_sintetico() -> bytes:
    return (
        _elemento(0x0010, 0x0020, "LO", b"12345")
        + _elemento(0x0010, 0x0010, "PN", b"REYES^ROMINA")
        + _elemento(0x0010, 0x0040, "CS", b"O")
        + _elemento(0x0008, 0x0022, "DA", b"20180411")
        + _elemento(0x0018, 0x0015, "CS", b"TORAX")
        + _elemento(0x0018, 0x1400, "LO", b"TORAX VD CANINO")
        + _elemento(0x0008, 0x0060, "CS", b"CR")
        + _elemento(0x0008, 0x0080, "LO", b"HOSPITAL DE CLINICAS - F.C.V.")
    )


def test_parse_ddo_bytes_extrae_campos_basicos():
    tags = parse_ddo_bytes(_ddo_sintetico())

    assert get_tag(tags, 0x0010, 0x0020) == "12345"
    assert get_tag(tags, 0x0010, 0x0010) == "REYES^ROMINA"
    assert get_tag(tags, 0x0010, 0x0040) == "O"
    assert get_tag(tags, 0x0008, 0x0022) == "20180411"
    assert get_tag(tags, 0x0018, 0x0015) == "TORAX"
    assert get_tag(tags, 0x0018, 0x1400) == "TORAX VD CANINO"
    assert get_tag(tags, 0x0008, 0x0060) == "CR"
    assert get_tag(tags, 0x0008, 0x0080) == "HOSPITAL DE CLINICAS - F.C.V."


def test_get_tag_default_cuando_falta():
    tags = parse_ddo_bytes(_ddo_sintetico())
    assert get_tag(tags, 0x9999, 0x9999, default="") == ""
    assert get_tag(tags, 0x9999, 0x9999, default="N/A") == "N/A"


def test_regresion_seq_delimitation_item_no_desincroniza_offsets():
    """
    FR-002: el tag de cierre de secuencia DICOM es (FFFE,E0DD), NO (FFFE,DD00).
    Si el parser confunde estos dos (se ven "espejados" en bytes), no reconoce el
    cierre real de la secuencia, sigue intentando leer elementos anidados donde ya
    no los hay, y termina leyendo basura / offsets incorrectos en el resto del
    archivo. Este test arma una secuencia (SQ) de largo indefinido con UN item
    anidado de largo finito, la cierra con el tag CORRECTO (FFFE,E0DD), y verifica
    que el elemento que viene justo despues en el archivo se sigue leyendo bien.
    """
    item_relleno = b"\x00" * 6
    item_anidado = struct.pack("<HH", *ITEM) + struct.pack("<I", len(item_relleno)) + item_relleno

    secuencia = (
        struct.pack("<HH", 0x0008, 0x9999)
        + b"SQ"
        + struct.pack("<I", 0xFFFFFFFF)
        + item_anidado
        + struct.pack("<HH", *SEQ_DELIM_CORRECTO)
        + struct.pack("<I", 0)
    )

    marcador_siguiente = _elemento(0x0010, 0x0010, "PN", b"MARCADOR^OK")

    tags = parse_ddo_bytes(secuencia + marcador_siguiente)

    assert get_tag(tags, 0x0010, 0x0010) == "MARCADOR^OK"


def test_fecha_dicom_a_puntos_formato_valido():
    assert fecha_dicom_a_puntos("20180411") == "11.04.2018"


def test_fecha_dicom_a_puntos_formato_inesperado_no_falla():
    assert fecha_dicom_a_puntos("") == ""
    assert fecha_dicom_a_puntos("2018") == "2018"


def test_generar_txt_desde_ddo_escribe_las_8_lineas(tmp_path):
    ddo_path = tmp_path / "estudio.ddo"
    ddo_path.write_bytes(_ddo_sintetico())
    txt_path = tmp_path / "estudio.txt"

    generar_txt_desde_ddo(ddo_path, txt_path)
    contenido = txt_path.read_text(encoding="utf-8")

    assert "ID del paciente:12345" in contenido
    assert "Nombre del paciente:REYES ROMINA" in contenido
    assert "Sexo:O" in contenido
    assert "Fecha de exposición:11.04.2018" in contenido
    assert "Región anatómica:TORAX" in contenido
    assert "Nombre del menú de exposición:TORAX VD CANINO" in contenido
    assert "Modalidad:CR" in contenido
    assert "Institución:HOSPITAL DE CLINICAS - F.C.V." in contenido
