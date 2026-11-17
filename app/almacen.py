"""Persistencia del MVP en SQLite + imagenes en disco (spec 004, FR-006 a FR-011).

Una base de un solo archivo y una carpeta de imagenes, sin ORM: alcanza para un MVP de un solo
usuario local y cualquiera del equipo puede leer el esquema entero en esta pantalla. La imagen se
guarda con el codigo del estudio como nombre: el nombre de archivo original nunca llega a disco
(FR-010).
"""
import json
import secrets
import sqlite3
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

from app.errores import ErrorApp

VERSION_ESQUEMA = 1

_ESQUEMA = """
CREATE TABLE IF NOT EXISTS version_esquema (version INTEGER NOT NULL);

CREATE TABLE IF NOT EXISTS estudio (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT NOT NULL UNIQUE,
    especie TEXT NOT NULL,
    formato TEXT NOT NULL,
    hash_contenido TEXT NOT NULL,
    duplicado_de TEXT,
    estado TEXT NOT NULL,
    region_etiqueta TEXT,
    region_confianza REAL,
    region_nivel TEXT,
    modelos_json TEXT NOT NULL,
    tiempo_inferencia_ms REAL NOT NULL,
    fecha_carga TEXT NOT NULL,
    fecha_cierre TEXT
);

CREATE TABLE IF NOT EXISTS hallazgo (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    estudio_codigo TEXT NOT NULL,
    origen TEXT NOT NULL,
    modelo TEXT,
    tipo TEXT NOT NULL,
    tipo_propuesto TEXT,
    confianza REAL,
    nivel TEXT,
    estado TEXT NOT NULL,
    comentario TEXT,
    fecha_decision TEXT
);
"""


def _ahora():
    return datetime.now(timezone.utc).isoformat()


def _limpio(texto):
    texto = (texto or "").strip()
    return texto or None


