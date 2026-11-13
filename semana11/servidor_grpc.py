"""Servidor gRPC RepoSync. Dominio compartido con la API JSON-RPC.

FALLA=no|primera|siempre, DEMORA (segundos), DEDUP=0|1.
La falla se simula DESPUES de aplicar el cambio pero ANTES de responder.
"""
import os
import signal
import threading
import time
from concurrent import futures

import grpc
import dominio
import servicio_pb2 as pb
import servicio_pb2_grpc as pb_grpc

PUERTO = os.getenv("SERVIDOR_PUERTO", "50051")
FALLA = os.getenv("FALLA", "no")
DEMORA = float(os.getenv("DEMORA", "3"))
DEDUP = os.getenv("DEDUP", "0") == "1"
_dedup_lock = threading.Lock()
_vistas = {}  # id_solicitud => ("ok", dict) o ("error", codigo, mensaje)
_ya_fallo = False


def log(msg):
    print(f"[servidor] {msg}", flush=True)


def demorar_si_corresponde():
    global _ya_fallo
    with _dedup_lock:
        demorar = FALLA == "siempre" or (FALLA == "primera" and not _ya_fallo)
        if demorar:
            _ya_fallo = True
    if demorar:
        log(f"FALLA={FALLA}, YA aplicado, demoro respuesta {DEMORA:.0f} s")
        time.sleep(DEMORA)


class RepoSync(pb_grpc.RepoSyncServicer):
    def Clonar(self, request, context):
        try:
            data = dominio.clonar(request.repo, request.rama)
        except (dominio.ErrorDominio, dominio.ErrorParametros) as e:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT if isinstance(e, dominio.ErrorParametros) else grpc.StatusCode.FAILED_PRECONDITION, str(e))
        log(f"Clonar {request.repo}/{request.rama} -> HEAD={data['head']}")
        return pb.EstadoRamaRespuesta(**data)

    def Historial(self, request, context):
        try:
            data = dominio.historial(request.repo, request.rama)
        except (dominio.ErrorDominio, dominio.ErrorParametros) as e:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT if isinstance(e, dominio.ErrorParametros) else grpc.StatusCode.FAILED_PRECONDITION, str(e))
        log(f"Historial {request.repo}/{request.rama} -> {len(data['revisiones'])} revisiones")
        return pb.HistorialRespuesta(revisiones=[pb.Revision(**i) for i in data['revisiones']])

    def Rama(self, request, context):
        return self._modificar("Rama", request, context,
            lambda: dominio.rama(request.repo, request.nueva, request.origen), pb.EstadoRamaRespuesta)

    def Push(self, request, context):
        return self._modificar("Push", request, context,
            lambda: dominio.push(request.repo, request.rama, request.base, request.mensaje), pb.EstadoRamaRespuesta)

    def PublicarAuto(self, request, context):
        return self._modificar("PublicarAuto", request, context,
            lambda: dominio.publicar_auto(request.repo, request.rama, request.mensaje), pb.EstadoRamaRespuesta)

    # Logica de la plantilla oficial: cachear antes de responder.
    def _modificar(self, nombre, request, context, aplicar, respuesta):
        ids = request.id_solicitud
        if not ids:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "falta id_solicitud")
        repetido = False
        with _dedup_lock:
            if DEDUP and ids in _vistas:
                resultado = _vistas[ids]
                repetido = True
                log(f"{nombre} id={ids} repetido, resultado cacheado SIN aplicar de nuevo")
            else:
                try:
                    resultado = ("ok", aplicar())
                except dominio.ErrorParametros as e:
                    resultado = ("error", grpc.StatusCode.INVALID_ARGUMENT, str(e))
                except dominio.ErrorDominio as e:
                    resultado = ("error", grpc.StatusCode.FAILED_PRECONDITION, str(e))
                detalle = resultado[1] if resultado[0] == "ok" else resultado[2]
                log(f"{nombre} id={ids} -> {detalle}")
                if DEDUP:
                    _vistas[ids] = resultado
        if resultado[0] == "error":
            context.abort(resultado[1], resultado[2])
        if not repetido:
            demorar_si_corresponde()
        return respuesta(**resultado[1])


def main():
    servidor = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    pb_grpc.add_RepoSyncServicer_to_server(RepoSync(), servidor)
    servidor.add_insecure_port(f"0.0.0.0:{PUERTO}")
    servidor.start()
    log(f"RepoSync gRPC puerto={PUERTO} FALLA={FALLA} DEMORA={DEMORA} DEDUP={int(DEDUP)}")
    signal.signal(signal.SIGTERM, lambda *_: servidor.stop(1))
    servidor.wait_for_termination()


if __name__ == "__main__":
    main()
