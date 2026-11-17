"""Tests de app/api.py y app/modelos_ia.py (spec 004).

Usan el TestClient de FastAPI, una base temporal y modelos falsos: no necesitan `models/`.
Los unicos tests que tocan el modelo real (paridad ONNX <-> PyTorch, FR-013) se saltean si no esta.
"""
from pathlib import Path

import numpy as np
import pytest

from app import modelos_ia
from app.modelos_ia import (
    DEFINICIONES,
    ModeloOnnx,
    RegistroModelos,
    nivel_de_confianza,
    normalizar_rango_xrv,
    preparar_entrada,
)
from ayudas_app import ModeloFalso, crear_cliente, imagen_sintetica, jpg_sintetico, png_sintetico, subir

RAIZ = Path(__file__).resolve().parent.parent


@pytest.fixture
def cliente(tmp_path):
    return crear_cliente(tmp_path)[0]


# ---------------------------------------------------------------- salud y contrato

def test_salud_informa_modelos_y_catalogos(cliente):
    cuerpo = cliente.get("/api/salud").json()
    assert cuerpo["estado"] == "ok"
    assert cuerpo["hay_modelo_region"] is True
    assert cuerpo["hay_modelo_hallazgos"] is False
    assert cuerpo["modelos"][0]["nombre"] == "puerta_falsa"
    assert {"id": "cardiomegalia", "etiqueta": "Cardiomegalia"} in cuerpo["tipos_hallazgo"]
    assert len(cuerpo["tipos_hallazgo"]) == 10
    assert "No es un diagnóstico definitivo" in cuerpo["descargo"]


def test_el_contrato_es_openapi_3_1(cliente):
    contrato = cliente.get("/openapi.json").json()
    assert contrato["openapi"].startswith("3.1")
    for ruta in ("/api/salud", "/api/estudios", "/api/estudios/{codigo}",
                 "/api/estudios/{codigo}/imagen", "/api/estudios/{codigo}/hallazgos",
                 "/api/estudios/{codigo}/hallazgos/{id_hallazgo}", "/api/estudios/{codigo}/cerrar"):
        assert ruta in contrato["paths"], ruta


def test_la_interfaz_se_sirve_desde_el_mismo_proceso(cliente):
    pagina = cliente.get("/")
    assert pagina.status_code == 200
    assert "VetVision" in pagina.text
    assert cliente.get("/static/app.js").status_code == 200
    assert cliente.get("/static/estilos.css").status_code == 200


# ---------------------------------------------------------------- carga

def test_cargar_jpg_crea_estudio_con_borrador(cliente):
    respuesta = subir(cliente)
    assert respuesta.status_code == 201
    estudio = respuesta.json()
    assert estudio["codigo"].startswith("EST-")
    assert estudio["estado"] == "borrador"
    assert estudio["especie"] == "canino"
    assert estudio["region"] == {"etiqueta": "TORAX", "es_torax": True, "confianza": 0.95,
                                 "nivel": "alta"}
    assert estudio["modelos"][0]["nombre"] == "puerta_falsa"
    assert estudio["modelos"][0]["huella_sha256"] == "f" * 64
    assert estudio["tiempo_inferencia_ms"] >= 0
    assert estudio["hallazgos"] == []
    assert "No es un diagnóstico definitivo" in estudio["descargo"]
    # Sin modelo de hallazgos, el sistema lo dice (historia 1, escenario 4).
    assert "sin_modelo_hallazgos" in {a["codigo"] for a in estudio["avisos"]}


def test_cargar_png_tambien_funciona(cliente):
    assert subir(cliente, png_sintetico()).status_code == 201


@pytest.mark.parametrize("contenido, codigo", [
    (b"", "archivo_vacio"),
    (b"no soy una imagen" * 20, "tipo_no_soportado"),
    (b"\xff\xd8\xff\xe0" + b"\x00" * 2000 + b"\xff\xd9", "imagen_corrupta"),
    (jpg_sintetico(ancho=100, alto=100), "imagen_muy_chica"),
])
def test_carga_invalida_no_crea_estudio(cliente, contenido, codigo):
    respuesta = subir(cliente, contenido)
    assert respuesta.status_code == 422
    cuerpo = respuesta.json()
    assert set(cuerpo) == {"codigo", "mensaje"}
    assert cuerpo["codigo"] == codigo
    assert cliente.get("/api/estudios").json()["estudios"] == []


def test_carga_que_supera_el_tamano_maximo(tmp_path):
    contenido = jpg_sintetico()
    cliente, configuracion = crear_cliente(tmp_path, max_bytes=len(contenido) - 1)
    respuesta = subir(cliente, contenido)
    assert respuesta.status_code == 413
    assert respuesta.json()["codigo"] == "archivo_muy_grande"
    assert not list(configuracion.dir_imagenes.glob("*"))


