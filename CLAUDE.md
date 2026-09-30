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

# Train / evaluate / export (stage 0 only — TORAX/NO_TORAX binary classifier)
python -m src.train --data-dir data/processed --epochs 15 --batch-size 8 --lr 1e-4
python -m src.evaluate --data-dir data/processed --model-path models/etapa0_region.pt
python -m src.export_onnx --model-path models/etapa0_region.pt
mlflow ui                                       # view training runs at localhost:5000

# Raw dataset extraction/classification (run dry-run first, always)
python limpiar_datos_fcr.py <ruta_raiz>                       # simulation only, writes reporte_fcr.csv
python limpiar_datos_fcr.py <ruta_raiz> --confirmar           # actually copies/moves/decodes files
```

No lint/format tooling is configured yet.

On Windows, the first run that downloads TorchXRayVision's pretrained weights
needs `PYTHONIOENCODING=utf-8` set (the library's progress bar prints a
Unicode block character the default `cp1252` console can't encode, which
crashes the download mid-way and leaves a corrupt cached file at
`~/.torchxrayvision/models_data/` — delete it and retry with the env var set
if that happens). Not needed once the weights are cached.

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

**Model is a 2-stage-plus-gate cascade (`specs/model-tensor.spec.yaml`,
`specs/ground-truth-annotation.spec.yaml`), only stage 0 exists in code:**
- Etapa 0 (implemented: `src/dataset.py`, `src/model.py`, `src/train.py`,
  `src/evaluate.py`, `src/export_onnx.py`) — **binary** `TORAX`/`NO_TORAX` gate,
  not a 6-region classifier (redefined by
  `specs/002-etapa0-torax-clasificador/`) — since every downstream disease class
  in Etapa 2 is thoracic, non-thorax studies are filtered here instead of
  classified by region. Labels come automatically from the `.txt` metadata via
  `region_a_etiqueta_binaria()`; studies whose region is `"DESCONOCIDA"` are
  excluded from training/eval, never forced into either class (see
  `VetVisionEtapa0Dataset.n_excluidos_desconocida`). No clinical annotation
  needed for this stage.
- Etapa 1 (triaje sano/no-sano) and Etapa 2 (diagnóstico, multi-label) — not yet
  implemented; blocked on pending clinical annotation (see
  `specs/ground-truth-annotation.spec.yaml`). Etapa 2 is meant to initialize from
  Etapa 1's fine-tuned weights, not train independently, once it exists.
- `src/model.py` backbone is DenseNet-121 pretrained on human chest X-ray
  (TorchXRayVision), frozen by default (`freeze_backbone=True`). Partial
  fine-tuning is supported via `--unfreeze-layers` (`src/train.py` CLI, e.g.
  `denseblock4,norm5` — matches `self.features`' named children) with a
  separate, lower learning rate for the unfrozen backbone params
  (`--backbone-lr-factor`, default 0.1x the head's LR) so pretrained weights
  aren't destroyed in a few steps. `build_model_etapa0(num_classes)` is
  generic — Etapa 0's redefinition from 6 classes to 2 (`ETIQUETAS_A_IDX`)
  required no change to `model.py` itself.
- `src/train.py` saves the **best** epoch's checkpoint (by `val_balanced_acc`,
  computed every epoch), not the last one — training can keep improving past
  the point where it starts to overfit, and without this the final save would
  silently be worse than an earlier epoch.
- Promotion threshold (`src/evaluate.py::UMBRAL_PROMOCION_ACC`) is 0.90, checked
  against `balanced_accuracy`, not plain `accuracy` — a binary TORAX/NO_TORAX
  split isn't guaranteed 50/50, and plain accuracy can hide poor performance on
  the minority class.

**Training data path:** `src/dataset.py` reads `.txt`+jpg pairs from a flat
directory and maps `region` → `TORAX`/`NO_TORAX` via `region_a_etiqueta_binaria()`.
`src/preprocessing.py` (`normalizar_jpg_veterinario`) normalizes the 8-bit "jpg
pesado" (CLAHE + resize to 512, stays **grayscale, 1 channel** — no RGB
conversion) — **not** the 16-bit `.png` decoded from `.hq`, despite the `.png`
being the higher-fidelity source per `specs/data-contract.spec.yaml`. If the
training path is ever repointed to the `.png`, remember it is NOT
pre-normalized (see the 16-bit note below).
`VetVisionEtapa0Dataset.__getitem__` then applies `xrv.utils.normalize(img,
maxval=255, reshape=True)`, scaling to TorchXRayVision's expected ~[-1024,
1024] range with the channel dim first — **not** `/255.0` and **not**
`imagenet_mean_std` (the backbone's first conv layer is shaped for 1 input
channel; feeding it 3 or the wrong value range crashes or silently degrades
training). This was discovered and fixed while actually running training for
the first time in `specs/002-etapa0-torax-clasificador/` — the pipeline had
never been exercised end-to-end before that.

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
