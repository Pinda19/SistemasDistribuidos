"""Cliente interactivo por lineas del protocolo de texto (el mismo de la Semana 6)."""
import os
import socket
import sys

HOST = os.environ.get("SERVIDOR_HOST", "servidor")
PUERTO = int(os.environ.get("SERVIDOR_PUERTO", "5000"))


def main():
    with socket.create_connection((HOST, PUERTO), timeout=5) as s:
        print(f"conectado a {HOST}:{PUERTO}. Escribe comandos (SALIR para terminar)")
        entrada = s.makefile("r", encoding="utf-8")
        for linea in sys.stdin:
            linea = linea.strip()
            if not linea:
                continue
            s.sendall((linea + "\n").encode("utf-8"))
            try:
                respuesta = entrada.readline()
            except socket.timeout:
                print("<< (sin respuesta en 5 s)")
                continue
            if not respuesta:
                print("<< (el servidor cerro la conexion)")
                break
            print("<<", respuesta.strip())
            if linea.upper() == "SALIR":
                break


if __name__ == "__main__":
    main()
