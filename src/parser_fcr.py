from pathlib import Path

REGIONES_VALIDAS = {"CERVICAL", "TORAX", "ABDOMEN", "PELVIS", "EXTREMIDADES"}
VISTAS_VALIDAS = {"LAT", "VD", "DV", "AP"}
ESPECIES_VALIDAS = {"CANINO", "FELINO"}

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
    region = campos.get("Región anatómica", "").upper()
    if region not in REGIONES_VALIDAS:
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
