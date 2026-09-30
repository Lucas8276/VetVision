# Formato interno del FCR PRIMA (Fujifilm) — .ddo y .hq

Documentación de ingeniería inversa ya resuelta. **No hace falta volver a
investigar esto** — usar directamente el código de referencia de más abajo.

Contexto: el equipo de rayos X computarizado FCR PRIMA (Fujifilm) guarda cada
exposición en 8 archivos con el mismo nombre base y distinta extensión:
`.ddo .dsp .edk .edr .hq .std` + un `.jpg` grande (>6KB) + un `.jpg` chico
(miniatura, <=5KB, termina en "s"). El software oficial para leer el `.ddo`
(DDOView) depende de un componente viejo de Windows (`MSCOMCTL.OCX`, de Visual
Basic 6) que no siempre está disponible y no es necesario: **ambos formatos se
decodifican con Python puro**, sin ningún componente de Windows.

---

## 1. `.ddo` — metadata del estudio (tipo DICOM, pero NO es DICOM válido)

### Qué es
Contiene la metadata del paciente/estudio (ID, nombre, sexo, fecha, región
anatómica, modalidad, institución, rutas internas a los otros archivos, y
configuración de impresión/almacenamiento). Estructura muy similar a DICOM
Explicit VR Little Endian, pero **no es DICOM estándar**:

- No tiene el preámbulo de 128 bytes ni la firma `DICM` al inicio del archivo.
- Usa grupos privados de Fuji (`0007,xxxx`, `00f0,xxxx`, `00f1,xxxx`, etc.)
  junto con grupos públicos DICOM estándar (`0008`, `0010`, `0018` — Study,
  Patient, Acquisition — que sí traen los datos que nos interesan).
- **Diferencia clave que rompe cualquier parser DICOM estándar**: el campo de
  longitud es **siempre 4 bytes**, para TODOS los VR (incluidos los "cortos"
  como CS/DA/TM/PN/SL, que en DICOM real usan 2 bytes de longitud). Por eso
  ni pydicom ni ningún visor DICOM lo abre, aunque le cambies la extensión a
  `.dcm`.
- Las secuencias (VR=SQ) SÍ siguen la codificación estándar de DICOM para
  Item / ItemDelimitationItem / SequenceDelimitationItem.

### Tags DICOM importantes con datos reales (grupo, elemento):

| Tag | Campo | Ejemplo real |
|---|---|---|
| (0008,0022) | Fecha de adquisición (YYYYMMDD) | `20180411` |
| (0008,0060) | Modalidad | `CR` |
| (0008,0080) | Institución | `HOSPITAL DE CLINICAS - F.C.V.` |
| (0010,0010) | Nombre paciente (formato `APELLIDO^NOMBRE`) | `PACIENTE^PRUEBA` |
| (0010,0020) | ID paciente | `0000-1` |
| (0010,0040) | Sexo | `O` |
| (0018,0015) | Región anatómica | `CHEST` |
| (0018,1400) | Descripción del menú de exposición (especie+vista+zona) | `TORAX VD/DV CANINO` |

También existen, dentro de grupos privados `0007,e1xx` / `00f1,xxxx`, rutas de
archivo embebidas (`file://X:\FujiFilm\Hobbit\Data\Image\...\NOMBRE.jpg`,
`...NOMBRE.hq`) y dimensiones/pixel spacing — no fueron necesarias para el
dataset pero están ahí si hicieran falta.

### ⚠️ Bug ya corregido — no repetirlo
Los tags de cierre de secuencia DICOM son:
- Item: `(FFFE,E000)`
- Item Delimitation Item: `(FFFE,E00D)`
- **Sequence Delimitation Item: `(FFFE,E0DD)`** — NO `(FFFE,DD00)`. Confundir
  estos dos (parecen "espejados") causa que el parser se desalinee y termine
  leyendo offsets basura más adelante en el archivo (crashea con
  "unpack_from requires a buffer of at least N bytes").

### Código de referencia (parser completo y probado)

```python
import struct

ITEM = (0xFFFE, 0xE000)
ITEM_DELIM = (0xFFFE, 0xE00D)
SEQ_DELIM = (0xFFFE, 0xE0DD)  # ojo: NO (0xFFFE, 0xDD00)


def parse_ddo_bytes(data: bytes) -> dict:
    """Devuelve {(group, elem): (vr, raw_bytes_o_None)}"""
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

        if length == 0xFFFFFFFF:  # secuencia (SQ) de largo indefinido
            while True:
                g2, e2 = struct.unpack_from("<HH", data, j)
                if (g2, e2) == SEQ_DELIM:
                    l2 = struct.unpack_from("<I", data, j + 4)[0]
                    j += 8 + l2
                    break
                j, _ = read_element(j)
            return j, ((group, elem), vr, None)

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
    return raw.decode("ascii", errors="replace").strip("\x00 ").strip()
```

