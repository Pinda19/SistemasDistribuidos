"""mensajes.py — esquema del protocolo (Semana 9).

Hasta la semana 7 el protocolo era "una línea de texto". Desde esta semana
cada mensaje es una estructura con campos definidos. El esquema es el mismo
sin importar el formato con que se codifique (JSON o binario).

Paso 1 del laboratorio: completar la lista OPERACIONES con las operaciones
del dominio del equipo (las de inventario son solo el ejemplo de referencia).
"""
from dataclasses import dataclass, field, asdict

VERSION = 2  # versión del protocolo que el servidor acepta

# Operaciones del dominio. Reemplacen las de inventario por las de su equipo.
OPERACIONES = ["HOLA", "ECO", "LISTAR", "AGREGAR", "QUITAR", "ESPERA", "SALIR"]


@dataclass
class Solicitud:
    operacion: str                       # nombre de la operación, por ejemplo "AGREGAR"
    argumentos: list = field(default_factory=list)  # lista de textos, por ejemplo ["tornillo", "25"]
    id: int = 0                          # correlativo que pone el cliente para parear la respuesta
    version: int = VERSION               # versión del protocolo

    def to_dict(self):
        return asdict(self)

    @staticmethod
    def from_dict(d):
        return Solicitud(
            operacion=str(d["operacion"]),
            argumentos=[str(a) for a in d.get("argumentos", [])],
            id=int(d.get("id", 0)),
            version=int(d.get("version", 0)),
        )


@dataclass
class Respuesta:
    id: int                              # mismo id de la solicitud
    estado: str                          # "OK" o "ERROR"
    datos: list = field(default_factory=list)  # resultado, lista de textos
    error: str = ""                      # mensaje legible cuando estado == "ERROR"

    def to_dict(self):
        return asdict(self)

    @staticmethod
    def from_dict(d):
        return Respuesta(
            id=int(d.get("id", 0)),
            estado=str(d["estado"]),
            datos=[str(x) for x in d.get("datos", [])],
            error=str(d.get("error", "")),
        )


def ok(solicitud, datos=None):
    return Respuesta(id=solicitud.id, estado="OK", datos=datos or [])


def error(solicitud_id, mensaje):
    return Respuesta(id=solicitud_id, estado="ERROR", error=mensaje)
