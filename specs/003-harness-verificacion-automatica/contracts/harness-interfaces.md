# Contracts: interfaces del harness

Este proyecto no expone una API externa; los contratos relevantes son las interfaces por las que las
tres capas (asistente, git, CI) invocan el harness, y los formatos de los archivos que lo configuran.

## 1. Línea de comandos

```text
python -m harness [contratos | guardia | todo]        # default: todo
python -m harness guardia --preparados                # solo lo preparado para commit (git index)
python -m harness guardia --archivos RUTA [RUTA ...]  # archivos puntuales (usado por hooks)
python -m harness todo --rapido                       # omite lo lento (construir el modelo)
```

| Salida | Significado |
|---|---|
| código `0` | ninguna verificación en estado `falla` |
| código `1` | al menos una verificación en estado `falla` |
| código `2` | error del propio harness (no pudo ejecutarse) — **nunca** se interpreta como "pasó" |

Reporte por stdout, una línea por resultado: `ESTADO  verificacion  ubicacion  [regla]  mensaje`,
más un resumen final con los conteos de `ok / falla / pendiente / sin_verificacion`. Las líneas de la
guardia **no** contienen el valor detectado.

## 2. Contratos YAML

Único cambio de formato: una sección puede llevar `estado: pendiente | implementado` (por defecto
`implementado`). Una sección `pendiente` se informa completa como una sola línea `pendiente`.

Cambios de contenido previos a activar el validador (spec primero):
- `data-contract.spec.yaml › proyecciones_admitidas`: pasa a `[LAT, VD, DV, AP, VD/DV]`.
- `model-tensor.spec.yaml › etapas › etapa_1_triaje` y `etapa_2_diagnostico`: `estado: pendiente`.
- `ground-truth-annotation.spec.yaml › etapa_1_triaje` y `etapa_2_diagnostico`: `estado: pendiente`.

## 3. Hooks del asistente (`.claude/settings.json`)

| Evento | Cuándo | Comando | Efecto |
|---|---|---|---|
| `PreToolUse` | antes de `git commit` (Bash y PowerShell) | `python harness/lanzar.py hook pre-commit` | guardia sobre lo preparado; salida `2` bloquea y explica |
| `PostToolUse` | tras editar `src/**`, `specs/**`, `tests/**` | `python harness/lanzar.py hook post-edit` | verificaciones aplicables en segundo plano; si fallan, despierta al asistente |

Entrada: JSON del hook por stdin (`tool_name`, `tool_input`). Convención de salida: `0` continuar,
`2` bloquear/avisar con el motivo por stderr. Las reglas `permissions.ask` para `git commit` y
`git push` (FR-019/FR-020) ya existen y no se modifican.

## 4. Hooks de git (`.githooks/`)

| Hook | Ejecuta | Falla si |
|---|---|---|
| `pre-commit` | `python harness/lanzar.py guardia --preparados` | hay hallazgos en lo preparado |
| `pre-push` | `python harness/lanzar.py todo` | cualquier verificación falla |

Activación (una vez por clon, explícita): `python scripts/instalar_hooks.py` →
`git config --local core.hooksPath .githooks`. Sin activar, los hooks no corren.

## 5. CI (`.github/workflows/verificar.yml`)

| Aspecto | Contrato |
|---|---|
| Disparadores | `push` y `pull_request` |
| Permisos | `contents: read` únicamente; sin secretos |
| Pasos | checkout → Python 3.13 → instalar PyTorch CPU + `requirements-ci.txt` → `python -m harness` |
| Fallo | el trabajo termina en rojo si el harness devuelve ≠ 0; el motivo es visible en el resumen |
| Requisito para "bloquear" | protección de rama con este chequeo obligatorio (acción del dueño del repo) |

## 6. `harness/valores_ficticios.txt`

Texto plano UTF-8, un valor por línea, `#` para comentarios. Solo valores evidentemente inventados.
La guardia compara sin distinguir mayúsculas y sin espacios sobrantes.

## 7. `docs/MEMORIA.md` y su import

`CLAUDE.md` incluye la línea `@docs/MEMORIA.md`. El documento comienza con un encabezado que enuncia
la política de contenido (qué se puede y qué no) y mantiene las cinco secciones de `data-model.md`.
