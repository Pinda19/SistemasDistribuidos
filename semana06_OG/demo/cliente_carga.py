"""Cliente de carga: abre N conexiones SIMULTÁNEAS y mide cuánto tarda cada una
y el total. Sirve para comparar los modelos de concurrencia y para provocar
condiciones de carrera con CONTAR.

Uso:
  python cliente_carga.py --clientes 5 --comando "ESPERA 2"
  python cliente_carga.py --clientes 20 --comando CONTAR --repeticiones 50
"""
import argparse
import os
import socket
import threading
import time

HOST = os.environ.get("SERVIDOR_HOST", "servidor")
PUERTO = int(os.environ.get("SERVIDOR_PUERTO", "5000"))


def un_cliente(i, comando, repeticiones, resultados, saludo, cierre):
    inicio = time.perf_counter()
    ultima = ""
    en_fila = 0.0       # desde connect() hasta la primera respuesta del servidor
    operacion = 0.0     # desde que se envía el comando hasta que llega su respuesta
    try:
        with socket.create_connection((HOST, PUERTO), timeout=120) as s:
            f = s.makefile("r", encoding="utf-8")
            if saludo:
                s.sendall((saludo.replace("{i}", str(i)) + "\n").encode())
                f.readline()
                en_fila = time.perf_counter() - inicio
            t_op = time.perf_counter()
            for _ in range(repeticiones):
                s.sendall((comando + "\n").encode())
                ultima = f.readline().strip()
            operacion = time.perf_counter() - t_op
            if cierre:
                s.sendall((cierre + "\n").encode())
                f.readline()
    except Exception as e:  # noqa: BLE001
        ultima = f"ERROR_CLIENTE {e.__class__.__name__}"
    resultados[i] = (time.perf_counter() - inicio, en_fila, operacion, ultima)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--clientes", type=int, default=5)
    ap.add_argument("--comando", default="ESPERA 2")
    ap.add_argument("--repeticiones", type=int, default=1)
    ap.add_argument("--saludo", default="HOLA carga{i}", help="mensaje inicial ('' para omitir)")
    ap.add_argument("--cierre", default="SALIR", help="mensaje final ('' para omitir)")
    args = ap.parse_args()

    resultados = {}
    hilos = [threading.Thread(target=un_cliente, args=(i, args.comando, args.repeticiones, resultados, args.saludo, args.cierre))
             for i in range(args.clientes)]
    t0 = time.perf_counter()
    for h in hilos:
        h.start()
    for h in hilos:
        h.join()
    total = time.perf_counter() - t0

    print(f"servidor={HOST}:{PUERTO} clientes={args.clientes} comando='{args.comando}' repeticiones={args.repeticiones}")
    print("  cliente   en fila   operacion      total   ultima respuesta")
    for i in sorted(resultados, key=lambda k: resultados[k][0]):
        dur, en_fila, operacion, ultima = resultados[i]
        print(f"  {i:7d}  {en_fila:6.2f} s  {operacion:6.2f} s  {dur:6.2f} s   {ultima}")
    print(f"TOTAL: {total:.2f} s")
    if args.comando.upper() == "CONTAR":
        esperado = args.clientes * args.repeticiones
        print(f"valor esperado del contador si no hubo carrera: {esperado} (suma acumulada desde el inicio del servidor)")


if __name__ == "__main__":
    main()
