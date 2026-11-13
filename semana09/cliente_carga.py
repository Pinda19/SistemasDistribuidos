"""Prueba adicional: veinte clientes RepoSync con mismo HEAD, dos codecs."""
import argparse
import os
import socket
import threading
import time
import codec
from mensajes import Solicitud, Respuesta

HOST = os.environ.get("SERVIDOR_HOST", "servidor")
PUERTO = int(os.environ.get("SERVIDOR_PUERTO", "5000"))


def un_cliente(i, tokens, resultados):
    comienzo = time.perf_counter()
    try:
        with socket.create_connection((HOST, PUERTO), timeout=5) as sock:
            sock.settimeout(10)
            codec.enviar(sock, Solicitud(tokens[0], tokens[1:], id=i + 1))
            resp = codec.recibir(sock, Respuesta)
            estado = resp.estado
            detalle = " ".join(resp.datos) if estado == "OK" else resp.error
    except (OSError, ValueError, ConnectionError) as e:
        estado, detalle = "ERROR", f"{type(e).__name__}: {e}"
    resultados[i] = (time.perf_counter() - comienzo, estado, detalle)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--clientes", type=int, default=20)
    p.add_argument("--comando", default="PUSH proyecto main 0 simultaneo")
    a = p.parse_args()
    tokens = a.comando.split()
    if not tokens or not 1 <= a.clientes <= 200:
        raise SystemExit("Comando y cantidad de clientes válidos requeridos")
    resultados = {}
    hilos = [threading.Thread(target=un_cliente, args=(i, tokens, resultados)) for i in range(a.clientes)]
    inicio = time.perf_counter()
    for hilo in hilos:
        hilo.start()
    for hilo in hilos:
        hilo.join()
    for i, (segundos, estado, detalle) in sorted(resultados.items()):
        print(f"cliente {i}: {estado} {detalle} ({segundos:.3f}s)")
    correctos = sum(1 for _, estado, _ in resultados.values() if estado == "OK")
    print(f"CODEC={codec.CODEC} total={time.perf_counter()-inicio:.3f}s RESUMEN OK={correctos} ERROR={len(resultados)-correctos}")


if __name__ == "__main__":
    main()
