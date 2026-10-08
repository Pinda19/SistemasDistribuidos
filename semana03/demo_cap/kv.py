#!/usr/bin/env python3
"""kv.py — réplica mínima de un almacén clave-valor para la demo del teorema CAP.

Dos réplicas (replica_a y replica_b) se sincronizan entre sí por HTTP.
La variable MODO decide qué sacrifica la réplica cuando no alcanza a su par:
  MODO=AP  -> sigue respondiendo (Disponibilidad), aunque el dato quede desactualizado.
  MODO=CP  -> rechaza la operación con 503 (Consistencia), antes que responder mal.

Solo biblioteca estándar: http.server + urllib. Sin dependencias externas.
"""
import json
import os
import sys
import urllib.request
import urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

NOMBRE = os.environ.get("NOMBRE", "replica")
PEER = os.environ.get("PEER", "")            # p. ej. http://peer_b:8000
MODO = os.environ.get("MODO", "AP").upper()  # AP o CP
PUERTO = int(os.environ.get("PUERTO", "8000"))
TIMEOUT = float(os.environ.get("TIMEOUT", "1.0"))

DATOS = {}   # clave -> valor (memoria del proceso; se pierde al reiniciar)


def log(msg):
    print(f"[{NOMBRE}/{MODO}] {msg}", flush=True)


def peer_alcanzable():
    """¿Puedo hablar con mi réplica par ahora mismo?"""
    if not PEER:
        return False
    try:
        with urllib.request.urlopen(PEER + "/ping", timeout=TIMEOUT) as r:
            return r.status == 200
    except Exception as e:  # DNS fallido, timeout, conexión rechazada...
        log(f"par NO alcanzable: {type(e).__name__}")
        return False


def replicar(k, v):
    """Envía la escritura al par marcada como réplica (para no rebotar)."""
    try:
        url = f"{PEER}/set?k={k}&v={v}&replica=1"
        with urllib.request.urlopen(url, timeout=TIMEOUT) as r:
            return r.status == 200
    except Exception as e:
        log(f"replicación falló: {type(e).__name__}")
        return False


class Handler(BaseHTTPRequestHandler):
    def responder(self, codigo, cuerpo):
        datos = json.dumps(cuerpo, ensure_ascii=False).encode()
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(datos)))
        self.end_headers()
        self.wfile.write(datos)

    def log_message(self, fmt, *args):  # silenciar log por defecto
        pass

    def do_GET(self):
        u = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(u.query).items()}

        if u.path == "/ping":
            return self.responder(200, {"replica": NOMBRE, "modo": MODO})

        if u.path == "/get":
            k = q.get("k", "")
            if MODO == "CP" and not peer_alcanzable():
                log(f"GET {k} rechazado: sin par no garantizo consistencia")
                return self.responder(503, {"replica": NOMBRE, "modo": MODO,
                                            "error": "particion de red: no puedo garantizar consistencia"})
            if k in DATOS:
                log(f"GET {k} -> {DATOS[k]}")
                return self.responder(200, {"replica": NOMBRE, "modo": MODO, "k": k, "v": DATOS[k]})
            return self.responder(404, {"replica": NOMBRE, "modo": MODO, "k": k, "error": "clave inexistente"})

        if u.path == "/set":
            k, v = q.get("k", ""), q.get("v", "")
            es_replica = q.get("replica") == "1"
            if es_replica:                       # escritura que viene del par
                DATOS[k] = v
                log(f"SET replicado {k}={v}")
                return self.responder(200, {"replica": NOMBRE, "modo": MODO, "k": k, "v": v, "origen": "par"})
            if MODO == "CP":
                if not peer_alcanzable():
                    log(f"SET {k} rechazado: par no alcanzable")
                    return self.responder(503, {"replica": NOMBRE, "modo": MODO,
                                                "error": "particion de red: escritura rechazada para no divergir"})
                DATOS[k] = v
                ok = replicar(k, v)
                return self.responder(200, {"replica": NOMBRE, "modo": MODO, "k": k, "v": v, "replicado": ok})
            # MODO AP: escribo local y hago lo posible por replicar
            DATOS[k] = v
            ok = replicar(k, v)
            aviso = None if ok else "guardado localmente; la replica no fue alcanzada (datos pueden divergir)"
            log(f"SET {k}={v} replicado={ok}")
            return self.responder(200, {"replica": NOMBRE, "modo": MODO, "k": k, "v": v,
                                        "replicado": ok, "aviso": aviso})

        return self.responder(404, {"error": "ruta desconocida"})


if __name__ == "__main__":
    log(f"escuchando en :{PUERTO}, par={PEER or '(ninguno)'}")
    ThreadingHTTPServer(("0.0.0.0", PUERTO), Handler).serve_forever()
