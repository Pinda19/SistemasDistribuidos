"""JSON-RPC de Semana 10 usando el MISMO dominio.py (en el mismo proceso).

Si se arranca en OTRO proceso no comparte el estado RAM con el servidor gRPC.
"""
import json
from fastapi import FastAPI, Request, Response
import dominio

app = FastAPI(title="RepoSync JSON-RPC reutilizando dominio.py (Semana 11)")
METODOS = {
    "rama": dominio.rama,
    "clonar": dominio.clonar,
    "push": dominio.push,
    "historial": dominio.historial,
    "publicar_auto": dominio.publicar_auto,
}


def error(id_, codigo, mensaje, datos=None):
    e = {"code": codigo, "message": mensaje}
    if datos is not None:
        e["data"] = datos
    return {"jsonrpc": "2.0", "error": e, "id": id_}


def atender(req):
    if not isinstance(req, dict) or req.get("jsonrpc") != "2.0" or not isinstance(req.get("method"), str) or not req["method"]:
        return error(None, -32600, "Invalid Request")
    id_ = req.get("id")
    notify = "id" not in req
    if "id" in req and (isinstance(id_, (bool, list, dict)) or (isinstance(id_, float) and not id_.is_integer())):
        return error(None, -32600, "Invalid Request")
    method = METODOS.get(req["method"])
    if method is None:
        return None if notify else error(id_, -32601, "Method not found")
    params = req.get("params", [])
    if not isinstance(params, (list, dict)):
        return None if notify else error(id_, -32602, "Invalid params")
    try:
        value = method(**params) if isinstance(params, dict) else method(*params)
    except (TypeError, dominio.ErrorParametros) as exc:
        return None if notify else error(id_, -32602, "Invalid params", str(exc))
    except dominio.ErrorDominio as exc:
        return None if notify else error(id_, -32000, "Error del dominio", str(exc))
    except Exception:
        return None if notify else error(id_, -32603, "Internal error")
    return None if notify else {"jsonrpc": "2.0", "result": value, "id": id_}


@app.post("/rpc")
async def rpc(request: Request):
    try:
        data = json.loads(await request.body())
    except (json.JSONDecodeError, UnicodeDecodeError):
        return error(None, -32700, "Parse error")
    if isinstance(data, list):
        if not data:
            return error(None, -32600, "Invalid Request")
        result = [r for r in (atender(x) for x in data) if r is not None]
        return result if result else Response(status_code=204)
    answer = atender(data)
    return answer if answer is not None else Response(status_code=204)
