"""Servidor TCP concurrente — plantilla de la Semana 6 (hilo por cliente).

Dominio de referencia: INVENTARIO (equipo E-commerce). Cada equipo reemplaza
las operaciones por las de su propio dominio, manteniendo la estructura:
  - un hilo por cliente
  - estado compartido protegido por un Lock
  - manejo explícito de errores y desconexión abrupta
  - logging con identificador del cliente en cada línea

Protocolo por líneas, UTF-8, terminador "\n". Ver protocolo.md.
"""
import logging
import os
import socket
import threading
import time

HOST = os.environ.get("HOST", "0.0.0.0")
PUERTO = int(os.environ.get("PUERTO", "5000"))
SIN_LOCK = os.environ.get("SIN_LOCK", "0") == "1"
TIMEOUT_CLIENTE = int(os.environ.get("TIMEOUT_CLIENTE", "60"))

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [servidor] %(threadName)s %(message)s")

# ----------------------------------------------------------------- estado compartido
estado = {"inventario": {"manzana": 100, "pera": 100}, "operaciones": 0}
lock = threading.Lock()


class SinLock:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def seccion_critica():
    return SinLock() if SIN_LOCK else lock


# ----------------------------------------------------------------- operaciones del dominio
def op_listar(arg):
    with seccion_critica():
        items = " ".join(f"{k}:{v}" for k, v in sorted(estado["inventario"].items()))
    return f"OK {items}"


def op_agregar(arg):
    partes = arg.split()
    if len(partes) != 2 or not partes[1].isdigit():
        return "ERROR FORMATO AGREGAR <item> <cantidad>"
    item, cant = partes[0].lower(), int(partes[1])
    with seccion_critica():
        actual = estado["inventario"].get(item, 0)
        time.sleep(0.001)                      # ventana para observar la carrera sin Lock
        estado["inventario"][item] = actual + cant
        nuevo = estado["inventario"][item]
    return f"OK {item} {nuevo}"


def op_quitar(arg):
    partes = arg.split()
    if len(partes) != 2 or not partes[1].isdigit():
        return "ERROR FORMATO QUITAR <item> <cantidad>"
    item, cant = partes[0].lower(), int(partes[1])
    with seccion_critica():
        actual = estado["inventario"].get(item)
        if actual is None:
            return "ERROR ITEM_NO_EXISTE"
        if actual < cant:
            return f"ERROR STOCK_INSUFICIENTE {actual}"
        time.sleep(0.001)
        estado["inventario"][item] = actual - cant
        nuevo = estado["inventario"][item]
    return f"OK {item} {nuevo}"


def op_espera(arg):
    try:
        seg = float(arg)
    except ValueError:
        return "ERROR FORMATO ESPERA <segundos>"
    time.sleep(seg)                            # operación lenta, NO toma el Lock
    return f"OK ESPERA {arg}"


OPERACIONES = {
    "LISTAR": op_listar,
    "AGREGAR": op_agregar,
    "QUITAR": op_quitar,
    "ESPERA": op_espera,
}


def procesar(linea):
    """Devuelve (respuesta, seguir)."""
    partes = linea.strip().split(" ", 1)
    cmd = partes[0].upper() if partes and partes[0] else ""
    arg = partes[1] if len(partes) > 1 else ""
    if cmd == "HOLA":
        return f"OK HOLA {arg or 'anonimo'}", True
    if cmd == "SALIR":
        return "OK CHAO", False
    if cmd in OPERACIONES:
        with seccion_critica():
            estado["operaciones"] += 1
        return OPERACIONES[cmd](arg), True
    return "ERROR COMANDO_DESCONOCIDO", True


# ----------------------------------------------------------------- atención de un cliente
def atender(conn, addr):
    logging.info("conexion de %s", addr)
    conn.settimeout(TIMEOUT_CLIENTE)
    try:
        with conn, conn.makefile("r", encoding="utf-8", errors="replace") as entrada:
            for linea in entrada:
                respuesta, seguir = procesar(linea)
                conn.sendall((respuesta + "\n").encode("utf-8"))
                if not seguir:
                    break
    except (ConnectionResetError, BrokenPipeError) as e:
        logging.warning("cliente %s se desconecto abruptamente (%s)", addr, e.__class__.__name__)
    except socket.timeout:
        logging.warning("cliente %s inactivo %ss, cerrando", addr, TIMEOUT_CLIENTE)
    except Exception as e:  # noqa: BLE001  — un cliente nunca puede botar el servidor
        logging.error("error inesperado con %s: %r", addr, e)
    finally:
        logging.info("cierre de %s | operaciones=%s", addr, estado["operaciones"])


def main():
    logging.info("SIN_LOCK=%s timeout=%ss", SIN_LOCK, TIMEOUT_CLIENTE)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((HOST, PUERTO))
        srv.listen(64)
        logging.info("escuchando en %s:%s", HOST, PUERTO)
        while True:
            conn, addr = srv.accept()
            threading.Thread(target=atender, args=(conn, addr),
                             name=f"cli-{addr[1]}", daemon=True).start()


if __name__ == "__main__":
    main()
