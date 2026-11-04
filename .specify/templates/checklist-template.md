# Checklist de [TIPO DE CHECKLIST]: [NOMBRE DE LA FUNCIONALIDAD]

**Propósito**: [Descripción breve de lo que cubre este checklist]
**Creado**: [FECHA]
**Funcionalidad**: [Enlace a spec.md o a la documentación relevante]

**Nota**: Este checklist personalizado lo genera el comando `/speckit-checklist` a partir del contexto y los requisitos de la funcionalidad.
**Responsable de la revisión**: Este checklist es un artefacto de revisión de la calidad de los requisitos, a cargo de quien revisa. Marcá un ítem con `[x]` solo cuando quien revisa determine que se cumple el criterio de calidad del requisito.
**Semántica del marcador**: `[x]` significa que el criterio fue revisado y se cumple en cuanto a la calidad del requisito. No significa que el trabajo de implementación esté terminado.

<!--
  ============================================================================
  IMPORTANTE: Los ítems del checklist de abajo son EJEMPLOS ilustrativos.

  El comando /speckit-checklist DEBE reemplazarlos por ítems reales basados en:
  - El pedido específico de checklist del usuario
  - Los requisitos de la funcionalidad en spec.md
  - El contexto técnico de plan.md
  - Los detalles de implementación de tasks.md

  NO conserves estos ítems de ejemplo en el archivo de checklist generado.
  ============================================================================
-->

## [Categoría 1]

- [ ] CHK001 Primer ítem del checklist con una acción clara
- [ ] CHK002 Segundo ítem del checklist
- [ ] CHK003 Tercer ítem del checklist

## [Categoría 2]

- [ ] CHK004 Otro ítem de la categoría
- [ ] CHK005 Ítem con criterios específicos
- [ ] CHK006 Último ítem de esta categoría

## Notas

- Marcá los ítems con `[x]` solo después de que la revisión confirme que se cumple el criterio de calidad del requisito
- Dejá los ítems sin marcar cuando todavía requieran aclaración, corrección o evaluación de quien revisa
- `/speckit-implement` lee el estado de las casillas del checklist como una puerta y no debe modificar los marcadores
- `checklists/requirements.md` tiene un ciclo de vida propio, mantenido por `/speckit-specify` y `/speckit-clarify`
- Agregá comentarios o hallazgos en línea
- Enlazá recursos o documentación relevante
- Los ítems se numeran de forma secuencial para facilitar la referencia