class Almacen:
    def __init__(self, ruta_base, dir_imagenes):
        self.ruta_base = Path(ruta_base)
        self.dir_imagenes = Path(dir_imagenes)
        self.ruta_base.parent.mkdir(parents=True, exist_ok=True)
        self.dir_imagenes.mkdir(parents=True, exist_ok=True)
        with self._conectar() as con:
            con.executescript(_ESQUEMA)
            if con.execute("SELECT COUNT(*) FROM version_esquema").fetchone()[0] == 0:
                con.execute("INSERT INTO version_esquema (version) VALUES (?)", (VERSION_ESQUEMA,))

    def _conectar(self):
        con = sqlite3.connect(self.ruta_base)
        con.row_factory = sqlite3.Row
        return con

    def nuevo_codigo(self):
        return "EST-" + secrets.token_hex(4).upper()

    def guardar_imagen(self, codigo, contenido, formato):
        self.dir_imagenes.mkdir(parents=True, exist_ok=True)
        (self.dir_imagenes / f"{codigo}.{formato}").write_bytes(contenido)

    def ruta_imagen(self, codigo):
        coincidencias = sorted(self.dir_imagenes.glob(f"{codigo}.*"))
        if not coincidencias:
            raise ErrorApp("estudio_no_encontrado", f"No se encontró la imagen del estudio {codigo}.")
        return coincidencias[0]

    # ---------------------------------------------------------------- creacion

    def crear_estudio(self, codigo, especie, formato, contenido, ancho, alto, region, modelos,
                      hallazgos):
        hash_contenido = sha256(contenido).hexdigest()
        tiempo_total = sum(float(m.get("tiempo_ms", 0.0)) for m in modelos)
        with self._conectar() as con:
            previo = con.execute(
                "SELECT codigo FROM estudio WHERE hash_contenido = ? ORDER BY id ASC LIMIT 1",
                (hash_contenido,)).fetchone()
            duplicado_de = previo["codigo"] if previo else None
            con.execute(
                "INSERT INTO estudio (codigo, especie, formato, hash_contenido, duplicado_de,"
                " estado, region_etiqueta, region_confianza, region_nivel, modelos_json,"
                " tiempo_inferencia_ms, fecha_carga, fecha_cierre)"
                " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,NULL)",
                (codigo, especie, formato, hash_contenido, duplicado_de, "borrador",
                 region.get("etiqueta"), region.get("confianza"), region.get("nivel"),
                 json.dumps(modelos, ensure_ascii=False), tiempo_total, _ahora()))
            for h in hallazgos:
                con.execute(
                    "INSERT INTO hallazgo (estudio_codigo, origen, modelo, tipo, tipo_propuesto,"
                    " confianza, nivel, estado, comentario, fecha_decision)"
                    " VALUES (?, 'modelo', ?, ?, ?, ?, ?, 'pendiente', NULL, NULL)",
                    (codigo, h.get("modelo"), h["tipo"], h["tipo"], h.get("confianza"),
                     h.get("nivel")))
        return self.obtener_estudio(codigo)

    # ---------------------------------------------------------------- lectura

    def _fila_estudio(self, con, codigo):
        fila = con.execute("SELECT * FROM estudio WHERE codigo = ?", (codigo,)).fetchone()
        if fila is None:
            raise ErrorApp("estudio_no_encontrado", f"No existe ningún estudio con el código {codigo}.")
        return fila

    def obtener_estudio(self, codigo):
        with self._conectar() as con:
            fila = self._fila_estudio(con, codigo)
            hallazgos = [dict(h) for h in con.execute(
                "SELECT * FROM hallazgo WHERE estudio_codigo = ? ORDER BY id ASC", (codigo,))]
            return {
                "codigo": fila["codigo"],
                "especie": fila["especie"],
                "formato": fila["formato"],
                "estado": fila["estado"],
                "duplicado_de": fila["duplicado_de"],
                "region": {"etiqueta": fila["region_etiqueta"], "confianza": fila["region_confianza"],
                          "nivel": fila["region_nivel"]},
                "modelos": json.loads(fila["modelos_json"]),
                "tiempo_inferencia_ms": fila["tiempo_inferencia_ms"],
                "fecha_carga": fila["fecha_carga"],
                "fecha_cierre": fila["fecha_cierre"],
                "hallazgos": hallazgos,
            }

    def listar_estudios(self, estado=None):
        with self._conectar() as con:
            if estado:
                filas = con.execute(
                    "SELECT * FROM estudio WHERE estado = ? ORDER BY fecha_carga DESC, id DESC",
                    (estado,)).fetchall()
            else:
                filas = con.execute(
                    "SELECT * FROM estudio ORDER BY fecha_carga DESC, id DESC").fetchall()
            resultado = []
            for fila in filas:
                estados_h = [h["estado"] for h in con.execute(
                    "SELECT estado FROM hallazgo WHERE estudio_codigo = ?", (fila["codigo"],))]
                resultado.append({
                    "codigo": fila["codigo"],
                    "estado": fila["estado"],
                    "especie": fila["especie"],
                    "fecha_carga": fila["fecha_carga"],
                    "region": {"etiqueta": fila["region_etiqueta"]},
                    "cantidad_hallazgos": len(estados_h),
                    "pendientes": sum(1 for e in estados_h if e == "pendiente"),
                })
            return resultado

    # ---------------------------------------------------------------- decisiones

    def _verificar_abierto(self, con, codigo):
        fila = self._fila_estudio(con, codigo)
        if fila["estado"] != "borrador":
            raise ErrorApp("estudio_cerrado", "El informe ya está cerrado y no se puede modificar.")
        return fila

    def _hallazgo_del_estudio(self, con, codigo, id_hallazgo):
        fila = con.execute(
            "SELECT * FROM hallazgo WHERE id = ? AND estudio_codigo = ?", (id_hallazgo, codigo)
        ).fetchone()
        if fila is None:
            raise ErrorApp("hallazgo_no_encontrado", "No existe ese hallazgo para este estudio.")
        return fila

    def decidir_hallazgo(self, codigo, id_hallazgo, accion, tipo=None, comentario=None):
        with self._conectar() as con:
            self._verificar_abierto(con, codigo)
            actual = self._hallazgo_del_estudio(con, codigo, id_hallazgo)
            ahora = _ahora()
            if accion == "corregir":
                nuevo_tipo = tipo if tipo else actual["tipo"]
                nuevo_comentario = _limpio(comentario)
                if nuevo_tipo == actual["tipo"] and nuevo_comentario == actual["comentario"]:
                    raise ErrorApp(
                        "correccion_sin_cambios",
                        "La corrección no cambia nada: elegí otro tipo de hallazgo o agregá un"
                        " comentario.")
                con.execute(
                    "UPDATE hallazgo SET estado='corregido', tipo=?, comentario=?, fecha_decision=?"
                    " WHERE id=?", (nuevo_tipo, nuevo_comentario, ahora, id_hallazgo))
            elif accion == "validar":
                con.execute(
                    "UPDATE hallazgo SET estado='validado', comentario=COALESCE(?, comentario),"
                    " fecha_decision=? WHERE id=?", (_limpio(comentario), ahora, id_hallazgo))
            elif accion == "descartar":
                con.execute(
                    "UPDATE hallazgo SET estado='descartado', comentario=COALESCE(?, comentario),"
                    " fecha_decision=? WHERE id=?", (_limpio(comentario), ahora, id_hallazgo))
            else:
                raise ErrorApp("accion_invalida", f"Acción no reconocida: {accion}.")
        return self.obtener_estudio(codigo)

    def agregar_hallazgo_manual(self, codigo, tipo, comentario):
        with self._conectar() as con:
            self._verificar_abierto(con, codigo)
            con.execute(
                "INSERT INTO hallazgo (estudio_codigo, origen, modelo, tipo, tipo_propuesto,"
                " confianza, nivel, estado, comentario, fecha_decision)"
                " VALUES (?, 'manual', NULL, ?, NULL, NULL, NULL, 'validado', ?, ?)",
                (codigo, tipo, _limpio(comentario), _ahora()))
            id_nuevo = con.execute("SELECT last_insert_rowid()").fetchone()[0]
        estudio = self.obtener_estudio(codigo)
        return next(h for h in estudio["hallazgos"] if h["id"] == id_nuevo)

    def cerrar_estudio(self, codigo):
        with self._conectar() as con:
            fila = self._fila_estudio(con, codigo)
            if fila["estado"] != "borrador":
                raise ErrorApp("estudio_cerrado", "El informe ya está cerrado.")
            hallazgos = [dict(h) for h in con.execute(
                "SELECT * FROM hallazgo WHERE estudio_codigo = ?", (codigo,))]
            pendientes = [h for h in hallazgos if h["estado"] == "pendiente"]
            if pendientes:
                tipos = sorted({h["tipo"].replace("_", " ").capitalize() for h in pendientes})
                raise ErrorApp(
                    "hallazgos_pendientes",
                    "No se puede cerrar el informe: todavía hay hallazgos sin revisar ("
                    + ", ".join(tipos) + "). Validá, corregí o descartá cada uno antes de cerrar.")
            vigentes = [h for h in hallazgos if h["estado"] in ("validado", "corregido")]
            if not vigentes:
                raise ErrorApp(
                    "informe_vacio",
                    "No se puede cerrar un informe sin ningún hallazgo vigente: agregá al menos uno"
                    " (puede ser \"sin hallazgos\") o validá uno de los propuestos.")
            con.execute("UPDATE estudio SET estado='validado', fecha_cierre=? WHERE codigo=?",
                       (_ahora(), codigo))
        return self.obtener_estudio(codigo)
