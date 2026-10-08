"""Servidor TCP secuencial — Sistemas Distribuidos FDICI25, semana 4.

Protocolo de texto, una línea por mensaje, terminada en \\n.
  HOLA <nombre>   -> OK hola <nombre>
  ECO <texto>     -> ECO <texto>
  CONTAR          -> OK <n>            (mensajes recibidos en ESTA conexión)
  SALIR           -> ADIOS             (el servidor cierra la conexión)
  otro            -> ERROR comando desconocido

Atiende UN cliente a la vez. Es a propósito: en la semana 6 lo harán concurrente.
"""
import socket
import sys
from datetime import datetime

HOST = "0.0.0.0"
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 5000


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def procesar(linea, estado):
    """Recibe una línea sin \\n y el estado de la conexión. Devuelve la respuesta."""
    estado["recibidos"] += 1
    partes = linea.split(" ", 1)
    comando = partes[0].upper()
    argumento = partes[1] if len(partes) > 1 else ""

    if comando == "HOLA":
        estado["nombre"] = argumento or "anónimo"
        return f"OK hola {estado['nombre']}"
    if comando == "ECO":
        return f"ECO {argumento}"
    if comando == "CONTAR":
        return f"OK {estado['recibidos']}"
    if comando == "SALIR":
        return "ADIOS"
    # --- Agreguen aquí la operación propia de su equipo (paso 3 del laboratorio) ---
    if comando == "ACUMULAR":
        try:
            numero = int(argumento)
        except ValueError:
            return "ERROR numero invalido"

        estado["acumulado"] += numero
        return f"OK acumulado {estado['acumulado']}"
    return "ERROR comando desconocido"


def atender(conn, addr):
    estado = {"recibidos": 0, "nombre": None, "acumulado": 0}
    log(f"conexión desde {addr[0]}:{addr[1]}")
    archivo = conn.makefile("r", encoding="utf-8", newline="\n")
    try:
        for linea in archivo:
            linea = linea.rstrip("\n")
            respuesta = procesar(linea, estado)
            log(f"  {addr[1]} <- {linea!r}  ->  {respuesta!r}")
            conn.sendall((respuesta + "\n").encode("utf-8"))
            if respuesta == "ADIOS":
                break
    except (ConnectionResetError, BrokenPipeError) as e:
        log(f"  {addr[1]} desconexión abrupta: {e.__class__.__name__}")
    finally:
        conn.close()
        log(f"cierre de {addr[0]}:{addr[1]} ({estado['recibidos']} mensajes)")


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((HOST, PORT))
        srv.listen(5)
        log(f"servidor escuchando en {HOST}:{PORT} (secuencial, un cliente a la vez)")
        while True:
            conn, addr = srv.accept()   # bloquea hasta que llega un cliente
            atender(conn, addr)         # y no vuelve a accept() hasta terminar con él


if __name__ == "__main__":
    main()
