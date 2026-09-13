# SADRV / VetVision AI

Sistema de diagnóstico radiológico veterinario asistido por IA.

## Contexto

Dataset real: ~228 radiografías (perros/gatos) del Hospital de Clínicas F.C.V.,
capturadas en un equipo Fujifilm FCR PRIMA (CR). Cada paciente genera 3 archivos
(jpg pesado, jpg liviano, txt con metadata) procesados por `limpiar_datos_fcr.py`
a partir de los `.ddo` originales.

El `.txt` trae metadata (ID paciente, sexo, fecha, región anatómica, menú de
exposición, modalidad, institución) pero NO diagnóstico clínico — eso se
gestiona aparte con un profesional veterinario que anota las placas.

## Modelo

DenseNet-121 pre-entrenado en tórax humano (TorchXRayVision), transfer
learning, arquitectura en cascada de 2 etapas:

- **Etapa 0**: clasificación por región anatómica (automática, desde metadata del `.txt`)
- **Etapa 1**: triaje sano / no-sano (requiere anotación clínica)
- **Etapa 2**: clasificación de patología (requiere anotación clínica)

Ver [specs/ground-truth-annotation.spec.yaml](specs/ground-truth-annotation.spec.yaml)
y [specs/data-contract.spec.yaml](specs/data-contract.spec.yaml).

## Setup

```bash
python -m venv venv
source venv/bin/activate    # en Windows: venv\Scripts\activate
pip install -r requirements.txt

dvc init
dvc remote add -d storage s3://tu-bucket-sadrv/dvc-storage   # o gcs://
```

## Estructura

```
sadrv-vetvision/
├── data/
│   ├── raw/            # jpg pesado + liviano + txt, tal cual salen del parser
│   └── processed/      # imágenes normalizadas, listas para el Dataset de PyTorch
├── specs/              # contratos de datos y anotación
├── src/                # parser, preprocessing, dataset, modelo, train/eval/export
├── notebooks/          # exploración
└── tests/
```
