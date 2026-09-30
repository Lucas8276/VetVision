# Log de entrenamientos — Etapa 0 (Tórax vs. No-Tórax)

Registro de cada corrida real de entrenamiento del modelo, para que el equipo (Stiven y Lucas)
tenga visibilidad de qué se probó, qué resultado dio, y por qué se tomó cada decisión — sin tener
que levantar MLflow local de quien corrió el entrenamiento para enterarse.

Cada entrada nueva se agrega al final. No se borran corridas viejas aunque hayan salido mal — el
"por qué no funcionó" es tan útil como el "qué funcionó".

## Cómo leer este log

- **Config**: comando exacto usado.
- **Dataset**: de dónde salieron las imágenes y cuántas entraron.
- **Resultado**: métricas reales, no estimadas.
- **Duración real**: tiempo de reloj, no estimado — importa para planificar la próxima corrida.
- **Conclusión**: qué se decidió a partir de este resultado.

---

## Corrida 1 — 2026-09-28 — validación rápida, 3 épocas

**Contexto**: primera vez que se corre `src/train.py` contra datos reales de punta a punta. En el
camino se encontraron y corrigieron 3 bugs que nunca se habían disparado porque el pipeline nunca
se había ejecutado hasta ahora:

1. `_encontrar_jpg_pesado` usaba `glob(f"{stem}*.jpg")` (coincidencia por *prefijo*, no nombre
   exacto) — con miles de estudios reales, esto podía emparejar la metadata de un paciente con la
   imagen de **otro** paciente (ej. `FCR1.txt` matcheando `FCR10.jpg`), además de ser
   cuasi-cuadrático en tiempo (colgaba con el dataset completo). Corregido: lookup por nombre
   exacto, indexado una sola vez.
2. `src/preprocessing.py` convertía la imagen a RGB (3 canales), pero el backbone de
   TorchXRayVision espera **1 canal**. Crasheaba el forward pass.
3. La normalización de píxeles usaba `/255.0` (rango `[0,1]`), pero TorchXRayVision espera
   `~[-1024, 1024]` (`xrv.utils.normalize`). No crasheaba, pero degradaba el entrenamiento
   silenciosamente si no se corregía.

Ver `specs/002-etapa0-torax-clasificador/` y `CLAUDE.md` (sección "Known gotchas") para el detalle
de cada corrección.

**Config**:
```bash
python -m src.train --data-dir "C:\Users\Usuario\Music\DatasetVetVision" --epochs 3 --batch-size 8 --lr 1e-4
```
(semilla fija para el split train/val agregada *después* de esta corrida — ver Corrida 2 en
adelante)

**Dataset**: 8015 imágenes reales (Hospital de Clínicas F.C.V., vía FCR PRIMA), 0 excluidas por
región `"DESCONOCIDA"` (confirma el fix de `specs/001-fcr-metadata-extraction/`). Balance de
clases: 4219 `NO_TORAX` / 3796 `TORAX`. Split 80/20 → 6412 train / 1603 validación.

**Resultado** (accuracy simple sobre el split de validación — todavía no se midió
`balanced_accuracy`/F1 para esta corrida puntual, ver nota abajo):

| Época | train_loss | val_loss | val_acc |
|---|---|---|---|
| 1 | 0.6219 | 0.5851 | 79.48% |
| 2 | 0.5408 | 0.5514 | 80.85% |
| 3 | 0.4952 | 0.5364 | 81.22% |

**Duración real**: ~92 minutos (3 épocas), en CPU (sin GPU disponible), usando ~2.7 de 12 núcleos.
Más lento de lo estimado inicialmente por una prueba de un solo batch — el costo real por imagen
varía más en la práctica.

