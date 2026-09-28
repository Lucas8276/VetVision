from pathlib import Path

REGIONES_VALIDAS = {"CERVICAL", "TORAX", "ABDOMEN", "PELVIS", "EXTREMIDADES", "CRANEO"}
VISTAS_VALIDAS = {"LAT", "VD", "DV", "AP", "VD/DV"}
ESPECIES_VALIDAS = {"CANINO", "FELINO"}

# Codigos reales de region anatomica que entrega el equipo FCR PRIMA en el tag
# (0018,0015), distintos de los nombres en espanol que ya se validan. Ver
# specs/001-fcr-metadata-extraction/research.md (Decision 1) para el origen de
# esta tabla: se releva de una muestra real de ~500 estudios.
_CODIGOS_REGION_EQUIPO = {
    "CHEST": "TORAX",
    "NECK": "CERVICAL",
    "HEAD": "CRANEO",
    "UP_EXM": "EXTREMIDADES",
    "LOW_EXM": "EXTREMIDADES",
}


def _normalizar_codigo_region(valor_tag: str):
    """Mapea codigos reales del equipo a la region canonica en espanol.
    Devuelve None si valor_tag no esta en la tabla (el llamador decide el
    fallback), no "DESCONOCIDA" directamente."""
    return _CODIGOS_REGION_EQUIPO.get(valor_tag)


def parsear_metadata_fcr(txt_path):
    campos = {}
    with open(txt_path, encoding="utf-8") as f:
        for linea in f:
            if ":" in linea:
                clave, valor = linea.split(":", 1)
                campos[clave.strip()] = valor.strip()

    menu = campos.get("Nombre del menú de exposición", "")
    partes = menu.upper().split()

    especie = next((p for p in partes if p in ESPECIES_VALIDAS), None)
    vista = next((p for p in partes if p in VISTAS_VALIDAS), None)
    region_tag = campos.get("Región anatómica", "").upper()
    if region_tag in REGIONES_VALIDAS:
        region = region_tag
    else:
        region = _normalizar_codigo_region(region_tag)
        if region is None:
            region = next((p for p in partes if p in REGIONES_VALIDAS), "DESCONOCIDA")

    return {
        "id_paciente": campos.get("ID del paciente"),
        "region": region,
        "vista": vista,
        "especie": especie,
        "modalidad": campos.get("Modalidad"),
    }


if __name__ == "__main__":
    import sys
    print(parsear_metadata_fcr(sys.argv[1]))