def test_especie_invalida_o_faltante(cliente):
    assert subir(cliente, especie="dragon").json()["codigo"] == "especie_invalida"
    sin_especie = cliente.post("/api/estudios", files={"imagen": ("a.jpg", jpg_sintetico())})
    assert sin_especie.status_code == 422
    assert set(sin_especie.json()) == {"codigo", "mensaje"}


def test_especie_felina_se_permite_con_aviso(cliente):
    estudio = subir(cliente, especie="felino").json()
    assert estudio["especie"] == "felino"
    assert "especie_fuera_de_alcance" in {a["codigo"] for a in estudio["avisos"]}


def test_no_torax_avisa_pero_no_bloquea(tmp_path):
    cliente, _ = crear_cliente(tmp_path, modelos=[ModeloFalso(etiqueta="NO_TORAX", confianza=0.8)])
    respuesta = subir(cliente)
    assert respuesta.status_code == 201  # FR-002: aviso, nunca bloqueo
    estudio = respuesta.json()
    assert estudio["region"]["es_torax"] is False
    assert estudio["region"]["nivel"] == "media"
    assert "region_no_torax" in {a["codigo"] for a in estudio["avisos"]}
    manual = cliente.post(f"/api/estudios/{estudio['codigo']}/hallazgos",
                          json={"tipo": "cardiomegalia"})
    assert manual.status_code == 201


def test_duplicado_crea_dos_estudios_y_avisa_en_el_segundo(cliente):
    primero = subir(cliente).json()
    segundo = subir(cliente).json()
    assert primero["codigo"] != segundo["codigo"]
    assert "duplicado" not in {a["codigo"] for a in primero["avisos"]}
    aviso = next(a for a in segundo["avisos"] if a["codigo"] == "duplicado")
    assert primero["codigo"] in aviso["mensaje"]


def test_sin_modelo_de_region_la_app_funciona_y_la_carga_explica(tmp_path):
    cliente, configuracion = crear_cliente(
        tmp_path, modelos=[],
        no_disponibles=[{"nombre": "etapa0_region", "papel": "region",
                         "motivo": "archivo_no_encontrado"}],
    )
    salud = cliente.get("/api/salud").json()
    assert salud["hay_modelo_region"] is False
    assert salud["modelos"][0]["disponible"] is False
    assert cliente.get("/api/estudios").status_code == 200  # el listado sigue funcionando
    respuesta = subir(cliente)
    assert respuesta.status_code == 503
    assert respuesta.json()["codigo"] == "modelo_no_disponible"
    assert not list(configuracion.dir_imagenes.glob("*"))


def test_modelo_de_hallazgos_registrado_genera_hallazgos_sin_tocar_nada_mas(tmp_path):
    """FR-003: sumar la Etapa 1 es agregar un modelo al registro; API, base e interfaz no cambian."""
    etapa1 = ModeloFalso(nombre="etapa1_falsa", papel="hallazgos", etiqueta="NO_SANO",
                         confianza=0.65, hallazgo_por_clase={"NO_SANO": "no_sano"})
    cliente, _ = crear_cliente(tmp_path, modelos=[ModeloFalso(), etapa1])
    estudio = subir(cliente).json()
    assert cliente.get("/api/salud").json()["hay_modelo_hallazgos"] is True
    assert "sin_modelo_hallazgos" not in {a["codigo"] for a in estudio["avisos"]}
    assert [m["nombre"] for m in estudio["modelos"]] == ["puerta_falsa", "etapa1_falsa"]
    hallazgo = estudio["hallazgos"][0]
    assert hallazgo["origen"] == "modelo"
    assert hallazgo["modelo"] == "etapa1_falsa"
    assert hallazgo["tipo"] == "no_sano"
    assert hallazgo["tipo_etiqueta"] == "No sano"  # tipo fuera del catalogo: etiqueta derivada
    assert hallazgo["confianza"] == 0.65
    assert hallazgo["nivel"] == "baja"  # confianza baja: se muestra igual, marcada
    assert hallazgo["estado"] == "pendiente"
    assert estudio["pendientes"] == 1
    assert estudio["puede_cerrarse"] is False


# ---------------------------------------------------------------- detalle, imagen, hallazgos

def test_detalle_e_imagen(cliente):
    contenido = jpg_sintetico()
    codigo = subir(cliente, contenido).json()["codigo"]
    assert cliente.get(f"/api/estudios/{codigo}").json()["codigo"] == codigo
    imagen = cliente.get(f"/api/estudios/{codigo}/imagen")
    assert imagen.status_code == 200
    assert imagen.headers["content-type"] == "image/jpeg"
    assert imagen.content == contenido


