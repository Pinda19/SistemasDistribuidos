"""cliente.py — cliente TCP con mensajes estructurados (Semana 9).

Uso
  python cliente.py                      modo interactivo, una operación por línea
  python cliente.py AGREGAR tornillo 25  una sola operación y sale

El codec se toma de la variable CODEC (json | bin) y debe coincidir con el
del servidor. Si no coincide, van a ver qué pasa en el paso 5.
"""
import os
import socket
import sys

import codec
from mensajes import Solicitud, Respuesta

HOST = os.environ.get("SERVIDOR_HOST", "servidor")
PUERTO = int(os.environ.get("SERVIDOR_PUERTO", "5000"))
TIMEOUT = float(os.environ.get("TIMEOUT_CLIENTE", "5"))

correlativo = 0


def llamar(sock, operacion, argumentos):
    global correlativo
    correlativo += 1
    sol = Solicitud(operacion=operacion, argumentos=argumentos, id=correlativo)
    codec.enviar(sock, sol)
    resp = codec.recibir(sock, Respuesta)
    if resp.id != sol.id:
        print(f"  ! la respuesta trae id {resp.id} y esperaba {sol.id}")
    return resp


def mostrar(resp):
    if resp.estado == "OK":
        print("  OK", " | ".join(resp.datos) if resp.datos else "(sin datos)")
    else:
        print("  ERROR", resp.error)


def main():
    sock = socket.create_connection((HOST, PUERTO), timeout=TIMEOUT)
    print(f"conectado a {HOST}:{PUERTO} con codec={codec.CODEC} (timeout {TIMEOUT} s)")
    try:
        if len(sys.argv) > 1:
            mostrar(llamar(sock, sys.argv[1], sys.argv[2:]))
            return
        while True:
            try:
                linea = input("> ").strip()
            except EOFError:
                break
            if not linea:
                continue
            partes = linea.split()
            resp = llamar(sock, partes[0], partes[1:])
            mostrar(resp)
            if partes[0].upper() == "SALIR":
                break
    except socket.timeout:
        print(f"  ! sin respuesta en {TIMEOUT} s, el servidor no contestó (comunicación transiente, el mensaje se perdió)")
    except ConnectionRefusedError:
        print("  ! conexión rechazada, no hay nadie escuchando en el puerto")
    except ConnectionError as e:
        print("  !", e)
    finally:
        sock.close()


if __name__ == "__main__":
    main()
