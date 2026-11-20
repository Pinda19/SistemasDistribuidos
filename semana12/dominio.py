"""Dominio puro RepoSync: sin redes ni protocolos. Usado por JSON-RPC y gRPC.

El estado es local al proceso. Si se recrea el servidor se pierde la RAM.
"""
import threading

_lock = threading.Lock()
_estado = {
    "repos": {
        "proyecto": {
            "ramas": {"main": 0},
            "commits": {0: {"padre": None, "mensaje": "inicio"}},
            "siguiente": 1,
        }
    }
}


class ErrorDominio(Exception):
    """Un recurso no existe o la operacion contradice el estado actual."""


class ErrorParametros(Exception):
    """Una solicitud trae valores invalidos."""


def _texto(valor, nombre):
    if not isinstance(valor, str) or not valor.strip():
        raise ErrorParametros(f"{nombre} debe ser texto no vacio")
    return valor.strip()


def _repo(nombre):
    repo = _estado["repos"].get(nombre)
    if repo is None:
        raise ErrorDominio("REPO_NO_EXISTE")
    return repo


def _rama(repo, nombre):
    if nombre not in repo["ramas"]:
        raise ErrorDominio("RAMA_NO_EXISTE")
    return repo["ramas"][nombre]


def clonar(repo: str, rama: str):
    _texto(repo, "repo")
    _texto(rama, "rama")
    with _lock:
        r = _repo(repo)
        head = _rama(r, rama)
        return {"repositorio": repo, "rama": rama, "head": head}


def rama(repo: str, nueva: str, origen: str):
    for nombre, valor in (("repo", repo), ("nueva", nueva), ("origen", origen)):
        _texto(valor, nombre)
    with _lock:
        r = _repo(repo)
        origen_head = _rama(r, origen)
        if nueva in r["ramas"]:
            raise ErrorDominio("RAMA_EXISTE")
        r["ramas"][nueva] = origen_head
        return {"repositorio": repo, "rama": nueva, "head": origen_head}


def _registrar(r, nombre_rama, mensaje):
    anterior = r["ramas"][nombre_rama]
    siguiente = r["siguiente"]
    r["siguiente"] += 1
    r["commits"][siguiente] = {"padre": anterior, "mensaje": mensaje}
    r["ramas"][nombre_rama] = siguiente
    return siguiente


def push(repo: str, rama: str, base: int, mensaje: str):
    _texto(repo, "repo")
    _texto(rama, "rama")
    _texto(mensaje, "mensaje")
    if not isinstance(base, int) or isinstance(base, bool) or base < 0:
        raise ErrorParametros("base debe ser entero >= 0")
    with _lock:
        r = _repo(repo)
        actual = _rama(r, rama)
        if actual != base:
            raise ErrorDominio(f"CONFLICTO HEAD={actual}")
        head = _registrar(r, rama, mensaje)
        return {"repositorio": repo, "rama": rama, "head": head}


def publicar_auto(repo: str, rama: str, mensaje: str):
    """NUEVA operacion de laboratorio: agrega una revision al HEAD actual.

    A diferencia de PUSH no requiere base: es intencionalmente no idempotente.
    Su funcion es mostrar el efecto de los reintentos y la deduplicacion.
    """
    _texto(repo, "repo")
    _texto(rama, "rama")
    _texto(mensaje, "mensaje")
    with _lock:
        r = _repo(repo)
        _rama(r, rama)
        head = _registrar(r, rama, mensaje)
        return {"repositorio": repo, "rama": rama, "head": head}


def historial(repo: str, rama: str):
    _texto(repo, "repo")
    _texto(rama, "rama")
    with _lock:
        r = _repo(repo)
        cursor = _rama(r, rama)
        revisiones = []
        while cursor is not None:
            commit = r["commits"][cursor]
            revisiones.append({"numero": cursor, "mensaje": commit["mensaje"]})
            cursor = commit["padre"]
        return {"revisiones": revisiones}