def test_estudio_inexistente_devuelve_404_con_codigo(cliente):
    for respuesta in (
        cliente.get("/api/estudios/EST-00000000"),
        cliente.get("/api/estudios/EST-00000000/imagen"),
        cliente.post("/api/estudios/EST-00000000/hallazgos", json={"tipo": "otro"}),
        cliente.patch("/api/estudios/EST-00000000/hallazgos/1", json={"accion": "validar"}),
        cliente.post("/api/estudios/EST-00000000/cerrar"),
    ):
        assert respuesta.status_code == 404
        assert respuesta.json()["codigo"] == "estudio_no_encontrado"


def test_hallazgo_manual_valida_el_tipo(cliente):
    codigo = subir(cliente).json()["codigo"]
    malo = cliente.post(f"/api/estudios/{codigo}/hallazgos", json={"tipo": "inventado"})
    assert malo.status_code == 422
    assert malo.json()["codigo"] == "tipo_invalido"
    bueno = cliente.post(f"/api/estudios/{codigo}/hallazgos",
                         json={"tipo": "efusion_pleural", "comentario": "leve"})
    assert bueno.status_code == 201
    hallazgo = bueno.json()["hallazgos"][0]
    assert hallazgo["tipo_etiqueta"] == "Efusión pleural"
    assert hallazgo["origen"] == "manual"
    assert hallazgo["comentario"] == "leve"


def test_accion_invalida_y_hallazgo_inexistente(cliente):
    codigo = subir(cliente).json()["codigo"]
    id_hallazgo = cliente.post(f"/api/estudios/{codigo}/hallazgos",
                               json={"tipo": "otro"}).json()["hallazgos"][0]["id"]
    mala = cliente.patch(f"/api/estudios/{codigo}/hallazgos/{id_hallazgo}",
                         json={"accion": "borrar"})
    assert mala.status_code == 422
    assert set(mala.json()) == {"codigo", "mensaje"}
    inexistente = cliente.patch(f"/api/estudios/{codigo}/hallazgos/9999",
                                json={"accion": "validar"})
    assert inexistente.status_code == 404
    assert inexistente.json()["codigo"] == "hallazgo_no_encontrado"


def test_filtro_por_estado_invalido(cliente):
    respuesta = cliente.get("/api/estudios", params={"estado": "cualquiera"})
    assert respuesta.status_code == 422
    assert set(respuesta.json()) == {"codigo", "mensaje"}


# ---------------------------------------------------------------- modelos_ia

def test_niveles_de_confianza():
    assert nivel_de_confianza(0.95) == "alta"
    assert nivel_de_confianza(0.90) == "alta"
    assert nivel_de_confianza(0.8999) == "media"
    assert nivel_de_confianza(0.70) == "media"
    assert nivel_de_confianza(0.6999) == "baja"


def test_registro_informa_modelo_ausente_sin_romper(tmp_path):
    registro = RegistroModelos.desde_definiciones(DEFINICIONES, raiz=tmp_path)
    assert registro.disponibles("region") == []
    estado = registro.estado()
    assert estado[0]["disponible"] is False
    assert estado[0]["motivo"] == "archivo_no_encontrado"


def test_las_clases_del_registro_coinciden_con_el_entrenamiento():
    """El registro repite las clases para no importar torch al arrancar: este test evita que
    queden desalineadas de src/dataset.py."""
    pytest.importorskip("torchxrayvision")
    from src.dataset import ETIQUETAS_A_IDX

    clases = DEFINICIONES["etapa0_region"]["clases"]
    assert {clase: i for i, clase in enumerate(clases)} == ETIQUETAS_A_IDX


def test_la_normalizacion_replicada_es_identica_a_la_de_torchxrayvision():
    xrv = pytest.importorskip("torchxrayvision")
    imagen = imagen_sintetica(512, 512)
    esperado = xrv.utils.normalize(imagen, maxval=255, reshape=True)
    obtenido = normalizar_rango_xrv(imagen)
    assert obtenido.dtype == esperado.dtype
    assert np.array_equal(obtenido, esperado)


def test_preparar_entrada_usa_el_mismo_preprocesamiento_que_el_entrenamiento(tmp_path):
    from src.preprocessing import normalizar_jpg_veterinario

    ruta = tmp_path / "sintetica.jpg"
    ruta.write_bytes(jpg_sintetico(700, 600))
    entrada = preparar_entrada(ruta)
    assert entrada.shape == (1, 1, 512, 512)
    assert entrada.dtype == np.float32
    assert np.array_equal(entrada[0], normalizar_rango_xrv(normalizar_jpg_veterinario(ruta)))


