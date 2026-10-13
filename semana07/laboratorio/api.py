"""Puerta HTTP (API REST) delante del servidor TCP de la Semana 6.

Cada peticion HTTP se TRADUCE a una linea del protocolo de texto, se envia
al servidor TCP y la respuesta se traduce de vuelta a JSON y a un codigo HTTP.

    GET  /items                  ->  LISTAR
    GET  /items/{item}           ->  LISTAR (y se filtra)
    POST /items/{item}/entradas  ->  AGREGAR <item> <cantidad>
    POST /items/{item}/salidas   ->  QUITAR  <item> <cantidad>

Plantilla del laboratorio, dominio de referencia INVENTARIO. Cada equipo
reemplaza los recursos por los de su dominio y mantiene la estructura
    pedir()     habla con el servidor TCP  (no se toca)
    traducir()  convierte OK / ERROR en datos o en un codigo HTTP  (no se toca)
    ERRORES     tabla codigo del protocolo -> codigo HTTP  (se adapta)
    recursos    una funcion por operacion expuesta  (se adapta)

La API NO guarda nada. Todo el estado sigue viviendo en el servidor TCP.
"""
import os
import socket

from fastapi import FastAPI, HTTPException, Path
from pydantic import BaseModel, Field

SERVIDOR_HOST = os.environ.get("SERVIDOR_HOST", "servidor")
SERVIDOR_PUERTO = int(os.environ.get("SERVIDOR_PUERTO", "5000"))
TIMEOUT_SERVIDOR = float(os.environ.get("TIMEOUT_SERVIDOR", "3"))
REPLICA = os.environ.get("REPLICA", socket.gethostname())

app = FastAPI(title="API de inventario", version="1.0",
              description="Puerta HTTP del servicio propio. Semana 7.")

ITEM = Path(pattern=r"^[a-z0-9_]{1,30}$", description="nombre del item, sin espacios")

# Codigo de error del protocolo de texto  ->  codigo de estado HTTP
ERRORES = {
    "ITEM_NO_EXISTE": 404,          # el recurso no existe
    "STOCK_INSUFICIENTE": 409,      # la peticion es valida pero choca con el estado actual
    "FORMATO": 400,                 # la peticion esta mal armada
    "COMANDO_DESCONOCIDO": 501,     # el servidor no implementa esa operacion
}


class Movimiento(BaseModel):
    cantidad: int = Field(gt=0, description="unidades, entero mayor que cero")


# ----------------------------------------------------------------- hablar con el nivel de datos
def pedir(linea: str) -> str:
    """Envia UNA linea al nivel de datos y devuelve UNA linea de respuesta."""
    try:
        with socket.create_connection((SERVIDOR_HOST, SERVIDOR_PUERTO),
                                      timeout=TIMEOUT_SERVIDOR) as s:
            s.sendall((linea + "\n").encode("utf-8"))
            respuesta = s.makefile("r", encoding="utf-8").readline().strip()
    except socket.timeout:
        raise HTTPException(504, {"error": "SERVIDOR_NO_RESPONDE", "replica": REPLICA})
    except OSError as e:                     # no resuelve el nombre, conexion rechazada, red caida
        raise HTTPException(503, {"error": "SERVIDOR_NO_DISPONIBLE",
                                  "detalle": e.__class__.__name__, "replica": REPLICA})
    if not respuesta:
        raise HTTPException(503, {"error": "SERVIDOR_CERRO_LA_CONEXION", "replica": REPLICA})
    return respuesta


def traducir(respuesta: str) -> list[str]:
    """'OK a b c' -> ['a','b','c'].  'ERROR CODIGO detalle' -> excepcion HTTP."""
    partes = respuesta.split()
    if partes[0] == "OK":
        return partes[1:]
    codigo = partes[1] if len(partes) > 1 else "DESCONOCIDO"
    raise HTTPException(ERRORES.get(codigo, 500),
                        {"error": codigo, "detalle": " ".join(partes[2:]), "replica": REPLICA})


def inventario() -> dict[str, int]:
    pares = (p.split(":") for p in traducir(pedir("LISTAR")))
    return {nombre: int(cantidad) for nombre, cantidad in pares}


# ----------------------------------------------------------------- recursos
@app.get("/salud")
def salud():
    return {"estado": "ok", "replica": REPLICA}


@app.get("/items")
def listar_items():
    return {"items": inventario(), "replica": REPLICA}


@app.get("/items/{item}")
def ver_item(item: str = ITEM):
    items = inventario()
    if item not in items:
        raise HTTPException(404, {"error": "ITEM_NO_EXISTE", "replica": REPLICA})
    return {"item": item, "cantidad": items[item], "replica": REPLICA}


@app.post("/items/{item}/entradas", status_code=201)
def registrar_entrada(mov: Movimiento, item: str = ITEM):
    nombre, total = traducir(pedir(f"AGREGAR {item} {mov.cantidad}"))
    return {"item": nombre, "cantidad": int(total), "replica": REPLICA}


@app.post("/items/{item}/salidas", status_code=201)
def registrar_salida(mov: Movimiento, item: str = ITEM):
    nombre, total = traducir(pedir(f"QUITAR {item} {mov.cantidad}"))
    return {"item": nombre, "cantidad": int(total), "replica": REPLICA}
