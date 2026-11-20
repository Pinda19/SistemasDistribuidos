"""
medir.py, Evaluación 4 (Reporte de Servicios Cliente-Servidor).

Mide la MISMA operación de consulta sobre un mecanismo de comunicación y
entrega una fila lista para pegar en el informe. Se ejecuta una vez por
mecanismo, dentro del contenedor cliente de la semana que corresponde.

  python medir.py pyro    [--metodo listar] [--n 200]            (semana12)
  python medir.py jsonrpc --url http://servidor:8000/rpc [--metodo listar]
                                                                 (semana10)
  python medir.py grpc    [--n 200]      (semana11, editar llamar_grpc)

Solo usa la biblioteca estándar. Cada adaptador importa lo suyo.
Los tiempos son de su notebook con Docker, sirven para COMPARAR entre
mecanismos, no como cifras absolutas.
"""
import argparse
import json
import os
import statistics
import time
import urllib.request


# ------------------------------------------------------------ adaptadores
def adaptador_pyro(a):
    """Devuelve (funcion_que_llama, bytes_de_respuesta). Semana 12."""
    import serpent
    from Pyro5.api import Proxy
    ns_host = os.environ.get("NOMBRES_HOST", "nombres")
    ns_puerto = os.environ.get("NOMBRES_PUERTO", "9090")
    equipo = os.environ.get("EQUIPO", "referencia")
    nombre = a.nombre or f"sd.{equipo}.repositorio"
    proxy = Proxy(f"PYRONAME:{nombre}@{ns_host}:{ns_puerto}")
    metodo = getattr(proxy, a.metodo)
    params = json.loads(a.params)

    def llamar():
        return metodo(**params)

    return llamar, len(serpent.dumps(llamar()))


def adaptador_jsonrpc(a):
    """JSON-RPC 2.0 sobre HTTP. Semana 10."""
    cuerpo = json.dumps({"jsonrpc": "2.0", "id": 1, "method": a.metodo,
                         "params": json.loads(a.params)}).encode()

    def llamar():
        req = urllib.request.Request(a.url, data=cuerpo,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=5) as r:
            datos = r.read()
        if b'"error"' in datos:
            raise RuntimeError(datos.decode()[:200])
        return datos

    return llamar, len(llamar())


def adaptador_grpc(a):
    """RepoSync: misma consulta Clonar(proyecto, main) que Pyro5."""
    import grpc
    import servicio_pb2
    import servicio_pb2_grpc
    host = os.environ.get("SERVIDOR_HOST", "servidor")
    puerto = os.environ.get("SERVIDOR_PUERTO", "50051")
    canal = grpc.insecure_channel(f"{host}:{puerto}")
    stub = servicio_pb2_grpc.RepoSyncStub(canal)

    def llamar():
        return stub.Clonar(servicio_pb2.ClonarSolicitud(**json.loads(a.params)), timeout=5)

    return llamar, llamar().ByteSize()


ADAPTADORES = {"pyro": adaptador_pyro, "jsonrpc": adaptador_jsonrpc,
               "grpc": adaptador_grpc}


# ------------------------------------------------------------ medición
def percentil(valores, p):
    orden = sorted(valores)
    k = max(0, min(len(orden) - 1, round(p / 100 * (len(orden) - 1))))
    return orden[k]


def medir(llamar, n, calentamiento=10):
    for _ in range(calentamiento):
        llamar()
    tiempos = []
    for _ in range(n):
        t0 = time.perf_counter()
        llamar()
        tiempos.append((time.perf_counter() - t0) * 1000)
    return tiempos


def main():
    p = argparse.ArgumentParser(description="Medición para la Evaluación 4")
    p.add_argument("mecanismo", choices=sorted(ADAPTADORES))
    p.add_argument("--n", type=int, default=200, help="llamadas medidas")
    p.add_argument("--metodo", default="clonar", help="operación de CONSULTA")
    p.add_argument("--params", default='{"repo":"proyecto","rama":"main"}', help="parámetros en JSON")
    p.add_argument("--url", default="http://servidor:8000/rpc")
    p.add_argument("--nombre", default="", help="nombre lógico Pyro5")
    p.add_argument("--csv", default="mediciones.csv")
    a = p.parse_args()

    if a.n < 200:
        p.error("La evaluación exige al menos 200 llamadas")
    llamar, tamano = ADAPTADORES[a.mecanismo](a)
    t = medir(llamar, a.n)
    fila = {"mecanismo": a.mecanismo, "operacion": a.metodo, "n": a.n,
            "p50_ms": round(percentil(t, 50), 2), "p95_ms": round(percentil(t, 95), 2),
            "media_ms": round(statistics.mean(t), 2), "max_ms": round(max(t), 2),
            "respuesta_bytes": tamano}

    print("| Mecanismo | Operación | n | p50 ms | p95 ms | media ms | máx ms | respuesta bytes |")
    print("|---|---|---|---|---|---|---|---|")
    print("| " + " | ".join(str(v) for v in fila.values()) + " |")

    nuevo = not os.path.exists(a.csv)
    with open(a.csv, "a", encoding="utf-8") as f:
        if nuevo:
            f.write(",".join(fila) + "\n")
        f.write(",".join(str(v) for v in fila.values()) + "\n")
    print(f"\nfila agregada a {a.csv}")


if __name__ == "__main__":
    main()
