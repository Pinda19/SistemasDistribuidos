"""RepoSync / Semana 7: puerta REST sin estado delante del servidor TCP.

Las reglas de control de versiones y todas las revisiones siguen viviendo en
servidor.py. Cada petición HTTP se traduce a UNA línea del protocolo TCP.

GET  /salud
GET  /repos
GET  /repos/{repo}/ramas/{rama}
GET  /repos/{repo}/ramas/{rama}/historial
POST /repos/{repo}/ramas                    {"nueva":"desarrollo","origen":"main"}
POST /repos/{repo}/ramas/{rama}/commits     {"base":0,"mensaje":"primer_cambio"}
"""
import os
import re
import socket

from fastapi import FastAPI, HTTPException, Path
from pydantic import BaseModel, Field

SERVIDOR_HOST = os.environ.get("SERVIDOR_HOST", "servidor")
SERVIDOR_PUERTO = int(os.environ.get("SERVIDOR_PUERTO", "5000"))
TIMEOUT_SERVIDOR = float(os.environ.get("TIMEOUT_SERVIDOR", "3"))
REPLICA = os.environ.get("REPLICA", socket.gethostname())

app = FastAPI(
    title="RepoSync — API REST",
    version="2.0",
    description="Puerta HTTP sin estado del servicio de control de versiones distribuido (Semana 7).",
)

# Un identificador es una sola palabra: sin espacios, saltos de línea ni comandos inyectados.
ID_PATTERN = r"^[A-Za-z0-9_-]{1,30}$"
REPO = Path(pattern=ID_PATTERN, description="Identificador del repositorio")
RAMA = Path(pattern=ID_PATTERN, description="Nombre de rama")

# Códigos del protocolo TCP -> HTTP.
ERRORES = {
    "FORMATO": 422,
    "COMANDO_DESCONOCIDO": 501,
    "REPO_NO_EXISTE": 404,
    "RAMA_NO_EXISTE": 404,
    "RAMA_EXISTE": 409,
    "CONFLICTO": 409,
    "HISTORIAL_INCONSISTENTE": 500,
}


class NuevaRama(BaseModel):
    nueva: str = Field(min_length=1, max_length=30, pattern=ID_PATTERN)
    origen: str = Field(min_length=1, max_length=30, pattern=ID_PATTERN)


class NuevoCommit(BaseModel):
    base: int = Field(ge=0)
    mensaje: str = Field(min_length=1, max_length=80)


# Se conserva la estructura de transporte indicada por la plantilla docente.
def pedir(linea: str) -> str:
    """Traduce una solicitud HTTP a una solicitud TCP y espera UNA respuesta."""
    try:
        with socket.create_connection(
            (SERVIDOR_HOST, SERVIDOR_PUERTO), timeout=TIMEOUT_SERVIDOR
        ) as s:
            s.sendall((linea + "\n").encode("utf-8"))
            respuesta = s.makefile("r", encoding="utf-8").readline().strip()
    except socket.timeout:
        raise HTTPException(504, {"error": "SERVIDOR_NO_RESPONDE", "replica": REPLICA})
    except OSError as e:
        raise HTTPException(
            503,
            {
                "error": "SERVIDOR_NO_DISPONIBLE",
                "detalle": e.__class__.__name__,
                "replica": REPLICA,
            },
        )
    if not respuesta:
        raise HTTPException(503, {"error": "SERVIDOR_CERRO_LA_CONEXION", "replica": REPLICA})
    return respuesta


def traducir(respuesta: str) -> list[str]:
    """'OK a b' -> ['a','b']; 'ERROR CODIGO detalle' -> HTTPException."""
    partes = respuesta.split()
    if partes and partes[0] == "OK":
        return partes[1:]
    codigo = partes[1] if len(partes) > 1 else "DESCONOCIDO"
    raise HTTPException(
        ERRORES.get(codigo, 500),
        {"error": codigo, "detalle": " ".join(partes[2:]), "replica": REPLICA},
    )


def obtener_head(token: str) -> int:
    if not token.startswith("HEAD=") or not token[5:].isdigit():
        raise HTTPException(502, {"error": "RESPUESTA_TCP_INVALIDA", "replica": REPLICA})
    return int(token[5:])


@app.get("/salud")
def salud():
    """Salud de la puerta HTTP, no garantiza disponibilidad del servidor TCP."""
    return {"estado": "ok", "replica": REPLICA}


@app.get("/repos")
def repositorios():
    partes = traducir(pedir("REPOS"))
    return {"repositorios": partes, "replica": REPLICA}


@app.get("/repos/{repo}/ramas/{rama}")
def consultar_rama(repo: str = REPO, rama: str = RAMA):
    partes = traducir(pedir(f"CLONAR {repo} {rama}"))
    if len(partes) != 3:
        raise HTTPException(502, {"error": "RESPUESTA_TCP_INVALIDA", "replica": REPLICA})
    return {
        "repositorio": partes[0],
        "rama": partes[1],
        "head": obtener_head(partes[2]),
        "replica": REPLICA,
    }


@app.get("/repos/{repo}/ramas/{rama}/historial")
def consultar_historial(repo: str = REPO, rama: str = RAMA):
    respuesta = pedir(f"HISTORIAL {repo} {rama}")
    traducir(respuesta)  # valida OK / ERROR respetando el protocolo TCP
    # Historial en texto: se preserva exactamente la representación del servidor.
    return {"repositorio": repo, "rama": rama, "historial": respuesta[3:], "replica": REPLICA}


@app.post("/repos/{repo}/ramas", status_code=201)
def crear_rama(datos: NuevaRama, repo: str = REPO):
    partes = traducir(pedir(f"RAMA {repo} {datos.nueva} {datos.origen}"))
    if len(partes) != 3 or partes[0] != "RAMA":
        raise HTTPException(502, {"error": "RESPUESTA_TCP_INVALIDA", "replica": REPLICA})
    return {"repositorio": repo, "rama": partes[1], "head": obtener_head(partes[2]), "replica": REPLICA}


@app.post("/repos/{repo}/ramas/{rama}/commits", status_code=201)
def publicar_commit(datos: NuevoCommit, repo: str = REPO, rama: str = RAMA):
    mensaje = datos.mensaje.strip()
    if not mensaje or any(c in mensaje for c in "\r\n"):
        raise HTTPException(422, {"error": "FORMATO", "detalle": "Mensaje invalido", "replica": REPLICA})
    partes = traducir(pedir(f"PUSH {repo} {rama} {datos.base} {mensaje}"))
    if len(partes) != 3 or partes[0] != "PUSH":
        raise HTTPException(502, {"error": "RESPUESTA_TCP_INVALIDA", "replica": REPLICA})
    return {"repositorio": repo, "rama": partes[1], "head": obtener_head(partes[2]), "replica": REPLICA}
