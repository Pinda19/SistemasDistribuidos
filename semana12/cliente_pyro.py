"""Cliente RepoSync: nombres, operaciones, referencias y vigilancia de fallos."""
import argparse
import os
import sys
import time
from pathlib import Path
from Pyro5.api import Proxy, locate_ns, register_dict_to_class
from Pyro5.errors import CommunicationError, NamingError, DaemonError, SerializeError
import dominio

NS_HOST = os.environ.get("NOMBRES_HOST", "nombres")
NS_PUERTO = int(os.environ.get("NOMBRES_PUERTO", "9090"))
NOMBRE = f"sd.{os.environ.get('EQUIPO', 'pinda')}.repositorio"


def _a_excepcion(nombre, datos):
    clases = {"dominio.ErrorDominio": dominio.ErrorDominio,
              "dominio.ErrorParametros": dominio.ErrorParametros}
    return clases[nombre](*datos.get("args", ()))


for _nombre in ("ErrorDominio", "ErrorParametros"):
    register_dict_to_class(f"dominio.{_nombre}", _a_excepcion)


def log(mensaje):
    print(time.strftime("%H:%M:%S"), mensaje, flush=True)


def repositorio():
    """Localiza por nombre; tras el primer contacto el Proxy conserva la URI."""
    proxy = Proxy(f"PYRONAME:{NOMBRE}@{NS_HOST}:{NS_PUERTO}")
    proxy._pyroTimeout = 2
    return proxy


def cmd_uri(_):
    with locate_ns(host=NS_HOST, port=NS_PUERTO) as ns:
        log(f"{NOMBRE} -> {ns.lookup(NOMBRE)}")
        log(f"nombres registrados {sorted(ns.list())}")


def cmd_operacion(a):
    campos = {"clonar": ("repo", "rama"), "rama": ("repo", "nueva", "origen"),
              "push": ("repo", "rama", "base", "mensaje"),
              "historial": ("repo", "rama")}
    with repositorio() as obj:
        log(getattr(obj, a.cmd)(*(getattr(a, n) for n in campos[a.cmd])))


def cmd_quien(a):
    for etiqueta in ("proxy A", "proxy B"):
        with repositorio() as obj:
            for _ in range(a.veces):
                log(f"{etiqueta} -> {obj.quien_soy()}")


def cmd_vivos(_):
    with repositorio() as obj:
        log(f"cambios vivos {obj.cambios_vivos()}")


def cmd_cambio(a):
    with repositorio() as obj:
        cambio = obj.abrir_cambio(a.repo, a.rama, a.autor)
        cambio._pyroTimeout = 2
        with cambio:
            log(f"recibí {type(cambio).__name__}, referencia {cambio._pyroUri}")
            for ruta in a.archivos:
                cambio.agregar(ruta)
            log(f"estado remoto {cambio.ver()}")
            if a.esperar:
                log(f"espero {a.esperar} s; ahora se puede provocar la caída")
                time.sleep(a.esperar)
            # No reintentamos una escritura cuyo resultado sea desconocido.
            log(f"confirmar -> {cambio.confirmar(a.mensaje)}")
            try:
                cambio.ver()
            except (DaemonError, CommunicationError) as e:
                if "unknown object" not in str(e):
                    raise
                log(f"REFERENCIA COLGANTE esperada: {e}")
            else:
                raise AssertionError("El cambio debió desregistrarse")


def cmd_vigilar(a):
    with repositorio() as obj:
        i = 0
        while not a.veces or i < a.veces:
            if a.detener and Path(a.detener).exists():
                break
            try:
                log(f"ok {obj.clonar(a.repo, a.rama)} [{obj._pyroUri}]")
            except (CommunicationError, NamingError) as e:
                log(f"FALLA {type(e).__name__}: {e}")
                try:
                    obj._pyroReconnect(tries=1)
                    log("reconectado")
                except (CommunicationError, NamingError) as error:
                    log(f"sin reconexión: {type(error).__name__}")
            i += 1
            time.sleep(a.cada)


def main():
    parser = argparse.ArgumentParser(description="RepoSync / Pyro5 / Semana 12")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("uri").set_defaults(f=cmd_uri)
    sub.add_parser("vivos").set_defaults(f=cmd_vivos)
    p = sub.add_parser("quien")
    p.add_argument("--veces", type=int, default=2)
    p.set_defaults(f=cmd_quien)
    for nombre in ("clonar", "historial", "push", "rama", "cambio", "vigilar"):
        p = sub.add_parser(nombre)
        if nombre == "vigilar":
            p.add_argument("repo", nargs="?", default="proyecto")
            p.add_argument("rama", nargs="?", default="main")
            p.add_argument("--cada", type=float, default=1)
            p.add_argument("--veces", type=int, default=0)
            p.add_argument("--detener", help="Termina si aparece este archivo")
            p.set_defaults(f=cmd_vigilar)
            continue
        p.add_argument("repo")
        if nombre == "rama":
            p.add_argument("nueva")
            p.add_argument("origen")
        else:
            p.add_argument("rama")
        if nombre == "push":
            p.add_argument("base", type=int)
            p.add_argument("mensaje")
        if nombre == "cambio":
            p.add_argument("autor")
            p.add_argument("archivos", nargs="+")
            p.add_argument("--mensaje", default="cambio_de_laboratorio")
            p.add_argument("--esperar", type=float, default=0)
        p.set_defaults(f=cmd_cambio if nombre == "cambio" else cmd_operacion)
    a = parser.parse_args()
    try:
        a.f(a)
        return 0
    except KeyboardInterrupt:
        return 0
    except NamingError as e:
        log(f"ERROR de nombres: {e}")
        return 2
    except DaemonError as e:
        log(f"ERROR referencia colgante: {e}")
        return 3
    except SerializeError as e:
        log(f"ERROR de serialización por valor: {e}")
        return 4
    except CommunicationError as e:
        log(f"ERROR de comunicación; resultado de una escritura puede ser DESCONOCIDO: {e}")
        return 5
    except (dominio.ErrorDominio, dominio.ErrorParametros) as e:
        log(f"ERROR remoto {type(e).__name__}: {e}")
        return 6
    except Exception as e:
        log(f"ERROR {type(e).__name__}: {e}")
        return 7


if __name__ == "__main__":
    sys.exit(main())
