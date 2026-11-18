# Plan de cierre de VetVision AI

> Versión pública y resumida. El contenido del documento de entrega, las planillas de diagnósticos y
> el detalle por capítulo son privados y no se versionan (`docs/privado/`, ver `.gitignore`).
> Última actualización: 2026-11-17.

## Fechas

| Corte | Fecha | Qué tiene que existir |
|---|---|---|
| Entrega | miércoles 2026-11-25 | Documento del proyecto completo y MVP funcionando de punta a punta |
| Cierre | sábado 2026-12-12 | Correcciones incorporadas, repositorio congelado y defensa ensayada |

"Documento completo" significa: ningún capítulo en estado de plantilla, ningún `[A completar]`, y los
`[PENDIENTE]` que queden dependen de terceros y llevan su motivo escrito.

## Qué es el MVP

Una aplicación web local que se levanta con un solo comando y cubre este flujo:

| # | Capacidad | Criterio de aceptación | Estado al 2026-11-17 |
|---|---|---|---|
| 1 | Cargar una radiografía JPG o PNG | Rechaza con mensaje claro otros tipos, archivos corruptos y tamaños fuera de límite; tests de cada caso | Parcial: la demo acepta el archivo sin validarlo |
| 2 | Ejecutar el modelo | Etapa 0 (¿es tórax?) siempre; Etapa 1 (sano / no sano) si los datos alcanzan (ver "Decisiones") | Etapa 0 hecha; Etapa 1 falta |
| 3 | Borrador de hallazgos con nivel de confianza y descargo | Cada hallazgo muestra su confianza; el descargo de "no es diagnóstico definitivo" aparece siempre | Parcial: solo TÓRAX / NO TÓRAX con porcentaje |
| 4 | Validar, corregir o descartar cada hallazgo | La decisión del veterinario se guarda y se ve al reabrir el estudio; test de extremo a extremo | Falta |
| 5 | Consultar los estudios procesados | Listado con fecha, resultado y estado de validación | Falta |
| 6 | Robustez | Latencia medida contra el criterio de 2 s por imagen; ningún dato de paciente en los registros; persistencia local reproducible | Falta medir y construir |

Fuera del MVP: usuarios con perfiles, historial detallado por paciente, integración con sistemas de
gestión de clínicas, y la estimación del índice cardíaco vertebral (no hay anotación de puntos para
entrenarla ni para medirla).

## Plan día por día hasta la entrega

| Día | Documento | MVP y modelo |
|---|---|---|
| Mar 17 | Importación del documento a Markdown; auditoría documento ↔ repositorio | Evaluación completa de la Etapa 0 y chequeo de fuga por paciente; primer cruce diagnósticos ↔ placas |
| Mié 18 | Spec y primeras reglas del harness del documento | Normalizador de diagnósticos con tests; cantidad por clase; veredicto de viabilidad; spec de evaluación congelado |
| Jue 19 – Vie 20 | Capítulos de diseño, metodología y entregables | Spec `004-mvp-web` e implementación: validación de entradas, persistencia, flujo de validación, listado, tests |
| Sáb 21 – Dom 22 | Lecciones, oportunidades, conclusiones, anexos, bibliografía | Latencia, Grad-CAM, tarjeta de evaluación; validación cruzada de la Etapa 1 |
| Lun 23 | Revisión humana de todas las secciones | Correcciones |
| Mar 24 | Verificación de entrega y exportación | Congelamiento, pull requests y ensayo |

Del 26/11 al 12/12: correcciones, experimentos comparativos del modelo, ampliación del harness y
ensayo de la defensa.

## Reglas de trabajo

- **Spec primero** y **tests primero**; `python -m harness` en verde antes de avanzar.
- Todo cambio entra por rama y pull request; quien no lo escribió lo revisa.
- **Ningún número sin fuente**: las cifras del documento salen de un registro de hechos que apunta a un
  archivo de este repositorio. Lo no verificado se escribe `[PENDIENTE: motivo]`.
- **Revisión humana registrada**: ninguna sección se da por final sin que uno de los autores la haya
  leído y confirmado. El uso de asistentes de IA se registra por apartado.
- Los datos de pacientes no salen de las máquinas del equipo. Solo se versionan conteos agregados.

## Decisiones que toma el equipo

1. Alcance del modelo en el MVP, según la cantidad real de diagnósticos por clase (miércoles 18).
2. Qué hacer con el hallazgo de fuga por paciente en la partición de la Etapa 0 (ver
   `docs/MEMORIA.md`, sección Estado).
3. Si los hallazgos no torácicos anotados en una placa de tórax cuentan como "no sano".

## Riesgos

| Riesgo | Señal | Respuesta |
|---|---|---|
| Pocos casos normales para la Etapa 1 | Menos casos de los que el spec de evaluación fije como mínimo | El MVP muestra la Etapa 1 como exploratoria, con su intervalo de confianza |
| El cruce diagnóstico ↔ placa asigna el diagnóstico a una placa equivocada | Un mismo identificador con estudios en varias fechas | Se vincula por identificador y fecha; lo ambiguo va a revisión humana y no se etiqueta |
| La revisión humana no alcanza a todo el documento | Secciones sin revisor el lunes 23 | Entregas diarias por capítulo; lo no revisado no se marca como final |
| Corte de energía durante un entrenamiento | — | Trabajos cortos por pliegue, con punto de control por época y relanzamiento que saltea lo terminado |
