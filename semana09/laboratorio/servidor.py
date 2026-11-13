"""servidor.py — servidor TCP con hilo por cliente y mensajes estructurados (Semana 9).

Evoluciona el servidor de la semana 6/7. Cambia solo la forma de leer y
escribir mensajes. Antes, una línea de texto. Ahora, un mensaje enmarcado y
codificado con codec.py (JSON o binario según la variable CODEC).

El dominio de referencia es un inventario (LISTAR, AGREGAR, QUITAR). Cada
equipo reemplaza esas operaciones por las de su propio servicio.
"""
import json
import os
import socket
import struct
import threading
import time

import codec
from mensajes import Solicitud, VERSION, ok, error

HOST = "0.0.0.0"
PUERTO = int(os.environ.get("SERVIDOR_PUERTO", "5000"))
TIMEOUT = float(os.environ.get("TIMEOUT_SERVIDOR", "30"))

inventario = {}
lock = threading.Lock()


def log(*args):
    print(time.strftime("%H:%M:%S"), f"[{threading.current_thread().name}]", *args, flush=True)


# ---------------------------------------------------------------- dominio
def procesar(sol):
    """Recibe una Solicitud y devuelve una Respuesta. Aquí va el dominio del equipo."""
    op, args = sol.operacion.upper(), sol.argumentos
    if op == "HOLA":
        return ok(sol, ["Bienvenido al inventario v2"])
    if op == "ECO":
        return ok(sol, [" ".join(args)])
    if op == "LISTAR":
        with lock:
            return ok(sol, [f"{k}={v}" for k, v in sorted(inventario.items())])
    if op in ("AGREGAR", "QUITAR"):
        if len(args) != 2 or not args[1].lstrip("-").isdigit():
            return error(sol.id, f"{op} requiere producto y cantidad entera")
        producto, cantidad = args[0], int(args[1])
        if cantidad <= 0:
            return error(sol.id, "la cantidad debe ser positiva")
        with lock:
            actual = inventario.get(producto, 0)
            nuevo = actual + cantidad if op == "AGREGAR" else actual - cantidad
            if nuevo < 0:
                return error(sol.id, f"stock insuficiente de {producto} ({actual})")
            inventario[producto] = nuevo
        return ok(sol, [f"{producto}={nuevo}"])
    if op == "ESPERA":
        segundos = float(args[0]) if args else 1.0
        time.sleep(segundos)
        return ok(sol, [f"esperé {segundos} s"])
    if op == "SALIR":
        return ok(sol, ["chao"])
    return error(sol.id, f"operación desconocida {op}")


# ---------------------------------------------------------------- conexión
def atender(conn, addr):
    conn.settimeout(TIMEOUT)
    log("conectado", addr)
    try:
        while True:
            try:
                sol = codec.recibir(conn, Solicitud)
            except ConnectionError:
                break
            except (struct.error, json.JSONDecodeError, UnicodeDecodeError, ValueError, KeyError, IndexError) as e:
                # Mensaje mal formado. El servidor responde y cierra ESTA conexión, no muere.
                nombre = "struct.error" if isinstance(e, struct.error) else type(e).__name__
                log("mensaje mal formado desde", addr, "->", nombre, e)
                codec.enviar(conn, error(0, f"mensaje mal formado ({nombre})"))
                break
            if sol.version != VERSION:
                log("versión no soportada", sol.version, "desde", addr)
                codec.enviar(conn, error(sol.id, f"versión {sol.version} no soportada, use {VERSION}"))
                continue
            log("solicitud", sol.id, sol.operacion, sol.argumentos)
            resp = procesar(sol)
            codec.enviar(conn, resp)
            if sol.operacion.upper() == "SALIR":
                break
    except socket.timeout:
        log("timeout de", addr, "sin mensajes completos en", TIMEOUT, "s")
    except OSError as e:
        log("error de red con", addr, e)
    finally:
        conn.close()
        log("desconectado", addr)


def main():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((HOST, PUERTO))
    srv.listen(16)
    log(f"servidor inventario v{VERSION} en {HOST}:{PUERTO}  codec={codec.CODEC}  hilo por cliente")
    n = 0
    while True:
        conn, addr = srv.accept()
        n += 1
        threading.Thread(target=atender, args=(conn, addr), name=f"cli-{n}", daemon=True).start()


if __name__ == "__main__":
    main()
