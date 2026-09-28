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
