# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

VetVision AI: AI-assisted diagnosis for dog/cat X-rays. Two raw-data pipelines feed a
three-stage cascade classifier (only stage 0 is implemented so far — see Architecture).

## Commands

```bash
# Setup
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt

# Tests
pytest                                          # full suite
pytest tests/test_parser_fcr.py -v              # single file
pytest tests/test_parser_fcr.py::test_parsear_metadata_fcr_region_desconocida  # single test

# Train / evaluate / export (stage 0 only — region classifier)
python -m src.train --data-dir data/processed --epochs 15 --batch-size 8 --lr 1e-4
python -m src.evaluate --data-dir data/processed --model-path models/etapa0_region.pt
python -m src.export_onnx --model-path models/etapa0_region.pt

# Raw dataset extraction/classification (run dry-run first, always)
python limpiar_datos_fcr.py <ruta_raiz>                       # simulation only, writes reporte_fcr.csv
python limpiar_datos_fcr.py <ruta_raiz> --confirmar           # actually copies/moves/decodes files
```

No lint/format tooling is configured yet.

## Architecture

**Two independent parsers — don't confuse them:**
- `src/ddo_parser.py` — reads the raw FCR PRIMA `.ddo` binary directly
  (`parse_ddo_bytes`, custom DICOM-like tag reader — NOT valid DICOM, see
  `formato_ddo_hq_FCR_PRIMA.md` for the full reverse-engineered format and known
  pitfalls before touching this) and generates the `.txt` metadata sidecar
  (`generar_txt_desde_ddo`). Tested in `tests/test_ddo_parser.py`, including a
  regression test locking in the `SEQ_DELIM` tag bug fix.
- `limpiar_datos_fcr.py` (repo root) — CLI wrapper: walks a batch, classifies every
  file from a study into CONSERVAR/SOBRANTE/REVISAR, decodes `.hq` (JPEG-Lossless)
  to 16-bit `.png` (`decodificar_y_guardar_hq`), and delegates `.ddo`→`.txt` to
  `src/ddo_parser.py`. Tested in `tests/test_limpiar_datos_fcr.py`.
- `src/parser_fcr.py` — reads the already-generated `.txt` sidecar into a structured
  dict (`parsear_metadata_fcr`), with validation sets `REGIONES_VALIDAS`,
  `VISTAS_VALIDAS`, `ESPECIES_VALIDAS` (now includes `CRANEO` and the combined
  `VD/DV` vista, plus a `_normalizar_codigo_region` table mapping the equipment's
  English region codes — `CHEST`, `NECK`, `HEAD`, `UP_EXM`, `LOW_EXM` — to their
  canonical Spanish region). Has tests (`tests/test_parser_fcr.py`).

**Model is a planned 3-stage cascade (`specs/model-tensor.spec.yaml`,
`specs/ground-truth-annotation.spec.yaml`), only stage 0 exists in code:**
- Etapa 0 (implemented: `src/dataset.py`, `src/model.py`, `src/train.py`,
  `src/evaluate.py`, `src/export_onnx.py`) — anatomical region classifier, labels
  come automatically from the `.txt` metadata, no clinical annotation needed.
- Etapa 1 (triaje sano/no-sano) and Etapa 2 (diagnóstico, multi-label) — not yet
  implemented; blocked on pending clinical annotation (see
  `specs/ground-truth-annotation.spec.yaml`). Etapa 2 is meant to initialize from
  Etapa 1's fine-tuned weights, not train independently, once it exists.
- `src/model.py` backbone is DenseNet-121 pretrained on human chest X-ray
  (TorchXRayVision), with the backbone frozen by default (`freeze_backbone=True`).

**Training data path:** `src/dataset.py` reads `.txt`+jpg pairs from a flat
directory and maps `region` → class index via `REGIONES_VALIDAS`.
`src/preprocessing.py` (`normalizar_jpg_veterinario`) normalizes the 8-bit "jpg
pesado" (CLAHE + resize to 512 + grayscale→RGB) — **not** the 16-bit `.png`
decoded from `.hq`, despite the `.png` being the higher-fidelity source per
`specs/data-contract.spec.yaml`. If the training path is ever repointed to the
`.png`, remember it is NOT pre-normalized (see the 16-bit note below).

**`specs/*.spec.yaml` are contracts, not yet enforced.** Nothing in `src/` loads
or validates against them at runtime — they currently only document intent.

**SDD tooling:** spec-kit is installed (`.specify/`, `.claude/skills/speckit-*`).
Use `/speckit-constitution` → `/speckit-specify` → `/speckit-plan` →
`/speckit-tasks` → `/speckit-implement` for new feature work instead of writing
code directly against an informal request.

## Known gotchas

- `src/dataset.py`'s `_encontrar_jpg_pesado` looks for a `{stem}_pesado.jpg`
  naming convention that does not match `limpiar_datos_fcr.py`'s actual output
  (it keeps the original stem, e.g. `FCR1.jpg`) — the glob fallback covers it,
  but the primary-candidate path is dead code against real output. Not yet
  fixed (out of scope of `specs/001-fcr-metadata-extraction/`, which only
  covers extraction, not `src/dataset.py`).
- The `.png` decoded from `.hq` is 16-bit and deliberately NOT normalized to
  0-255 (real values occupy a small slice of the range, e.g. 0–2700) — expected,
  not a bug. Normalization belongs in the data-loading pipeline, not before.

Resolved by `specs/001-fcr-metadata-extraction/` (region code mapping, combined
`VD/DV` vista, and the `SEQ_DELIM` regression are now covered by tests in
`tests/test_parser_fcr.py` and `tests/test_ddo_parser.py` — see that feature's
`research.md` for the full rationale of each fix).

## Data handling

- Raw imagery and metadata (`*.jpg`, `*.png`, `*.ddo`, `*.hq`, `*.std`, `*.dsp`,
  `*.edk`, `*.edr`, `data/raw/`, `data/processed/`) are gitignored — never force-add.
- Patient identifiers must be anonymized before any cloud upload — see the
  `anonimizacion` section of `specs/data-contract.spec.yaml`.
- DVC remote credentials belong in `.dvc/config.local` (gitignored) or env vars,
  set via `dvc remote modify --local ...` — never in `.dvc/config`, which is
  committed and shared with the team.
