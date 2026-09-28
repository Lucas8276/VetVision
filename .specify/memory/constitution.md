<!--
Sync Impact Report
- Version change: [TEMPLATE] → 1.0.0 (initial ratification)
- Principles established:
  1. Spec-First Development (NON-NEGOTIABLE)
  2. Real-Data-Grounded Specs
  3. Test-First for Parsers (NON-NEGOTIABLE)
  4. Patient Data Protection
  5. Simplicity / No Speculative Stages
- Added sections: Additional Constraints (stack/environment), Development Workflow
  (SDD pipeline, timeline constraint, commit conventions), Governance
- Removed sections: none (initial document)
- Deferred items: none — all placeholders resolved from repo context
  (README.md, CLAUDE.md, formato_ddo_hq_FCR_PRIMA.md, specs/*.spec.yaml, and
  project history discussed with Stiven Monsalvo)
- Templates requiring follow-up: none checked yet — run /speckit-specify next
  and confirm plan/tasks templates render without unresolved placeholders
-->

# VetVision AI Constitution

## Core Principles

### I. Spec-First Development (NON-NEGOTIABLE)
No non-trivial feature, parser change, or model-pipeline change is implemented directly
from an informal request. It MUST go through `/speckit-specify` → `/speckit-plan` →
`/speckit-tasks` → `/speckit-implement` before code is written. Trivial fixes (typo,
formatting, a single-line dependency bump) are exempt.
**Rationale**: this project exists partly to learn Spec-Driven Development properly;
skipping the flow for convenience defeats the purpose and reintroduces the undocumented,
tribal-knowledge state the specs were created to fix (see `specs/*.spec.yaml`, which
existed as intent with zero enforcement before this constitution).

### II. Real-Data-Grounded Specs
Specs and validation logic MUST be written against values actually observed in the
production dataset, not assumed values. Before writing or updating a spec that touches
metadata fields (region, vista, especie, etc.), sample real `.txt`/`.ddo` output and
encode the actual observed value set. Known real-world mismatches already discovered
MUST be treated as required spec inputs, not left as silent fallbacks: anatomical region
codes arrive in English/equipment codes (`CHEST`, `NECK`, `HEAD`, `UP_EXM`, `LOW_EXM`),
not the Spanish set currently validated in `src/parser_fcr.py`; the "vista" field can be a
combined token (`VD/DV`) or absent; patient IDs can contain a dash (`336-7`).
**Rationale**: the current `REGIONES_VALIDAS`/`VISTAS_VALIDAS` sets were written from
assumption and silently misclassify most real records as `"DESCONOCIDA"` — a defect
found only by sampling `C:\Users\Usuario\Music\DatasetVetVision` directly, not by reading
the code or the old spec.

### III. Test-First for Parsers (NON-NEGOTIABLE)
Any change to `limpiar_datos_fcr.py`'s binary `.ddo`/`.hq` handling or to
`src/parser_fcr.py`'s metadata parsing MUST have a regression test written first,
covering the specific failure mode, before the fix is written. This applies retroactively
to every known-fixed bug: the codebase MUST carry a test asserting `SEQ_DELIM ==
(0xFFFE, 0xE0DD)` behavior (not the mirrored `(0xFFFE, 0xDD00)`) so it cannot regress
silently.
**Rationale**: this is reverse-engineered, undocumented binary format territory with no
upstream spec to check against (see `formato_ddo_hq_FCR_PRIMA.md`) — the only safety net
possible is tests encoding what was already learned the hard way.

### IV. Patient Data Protection
Raw patient identifiers (name, original patient ID) MUST be removed or hashed before any
data leaves local/DVC-controlled storage, per the `anonimizacion` section of
`specs/data-contract.spec.yaml`. Raw imagery and metadata files MUST stay gitignored
(`*.jpg`, `*.png`, `*.ddo`, `*.hq`, `*.std`, `*.dsp`, `*.edk`, `*.edr`, `data/raw/`,
`data/processed/`) and DVC remote credentials MUST live in `.dvc/config.local` or
environment variables (`dvc remote modify --local`), never in the committed `.dvc/config`.
**Rationale**: the dataset contains real veterinary patient/owner records from Hospital de
Clínicas F.C.V. (UNNE); this is a hospital data-handling obligation, not a style
preference, and the team (Stiven + Lucas) is bound by that relationship regardless of the
project's academic or commercial framing.

### V. Simplicity / No Speculative Stages
Do not build Etapa 1 (triaje) or Etapa 2 (diagnóstico) code, models, or dataset classes
ahead of the clinical annotation they depend on (`specs/ground-truth-annotation.spec.yaml`
marks both `requiere_anotacion_manual: true`). Etapa 2 MUST initialize from Etapa 1's
fine-tuned weights when it is eventually built — no independent training path for it is to
be scaffolded early "just in case." Only build what the currently available, currently
annotated data supports.
**Rationale**: matches the PFG's real constraint — annotation is still pending, the team
has reduced availability until 2026-10-19, and the final deadline is 2026-11-18;
speculative scaffolding for unannotated stages burns time the team does not have.

## Additional Constraints

- **Stack**: Python 3.13, PyTorch/TorchVision, TorchXRayVision (DenseNet-121 backbone,
  human chest X-ray pretrained — no veterinary foundational model exists), OpenCV +
  Albumentations for image ops, MLflow for experiment tracking, DVC for data
  versioning, ONNX (opset 17) for export, pytest for tests.
- **Environment**: primary development happens on Windows (PowerShell); scripts and
  path handling must not assume a POSIX-only environment.
- **Dependencies**: any new runtime dependency used by a committed script MUST be added
  to `requirements.txt` in the same change — do not let a script depend on an
  undeclared package (this already happened once with `limpiar_datos_fcr.py` and
  `numpy`/`Pillow`/`pylibjpeg`).
- **Third-party AI tooling**: no third-party agent extension, MCP server, or CLI plugin
  is installed with unreviewed/unapproved install scripts or at global machine scope
  for this project. Prefer first-party tooling (spec-kit from github/spec-kit, Claude
  Code's built-in memory) over unverified packages.

## Development Workflow

- Follow the spec-kit SDD pipeline (`/speckit-constitution` → `/speckit-specify` →
  `/speckit-plan` → `/speckit-tasks` → `/speckit-implement`) for feature work; use
  `/speckit-converge` when retrofitting a spec onto code that already exists (e.g. the
  `.ddo`→`.txt` parser).
- Commit messages are written in Spanish, imperative/descriptive, following the
  Conventional Commits-style prefixes already in use (`docs:`, `chore:`, `feat:`,
  `fix:`). Attribution lines follow whatever the user requests per commit; do not
  assume a standing rule either way.
- Given the team's reduced availability through 2026-10-19 (mandatory práctica
  profesional) and the 2026-11-18 PFG deadline, prefer small, independently mergeable
  increments over large batched changes — a change that cannot be demoed or tested
  before the next sync should be split.

## Governance

This constitution supersedes ad-hoc practice for anything it covers. Amendments are made
by re-running `/speckit-constitution` with the proposed change, which updates this file
and records a Sync Impact Report of what changed and why.

**Versioning policy** (semantic versioning for this document):
- MAJOR: a principle is removed or redefined in a backward-incompatible way.
- MINOR: a new principle or materially expanded section is added.
- PATCH: wording/clarification fixes with no rule change.

Every `/speckit-plan` output MUST be checked against these principles before
`/speckit-tasks` runs; a plan that conflicts with a principle must either be revised or
the conflict must be justified explicitly in that feature's plan (complexity/exception
must be justified, not silently overridden). Use `CLAUDE.md` for day-to-day runtime
development guidance (commands, architecture map, known gotchas) — this document is for
governing principles, not operational detail.

**Version**: 1.0.0 | **Ratified**: 2026-09-28 | **Last Amended**: 2026-09-28
