"""Cliente HTTP minimo (solo biblioteca estandar), para usar desde el contenedor cliente.

  python cliente_http.py GET /items
  python cliente_http.py POST /items/pera/entradas cantidad=5
  python cliente_http.py --repetir 6 GET /items/pera

Los pares clave=valor se envian como cuerpo JSON. La direccion base sale de API_URL.
"""
import argparse
import json
import os
import time
import urllib.error
import urllib.request

API_URL = os.environ.get("API_URL", "http://nginx")


def pedir(metodo, ruta, cuerpo):
    datos = json.dumps(cuerpo).encode("utf-8") if cuerpo else None
    req = urllib.request.Request(API_URL + ruta, data=datos, method=metodo,
                                 headers={"Content-Type": "application/json"})
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            estado, texto = r.status, r.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        estado, texto = e.code, e.read().decode("utf-8")
    except (urllib.error.URLError, OSError) as e:
        estado, texto = 0, f"SIN RESPUESTA ({getattr(e, 'reason', e)})"
    return estado, texto.strip(), time.perf_counter() - t0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("metodo", choices=["GET", "POST", "PUT", "DELETE"])
    ap.add_argument("ruta")
    ap.add_argument("campos", nargs="*", help="pares clave=valor para el cuerpo JSON")
    ap.add_argument("--repetir", type=int, default=1)
    args = ap.parse_args()

    cuerpo = {}
    for campo in args.campos:
        clave, _, valor = campo.partition("=")
        cuerpo[clave] = int(valor) if valor.lstrip("-").isdigit() else valor

    for _ in range(args.repetir):
        estado, texto, seg = pedir(args.metodo, args.ruta, cuerpo)
        print(f"{estado}  {seg:5.2f} s  {texto}")


if __name__ == "__main__":
    main()
