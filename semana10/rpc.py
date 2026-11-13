"""Semana 10: JSON-RPC 2.0 de RepoSync sobre FastAPI.

Adaptado del esqueleto del profesor. Implementa dos operaciones del dominio:
  rama(repo, nueva, origen) -> crea una rama
  clonar(repo, rama) -> consulta el HEAD
El estado es RAM de ESTE proceso RPC (no es el servidor TCP de Semana 9).
"""
import json
import threading
from fastapi import FastAPI, Request, Response

app = FastAPI(title="RepoSync - JSON-RPC 2.0 (Semana 10)")

# Dominio RepoSync: misma estructura inicial que el servidor TCP de semana 9.
estado = {"repos": {"proyecto": {"ramas": {"main": 0}}}}
lock = threading.Lock()


class ErrorDominio(ValueError):
    """Error esperado al ejecutar una operacion correcta con un recurso invalido."""


def _nombre(valor, parametro):
    if not isinstance(valor, str) or not valor.strip():
        raise TypeError(f"{parametro} debe ser un texto no vacio")
    return valor


def rama(repo: str, nueva: str, origen: str):
    """Equivale a RAMA <repo> <nueva> <origen> de Semana 9."""
    _nombre(repo, "repo")
    _nombre(nueva, "nueva")
    _nombre(origen, "origen")
    with lock:
        r = estado["repos"].get(repo)
        if r is None:
            raise ErrorDominio("REPO_NO_EXISTE")
        if origen not in r["ramas"]:
            raise ErrorDominio("RAMA_NO_EXISTE")
        if nueva in r["ramas"]:
            raise ErrorDominio("RAMA_EXISTE")
        r["ramas"][nueva] = r["ramas"][origen]
        return {"repositorio": repo, "rama": nueva, "head": r["ramas"][nueva]}


def clonar(repo: str, rama: str):
    """Equivale a CLONAR <repo> <rama> de Semana 9 (no descarga archivos)."""
    _nombre(repo, "repo")
    _nombre(rama, "rama")
    with lock:
        r = estado["repos"].get(repo)
        if r is None:
            raise ErrorDominio("REPO_NO_EXISTE")
        if rama not in r["ramas"]:
            raise ErrorDominio("RAMA_NO_EXISTE")
        return {"repositorio": repo, "rama": rama, "head": r["ramas"][rama]}


METODOS = {"rama": rama, "clonar": clonar}

PARSE_ERROR, INVALID_REQUEST, METHOD_NOT_FOUND, INVALID_PARAMS, INTERNAL = (
    -32700, -32600, -32601, -32602, -32603
)
SERVER_ERROR = -32000


def error(id_, codigo, mensaje, datos=None):
    e = {"code": codigo, "message": mensaje}
    if datos is not None:
        e["data"] = datos
    return {"jsonrpc": "2.0", "error": e, "id": id_}


def atender(req):
    """Procesa una request y devuelve respuesta o None para notificaciones."""
    if not isinstance(req, dict):
        return error(None, INVALID_REQUEST, "Invalid Request")
    id_ = req.get("id")
    if (req.get("jsonrpc") != "2.0"
            or not isinstance(req.get("method"), str)
            or not req.get("method")
            or ("id" in req and (isinstance(id_, (list, dict, bool))
                or (isinstance(id_, float) and not id_.is_integer())))):
        return error(None, INVALID_REQUEST, "Invalid Request")
    es_notificacion = "id" not in req
    metodo = METODOS.get(req["method"])
    if metodo is None:
        return None if es_notificacion else error(id_, METHOD_NOT_FOUND, "Method not found")
    params = req.get("params", [])
    if not isinstance(params, (list, dict)):
        return None if es_notificacion else error(id_, INVALID_PARAMS, "Invalid params")
    try:
        resultado = metodo(**params) if isinstance(params, dict) else metodo(*params)
    except TypeError as exc:
        return None if es_notificacion else error(id_, INVALID_PARAMS, "Invalid params", str(exc))
    except ErrorDominio as exc:
        return None if es_notificacion else error(id_, SERVER_ERROR, "Error del dominio", str(exc))
    except Exception:
        return None if es_notificacion else error(id_, INTERNAL, "Internal error")
    return None if es_notificacion else {"jsonrpc": "2.0", "result": resultado, "id": id_}


@app.post("/rpc")
async def rpc(request: Request):
    cuerpo = await request.body()
    try:
        datos = json.loads(cuerpo)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return error(None, PARSE_ERROR, "Parse error")
    if isinstance(datos, list):
        if not datos:
            return error(None, INVALID_REQUEST, "Invalid Request")
        respuestas = [r for r in (atender(x) for x in datos) if r is not None]
        return respuestas if respuestas else Response(status_code=204)
    resp = atender(datos)
    return resp if resp is not None else Response(status_code=204)
