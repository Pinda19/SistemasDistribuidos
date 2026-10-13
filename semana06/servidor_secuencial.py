"""RepoSync secuencial: misma lógica y protocolo, una conexión por vez."""
import logging
import socket
from servidor import HOST, PUERTO, atender


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((HOST, PUERTO))
        srv.listen(64)
        logging.info('RepoSync SECUENCIAL escuchando en %s:%s', HOST, PUERTO)
        while True:
            conn, addr = srv.accept()
            atender(conn, addr)


if __name__ == '__main__':
    main()