**Nota metodológica**: esta corrida no tenía semilla fija para el split train/validación, así que
`src/evaluate.py` no puede reconstruir hoy exactamente qué 1603 imágenes quedaron como held-out
para calcular `balanced_accuracy`/F1 de forma confiable sobre este checkpoint específico
(`models/etapa0_region.pt` de esta corrida). El único número confiable de esta corrida es el
`val_acc` de la tabla de arriba. Se corrigió agregando una semilla fija (`seed=42` por defecto) y
persistiendo los índices de validación (`models/etapa0_region_val_indices.json`) para que las
próximas corridas sí sean evaluables después con la métrica completa.

**Conclusión**: la tendencia es sana (pérdida bajando, accuracy subiendo, sin estancarse en 3
épocas) — no llegó al umbral de 90% de exactitud balanceada (`UMBRAL_PROMOCION_ACC`), pero es
esperable con solo 3 de 15 épocas. Sirvió para validar que el pipeline completo funciona de punta a
punta sobre datos reales por primera vez. Próximo paso: corrida completa de 15 épocas con el fix de
semilla aplicado.

---

## Corrida 2 — 2026-09-29 — 15 épocas completas, con semilla fija

**Config**:
```bash
python -m src.train --data-dir "C:\Users\Usuario\Music\DatasetVetVision" --epochs 15 --batch-size 8 --lr 1e-4
python -m src.evaluate --data-dir "C:\Users\Usuario\Music\DatasetVetVision" --model-path models/etapa0_region.pt
```

**Dataset**: mismas 8015 imágenes, mismo split 6412 train / 1603 validación (semilla `seed=42`,
reproducible — `models/etapa0_region_val_indices.json` persistido junto al checkpoint).

**Resultado por época** (val_acc, accuracy simple durante el loop de entrenamiento):

| Época | train_loss | val_loss | val_acc |
|---|---|---|---|
| 1 | 0.6181 | 0.5705 | 80.16% |
| 2 | 0.5383 | 0.5319 | 81.60% |
| 3 | 0.4984 | 0.5231 | 81.85% |
| 4 | 0.4714 | 0.5104 | 83.78% |
| 5 | 0.4515 | 0.5049 | 84.40% |
| 6 | 0.4423 | 0.4848 | 83.66% |
| 7 | 0.4378 | 0.5323 | 83.22% |
| 8 | 0.4164 | 0.5166 | 85.90% |
| 9 | 0.4101 | 0.4772 | 82.97% |
| 10 | 0.4054 | 0.4903 | 85.65% |
| 11 | 0.4054 | 0.5069 | 84.72% |
| 12 | 0.4081 | 0.5312 | 84.03% |
| 13 | 0.3986 | 0.4463 | 84.90% |
| 14 | 0.3967 | 0.5109 | 85.78% |
| 15 | 0.3931 | 0.5209 | 84.90% |

**Resultado final** (`src/evaluate.py`, sobre el held-out real de 1603 imágenes, vía
`etapa0_region_val_indices.json`):

| Métrica | Valor |
|---|---|
| accuracy | 84.90% |
| **balanced_accuracy** | **85.17%** |
| f1_macro | 84.90% |
| **promovible a producción** | **No** (umbral: 90% balanced_accuracy) |

**Duración real**: ~7h47m (15 épocas), CPU, background.

**Lectura de la tendencia**: `train_loss` baja de forma sostenida y consistente (0.62 → 0.39) en
toda la corrida, pero `val_acc` se **estanca alrededor de 83-86% desde la época ~4-5 en
adelante**, oscilando sin mejora clara hasta la época 15. Esto es la firma típica de un modelo que
llegó al techo de su capacidad actual: con el backbone congelado (`freeze_backbone=True`, solo se
entrena la última capa lineal), agregar más épocas no va a subir el desempeño — el cuello de
botella no es "faltan épocas", es la capacidad del modelo tal como está configurado hoy.

**Conclusión**: no llegó al umbral de 90%. No se recomienda otra corrida idéntica con más épocas
(el estancamiento indica que no va a mejorar solo por entrenar más tiempo). Alternativas a evaluar
antes de la próxima corrida: descongelar parcialmente el backbone (fine-tuning de las últimas
capas, no solo la cabeza), agregar aumentación de datos (hoy no se usa ninguna), o revisar si el
umbral de 90% era razonable para esta tarea específica.

