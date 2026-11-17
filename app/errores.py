"""Error de aplicacion con codigo estable y mensaje accionable.

El mensaje nunca repite un dato sensible (nombre de archivo, comentario del veterinario): solo
describe el problema y como resolverlo (spec 004, FR-010 y SC-003).
"""


class ErrorApp(Exception):
    def __init__(self, codigo, mensaje):
        super().__init__(mensaje)
        self.codigo = codigo
        self.mensaje = mensaje