Uso típico (genera el mismo formato de `.txt` que exportaba el sistema
oficial):

```python
with open(ruta_ddo, "rb") as f:
    tags = parse_ddo_bytes(f.read())

paciente_id = get_tag(tags, 0x0010, 0x0020)
nombre = get_tag(tags, 0x0010, 0x0010).replace("^", " ")
sexo = get_tag(tags, 0x0010, 0x0040)
fecha = get_tag(tags, 0x0008, 0x0022)  # YYYYMMDD -> reformatear si hace falta
region = get_tag(tags, 0x0018, 0x0015)
menu_exposicion = get_tag(tags, 0x0018, 0x1400)
modalidad = get_tag(tags, 0x0008, 0x0060)
institucion = get_tag(tags, 0x0008, 0x0080)
```

---

## 2. `.hq`, `.dsp`, `.std` — la imagen real (JPEG-Lossless, NO basura)

### Qué son
Los tres empiezan con la firma JPEG estándar `FF D8` seguida del marcador
`FF C3` (SOF3 = *Start Of Frame, lossless, sequential*) — es decir, son
**JPEG-Lossless real**, un formato JPEG sin pérdida usado en imágenes médicas.
No son un formato propietario ilegible: cualquier decodificador JPEG-Lossless
los abre.

- **`.hq`** = "High Quality": resolución completa, la de mayor calidad. En los
  casos vistos: ~2964×2364 px, profundidad real ~12 bits (valores 0–3125 sobre
  un rango de 16 bits posibles) — **es mejor calidad que el `.jpg` que exporta
  el sistema** (que es JPEG con pérdida, 8 bits, ya procesado/nivelado).
- **`.std`** ("Standard") y **`.dsp`** ("Display") = la misma imagen en
  resoluciones menores — redundantes si ya se tiene el `.hq`, se pueden
  descartar para el dataset.

### Decodificación
Pillow **no** decodifica JPEG-Lossless (SOF3) de forma nativa. Usar
`pylibjpeg` + el plugin `pylibjpeg-libjpeg`:

```bash
pip install pylibjpeg pylibjpeg-libjpeg --break-system-packages
```

```python
from pylibjpeg import decode
import numpy as np
from PIL import Image

with open(ruta_hq, "rb") as f:
    data = f.read()

arr = decode(data)                 # numpy array, dtype uint16 (o uint8)
arr16 = arr.astype(np.uint16)

# Pillow detecta el modo correcto (16 bits) solo por el dtype del array —
# no hace falta pasar mode="I;16" explícito.
Image.fromarray(arr16).save(ruta_png_salida)
```

### ⚠️ Punto importante para quien entrene el modelo con esto
El PNG de 16 bits generado **NO está normalizado a 0-255**. Los valores de
píxel reales ocupan solo una fracción chica del rango 0–65535 (ej. 0 a ~2700),
por lo que **se ve casi completamente negro en cualquier visor de imágenes
común** (Windows Photos, navegador, etc.) — esto es esperado, no es un archivo
corrupto ni mal decodificado. Para verlo a simple vista hace falta reescalar
manualmente (min-max u otro método) solo para visualización:

```python
norm = ((arr16.astype(np.float32) - arr16.min())
        / (arr16.max() - arr16.min()) * 255).astype(np.uint8)
```

**La normalización real para entrenamiento debe hacerse en el pipeline de
carga de datos al momento de entrenar** (no se pre-normaliza el PNG guardado),
para no perder flexibilidad si cambia el método de normalización (min-max
simple vs. percentile clipping, etc.) más adelante.

---

## 3. `.edk` / `.edr` — metadata de procesamiento, no imagen

- `.edk`: datos de calibración de la placa/cassette CR usada en esa
  exposición (contiene un identificador tipo `400000080247`, coincide con el
  formato de plate/cassette ID visto dentro del propio `.ddo`).
- `.edr`: curva de tono/gamma aplicada (secuencia de valores que sube y baja
  suavemente — un LUT de contraste, no una imagen).

Ninguno de los dos aporta contenido diagnóstico nuevo — son parámetros
internos del pipeline de procesamiento de Fuji. Para el dataset de
entrenamiento no son necesarios.

---

## 4. Resumen — qué conservar por placa

| Archivo | Acción |
|---|---|
| `.ddo` | Conservar (fuente de metadata, parsear con el código de arriba) |
| `.hq` | Conservar → decodificar a `.png` 16 bits (imagen para entrenar) |
| `.jpg` grande (>6KB) | Conservar (versión ya procesada, útil de complemento/QA visual) |
| `.dsp`, `.std` | Descartable (redundante con `.hq`) |
| `.edk`, `.edr` | Descartable (metadata de proceso, no imagen) |
| `.jpg` chico (miniatura, termina en "s") | Descartable |
