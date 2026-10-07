"""Servidor TCP mínimo para el Laboratorio N°1 (Semana 2).
Responde "PONG n" a cada línea "PING n". No modificar: es la caja negra
que el equipo mide esta semana; en la Semana 4 construirán el suyo.
"""
import os
import socket
import time

HOST = "0.0.0.0"
PUERTO = int(os.getenv("PUERTO", "5000"))
# Plan B: si `tc` no está disponible, el servidor puede simular latencia.
LATENCIA_SIMULADA = int(os.getenv("SIMULAR_LATENCIA_MS", "0")) / 1000

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PUERTO))
    s.listen()
    print(f"[servidor] escuchando en {HOST}:{PUERTO}", flush=True)
    while True:
        conn, addr = s.accept()
        with conn:
            conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            print(f"[servidor] conexión desde {addr}", flush=True)
            f = conn.makefile("rwb")
            for linea in f:
                if LATENCIA_SIMULADA:
                    time.sleep(LATENCIA_SIMULADA)
                numero = linea.strip()[5:]          # b"PING 7" -> b"7"
                f.write(b"PONG " + numero + b"\n")
                f.flush()
            print(f"[servidor] {addr} cerró la conexión", flush=True)
