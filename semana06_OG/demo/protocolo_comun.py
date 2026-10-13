"""Protocolo de aplicación común a los cuatro servidores de la demo.

Protocolo por líneas, UTF-8, cada mensaje termina en "\n".
  HOLA <nombre>   -> OK HOLA <nombre>
  ECO <texto>     -> OK <texto>
  CONTAR          -> OK <n>           (incrementa un contador compartido)
  ESPERA <seg>    -> OK ESPERA <seg>  (operación lenta, simula trabajo)
  SALIR           -> OK CHAO          (el servidor cierra la conexión)
  otro            -> ERROR COMANDO_DESCONOCIDO

La función procesar() es la misma en los cuatro modelos de concurrencia.
Lo único que cambia entre servidores es QUIÉN ejecuta procesar() y CUÁNDO.
"""
import os
import time

PUERTO = int(os.environ.get("PUERTO", "5000"))
HOST = os.environ.get("HOST", "0.0.0.0")


def dormir(segundos):
    """Trabajo lento bloqueante (se reemplaza por asyncio.sleep en el asíncrono)."""
    time.sleep(segundos)


class SinLock:
    """Sustituto de un Lock que no bloquea nada (para observar la carrera)."""

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def procesar(linea, estado, dormir=dormir, lock=SinLock()):
    """Devuelve (respuesta, seguir). estado es un dict compartido con clave 'contador'.
    `lock` protege SOLO la sección crítica de CONTAR; ESPERA no se serializa."""
    partes = linea.strip().split(" ", 1)
    cmd = partes[0].upper() if partes and partes[0] else ""
    arg = partes[1] if len(partes) > 1 else ""

    if cmd == "HOLA":
        return f"OK HOLA {arg or 'anonimo'}", True
    if cmd == "ECO":
        return f"OK {arg}", True
    if cmd == "CONTAR":
        # Lectura, pausa y escritura separadas A PROPÓSITO para que la
        # condición de carrera sea observable cuando no hay Lock.
        with lock:                       # sección crítica: leer, pausar, escribir
            valor = estado["contador"]
            dormir(0.001)
            estado["contador"] = valor + 1
            nuevo = estado["contador"]
        return f"OK {nuevo}", True
    if cmd == "ESPERA":
        try:
            seg = float(arg)
        except ValueError:
            return "ERROR ESPERA_REQUIERE_SEGUNDOS", True
        dormir(seg)
        return f"OK ESPERA {arg}", True
    if cmd == "SALIR":
        return "OK CHAO", False
    return "ERROR COMANDO_DESCONOCIDO", True
