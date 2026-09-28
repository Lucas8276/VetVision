# Contracts: interfaces internas de parsing

Este proyecto no expone una API externa — el "contrato" relevante es la interfaz de las funciones
Python que otros módulos del proyecto (`src/dataset.py`, `limpiar_datos_fcr.py`) importan y de las
que dependen. Documentarlas evita que `/speckit-implement` cambie una firma sin que quien lo lea
lo note.

## `src/ddo_parser.py` (nuevo módulo, extraído de `limpiar_datos_fcr.py`)

```python
def parse_ddo_bytes(data: bytes) -> dict[tuple[int, int], tuple[str, bytes | None]]:
    """Recorre un .ddo binario y devuelve {(group, elem): (vr, raw_value_o_None)}.
    No lanza excepción por tags desconocidos; puede lanzar si `data` no tiene
    estructura de tag válida (longitud fuera de rango, etc.) — el llamador
    (limpiar_datos_fcr.py) es responsable de capturarla y enrutar a REVISAR."""

def get_tag(tags: dict, group: int, elem: int, default: str = "") -> str:
    """Devuelve el valor ASCII decodeado y trimeado de un tag, o `default` si
    no existe o su valor es None (secuencia sin valor escalar)."""

def fecha_dicom_a_puntos(fecha: str) -> str:
    """'YYYYMMDD' -> 'DD.MM.YYYY'. Si `fecha` no tiene 8 dígitos, la devuelve
    sin modificar (no lanza excepción)."""

def generar_txt_desde_ddo(path_ddo: Path, destino_txt: Path) -> None:
    """Lee path_ddo, escribe destino_txt con las 8 líneas 'Campo:Valor'
    (ver data-model.md). Puede lanzar excepción (I/O, parsing) — el llamador
    decide qué hacer (limpiar_datos_fcr.py ya captura y loguea sin abortar el lote)."""
```

**Constante pública que el llamador debe seguir usando igual**: los tags de cierre de secuencia
DICOM — `ITEM`, `ITEM_DELIM`, `SEQ_DELIM = (0xFFFE, 0xE0DD)` — quedan expuestos como constantes de
módulo, no hardcodeadas de nuevo en `limpiar_datos_fcr.py`, para que exista una sola fuente de
verdad y el test de regresión de FR-002 cubra el único lugar donde se definen.

## `src/parser_fcr.py` (existente, extendido)

```python
REGIONES_VALIDAS: set[str]   # ahora incluye "CRANEO" (Decisión 2)
VISTAS_VALIDAS: set[str]     # ahora incluye "VD/DV" (Decisión 3)
ESPECIES_VALIDAS: set[str]   # sin cambios

def parsear_metadata_fcr(txt_path: Path) -> dict:
    """Devuelve {"id_paciente": str|None, "region": str, "vista": str|None,
    "especie": str|None, "modalidad": str|None}.
    `region` nunca es None (cae en "DESCONOCIDA" si no se resuelve).
    `vista` es None explícito cuando no hay token de vista reconocible — NO
    lanza excepción por eso (FR-007)."""
```

**Nueva función interna** (normalización de región, Decisión 1) — no se expone fuera del módulo,
pero cualquier test que valide FR-005 debe poder invocarla o inferir su efecto vía
`parsear_metadata_fcr`:

```python
def _normalizar_codigo_region(valor_tag: str) -> str | None:
    """Mapea codigos reales del equipo (CHEST, NECK, HEAD, UP_EXM, LOW_EXM) a
    la region canonica en espanol. Devuelve None si valor_tag no esta en la
    tabla (para que el llamador decida el fallback), no "DESCONOCIDA" —
    esa decision es responsabilidad de parsear_metadata_fcr, no de esta función."""
```

## Consumidores que dependen de estas firmas (no tocar sin actualizar)

- `src/dataset.py`: `REGIONES_A_IDX = {region: i for i, region in enumerate(sorted(REGIONES_VALIDAS))}`
  — agregar `"CRANEO"` cambia el tamaño y el orden de este mapping. Fuera de alcance de esta
  feature actualizar `src/model.py`/`src/train.py` para 6 clases (ver research.md, Decisión 2),
  pero cualquier test nuevo de `src/dataset.py` que asuma 5 clases quedaría desactualizado — no se
  toca en esta feature, se deja como nota para la siguiente.
- `limpiar_datos_fcr.py`: pasa a importar `parse_ddo_bytes`, `generar_txt_desde_ddo` desde
  `src/ddo_parser.py` en vez de definirlas localmente.
