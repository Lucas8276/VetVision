# Data Model: Extracción de metadata e imagen desde estudios FCR PRIMA

## Entidad: Estudio radiológico (input)

Conjunto de archivos que comparten el mismo nombre base (stem), producidos por el FCR PRIMA para
una exposición de un paciente.

| Archivo | Rol | Obligatorio |
|---|---|---|
| `<stem>.ddo` | Fuente de metadata (binario, tipo DICOM no-estándar) | Sí |
| `<stem>.hq` | Fuente de imagen de mayor calidad (JPEG-Lossless) | No (puede fallar/faltar → REVISAR) |
| `<stem>.jpg` (>6KB) | Imagen ya procesada por Fuji (8-bit) | No |
| `<stem>.jpg` (miniatura, ≤5KB, termina en "s") | Descartable | No |
| `<stem>.dsp`, `.std`, `.edk`, `.edr` | Descartables (redundantes/no diagnósticos) | No |

## Entidad: Registro de metadata (`.txt`, output)

Campos derivados del `.ddo`, en el mismo formato de texto plano `Campo:Valor` por línea que ya
producen tanto el software oficial de Fuji como `generar_txt_desde_ddo`.

| Campo | Tag DICOM `.ddo` | Tipo | Reglas de validación/normalización |
|---|---|---|---|
| ID del paciente | (0010,0020) | string | Se preserva completo, incluyendo guiones (FR-008) |
| Nombre del paciente | (0010,0010) | string | Formato `APELLIDO^NOMBRE` → se reemplaza `^` por espacio |
| Sexo | (0010,0040) | string | Sin transformación |
| Fecha de exposición | (0008,0022) | string | `YYYYMMDD` → reformateada a `DD.MM.YYYY` |
| Región anatómica | (0018,0015) | string | Normalizada por tabla de Decisión 1 antes de validar; fallback al menú de exposición; `"DESCONOCIDA"` solo si ninguna fuente resuelve (FR-005) |
| Nombre del menú de exposición | (0018,1400) | string | Texto libre; fuente de especie y vista cuando el tag de región no alcanza |
| Modalidad | (0008,0060) | string | Sin transformación (siempre `"CR"` en este dataset) |
| Institución | (0008,0080) | string | Sin transformación |

## Entidad: Metadata estructurada (output de `parsear_metadata_fcr`, consumido por `src/dataset.py`)

| Campo | Valores válidos | Notas |
|---|---|---|
| `id_paciente` | string, puede incluir `-` | FR-008 |
| `region` | `{CERVICAL, TORAX, ABDOMEN, PELVIS, EXTREMIDADES, CRANEO, DESCONOCIDA}` | `CRANEO` es nuevo (Decisión 2) |
| `vista` | `{LAT, VD, DV, AP, VD/DV, None}` | `VD/DV` es nuevo (Decisión 3); `None` = vista ausente, explícito (FR-007) |
| `especie` | `{CANINO, FELINO, None}` | Sin cambios |
| `modalidad` | string | Sin cambios |

## Entidad: Imagen de alta calidad (`.png`, output)

- Formato: PNG, 16 bits por canal (escala de grises), sin normalizar (valores de píxel reales del
  sensor, típicamente una fracción del rango 0–65535).
- Dimensiones: las del `.hq` origen (no se recorta ni reescala en esta etapa).
- Nombre: `<stem>.hq` → `<stem>.png`, con sufijo `_N` si ya existe un archivo con ese nombre en el
  destino (FR-011).

## Entidad: Reporte de clasificación (CSV, output de `limpiar_datos_fcr.py`)

Sin cambios de esquema respecto al comportamiento actual — se documenta porque FR-010 lo exige
explícitamente como contrato, no porque esta feature lo modifique:

| Columna | Contenido |
|---|---|
| `ruta_original` | Path del archivo de entrada |
| `accion` | `CONSERVAR` \| `SOBRANTE` \| `REVISAR` |
| `motivo` | Texto legible explicando la clasificación (FR-009, SC-005) |
| `tamano_bytes` | Tamaño del archivo de entrada |
| `destino` | Path final del archivo (o del `.png` generado, si aplica) |

## Transiciones de estado (por archivo, durante una corrida)

```
archivo de entrada
   │
   ├─ .ddo ──────────────────────────────► CONSERVAR (copiado) + genera .txt
   │                                          └─ si falla generar_txt_desde_ddo → CONSERVAR
   │                                             el .ddo igual, .txt no se genera (error logueado)
   │
   ├─ .hq ──► intenta decodificar ──┬─► éxito ─► CONSERVAR (como .png)
   │                                 └─► falla ─► REVISAR (.hq original, motivo = excepción)
   │
   ├─ .dsp/.std/.edk/.edr ───────────────────► SOBRANTE
   │
   ├─ .jpg > 6KB ─────────────────────────────► CONSERVAR
   ├─ .jpg ≤ 5KB, termina en "s" ──────────────► SOBRANTE
   ├─ .jpg ≤ 5KB, NO termina en "s" ───────────► REVISAR (motivo = tamaño ambiguo)
   ├─ .jpg tamaño intermedio ───────────────────► REVISAR (motivo = tamaño ambiguo)
   │
   └─ extensión no reconocida ──────────────────► REVISAR (motivo = extensión no reconocida)
```

Este diagrama documenta el comportamiento ya existente en `clasificar_archivo` — no cambia con
esta feature, se incluye para que `data-model.md` sea la referencia completa del pipeline.
