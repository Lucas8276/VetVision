# Plan de implementación: [FUNCIONALIDAD]

**Rama**: `[###-nombre-de-la-funcionalidad]` | **Fecha**: [FECHA] | **Spec**: [enlace]

**Entrada**: Especificación de la funcionalidad en `/specs/[###-nombre-de-la-funcionalidad]/spec.md`

**Nota**: Esta plantilla la completa el comando `/speckit-plan`; su definición describe el flujo de ejecución.

## Resumen

[Extraer de la spec: requisito principal + enfoque técnico surgido de la investigación]

## Contexto técnico

<!--
  ACCIÓN REQUERIDA: Reemplazá el contenido de esta sección con los detalles técnicos
  del proyecto. La estructura se presenta a modo orientativo para guiar
  el proceso iterativo.
-->

**Lenguaje/Versión**: [ej.: Python 3.11, Swift 5.9, Rust 1.75 o NEEDS CLARIFICATION]

**Dependencias principales**: [ej.: FastAPI, UIKit, LLVM o NEEDS CLARIFICATION]

**Almacenamiento**: [si aplica, ej.: PostgreSQL, CoreData, archivos o N/A]

**Pruebas**: [ej.: pytest, XCTest, cargo test o NEEDS CLARIFICATION]

**Plataforma objetivo**: [ej.: servidor Linux, iOS 15+, WASM o NEEDS CLARIFICATION]

**Tipo de proyecto**: [ej.: biblioteca/cli/servicio-web/app-móvil/compilador/app-de-escritorio o NEEDS CLARIFICATION]

**Objetivos de rendimiento**: [según el dominio, ej.: 1000 req/s, 10k líneas/s, 60 fps o NEEDS CLARIFICATION]

**Restricciones**: [según el dominio, ej.: <200 ms p95, <100 MB de memoria, funcionamiento sin conexión o NEEDS CLARIFICATION]

**Escala/Alcance**: [según el dominio, ej.: 10k usuarios, 1M de líneas de código, 50 pantallas o NEEDS CLARIFICATION]

## Verificación contra la constitution

*PUERTA: debe aprobarse antes de la investigación de la Fase 0. Volver a verificar después del diseño de la Fase 1.*

[Puertas determinadas a partir del archivo de la constitution]

## Estructura del proyecto

### Documentación (esta funcionalidad)

```text
specs/[###-funcionalidad]/
├── plan.md              # Este archivo (salida del comando /speckit-plan)
├── research.md          # Salida de la Fase 0 (comando /speckit-plan)
├── data-model.md        # Salida de la Fase 1 (comando /speckit-plan)
├── quickstart.md        # Salida de la Fase 1 (comando /speckit-plan)
├── contracts/           # Salida de la Fase 1 (comando /speckit-plan)
└── tasks.md             # Salida de la Fase 2 (comando /speckit-tasks; NO lo crea /speckit-plan)
```

### Código fuente (raíz del repositorio)
<!--
  ACCIÓN REQUERIDA: Reemplazá el árbol de ejemplo de abajo con la estructura concreta
  de esta funcionalidad. Eliminá las opciones que no uses y ampliá la estructura elegida
  con rutas reales (ej.: apps/admin, packages/algo). El plan entregado
  no debe incluir las etiquetas de "Opción".
-->

```text
# [ELIMINAR SI NO SE USA] Opción 1: Proyecto único (POR DEFECTO)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# [ELIMINAR SI NO SE USA] Opción 2: Aplicación web (cuando se detectan "frontend" + "backend")
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# [ELIMINAR SI NO SE USA] Opción 3: Móvil + API (cuando se detecta "iOS/Android")
api/
└── [igual que backend arriba]

ios/ o android/
└── [estructura propia de la plataforma: módulos de funcionalidad, flujos de UI, pruebas de plataforma]
```

**Decisión de estructura**: [Documentar la estructura elegida y referenciar los
directorios reales capturados arriba]

## Seguimiento de complejidad

> **Completar SOLO si la verificación contra la constitution tiene violaciones que deban justificarse**

| Violación | Por qué es necesaria | Alternativa más simple descartada porque |
|-----------|----------------------|------------------------------------------|
| [ej.: un 4.º proyecto] | [necesidad actual] | [por qué 3 proyectos no alcanzan] |
| [ej.: patrón Repository] | [problema específico] | [por qué el acceso directo a la BD no alcanza] |
