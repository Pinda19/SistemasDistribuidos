"""Modelo 2 — servidor HILO POR CLIENTE.
Cada accept() crea un hilo que atiende a ese cliente. Todos los hilos
comparten la misma memoria, por eso el contador necesita un Lock.
Con SIN_LOCK=1 el Lock se desactiva para observar la condición de carrera.
"""
import logging
import os
import socket
import threading
from protocolo_comun import HOST, PUERTO, SinLock, procesar

logging.basicConfig(level=logging.INFO, format="%(asctime)s [hilos] %(threadName)s %(message)s")
estado = {"contador": 0}
SIN_LOCK = os.environ.get("SIN_LOCK", "0") == "1"
lock = SinLock() if SIN_LOCK else threading.Lock()   # el Lock protege solo CONTAR


def atender(conn, addr):
    logging.info("conexion de %s", addr)
    conn.settimeout(60)
    try:
        with conn, conn.makefile("r", encoding="utf-8") as entrada:
            for linea in entrada:
                respuesta, seguir = procesar(linea, estado, lock=lock)
                conn.sendall((respuesta + "\n").encode("utf-8"))
                if not seguir:
                    break
    except (ConnectionResetError, BrokenPipeError) as e:
        logging.warning("cliente %s se desconecto abruptamente (%s)", addr, e.__class__.__name__)
    except socket.timeout:
        logging.warning("cliente %s inactivo, cerrando por timeout", addr)
    finally:
        logging.info("cierre de %s | contador=%s", addr, estado["contador"])


def main():
    logging.info("SIN_LOCK=%s", SIN_LOCK)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((HOST, PUERTO))
        srv.listen(64)
        logging.info("escuchando en %s:%s", HOST, PUERTO)
        while True:
            conn, addr = srv.accept()
            t = threading.Thread(target=atender, args=(conn, addr), daemon=True)
            t.start()                       # <-- vuelve de inmediato al accept()


if __name__ == "__main__":
    main()
