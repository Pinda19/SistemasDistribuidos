"""Modelo 1 — servidor PROCESO POR CLIENTE.
Cada accept() crea un proceso hijo. Los procesos NO comparten memoria:
cada uno tiene su propia copia de `estado`, por eso el contador "se reinicia"
en cada cliente. Es la misma característica que define a un sistema
distribuido (ausencia de memoria compartida), pero dentro de una máquina.
"""
import logging
import multiprocessing
import os
import socket
from protocolo_comun import HOST, PUERTO, procesar

logging.basicConfig(level=logging.INFO, format="%(asctime)s [procesos] pid=%(process)d %(message)s")
estado = {"contador": 0}


def atender(conn, addr):
    logging.info("conexion de %s", addr)
    conn.settimeout(60)
    try:
        with conn, conn.makefile("r", encoding="utf-8") as entrada:
            for linea in entrada:
                respuesta, seguir = procesar(linea, estado)
                conn.sendall((respuesta + "\n").encode("utf-8"))
                if not seguir:
                    break
    except (ConnectionResetError, BrokenPipeError, socket.timeout) as e:
        logging.warning("cliente %s cayo: %s", addr, e.__class__.__name__)
    finally:
        logging.info("cierre de %s | contador local=%s", addr, estado["contador"])


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((HOST, PUERTO))
        srv.listen(64)
        logging.info("escuchando en %s:%s (pid padre=%s)", HOST, PUERTO, os.getpid())
        while True:
            conn, addr = srv.accept()
            p = multiprocessing.Process(target=atender, args=(conn, addr), daemon=True)
            p.start()
            conn.close()                    # el padre suelta su copia del socket


if __name__ == "__main__":
    multiprocessing.set_start_method("fork")
    main()
