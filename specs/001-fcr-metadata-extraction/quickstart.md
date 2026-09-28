# Quickstart: validar la feature 001-fcr-metadata-extraction

Guía para comprobar, de punta a punta, que el comportamiento descrito en `spec.md` se cumple una
vez implementado (`/speckit-tasks` + `/speckit-implement`). No es un instructivo de uso general del
pipeline (eso ya está en `README.md`/`CLAUDE.md`) — es específico para verificar esta feature.

## Prerrequisitos

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## 1. Correr los tests de regresión (cubre FR-001, FR-002, FR-005 a FR-008)

```bash
pytest tests/test_ddo_parser.py tests/test_parser_fcr.py -v
```

**Resultado esperado**: todos pasan, incluyendo (nombres de test orientativos, ver `tasks.md` para
los definitivos):
- un test que reconstruye en bytes un `.ddo` sintético con una secuencia anidada y confirma que
  `(0xFFFE, 0xE0DD)` se usa como cierre de secuencia sin desincronizar offsets (FR-002),
- un test por cada código de región real (`CHEST`, `NECK`, `HEAD`, `UP_EXM`, `LOW_EXM`) que
  confirma que ninguno cae en `"DESCONOCIDA"` (FR-005, SC-003),
- un test con `"CRANEO VD/DV FELINO"` que confirma que `vista == "VD/DV"` (FR-006),
- un test con `"ESOFAGO CANINO"` que confirma `vista is None` sin excepción (FR-007),
- un test con `ID del paciente:336-7` que confirma que el ID se preserva completo (FR-008).

Todos los fixtures usados son sintéticos (Decisión 6 de `research.md`) — ningún test debe leer un
archivo de `C:\Users\Usuario\Music\DatasetVetVision`.

## 2. Correr el pipeline completo en modo simulación sobre una muestra chica

```bash
python limpiar_datos_fcr.py "C:\Users\Usuario\Music\DatasetVetVision" --reporte reporte_smoke.csv
```

(sin `--confirmar`: no mueve ni decodifica nada de verdad, solo genera el CSV — seguro de correr
contra el dataset real).

**Resultado esperado**:
- El log no debe listar errores de import (confirma que `limpiar_datos_fcr.py` importa
  correctamente desde `src/ddo_parser.py` tras el refactor de estructura).
- `reporte_smoke.csv` se genera con una fila por archivo de entrada.

## 3. Verificar SC-001 y SC-002 sobre el reporte generado

```bash
python -c "
import csv
from collections import Counter
with open('reporte_smoke.csv', encoding='utf-8') as f:
    rows = list(csv.DictReader(f))
acciones = Counter(r['accion'] for r in rows)
print(acciones)
"
```

**Resultado esperado** (línea base ya observada, no debería empeorar):
- Los `.ddo` de entrada deben tener 1:1 su `.txt` generado (SC-001, hoy 8158/8158 en el dataset de
  referencia).
- Al menos 98% de los `.hq` deben terminar en `CONSERVAR` (SC-002, hoy 8015/8158 ≈ 98.2%) — el
  resto en `REVISAR` con motivo legible, nunca silenciosamente perdidos.

## 4. Verificar manualmente SC-005 (motivo legible sin abrir el archivo original)

```bash
python -c "
import csv
with open('reporte_smoke.csv', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        if r['accion'] == 'REVISAR':
            print(r['ruta_original'], '->', r['motivo'])
"
```

Cada línea impresa debe explicar el motivo sin ambigüedad (ej. `"jpg chico pero sin 's'
(2535 bytes)"`, `"error al decodificar hq: <detalle>"`) — si aparece un motivo genérico o vacío,
SC-005 no se cumple.

## Limpieza

`reporte_smoke.csv` es un artefacto de validación local — no se commitea (ya cubierto por
`.gitignore` si sigue el patrón de reportes existente; si no, borrarlo a mano después de validar).
