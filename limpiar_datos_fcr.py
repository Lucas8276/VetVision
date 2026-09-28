import argparse
import csv
import os
import shutil
from pathlib import Path

import numpy as np
from PIL import Image
from pylibjpeg import decode as decode_jpeg_lossless

from src.ddo_parser import generar_txt_desde_ddo

# --- CONFIGURACIÓN ---
EXTENSIONES_A_MOVER_SIEMPRE = {".dsp", ".edk", ".edr", ".std"}  # .hq se maneja aparte (se decodifica)
EXTENSION_DDO = ".ddo"
EXTENSION_JPG = ".jpg"
EXTENSION_HQ = ".hq"

UMBRAL_JPG_GRANDE = 6 * 1024   # bytes (> 6 KB = conservar)
UMBRAL_JPG_CHICO = 5 * 1024    # bytes (<= 5 KB con 's' = sobrante)


def clasificar_archivo(path: Path):
    """
    Devuelve (accion, motivo) donde accion es 'CONSERVAR', 'SOBRANTE' o 'REVISAR'.
    El .hq se clasifica como CONSERVAR aqui, pero se procesa distinto (se decodifica)
    en vez de copiarse tal cual - ver decodificar_y_guardar_hq().
    """
    ext = path.suffix.lower()

    if ext == EXTENSION_DDO:
        return "CONSERVAR", "ddo (cabecera/metadata)"

    if ext == EXTENSION_HQ:
        return "CONSERVAR", "hq (se decodifica a png sin perdida)"

    if ext in EXTENSIONES_A_MOVER_SIEMPRE:
        return "SOBRANTE", f"extension sobrante ({ext})"

    if ext == EXTENSION_JPG:
        try:
            size = path.stat().st_size
        except OSError:
            return "REVISAR", "no se pudo leer el tamano"

        termina_en_s = path.stem.endswith("s")

        if size > UMBRAL_JPG_GRANDE:
            return "CONSERVAR", f"jpg grande ({size} bytes)"
        elif size <= UMBRAL_JPG_CHICO and termina_en_s:
            return "SOBRANTE", f"jpg miniatura con 's' ({size} bytes)"
        elif size <= UMBRAL_JPG_CHICO and not termina_en_s:
            return "REVISAR", f"jpg chico pero sin 's' ({size} bytes)"
        else:
            return "REVISAR", f"jpg tamano intermedio ({size} bytes)"

    return "REVISAR", f"extension no reconocida ({ext})"


def obtener_destino_unico(carpeta_destino: Path, nombre_archivo: str) -> Path:
    """Si ya existe un archivo con ese nombre, genera uno unico con sufijo _1, _2, etc."""
    destino = carpeta_destino / nombre_archivo
    if not destino.exists():
        return destino

    stem = Path(nombre_archivo).stem
    suffix = Path(nombre_archivo).suffix
    contador = 1
    while destino.exists():
        destino = carpeta_destino / f"{stem}_{contador}{suffix}"
        contador += 1
    return destino


def decodificar_y_guardar_hq(path_hq: Path, carpeta_destino: Path):
    """
    Decodifica un .hq (JPEG-Lossless) y lo guarda como PNG de 16 bits
    (sin perdida, conserva el rango de bits real del sensor) en carpeta_destino.
    Devuelve la ruta del png generado.
    Puede lanzar una excepcion si el archivo no decodifica bien - el llamador
    debe capturarla y mandar el .hq original a REVISAR en ese caso.
    """
    with open(path_hq, "rb") as f:
        data = f.read()

    arr = decode_jpeg_lossless(data)  # devuelve array uint16 (o uint8 segun el archivo)
    arr16 = arr.astype(np.uint16)

    nombre_png = path_hq.stem + ".png"
    destino_png = obtener_destino_unico(carpeta_destino, nombre_png)

    # Pillow detecta solo el modo correcto (16 bits) a partir del dtype uint16,
    # preservando el valor real de cada pixel (no lo normaliza a 0-255)
    Image.fromarray(arr16).save(destino_png)
    return destino_png


