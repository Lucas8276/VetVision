# Quickstart: validar la feature 003-harness-verificacion-automatica

Guía para comprobar de punta a punta que el harness cumple `spec.md`, una vez implementado
(`/speckit-tasks` + `/speckit-implement`). Los pasos 2 y 3 **rompen algo a propósito** para
comprobar que el harness lo detecta; el paso final de cada uno es revertirlo.

## Prerrequisitos

```bash
venv\Scripts\activate
pip install -r requirements.txt
python scripts/instalar_hooks.py        # activa .githooks en este clon (una vez)
```

## 1. Estado limpio (SC-001, SC-003, SC-006)

```bash
python -m harness
```

**Esperado**: código de salida 0. El resumen muestra contratos `ok`, las etapas 1 y 2 como
`pendiente`, los campos sin verificador (`resolucion_minima_px`, formatos de archivo, `anonimizacion`)
como `sin_verificacion`, guardia sin hallazgos y todos los tests en verde.

## 2. Deriva de contrato detectada (US1, SC-001)

Reintroducir a propósito cada deriva conocida y confirmar que falla nombrando el campo:

1. En `specs/model-tensor.spec.yaml` cambiar `input › canales` de `1` a `3` → `python -m harness
   contratos` debe fallar con el campo, el valor del spec (3) y el del código (1).
2. En `specs/model-tensor.spec.yaml` cambiar `export › opset` de `18` a `17` → falla con 17 vs 18.
3. En `specs/data-contract.spec.yaml` quitar `VD/DV` de `proyecciones_admitidas` → falla.

Revertir con `git checkout -- specs/` y confirmar que vuelve a pasar.

## 3. Guardia de datos personales (US3, SC-003)

Sin escribir datos reales: crear un archivo temporal (fuera del repo o ignorado) con un campo de
paciente cuyo valor **no** esté en `harness/valores_ficticios.txt` (cualquier texto inventado), y:

```bash
python -m harness guardia --archivos RUTA_DEL_TEMPORAL
```

**Esperado**: falla con `archivo:línea [R-CAMPO-PACIENTE]` y **sin** repetir el valor. Repetir con un
valor aprobado (`PACIENTE^PRUEBA`) → pasa. Probar también un archivo con extensión de datos crudos
del equipo de rayos X → `R-ARCHIVO-CRUDO`.

## 4. Bloqueo antes del commit (US3/US4, FR-014)

Preparar (`git add`) el archivo temporal del paso 3 dentro del repo e intentar `git commit`:

- Desde el asistente: el hook `PreToolUse` bloquea el commit y explica por qué.
- A mano con hooks activados: `.githooks/pre-commit` lo rechaza.

Deshacer con `git restore --staged` y borrar el temporal.

## 5. Las dos confirmaciones (US4, FR-019/FR-020, SC-008)

Pedirle al asistente un commit trivial: debe aparecer una **primera** confirmación con la lista
exacta de archivos. Aprobarla y pedir el push: debe aparecer una **segunda**, distinta, con los
commits que salen, el remoto y si el repo es público o privado. La aprobación de la primera no debe
haber valido para la segunda.

## 6. Configuración compartida (US4, SC-004)

En una carpeta limpia:

```bash
git clone <repo> prueba-clon && cd prueba-clon
```

**Esperado**: existen `.claude/skills/` y `.claude/settings.json`; los comandos `/speckit-*` están
disponibles al abrir el proyecto en el asistente (tras aceptar la confianza del proyecto); un archivo
`.claude/settings.local.json` creado a mano **no** aparece en `git status`.

## 7. Memoria compartida (US5, SC-005)

- `docs/MEMORIA.md` existe en el clon del paso 6.
- Abrir una sesión nueva y preguntar por un dato que solo figure en ese documento: debe responderlo
  sin que nadie se lo haya dicho (verifica el import `@docs/MEMORIA.md`).
- Agregarle un correo o "Dra. Fulana" → `python -m harness guardia` falla con `R-CONTACTO`.

## 8. CI (US2, SC-002)

1. Subir una rama de prueba con un test roto a propósito → el chequeo termina en rojo con el motivo
   visible y en menos de 10 minutos. Arreglar → verde. Es también la primera corrida de la suite en
   Linux: cualquier fallo de portabilidad aparece acá.
2. **Acción del dueño del repo (Lucas)**: en *Settings › Branches* exigir este chequeo antes de
   fusionar a `main`. Sin eso el CI marca rojo pero no impide fusionar (FR-005).

## 9. Constitution (US6)

`.specify/memory/constitution.md` enuncia el Principio VI, con su justificación y `Version: 1.1.0`.

## Limpieza

Borrar el clon de prueba, la rama de prueba y cualquier archivo temporal de los pasos 3 y 4.
