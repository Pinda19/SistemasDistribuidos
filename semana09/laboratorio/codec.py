"""codec.py — codificación y decodificación de mensajes (Semana 9).

Dos formatos para el mismo esquema de mensajes.py
  json   texto UTF-8 legible, tolerante a campos extra
  bin    binario compacto con struct, orden de bytes de red (big-endian)

Enmarcado (framing). Los dos formatos van precedidos por 4 bytes con el largo
del mensaje, así el receptor sabe cuántos bytes leer antes de decodificar.

    +----------+----------------------+
    | largo 4B |  mensaje (largo B)   |
    +----------+----------------------+

Paso 2 del laboratorio: completar codificar_bin / decodificar_bin.
"""
import json
import os
import struct

from mensajes import Solicitud, Respuesta

CODEC = os.environ.get("CODEC", "json")   # json | bin
LARGO = struct.Struct("!I")               # 4 bytes sin signo, big-endian
MAX_LARGO = 1_000_000                     # 1 MB, protege contra largos mentirosos

ESTADOS = {"OK": 0, "ERROR": 1}
ESTADOS_INV = {v: k for k, v in ESTADOS.items()}


# ---------------------------------------------------------------- JSON
def codificar_json(mensaje):
    return json.dumps(mensaje.to_dict(), ensure_ascii=False).encode("utf-8")


def decodificar_json(datos, clase):
    return clase.from_dict(json.loads(datos.decode("utf-8")))


# ---------------------------------------------------------------- BIN
def _texto(s):
    """Texto con largo prefijado de 2 bytes (máximo 65535 bytes)."""
    b = s.encode("utf-8")
    return struct.pack("!H", len(b)) + b


def _leer_texto(datos, pos):
    (n,) = struct.unpack_from("!H", datos, pos)
    pos += 2
    return datos[pos:pos + n].decode("utf-8"), pos + n


def _lista(items):
    return struct.pack("!B", len(items)) + b"".join(_texto(x) for x in items)


def _leer_lista(datos, pos):
    (n,) = struct.unpack_from("!B", datos, pos)
    pos += 1
    out = []
    for _ in range(n):
        x, pos = _leer_texto(datos, pos)
        out.append(x)
    return out, pos


def codificar_bin(mensaje):
    if isinstance(mensaje, Solicitud):
        # version 1B | id 4B | operacion (2B largo + texto) | argumentos (1B cantidad + textos)
        return (struct.pack("!BI", mensaje.version, mensaje.id)
                + _texto(mensaje.operacion)
                + _lista(mensaje.argumentos))
    if isinstance(mensaje, Respuesta):
        # TODO paso 2. Mismo patrón que la Solicitud, con este orden
        #   id 4B | estado 1B (ESTADOS) | datos (1B cantidad + textos) | error (2B largo + texto)
        raise NotImplementedError("codificar_bin(Respuesta) pendiente, paso 2")
    raise TypeError("mensaje desconocido")


def decodificar_bin(datos, clase):
    if clase is Solicitud:
        version, id_ = struct.unpack_from("!BI", datos, 0)
        operacion, pos = _leer_texto(datos, 5)
        argumentos, pos = _leer_lista(datos, pos)
        return Solicitud(operacion=operacion, argumentos=argumentos, id=id_, version=version)
    if clase is Respuesta:
        # TODO paso 2. Leer en el mismo orden en que se escribió. Pista,
        # struct.unpack_from("!IB", datos, 0) entrega (id, estado) y ocupa 5 bytes.
        raise NotImplementedError("decodificar_bin(Respuesta) pendiente, paso 2")
    raise TypeError("clase desconocida")


# ---------------------------------------------------------------- selector
CODECS = {
    "json": (codificar_json, decodificar_json),
    "bin": (codificar_bin, decodificar_bin),
}


def codificar(mensaje, codec=None):
    return CODECS[codec or CODEC][0](mensaje)


def decodificar(datos, clase, codec=None):
    return CODECS[codec or CODEC][1](datos, clase)


# ---------------------------------------------------------------- framing
def enviar(sock, mensaje, codec=None):
    cuerpo = codificar(mensaje, codec)
    sock.sendall(LARGO.pack(len(cuerpo)) + cuerpo)


def _recibir_exacto(sock, n):
    partes = b""
    while len(partes) < n:
        trozo = sock.recv(n - len(partes))
        if not trozo:
            raise ConnectionError("conexión cerrada por el otro extremo")
        partes += trozo
    return partes


def recibir(sock, clase, codec=None):
    (largo,) = LARGO.unpack(_recibir_exacto(sock, LARGO.size))
    if largo > MAX_LARGO:
        raise ValueError(f"largo anunciado inválido ({largo} bytes)")
    return decodificar(_recibir_exacto(sock, largo), clase, codec)


if __name__ == "__main__":
    # Prueba de ida y vuelta de los dos codecs
    s = Solicitud(operacion="AGREGAR", argumentos=["tornillo", "25"], id=7)
    r = Respuesta(id=7, estado="OK", datos=["tornillo=25"])
    pendientes = 0
    for nombre in CODECS:
        for etiqueta, msg, clase in (("solicitud", s, Solicitud), ("respuesta", r, Respuesta)):
            try:
                b = codificar(msg, nombre)
                assert decodificar(b, clase, nombre) == msg, "la ida y vuelta no devuelve el mismo mensaje"
                print(f"{nombre:5s} {etiqueta} {len(b):3d} bytes  {b!r}")
            except NotImplementedError as e:
                pendientes += 1
                print(f"{nombre:5s} {etiqueta}  PENDIENTE  ({e})")
    print("ida y vuelta OK en los dos codecs" if not pendientes else f"faltan {pendientes} funciones del paso 2")
