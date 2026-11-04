# Harness: flujo completo, de la edición al merge

Contexto: `specs/003-harness-verificacion-automatica/`. Tres capas con la misma verificación.

| Capa | Cuándo corre | Qué corre | Si falla |
|---|---|---|---|
| Hooks de Claude (`.claude/settings.json`) | Al editar `src/`, `specs/`, `tests/` y antes de un `git commit` hecho por Claude | Guardia (y contratos si es `src/` o `specs/`) | Código 2: bloquea o avisa con el motivo |
| Hooks de git (`.githooks/`, requieren `python scripts/instalar_hooks.py`) | `git commit` / `git push` desde cualquier lado | `pre-commit`: guardia sobre lo preparado. `pre-push`: harness completo | Aborta el commit o el push |
| CI (`.github/workflows/verificar.yml`) | Cada push y pull request | `python -m harness` | Chequeo `verificar` en rojo |

```mermaid
sequenceDiagram
    autonumber
    actor Dev as Integrante
    participant CC as Claude Code
    participant HC as Hooks de Claude
    participant H as python -m harness
    participant G as Git local
    participant CI as GitHub Actions
    participant BP as Protección de rama

    Dev->>CC: Pide un cambio (spec primero)
    CC->>CC: Edita src/, specs/ o tests/
    CC->>HC: PostToolUse (Edit/Write)
    HC->>H: hook post-edit
    H->>H: Guardia sobre el archivo y, si es src/specs, contratos
    alt hay falla
        H-->>CC: código 2 + motivo (sin el valor detectado)
        CC->>CC: Corrige (empezando por el spec)
    else todo ok
        H-->>CC: código 0
    end

    Dev->>CC: Pide commit
    CC->>Dev: Confirmación 1 (permissions.ask)
    Dev-->>CC: Aprueba commit
    CC->>HC: PreToolUse (git commit)
    HC->>H: hook pre-commit (guardia sobre lo preparado)
    alt guardia encuentra datos o archivos crudos
        H-->>CC: código 2, bloquea el commit
    else limpio
        CC->>G: git commit
        G->>H: .githooks/pre-commit (si fue activado)
        H-->>G: código 0
    end

    Dev->>CC: Pide push
    CC->>Dev: Confirmación 2, distinta (commits que salen, remoto, público/privado)
    Dev-->>CC: Aprueba push
    CC->>G: git push
    G->>H: .githooks/pre-push → harness completo
    alt contratos, guardia o tests fallan
        H-->>G: código 1, aborta el push
    else todo ok
        G->>CI: push / pull request
        CI->>H: python -m harness (Linux, torch CPU)
        H-->>CI: resumen ok / falla / pendiente / sin_verificacion
        CI->>BP: chequeo verificar (verde o rojo)
        alt rojo
            BP-->>Dev: merge bloqueado
        else verde
            BP-->>Dev: merge permitido
        end
    end
```

> La protección de rama es una configuración de GitHub del dueño del repo; sin ella el CI avisa pero no bloquea el merge.
