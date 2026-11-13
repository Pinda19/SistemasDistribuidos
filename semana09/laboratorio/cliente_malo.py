"""cliente_malo.py — provocación de fallas de protocolo (Semana 9, paso 5).

Manda mensajes que rompen el contrato para observar cómo reacciona el servidor.

  python cliente_malo.py version   solicitud con version=1 (el servidor exige 2)
  python cliente_malo.py largo     anuncia 60 bytes y manda solo 10 (largo mentiroso)
  python cliente_malo.py basura    largo correcto pero bytes al azar
  python cliente_malo.py cruzado   codifica en JSON contra un servidor bin, o al revés
"""
import os
import socket
import sys

import codec
from mensajes import Solicitud, Respuesta

HOST = os.environ.get("SERVIDOR_HOST", "servidor")
PUERTO = int(os.environ.get("SERVIDOR_PUERTO", "5000"))
TIMEOUT = float(os.environ.get("TIMEOUT_CLIENTE", "5"))

modo = sys.argv[1] if len(sys.argv) > 1 else "version"
sock = socket.create_connection((HOST, PUERTO), timeout=TIMEOUT)
print(f"modo={modo} codec={codec.CODEC}")

try:
    if modo == "version":
        sol = Solicitud(operacion="AGREGAR", argumentos=["tornillo", "25"], id=1, version=1)
        codec.enviar(sock, sol)
    elif modo == "largo":
        sock.sendall(codec.LARGO.pack(60) + b"0123456789")
    elif modo == "basura":
        basura = os.urandom(24)
        print("  enviando", basura.hex())
        sock.sendall(codec.LARGO.pack(len(basura)) + basura)
    elif modo == "cruzado":
        otro = "bin" if codec.CODEC == "json" else "json"
        print("  codificando con", otro)
        sol = Solicitud(operacion="AGREGAR", argumentos=["tornillo", "25"], id=1)
        codec.enviar(sock, sol, otro)
    else:
        raise SystemExit("modo desconocido")
    resp = codec.recibir(sock, Respuesta)
    print("  respuesta", resp)
except socket.timeout:
    print(f"  ! sin respuesta en {TIMEOUT} s")
except Exception as e:
    print("  ! el cliente falló al decodificar", type(e).__name__, e)
finally:
    sock.close()
