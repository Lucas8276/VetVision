# Quickstart: MVP web de VetVision AI

## Levantar la aplicación

```bash
venv\Scripts\python.exe -m app
```

Abre un único servidor en `http://127.0.0.1:8000` (solo accesible desde esta máquina). La base de
datos y las imágenes se crean en `data/app/` (fuera de git) la primera vez que se usa.

Si falta `models/etapa0_region.onnx`, la aplicación arranca igual y lo avisa en la consola; la
carga de estudios responde con el error `modelo_no_disponible` hasta que el archivo esté presente.

## Probar a mano en 5 pasos

1. Abrir `http://127.0.0.1:8000/` en el navegador.
2. En "Nuevo estudio", elegir especie "Canino" y arrastrar o seleccionar una radiografía JPG o PNG.
3. Revisar el borrador: la región detectada, el o los hallazgos con su confianza, y el descargo.
4. Validar, corregir o descartar cada hallazgo (o agregar uno manual) hasta que "Cerrar informe"
   deje de estar deshabilitado, y cerrarlo.
5. Ir a "Estudios" y comprobar que el estudio aparece en el listado con su estado y filtrar por
   "Validado".

## Tests automáticos

```bash
venv\Scripts\python.exe -m pytest tests/test_app_*.py -q
```

59 tests, sin necesitar `models/` ni el dataset (usan modelos falsos e imágenes sintéticas). Dos
tests se saltean si no existen `models/etapa0_region.onnx` y `.pt` (paridad ONNX/PyTorch).

## Latencia medida (2026-11-17, CPU compartida)

Medido en esta máquina (CPU, sin GPU) con el modelo real y una imagen sintética, **mientras corría
en paralelo el entrenamiento de la Corrida 4** (CPU compartida: esto es un peor caso, no el mejor):

| Métrica | Valor |
|---|---|
| Mediana, 10 repeticiones | ver `docs/privado/evaluacion/latencia-app.json` |
| Criterio del proyecto | < 2 s por imagen |

La medición exacta queda en el archivo privado citado (no se versiona el detalle porque se generó
corriendo contra el modelo real).

## Latencia medida en condiciones normales, dentro del MVP (2026-11-18)

Misma medición pero de punta a punta contra el endpoint real (`POST /api/estudios`, instancia
temporal de la app con un directorio de datos aislado para no mezclar con estudios reales), sin
nada más corriendo en la máquina: mediana de **0,124 s por imagen** sobre 10 repeticiones (la
primera, 0,576 s, es el arranque en frío de la sesión de ONNX Runtime — no representativo, porque
el proceso ya está arriba cuando el veterinario carga una radiografía). Muy por debajo del
criterio del proyecto (< 2 s) y más rápido que la medición con CPU compartida del día anterior, como
se esperaba. Detalle en `docs/privado/evaluacion/latencia-app-condiciones-normales.json` (privado).

## Qué falta (fuera de esta tanda)

- Historia 4 (mapa de calor Grad-CAM): no implementada.
- Un modelo de hallazgos real (Etapa 1): el registro ya soporta agregarlo sin tocar la API ni la
  interfaz (`app/modelos_ia.py::DEFINICIONES`).