def procesar(ruta_raiz: str, dir_conservados: str, dir_sobrantes: str, dir_revisar: str, reporte_csv: str, confirmar: bool):
    ruta_raiz = Path(ruta_raiz).resolve()
    dir_conservados = Path(dir_conservados).resolve()
    dir_sobrantes = Path(dir_sobrantes).resolve()
    dir_revisar = Path(dir_revisar).resolve()

    if confirmar:
        print("\n>>> MODO REAL ACTIVADO: Se copiaran, moveran y decodificaran archivos. <<<\n")
        dir_conservados.mkdir(parents=True, exist_ok=True)
        dir_sobrantes.mkdir(parents=True, exist_ok=True)
        dir_revisar.mkdir(parents=True, exist_ok=True)
    else:
        print("\n>>> MODO PRUEBA (SIMULACION): No se movera, copiara ni decodificara nada. <<<\n")

    carpetas_destino = {dir_conservados, dir_sobrantes, dir_revisar}

    total_conservados = 0
    total_sobrantes = 0
    total_revisar = 0
    total_hq_decodificados = 0
    total_hq_error = 0
    total_ddo_convertidos = 0
    total_ddo_error = 0

    print(f"Buscando archivos en: {ruta_raiz}")
    print(f"Carpeta Conservados:  {dir_conservados}")
    print(f"Carpeta Sobrantes:    {dir_sobrantes}")
    print(f"Carpeta Revisar:      {dir_revisar}")
    print("-" * 60)

    with open(reporte_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ruta_original", "accion", "motivo", "tamano_bytes", "destino"])

        for carpeta, _, archivos in os.walk(ruta_raiz):
            carpeta_path = Path(carpeta).resolve()

            if carpeta_path in carpetas_destino or any(
                carpeta_path == d or d in carpeta_path.parents for d in carpetas_destino
            ):
                continue

            for nombre in archivos:
                path = carpeta_path / nombre
                accion, motivo = clasificar_archivo(path)

                try:
                    size = path.stat().st_size
                except OSError:
                    size = -1

                destino_final = ""

                # --- Caso especial: .hq se decodifica en vez de copiarse tal cual ---
                if accion == "CONSERVAR" and path.suffix.lower() == EXTENSION_HQ:
                    if confirmar:
                        try:
                            destino_png = decodificar_y_guardar_hq(path, dir_conservados)
                            destino_final = str(destino_png)
                            total_conservados += 1
                            total_hq_decodificados += 1
                            print(f"[DECODIFICADO -> CONSERVADOS] {nombre} -> {destino_png.name}")
                        except Exception as e:
                            # si falla la decodificacion, el .hq original va a REVISAR
                            dest = obtener_destino_unico(dir_revisar, nombre)
                            destino_final = str(dest)
                            motivo = f"error al decodificar hq: {e}"
                            accion = "REVISAR"
                            total_revisar += 1
                            total_hq_error += 1
                            shutil.move(path, dest)
                            print(f"[ERROR DECODIFICANDO -> REVISAR] {nombre} ({e})")
                    else:
                        destino_final = str(dir_conservados / (path.stem + ".png"))
                        total_conservados += 1
                        print(f"[A DECODIFICAR -> CONSERVADOS] {nombre}")

                elif accion == "CONSERVAR" and path.suffix.lower() == EXTENSION_DDO:
                    dest = obtener_destino_unico(dir_conservados, nombre)
                    destino_final = str(dest)
                    total_conservados += 1
                    if confirmar:
                        shutil.copy2(path, dest)
                        try:
                            dest_txt = dest.with_suffix(".txt")
                            generar_txt_desde_ddo(path, dest_txt)
                            total_ddo_convertidos += 1
                            print(f"[COPIADO -> CONSERVADOS]  {nombre}  (+ {dest_txt.name})")
                        except Exception as e:
                            total_ddo_error += 1
                            print(f"[COPIADO -> CONSERVADOS]  {nombre}  (! no se pudo generar .txt: {e})")
                    else:
                        print(f"[A COPIAR -> CONSERVADOS] {nombre}  (+ .txt)")

                elif accion == "CONSERVAR":
                    dest = obtener_destino_unico(dir_conservados, nombre)
                    destino_final = str(dest)
                    total_conservados += 1
                    if confirmar:
                        shutil.copy2(path, dest)
                        print(f"[COPIADO -> CONSERVADOS]  {nombre}")
                    else:
                        print(f"[A COPIAR -> CONSERVADOS] {nombre}")

                elif accion == "SOBRANTE":
                    dest = obtener_destino_unico(dir_sobrantes, nombre)
                    destino_final = str(dest)
                    total_sobrantes += 1
                    if confirmar:
                        shutil.move(path, dest)
                        print(f"[MOVIDO  -> SOBRANTES]    {nombre} ({motivo})")
                    else:
                        print(f"[A MOVER -> SOBRANTES]    {nombre} ({motivo})")

                else:  # REVISAR
                    dest = obtener_destino_unico(dir_revisar, nombre)
                    destino_final = str(dest)
                    total_revisar += 1
                    if confirmar:
                        shutil.move(path, dest)
                        print(f"[MOVIDO  -> REVISAR]      {nombre} ({motivo})")
                    else:
                        print(f"[A MOVER -> REVISAR]      {nombre} ({motivo})")

                writer.writerow([str(path), accion, motivo, size, destino_final])

    print("\n" + "=" * 30 + " RESUMEN " + "=" * 30)
    print(f"Total Conservados:       {total_conservados} -> {dir_conservados}")
    print(f"  (de los cuales .hq decodificados a png: {total_hq_decodificados})")
    print(f"  (de los cuales .ddo convertidos a txt:  {total_ddo_convertidos}, con error: {total_ddo_error})")
    print(f"Total Sobrantes:         {total_sobrantes} -> {dir_sobrantes}")
    print(f"Total a Revisar:         {total_revisar} -> {dir_revisar}")
    print(f"  (de los cuales por error de decodificacion: {total_hq_error})")
    print(f"Reporte CSV generado en: {reporte_csv}")
    print("=" * 69)

    if not confirmar:
        print("\n* Nota: Fue una prueba (simulacion). Para ejecutar de verdad agrega --confirmar al final.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Organiza datos FCR en Conservados (con .hq decodificado a png), Sobrantes y Revisar.")
    parser.add_argument("ruta", help="Ruta de la carpeta raiz a escanear")
    parser.add_argument("--confirmar", action="store_true", help="Si se pasa, copia/mueve/decodifica de verdad. Sin esto, solo genera el CSV.")
    parser.add_argument("--conservados", default="CONSERVADOS", help="Carpeta destino para conservados")
    parser.add_argument("--sobrantes", default="SOBRANTES", help="Carpeta destino para sobrantes")
    parser.add_argument("--revisar", default="REVISAR", help="Carpeta destino para revisar 1x1")
    parser.add_argument("--reporte", default="reporte_fcr.csv", help="Archivo CSV de reporte")

    args = parser.parse_args()
    procesar(args.ruta, args.conservados, args.sobrantes, args.revisar, args.reporte, args.confirmar)
