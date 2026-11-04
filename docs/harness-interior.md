# Harness: qué hace `python -m harness` por dentro

Códigos de salida: `0` sin fallas, `1` al menos una falla, `2` error interno del harness
(nunca se interpreta como "pasó"). Contexto: `specs/003-harness-verificacion-automatica/`.

```mermaid
sequenceDiagram
    participant M as harness/__main__
    participant C as contratos.py
    participant S as specs/*.spec.yaml
    participant K as src/ (código real)
    participant G as guardia.py
    participant T as pytest

    M->>C: validar_contratos()
    C->>S: carga las hojas de cada contrato
    loop cada campo
        alt sección con estado pendiente
            C-->>M: PENDIENTE
        else sin verificador
            C-->>M: SIN_VERIFICACION
        else tiene verificador
            C->>K: obtiene el valor real (modelo sin pesos, dataset sintético)
            C-->>M: OK o FALLA (spec vs código)
        end
    end
    M->>G: guardia(árbol)
    G-->>M: hallazgos por regla y línea, sin el valor
    M->>T: pytest -m "not contratos"
    T-->>M: ok o falla
    M-->>M: resumen y código de salida (0, 1 o 2)
```
