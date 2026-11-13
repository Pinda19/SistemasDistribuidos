"""RepoSync Semana 9: servidor TCP concurrente con mensajes JSON o binarios.

A diferencia de Semana 7, procesar() recibe una Solicitud estructurada y
retorna una Respuesta estructurada. La lógica de dominio no cambia.
"""
import json
import os
import socket
import struct
import threading
import time

import codec
from mensajes import Solicitud, VERSION, OPERACIONES, ok, error

HOST = "0.0.0.0"
PUERTO = int(os.environ.get("SERVIDOR_PUERTO", "5000"))
TIMEOUT = float(os.environ.get("TIMEOUT_SERVIDOR", "30"))
PAUSA_CARRERA = float(os.environ.get("PAUSA_CARRERA", "0"))

estado = {
    "repos": {
        "proyecto": {
            "ramas": {"main": 0},
            "commits": {0: {"padre": None, "mensaje": "inicio"}},
            "siguiente": 1,
        }
    },
    "operaciones": 0,
}
lock = threading.Lock()


def log(*args):
    print(time.strftime("%H:%M:%S"), f"[{threading.current_thread().name}]", *args, flush=True)


def procesar(sol: Solicitud):
    """Recibe Solicitud y retorna Respuesta, manteniendo el dominio RepoSync."""
    op, args = sol.operacion.upper(), sol.argumentos

    if op not in OPERACIONES:
        return error(sol.id, "COMANDO_DESCONOCIDO")
    if op == "HOLA":
        return ok(sol, ["HOLA", args[0] if args else "anonimo"])
    if op == "SALIR":
        return ok(sol, ["CHAO"])

    with lock:
        estado["operaciones"] += 1

    if op == "ESPERA":
        try:
            if len(args) != 1:
                raise ValueError
            segundos = float(args[0])
            if not 0 <= segundos <= 10:
                raise ValueError
        except ValueError:
            return error(sol.id, "FORMATO ESPERA <segundos>")
        time.sleep(segundos)  # fuera del Lock
        return ok(sol, ["ESPERA", args[0]])

    if op == "REPOS":
        if args:
            return error(sol.id, "FORMATO REPOS")
        with lock:
            return ok(sol, sorted(estado["repos"]))

    if op in ("CLONAR", "HISTORIAL"):
        if len(args) != 2:
            return error(sol.id, f"FORMATO {op} <repo> <rama>")
        nombre, rama = args
        with lock:
            repo = estado["repos"].get(nombre)
            if repo is None:
                return error(sol.id, "REPO_NO_EXISTE")
            if rama not in repo["ramas"]:
                return error(sol.id, "RAMA_NO_EXISTE")
            cabeza = repo["ramas"][rama]
            if op == "CLONAR":
                return ok(sol, [nombre, rama, f"HEAD={cabeza}"])
            entradas = []
            while cabeza is not None and len(entradas) < 10:
                commit = repo["commits"].get(cabeza)
                if commit is None:
                    return error(sol.id, "HISTORIAL_INCONSISTENTE")
                entradas.append(f'{cabeza}:{commit["mensaje"]}')
                cabeza = commit["padre"]
            return ok(sol, entradas)

    if op == "RAMA":
        if len(args) != 3:
            return error(sol.id, "FORMATO RAMA <repo> <nueva> <origen>")
        nombre, nueva, origen = args
        with lock:
            repo = estado["repos"].get(nombre)
            if repo is None:
                return error(sol.id, "REPO_NO_EXISTE")
            if origen not in repo["ramas"]:
                return error(sol.id, "RAMA_NO_EXISTE")
            if nueva in repo["ramas"]:
                return error(sol.id, "RAMA_EXISTE")
            repo["ramas"][nueva] = repo["ramas"][origen]
            return ok(sol, ["RAMA", nueva, f'HEAD={repo["ramas"][nueva]}'])

    if op == "PUSH":
        if len(args) < 4 or not args[2].isdigit():
            return error(sol.id, "FORMATO PUSH <repo> <rama> <base> <mensaje>")
        nombre, rama, base_str = args[:3]
        base = int(base_str)
        mensaje = " ".join(args[3:]).strip()
        if not mensaje or len(mensaje) > 80:
            return error(sol.id, "FORMATO PUSH <repo> <rama> <base> <mensaje>")
        with lock:
            repo = estado["repos"].get(nombre)
            if repo is None:
                return error(sol.id, "REPO_NO_EXISTE")
            if rama not in repo["ramas"]:
                return error(sol.id, "RAMA_NO_EXISTE")
            actual = repo["ramas"][rama]
            if base != actual:
                return error(sol.id, f"CONFLICTO HEAD={actual}")
            if PAUSA_CARRERA > 0:
                time.sleep(PAUSA_CARRERA)
            nuevo = repo["siguiente"]
            repo["siguiente"] = nuevo + 1
            repo["commits"][nuevo] = {"padre": base, "mensaje": mensaje}
            repo["ramas"][rama] = nuevo
            return ok(sol, ["PUSH", rama, f"HEAD={nuevo}"])

    return error(sol.id, "COMANDO_DESCONOCIDO")


def atender(conn, addr):
    conn.settimeout(TIMEOUT)
    log("conectado", addr, "codec", codec.CODEC)
    try:
        while True:
            try:
                sol = codec.recibir(conn, Solicitud)
            except ConnectionError:
                break
            except (struct.error, json.JSONDecodeError, UnicodeDecodeError,
                    ValueError, KeyError, IndexError, TypeError) as e:
                log("mensaje mal formado desde", addr, "->", type(e).__name__, e)
                try:
                    codec.enviar(conn, error(0, f"mensaje mal formado ({type(e).__name__})"))
                except OSError:
                    pass
                break  # cierra solo esta conexión, no el servidor
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
        log("timeout de", addr, "sin mensaje completo en", TIMEOUT, "s")
    except OSError as e:
        log("error de red con", addr, e)
    finally:
        conn.close()
        log("desconectado", addr)


def main():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((HOST, PUERTO))
    srv.listen(64)
    log(f"RepoSync v{VERSION} en {HOST}:{PUERTO} codec={codec.CODEC} hilo por cliente + Lock")
    n = 0
    while True:
        conn, addr = srv.accept()
        n += 1
        threading.Thread(target=atender, args=(conn, addr),
                         name=f"cli-{n}", daemon=True).start()


if __name__ == "__main__":
    main()
