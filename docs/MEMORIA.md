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

## Estado (2026-11-17, actualizado de madrugada)

- Prompt de trabajo: `docs/PROMPT-FABLE.md`. Plan de cierre: `docs/PLAN-DE-CIERRE.md`.
- **Fuga por paciente, resuelta.** La Corrida 3 partía entrenamiento y validación al azar por imagen:
  91,9 % de la validación (1473 de 1603 imágenes) era de un paciente también presente en entrenamiento.
  Se especificó la partición por paciente (`specs/007-evaluacion-modelo`, `src/particion.py`) y se
  corrió de nuevo (Corrida 4, misma configuración, 0 grupos de paciente compartidos).
- **Etapa 0, modelo oficial actualizado (Corrida 4).** Balanced accuracy **91,45 %** sobre 1601 imágenes
  de validación sin ningún paciente compartido con entrenamiento (accuracy 91,57 %, F1 macro 91,53 %).
  Sigue por encima del umbral de promoción (0,90). Es 1 punto menos que el 92,45 % de la Corrida 3: la
  fuga inflaba la métrica, pero no de forma dramática. **Este es el checkpoint que usa la aplicación**
  (`models/etapa0_region.pt`/`.onnx`); el de la Corrida 3 se conserva como `..._c3.*` para referencia.
  Detalle completo en `ENTRENAMIENTOS.md`, Corrida 4.
- **Medición completa repetida sobre la Corrida 4** (2026-11-17, mismo conjunto de validación de 1601
  imágenes sin fuga): ROC-AUC 94,47 % (IC95 93,10–95,73), sensibilidad para TORAX 89,31 % (IC95
  87,15–91,34), especificidad para NO_TORAX 93,59 % (IC95 91,86–95,24), calibración razonable (ECE
  3,6 %; por encima de 95 % de confianza el acierto real es 95,7 %), latencia de punta a punta en CPU
  con mediana de 0,189 s por imagen. Por especie: canino 91,94 % de acierto (n=1352), **felino 86,80 %
  (n=197)** — confirma que dejar felinos fuera del alcance evaluado fue la decisión correcta por ahora.
  Hallazgo nuevo, sin confirmar con casos concretos: por **nombre** de paciente (no por ID) hay 97
  pacientes (30 % de la validación) que comparten nombre con entrenamiento, con ~3 puntos de mejor
  desempeño que los realmente nuevos. Explicación más probable (equipo, 2026-11-17): el mismo animal
  con placas de distintos momentos, registrado con un ID nuevo en cada visita — no un error del
  parser ni una coincidencia de nombres. Si es así, la partición por paciente (`grupo_paciente`,
  spec 007) no lo detecta porque agrupa por ID, no por identidad real del animal; es una limitación
  conocida de cómo el equipo de origen asigna el ID, no del código. No amerita una corrección ahora:
  dejarlo registrado como limitación del dataset. Detalle en `docs/privado/evaluacion/corrida4/`.
- **Dataset medido:** 8158 estudios, 8015 con imagen, años 2018 a 2026; 3796 imágenes de tórax
  (3415 caninas, 379 felinas, 2 sin dato de especie).
- **Diagnósticos:** cruce real contra el dataset (2026-11-17): 111 filas etiquetables, 98 pacientes con
  veredicto sano/no sano (28 normales, 70 no sanos) — Etapa 1 queda en carácter exploratorio por el
  tamaño de muestra. Detalle agregado en `docs/privado/etiquetas/resumen_etiquetas.md` (privado).
- **MVP web implementado** (`app/`, spec `004-mvp-web`): API con FastAPI, ONNX Runtime y SQLite, 59
  tests, incluida la paridad real ONNX↔PyTorch. Reemplaza a la demo de una sola pantalla; `server.py`,
  `VetVision Demo.dc.html` y `support.js` se retiraron del repositorio el 2026-11-17 (decisión del
  equipo), junto con `flask`/`flask-cors` de `requirements.txt` (sin otro uso). `python -m app` lo
  levanta con un solo comando. Panel visual rediseñado (2026-11-17)
  sobre la misma identidad oscura/turquesa: barra de confianza con umbrales, invertir/realzar
  contraste de la imagen, filtros y búsqueda en el listado; sin tocar la lógica ni romper tests.
  Pendiente de revisión visual humana en el navegador y de decidir si corregir región manualmente
  (como hallazgos) es parte del alcance.
- **Harness:** 158 tests; contratos con 12 campos `ok`, 4 secciones `pendiente` y 21 campos
  `sin_verificacion`. Nuevo subcomando `python -m harness documento` (verifica el documento de entrega:
  hechos, citas, datos personales, descargo, revisión humana). CI en verde.
- **Pendientes:** Etapa 1 (con el N real, exploratoria), spec de evaluación completo (incremento 2),
  anonimización, verificadores de contratos faltantes, Etapa 2 (necesita más anotación), revisión
  humana de los capítulos del documento reescritos esta madrugada.