---

## Corrida 3 — 2026-09-29 — 15 épocas, fine-tuning parcial (`denseblock4` + `norm5`)

**Config**:
```bash
python -m src.train --data-dir "C:\Users\Usuario\Music\DatasetVetVision" --epochs 15 --batch-size 8 --lr 1e-4 --unfreeze-layers denseblock4,norm5
python -m src.evaluate --data-dir "C:\Users\Usuario\Music\DatasetVetVision" --model-path models/etapa0_region.pt
```

**Cambio respecto a la Corrida 2**: en vez de mantener el backbone 100% congelado (solo entrenaba
la última capa lineal, ~2 mil parámetros), se descongelaron el último bloque denso
(`denseblock4`) y `norm5` — **2.162.178 parámetros entrenables** de 6.949.634 totales. El backbone
descongelado usa un learning rate 10x más bajo (`lr * 0.1`) que la cabeza nueva, para no destruir
de un salto los pesos preentrenados (práctica estándar de fine-tuning parcial). Mismo dataset,
mismo split (semilla `seed=42`, igual que la Corrida 2).

**Resultado por época**:

| Época | train_loss | val_loss | val_acc |
|---|---|---|---|
| 1 | 0.6136 | 0.5620 | 81.22% |
| 2 | 0.4979 | 0.5139 | 84.34% |
| 3 | 0.4334 | 0.4833 | 84.84% |
| 4 | 0.4059 | 0.4577 | 85.40% |
| 5 | 0.3727 | 0.4416 | 86.96% |
| 6 | 0.3497 | 0.4496 | 87.09% |
| 7 | 0.3300 | 0.4267 | 89.52% |
| 8 | 0.3289 | 0.3469 | 89.96% |
| 9 | 0.3045 | 0.4108 | 89.89% |
| 10 | 0.3044 | 0.4411 | 91.64% |
| 11 | 0.2862 | 0.3810 | 91.64% |
| 12 | 0.2782 | 0.3946 | 91.83% |
| 13 | 0.2765 | 0.3289 | 92.26% |
| 14 | 0.2653 | 0.4243 | 92.26% |
| 15 | 0.2611 | 0.3538 | **92.70%** |

**Resultado final** (`src/evaluate.py`, held-out real de 1603 imágenes):

| Métrica | Valor |
|---|---|
| accuracy | 92.70% |
| **balanced_accuracy** | **92.45%** |
| f1_macro | 92.63% |
| **promovible a producción** | **✅ Sí** (umbral: 90% balanced_accuracy) |

**Duración real**: ~8 horas (10:30 → 18:34), CPU, background. La sesión de Claude Code se cerró a
mitad de la corrida (el usuario tuvo que cortar) — el entrenamiento **siguió corriendo igual como
proceso de fondo del sistema operativo** y terminó solo, sin que nadie lo estuviera monitoreando en
vivo. Confirma que no hace falta mantener la sesión abierta para que una corrida larga termine.

**Lectura de la tendencia**: a diferencia de la Corrida 2 (estancada en ~83-86% desde la época 4),
acá `val_acc` **sigue subiendo de forma sostenida hasta la última época**, sin señales de
estancamiento ni de sobreajuste (train_loss y val_loss bajan juntos, no se separan). Confirma la
hipótesis de la Corrida 2: el cuello de botella era la capacidad del backbone congelado, no la
cantidad de épocas ni los datos.

**Conclusión**: primer modelo que cumple SC-002. Como `val_acc` seguía subiendo en la época 15 sin
aplanarse, es probable que unas pocas épocas más (o descongelar un bloque adicional) sigan dando
mejora — pero ya no es necesario para cumplir el criterio de éxito definido. Queda como
optimización opcional, no como bloqueante.