def _onnx_minimo(ruta, pesos):
    """Red de juguete (promedio global + capa lineal) con la misma firma que la Etapa 0."""
    onnx = pytest.importorskip("onnx")
    from onnx import TensorProto, helper, numpy_helper

    grafo = helper.make_graph(
        [
            helper.make_node("GlobalAveragePool", ["input"], ["promedio"]),
            helper.make_node("Flatten", ["promedio"], ["plano"]),
            helper.make_node("Gemm", ["plano", "pesos", "sesgo"], ["output"]),
        ],
        "juguete",
        [helper.make_tensor_value_info("input", TensorProto.FLOAT, ["n", 1, 512, 512])],
        [helper.make_tensor_value_info("output", TensorProto.FLOAT, ["n", 2])],
        [
            # Gemm con transB=0 (por defecto): A [n,1] @ B [1,2] -> [n,2]; de ahi (1, 2), no (2, 1).
            numpy_helper.from_array(np.array(pesos, dtype=np.float32).reshape(1, 2), "pesos"),
            numpy_helper.from_array(np.zeros(2, dtype=np.float32), "sesgo"),
        ],
    )
    modelo = helper.make_model(grafo, opset_imports=[helper.make_opsetid("", 18)])
    modelo.ir_version = 9
    onnx.save(modelo, str(ruta))


def test_modelo_onnx_de_juguete_predice_y_tiene_huella(tmp_path):
    """Ejercita ModeloOnnx de verdad (ONNX Runtime) sin los pesos reales, para que corra en CI."""
    pytest.importorskip("onnxruntime")
    ruta_modelo = tmp_path / "juguete.onnx"
    _onnx_minimo(ruta_modelo, pesos=[-0.01, 0.01])
    definiciones = {"juguete": {"papel": "region", "ruta": "juguete.onnx",
                                "clases": ["NO_TORAX", "TORAX"]}}
    registro = RegistroModelos.desde_definiciones(definiciones, raiz=tmp_path)
    (modelo,) = registro.disponibles("region")
    assert isinstance(modelo, ModeloOnnx)
    assert len(modelo.huella) == 64
    assert modelo.huella == modelos_ia.huella_sha256([ruta_modelo])

    ruta_imagen = tmp_path / "blanca.png"
    import cv2
    cv2.imwrite(str(ruta_imagen), np.full((600, 600), 255, dtype=np.uint8))
    prediccion = modelo.predecir(ruta_imagen)
    # Imagen blanca -> entrada 1024 -> logits (-10.24, 10.24) -> gana la clase 1.
    assert prediccion.etiqueta == "TORAX"
    assert prediccion.confianza > 0.99
    assert abs(sum(prediccion.probabilidades.values()) - 1) < 1e-5


def test_paridad_onnx_pytorch_con_entrada_sintetica(tmp_path):
    """FR-013: el ONNX exportado y el checkpoint original dan lo mismo para la misma entrada."""
    ruta_onnx = RAIZ / "models" / "etapa0_region.onnx"
    ruta_pt = RAIZ / "models" / "etapa0_region.pt"
    if not (ruta_onnx.exists() and ruta_pt.exists()):
        pytest.skip("faltan models/etapa0_region.onnx y .pt (no se versionan): paridad no verificada")
    torch = pytest.importorskip("torch")
    ort = pytest.importorskip("onnxruntime")
    from src.dataset import ETIQUETAS_A_IDX
    from src.model import build_model_etapa0

    ruta_imagen = tmp_path / "sintetica.jpg"
    ruta_imagen.write_bytes(jpg_sintetico(800, 700, semilla=11))
    entrada = preparar_entrada(ruta_imagen)

    sesion = ort.InferenceSession(str(ruta_onnx), providers=["CPUExecutionProvider"])
    salida_onnx = sesion.run(None, {sesion.get_inputs()[0].name: entrada})[0]

    modelo = build_model_etapa0(num_classes=len(ETIQUETAS_A_IDX))
    modelo.load_state_dict(torch.load(ruta_pt, map_location="cpu"))
    modelo.eval()
    with torch.no_grad():
        salida_pt = modelo(torch.from_numpy(entrada)).numpy()

    assert salida_onnx.shape == salida_pt.shape == (1, 2)
    assert np.allclose(salida_onnx, salida_pt, atol=1e-3), (salida_onnx, salida_pt)
    assert int(salida_onnx.argmax()) == int(salida_pt.argmax())
