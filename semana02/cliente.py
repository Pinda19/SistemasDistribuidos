"""Cliente TCP que realiza N llamadas remotas y mide cuánto tarda cada una.
Variables de entorno:
  SERVIDOR_HOST  nombre del contenedor servidor (por defecto: servidor)
  PUERTO         puerto TCP (por defecto: 5000)
  N_LLAMADAS     cantidad de llamadas (por defecto: 100)
  TIMEOUT_S      segundos de espera máxima; 0 = esperar para siempre
"""
import os
import socket
import statistics
import sys
import time

HOST = os.getenv("SERVIDOR_HOST", "servidor")
PUERTO = int(os.getenv("PUERTO", "5000"))
N = int(os.getenv("N_LLAMADAS", "100"))
TIMEOUT = float(os.getenv("TIMEOUT_S", "0")) or None

tiempos_ms = []
try:
    with socket.create_connection((HOST, PUERTO), timeout=TIMEOUT) as s:
        s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        f = s.makefile("rwb")
        inicio = time.perf_counter()
        for i in range(1, N + 1):
            t0 = time.perf_counter()
            f.write(f"PING {i}\n".encode())
            f.flush()
            respuesta = f.readline()          # <- aquí el cliente ESPERA a la red
            tiempos_ms.append((time.perf_counter() - t0) * 1000)
            if not respuesta:
                print("[cliente] el servidor cerró la conexión")
                sys.exit(1)
        total = time.perf_counter() - inicio
except socket.timeout:
    print(f"[cliente] TIMEOUT tras {TIMEOUT}s esperando al servidor "
          f"({len(tiempos_ms)} llamadas completadas)")
    sys.exit(2)
except OSError as e:
    print(f"[cliente] error de red: {e}")
    sys.exit(3)

print(f"llamadas={N} total={total:.3f}s "
      f"promedio={statistics.mean(tiempos_ms):.1f}ms "
      f"min={min(tiempos_ms):.1f}ms max={max(tiempos_ms):.1f}ms")
