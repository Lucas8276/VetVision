# Memoria compartida del proyecto VetVision AI

> **Política de contenido.** Este archivo es público y lo carga Claude Code en cada sesión
> (`@docs/MEMORIA.md` en `CLAUDE.md`). Permitido: decisiones, convenciones, lecciones y estado.
> **Prohibido:** datos de pacientes o dueños, nombres de contactos externos (se usa el rol),
> correos, teléfonos, credenciales, información de otros proyectos de los integrantes.
> Se actualiza cuando se toma una decisión durable; los cambios pasan por pull request.

## Objetivo y plazos

- VetVision AI ayuda a diagnosticar radiografías de perros y gatos. Es el Proyecto Final de Grado
  (PFG) de Stiven, con Lucas como compañero de equipo, y tiene intención de viabilidad comercial.
- **Plazos vigentes (confirmados por el equipo el 2026-11-16):** el **miércoles 2026-11-25 se entrega el
  documento completo y el MVP** funcionando de punta a punta; el **2026-12-12 es el cierre**: correcciones
  incorporadas, repositorio congelado y defensa ensayada. El hito original del 2026-11-18 quedó desfasado.
  Lo demostrable y evaluable pesa más que lo deseable. Plan: `docs/PLAN-DE-CIERRE.md`.
- **Entrega:** Proyecto Integrador Final (PIF): un documento y un MVP. El contenido del documento, las
  guías de la universidad y el PDF son privados y **no se versionan** (`docs/privado/`).
- **Uso de IA generativa:** autorizado por el profesor mientras los estudiantes puedan explicar el
  proyecto. Se registra en una declaración de uso y cada sección la revisa una persona.
- **Hardware:** la máquina principal no tiene GPU compatible con CUDA (PyTorch corre en CPU: unos 0,18 s
  por imagen en inferencia por lotes). La máquina del otro integrante tiene una GPU NVIDIA, pero con
  cortes de energía posibles: todo entrenamiento debe ser reanudable (trabajos cortos, punto de control
  por época).
- Datos de origen: equipo de radiografía computada del Hospital de Clínicas de la Facultad de
  Ciencias Veterinarias (UNNE). Hay un contacto de acceso a los datos y una radióloga colaboradora
  para la anotación clínica. Solo el subconjunto etiquetado y verificado cuenta como dataset real.

## Arquitectura y decisiones

- **Cascada de modelos:** Etapa 0 (puerta binaria TORAX / NO_TORAX), Etapa 1 (triaje sano / no
  sano) y Etapa 2 (diagnóstico multi-etiqueta, se inicializa desde los pesos de la Etapa 1).
  **Solo existe la Etapa 0**; las otras dos esperan la anotación clínica.
- **Backbone:** DenseNet-121 preentrenado en tórax humano (TorchXRayVision), 1 canal, rango
  `xrv.utils.normalize`. No existe un modelo fundacional veterinario.
- **Fine-tuning parcial** (`denseblock4` + `norm5`) con LR del backbone 10 veces menor; se guarda
  el mejor checkpoint por `val_balanced_acc`. Umbral de promoción: 0,90 de balanced accuracy.
- **Dos parsers independientes:** `src/ddo_parser.py` (binario `.ddo`) y `src/parser_fcr.py` (`.txt`).
- **Los datos nunca entran a git** (`.gitignore` + DVC). Anonimizar antes de cualquier subida a la
  nube: **la anonimización todavía no está implementada y bloquea usar AWS** (constitution, IV).
- **SDD con spec-kit:** specs en `specs/`, constitution en `.specify/memory/constitution.md`,
  comandos `/speckit-*` en `.claude/skills/` (traducidos al español).
- **Harness** (`python -m harness`): valida contratos `specs/*.spec.yaml` contra el código, guardia
  de datos personales y tests. Corre en hooks de Claude, hooks de git (opcionales) y CI.

## Convenciones

- Spec primero: si el código no coincide con el spec, el código está mal.
- `main` está protegida: los cambios van por rama y pull request, con el chequeo `verificar` en verde.
- Commit y push van por **dos confirmaciones separadas**; aprobar el commit no aprueba el push.
- Mensajes de commit en español con prefijo (`feat:`, `fix:`, `docs:`, `chore:`).
- Repositorio **público**: ningún nombre ni ID real en código, tests, docs, specs ni commits; usar
  valores ficticios (`PACIENTE^PRUEBA`, `0000-1`).
- Todo cambio de dependencias se declara en `requirements.txt` en el mismo cambio.

## Lecciones aprendidas

- El spec decía entrada RGB de 3 canales y el backbone exige 1: se descubrió recién al entrenar.
  Por eso existe el validador de contratos.
- El opset de ONNX del código (17) no coincidía con el spec (18); el harness lo detectó.
- Los códigos de región reales llegan en inglés (`CHEST`, `NECK`, ...) y la vista puede ser `VD/DV`.
- Emparejar metadata e imagen por prefijo mezclaba pacientes (`FCR1` con `FCR10`): se empareja por
  nombre exacto.
- Los hooks con rutas relativas fallan si el shell está en otra carpeta: usar `$CLAUDE_PROJECT_DIR`.
- En CI, `torch` y `torchvision` deben instalarse juntos desde el mismo índice (CPU).
- Hubo una filtración real de datos en el historial del repo público; la remediación depende del dueño.
- Partir entrenamiento y validación al azar **por imagen** mezcla placas del mismo paciente en los dos
  lados y puede inflar la métrica: la partición se hace por paciente.
- La planilla de diagnósticos de un año que no está en el dataset no sirve: antes de transcribir se
  verifica que el identificador exista en los datos.

## Estado (2026-11-17)

- Prompt de trabajo: `docs/PROMPT-FABLE.md`. Plan de cierre: `docs/PLAN-DE-CIERRE.md`.
- **Etapa 0 entrenada** (Corrida 3, detalle en `ENTRENAMIENTOS.md`). Medición exploratoria del 2026-11-17
  sobre el held-out de 1603 imágenes, a reproducir bajo el spec de evaluación: balanced accuracy 92,45 %
  (IC 95 % por bootstrap: 91,2 a 93,7), ROC-AUC 0,955 (0,942 a 0,967), sensibilidad para TORAX 88,3 %,
  especificidad 96,6 %, latencia de punta a punta en CPU con mediana de 0,14 s por imagen.
- **Hallazgo abierto: fuga por paciente.** 1473 de las 1603 imágenes de validación (91,9 %) son de un
  paciente que también tiene imágenes en entrenamiento. En las 130 imágenes de pacientes que solo están
  en validación la balanced accuracy es 88,1 % (muestra chica, todavía sin intervalo). Falta
  reparticionar por paciente y volver a medir; hasta entonces el 92,45 % se informa con esta salvedad.
- **Dataset medido:** 8158 estudios, 8015 con imagen, años 2018 a 2026; 3796 imágenes de tórax
  (3415 caninas, 379 felinas, 2 sin dato de especie).
- **Diagnósticos:** transcripción en curso (se hace por año). El cruce con las placas va por
  identificador y fecha; la unidad de análisis es el estudio, no la imagen.
- **Harness:** 61 tests; contratos con 11 campos `ok`, 4 secciones `pendiente` y 21 campos
  `sin_verificacion`. CI en verde.
- **Demo web local** (`server.py`): se reemplaza por el MVP de la feature `004-mvp-web` (en especificación).
- **Pendientes:** MVP, Etapa 1 (según cantidad de diagnósticos), spec de evaluación, harness del
  documento, anonimización, verificadores de contratos faltantes, Etapa 2 (necesita más anotación).
