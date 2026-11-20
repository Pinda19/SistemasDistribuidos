"""
Servidor Pyro5 del servicio, semana 12.

Crea un daemon (el que recibe las llamadas y las despacha a los objetos),
registra la clase Repositorio y la publica en el servidor de nombres con el
nombre sd.<EQUIPO>.repositorio.

Variables
  SERVIDOR_HOST    (servidor)   nombre con el que el daemon se anuncia
  SERVIDOR_PUERTO  (9100)       puerto fijo del daemon
  NOMBRES_HOST     (nombres)    dónde está el servidor de nombres
  NOMBRES_PUERTO   (9090)
  EQUIPO           (referencia) parte del nombre lógico
  MODO             single | session | percall
  REREGISTRO       (0) cada cuántos segundos volver a registrarse, 0 = nunca
"""
import os
import sys
import threading
import time

from Pyro5.api import Daemon, locate_ns
from Pyro5.errors import NamingError, CommunicationError

from objetos import MODO, Repositorio

HOST = os.environ.get("SERVIDOR_HOST", "servidor")
PUERTO = int(os.environ.get("SERVIDOR_PUERTO", "9100"))
NS_HOST = os.environ.get("NOMBRES_HOST", "nombres")
NS_PUERTO = int(os.environ.get("NOMBRES_PUERTO", "9090"))
EQUIPO = os.environ.get("EQUIPO", "pinda")
REREGISTRO = int(os.environ.get("REREGISTRO", "0"))
NOMBRE = f"sd.{EQUIPO}.repositorio"


def log(msg):
    print(time.strftime("%H:%M:%S"), "[servidor]", msg, flush=True)


def registrar(uri, intentos=30):
    """Publica la URI en el servidor de nombres. Reintenta si aún no está."""
    for i in range(intentos):
        try:
            with locate_ns(host=NS_HOST, port=NS_PUERTO) as ns:
                ns.register(NOMBRE, uri)
            return True
        except (NamingError, CommunicationError) as e:
            log(f"servidor de nombres no disponible ({e}), reintento {i + 1}")
            time.sleep(1)
    return False


def reregistrar_cada(uri, segundos):
    while True:
        time.sleep(segundos)
        try:
            with locate_ns(host=NS_HOST, port=NS_PUERTO) as ns:
                ns.register(NOMBRE, uri)
        except (NamingError, CommunicationError):
            log("re-registro falló, el servidor de nombres no responde")


def main():
    daemon = Daemon(host=HOST, port=PUERTO)
    uri = daemon.register(Repositorio, objectId="repositorio")
    log(f"daemon escuchando, modo de instancia {MODO}")
    log(f"URI {uri}")
    if not registrar(uri):
        log("no pude registrarme en el servidor de nombres, salgo")
        sys.exit(1)
    log(f"registrado como {NOMBRE}")
    if REREGISTRO > 0:
        threading.Thread(target=reregistrar_cada, args=(uri, REREGISTRO),
                         daemon=True).start()
        log(f"re-registro cada {REREGISTRO} s activado")
    daemon.requestLoop()


if __name__ == "__main__":
    main()
