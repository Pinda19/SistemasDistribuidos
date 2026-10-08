"""Cliente TCP — Sistemas Distribuidos FDICI25, semana 4.

Uso:
  python cliente.py                      modo interactivo (escriben comandos, Enter envía)
  python cliente.py --guion              envía una secuencia fija y termina
  python cliente.py servidor 5000        host y puerto explícitos

El servidor se ubica por NOMBRE (resolución DNS de la red Docker sd_net), nunca por localhost.
"""
import socket
import sys
import time

HOST = "servidor"
PORT = 5000
TIMEOUT = 5.0   # segundos que esperamos una respuesta antes de rendirnos

GUION = ["HOLA equipo", "ECO hola mundo", "CONTAR", "NOEXISTE", "ACUMULAR 3", "ACUMULAR 5","SALIR"]


def enviar(sock, archivo, mensaje):
    t0 = time.perf_counter()
    sock.sendall((mensaje + "\n").encode("utf-8"))
    respuesta = archivo.readline()
    ms = (time.perf_counter() - t0) * 1000
    if respuesta == "":
        raise ConnectionError("el servidor cerró la conexión sin responder")
    print(f"  > {mensaje}\n  < {respuesta.rstrip()}   ({ms:.1f} ms)")
    return respuesta.rstrip()


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    host = args[0] if len(args) > 0 else HOST
    port = int(args[1]) if len(args) > 1 else PORT
    guion = "--guion" in sys.argv

    print(f"conectando a {host}:{port} ...")
    with socket.create_connection((host, port), timeout=TIMEOUT) as sock:
        print(f"conectado desde {sock.getsockname()[0]}:{sock.getsockname()[1]}")
        archivo = sock.makefile("r", encoding="utf-8", newline="\n")
        try:
            if guion:
                for m in GUION:
                    if enviar(sock, archivo, m) == "ADIOS":
                        break
            else:
                print("escriban comandos (HOLA, ECO, CONTAR, SALIR). Ctrl+C para cortar de golpe.")
                while True:
                    m = input("> ").strip()
                    if not m:
                        continue
                    if enviar(sock, archivo, m) == "ADIOS":
                        break
        except socket.timeout:
            print(f"TIMEOUT: el servidor no respondió en {TIMEOUT:.0f} s. ¿Caído, sin red o lento? No se puede saber.")
        except (ConnectionResetError, BrokenPipeError, ConnectionError) as e:
            print(f"CONEXIÓN PERDIDA: {e.__class__.__name__}: {e}")
        except (KeyboardInterrupt, EOFError):
            print("\ncorte abrupto desde el cliente (sin SALIR)")


if __name__ == "__main__":
    main()
