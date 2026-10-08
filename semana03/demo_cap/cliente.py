#!/usr/bin/env python3
"""cliente.py — cliente mínimo para la demo CAP.

Uso (desde el contenedor cliente):
  python cliente.py a set nota 6.5
  python cliente.py b get nota
  python cliente.py a ping
"""
import json
import sys
import urllib.request
import urllib.error

REPLICAS = {"a": "http://replica_a:8000", "b": "http://replica_b:8000"}


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    base = REPLICAS.get(sys.argv[1], sys.argv[1])
    op = sys.argv[2]
    if op == "ping":
        url = f"{base}/ping"
    elif op == "get":
        url = f"{base}/get?k={sys.argv[3]}"
    elif op == "set":
        url = f"{base}/set?k={sys.argv[3]}&v={sys.argv[4]}"
    else:
        print("operación desconocida:", op)
        sys.exit(1)
    try:
        with urllib.request.urlopen(url, timeout=3) as r:
            print(r.status, json.dumps(json.loads(r.read()), ensure_ascii=False))
    except urllib.error.HTTPError as e:
        print(e.code, e.read().decode())
    except Exception as e:
        print("ERROR de red:", type(e).__name__, e)


if __name__ == "__main__":
    main()
