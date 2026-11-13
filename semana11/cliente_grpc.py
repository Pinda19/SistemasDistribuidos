"""Cliente gRPC RepoSync.

Ejemplos:
  python cliente_grpc.py clonar proyecto main
  python cliente_grpc.py rama proyecto demo main
  python cliente_grpc.py push proyecto demo 0 primer_cambio
  python cliente_grpc.py historial proyecto demo
  python cliente_grpc.py publicar-auto proyecto main cambio --reintentos 2

Los reintentos de una operacion usan SIEMPRE el mismo id_solicitud.
"""
import argparse
import os
import uuid
import grpc
import servicio_pb2 as pb
import servicio_pb2_grpc as pb_grpc

REINTENTABLES = {grpc.StatusCode.DEADLINE_EXCEEDED, grpc.StatusCode.UNAVAILABLE}


def main():
    parser = argparse.ArgumentParser(description="Cliente gRPC de RepoSync")
    parser.add_argument("--timeout", type=float, default=float(os.getenv("TIMEOUT_CLIENTE", "2")))
    parser.add_argument("--reintentos", type=int, default=int(os.getenv("REINTENTOS", "0")))
    parser.add_argument("--id", default=None, help="id_solicitud fijo opcional")
    sub = parser.add_subparsers(dest="metodo", required=True)
    p = sub.add_parser("clonar"); p.add_argument("repo"); p.add_argument("rama")
    p = sub.add_parser("rama"); p.add_argument("repo"); p.add_argument("nueva"); p.add_argument("origen")
    p = sub.add_parser("push"); p.add_argument("repo"); p.add_argument("rama"); p.add_argument("base", type=int); p.add_argument("mensaje")
    p = sub.add_parser("historial"); p.add_argument("repo"); p.add_argument("rama")
    p = sub.add_parser("publicar-auto"); p.add_argument("repo"); p.add_argument("rama"); p.add_argument("mensaje")
    # Se aceptan las opciones despues del subcomando, como en la guia.
    for p in sub.choices.values():
        p.add_argument("--timeout", type=float, default=argparse.SUPPRESS)
        p.add_argument("--reintentos", type=int, default=argparse.SUPPRESS)
        p.add_argument("--id", default=argparse.SUPPRESS)
    a = parser.parse_args()
    if a.timeout <= 0 or a.reintentos < 0:
        parser.error("timeout > 0 y reintentos >= 0")
    ident = a.id if a.id is not None else uuid.uuid4().hex[:8]
    canal = grpc.insecure_channel(f"{os.getenv('SERVIDOR_HOST', 'servidor')}:{os.getenv('SERVIDOR_PUERTO', '50051')}")
    stub = pb_grpc.RepoSyncStub(canal)
    if a.metodo == "clonar":
        call = stub.Clonar
        req = pb.ClonarSolicitud(repo=a.repo, rama=a.rama)
    elif a.metodo == "rama":
        call = stub.Rama
        req = pb.RamaSolicitud(id_solicitud=ident, repo=a.repo, nueva=a.nueva, origen=a.origen)
    elif a.metodo == "push":
        call = stub.Push
        req = pb.PushSolicitud(id_solicitud=ident, repo=a.repo, rama=a.rama, base=a.base, mensaje=a.mensaje)
    elif a.metodo == "historial":
        call = stub.Historial
        req = pb.HistorialSolicitud(repo=a.repo, rama=a.rama)
    else:
        call = stub.PublicarAuto
        req = pb.PublicarAutoSolicitud(id_solicitud=ident, repo=a.repo, rama=a.rama, mensaje=a.mensaje)

    for intento in range(1, a.reintentos + 2):
        print(f"[cliente] intento {intento}, id_solicitud={getattr(req,'id_solicitud','-')} timeout={a.timeout:g}s", flush=True)
        try:
            resp = call(req, timeout=a.timeout)
        except grpc.RpcError as e:
            print(f"[cliente]   {e.code().name}: {e.details()}", flush=True)
            if e.code() in REINTENTABLES and intento <= a.reintentos:
                continue
            if e.code() in REINTENTABLES:
                print("[cliente] estado de ejecucion DESCONOCIDO si hubo fallo intermedio", flush=True)
            else:
                print("[cliente] solicitud rechazada sin reintento", flush=True)
            return 1
        if a.metodo == "historial":
            historial = " | ".join(f"{i.numero}:{i.mensaje}" for i in resp.revisiones)
            print(f"[cliente]   OK {historial}", flush=True)
        else:
            print(f"[cliente]   OK {resp.repositorio}/{resp.rama} HEAD={resp.head}", flush=True)
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
