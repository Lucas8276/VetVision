"""Parsing binario del .ddo del FCR PRIMA (Fujifilm) y generacion del .txt de metadata.

Formato tipo DICOM Explicit VR Little Endian, pero NO DICOM estandar (sin preambulo,
grupos privados de Fuji, longitud siempre de 4 bytes incluso para VR "cortos"). Ver
formato_ddo_hq_FCR_PRIMA.md para el detalle completo de la ingenieria inversa.
"""

import struct
from pathlib import Path

ITEM = (0xFFFE, 0xE000)
ITEM_DELIM = (0xFFFE, 0xE00D)
SEQ_DELIM = (0xFFFE, 0xE0DD)  # ojo: NO (0xFFFE, 0xDD00) - ver formato_ddo_hq_FCR_PRIMA.md


def parse_ddo_bytes(data: bytes):
    """Devuelve {(group, elem): (vr, raw_bytes_o_None)}."""
    n = len(data)
    tags = {}

    def read_element(i):
        group, elem = struct.unpack_from("<HH", data, i)
        j = i + 4

        if (group, elem) == ITEM:
            length = struct.unpack_from("<I", data, j)[0]
            j += 4
            if length == 0xFFFFFFFF:
                while True:
                    g2, e2 = struct.unpack_from("<HH", data, j)
                    if (g2, e2) == ITEM_DELIM:
                        l2 = struct.unpack_from("<I", data, j + 4)[0]
                        j += 8 + l2
                        break
                    j, _ = read_element(j)
                return j, None
            else:
                j += length
                return j, None

        if (group, elem) in (ITEM_DELIM, SEQ_DELIM):
            length = struct.unpack_from("<I", data, j)[0]
            j += 4 + length
            return j, None

        vr = data[j:j + 2].decode("ascii", errors="replace")
        j += 2
        length = struct.unpack_from("<I", data, j)[0]
        j += 4

        if length == 0xFFFFFFFF:
            while True:
                g2, e2 = struct.unpack_from("<HH", data, j)
                if (g2, e2) == SEQ_DELIM:
                    l2 = struct.unpack_from("<I", data, j + 4)[0]
                    j += 8 + l2
                    break
                j, _ = read_element(j)
            return j, ((group, elem), vr, None)
        else:
            value = data[j:j + length]
            j += length
            return j, ((group, elem), vr, value)

    i = 0
    while i + 8 <= n:
        i, result = read_element(i)
        if result:
            tag, vr, value = result
            tags[tag] = (vr, value)
    return tags


def get_tag(tags, group, elem, default=""):
    v = tags.get((group, elem))
    if not v or v[1] is None:
        return default
    _, raw = v
    try:
        return raw.decode("ascii", errors="replace").strip("\x00 ").strip()
    except Exception:
        return default


def fecha_dicom_a_puntos(fecha: str) -> str:
    if len(fecha) == 8 and fecha.isdigit():
        return f"{fecha[6:8]}.{fecha[4:6]}.{fecha[0:4]}"
    return fecha


def generar_txt_desde_ddo(path_ddo: Path, destino_txt: Path):
    """Lee un .ddo y escribe el .txt de metadata (mismo formato que las exportaciones oficiales)."""
    with open(path_ddo, "rb") as f:
        data = f.read()
    tags = parse_ddo_bytes(data)

    contenido = (
        f"ID del paciente:{get_tag(tags, 0x0010, 0x0020)}\n"
        f"Nombre del paciente:{get_tag(tags, 0x0010, 0x0010).replace('^', ' ')}\n"
        f"Sexo:{get_tag(tags, 0x0010, 0x0040)}\n"
        f"Fecha de exposición:{fecha_dicom_a_puntos(get_tag(tags, 0x0008, 0x0022))}\n"
        f"Región anatómica:{get_tag(tags, 0x0018, 0x0015)}\n"
        f"Nombre del menú de exposición:{get_tag(tags, 0x0018, 0x1400)}\n"
        f"Modalidad:{get_tag(tags, 0x0008, 0x0060)}\n"
        f"Institución:{get_tag(tags, 0x0008, 0x0080)}\n"
    )
    with open(destino_txt, "w", encoding="utf-8") as f:
        f.write(contenido)
