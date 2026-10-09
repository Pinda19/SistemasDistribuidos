"""Modelo 0 — servidor SECUENCIAL (el de la semana 4).
Atiende UN cliente a la vez. Mientras atiende a uno, los demás esperan en la
cola de accept() del sistema operativo.
"""
import logging
import socket
from protocolo_comun import HOST, PUERTO, procesar

logging.basicConfig(level=logging.INFO, format="%(asctime)s [secuencial] %(message)s")
estado = {"contador": 0}


def atender(conn, addr):
    logging.info("conexion de %s", addr)
    conn.settimeout(60)
    with conn, conn.makefile("r", encoding="utf-8") as entrada:
        for linea in entrada:
            respuesta, seguir = procesar(linea, estado)
            conn.sendall((respuesta + "\n").encode("utf-8"))
            if not seguir:
                break
    logging.info("cierre de %s", addr)


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((HOST, PUERTO))
        srv.listen(16)
        logging.info("escuchando en %s:%s", HOST, PUERTO)
        while True:
            conn, addr = srv.accept()
            try:
                atender(conn, addr)          # <-- bloquea hasta que ESTE cliente termine
            except (ConnectionResetError, BrokenPipeError, socket.timeout) as e:
                logging.warning("cliente %s cayo: %s", addr, e.__class__.__name__)


if __name__ == "__main__":
    main()
