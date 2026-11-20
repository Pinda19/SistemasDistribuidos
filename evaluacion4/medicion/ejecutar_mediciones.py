"""Espera los servidores y ejecuta medir.py del curso sin depender de Windows."""
import datetime
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time

import grpc
from Pyro5.api import Proxy
import servicio_pb2 as pb
import servicio_pb2_grpc as pb_grpc


def esperar_servicios(registrar):
    host = os.environ.get("SERVIDOR_HOST", "grpc")
    puerto = os.environ.get("SERVIDOR_PUERTO", "50051")
    ns_host = os.environ.get("NOMBRES_HOST", "nombres")
    ns_port = os.environ.get("NOMBRES_PUERTO", "9090")
    nombre = "sd.pinda.repositorio"
    ultimo = None
    for intento in range(1, 46):
        try:
            with grpc.insecure_channel(f"{host}:{puerto}") as canal:
                dato = pb_grpc.RepoSyncStub(canal).Clonar(
                    pb.ClonarSolicitud(repo="proyecto", rama="main"), timeout=2)
                assert dato.repositorio == "proyecto" and dato.rama == "main" and dato.head == 0
            with Proxy(f"PYRONAME:{nombre}@{ns_host}:{ns_port}") as obj:
                obj._pyroTimeout = 2
                estado = obj.clonar("proyecto", "main")
                assert estado == {"repositorio": "proyecto", "rama": "main", "head": 0}
                registrar(f"Pyro5 listo: {nombre}; {estado}")
            registrar(f"gRPC listo: {host}:{puerto}; proyecto/main HEAD=0")
            return
        except Exception as error:
            ultimo = error
            if intento == 1 or intento % 10 == 0:
                registrar(f"Esperando servicios, intento {intento}: {type(error).__name__}: {error}")
            time.sleep(1)
    raise RuntimeError(f"Los servicios no estuvieron listos: {ultimo}")


def main():
    destino = Path(os.environ.get("RESULTADOS_DIR", "/resultados"))
    destino.mkdir(parents=True, exist_ok=True)
    corrida = destino / "corridas" / datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ")
    corrida.mkdir(parents=True)
    with (corrida / "medicion_terminal.txt").open("w", encoding="utf-8") as archivo:
        def registrar(texto):
            print(texto, flush=True)
            archivo.write(texto + "\n")
            archivo.flush()
        try:
            registrar("RepoSync - Evaluacion 4 - Medicion real")
            registrar("Fecha UTC: " + datetime.datetime.now(datetime.timezone.utc).isoformat())
            registrar("Python: " + platform.python_version())
            registrar("Misma consulta: clonar(proyecto, main), HEAD=0, sin escrituras")
            registrar("200 llamadas medidas por mecanismo + 10 de calentamiento + 1 de tamano")
            registrar("Los dos servidores permanecen activos; consultas secuenciales, un cliente")
            registrar("El tamano es payload serializado, no trafico completo de red")
            esperar_servicios(registrar)
            for mecanismo in ("grpc", "pyro"):
                csv = corrida / f"mediciones_{mecanismo}.csv"
                argumentos = [sys.executable, str(Path(__file__).with_name("medir.py")),
                              mecanismo, "--metodo", "clonar", "--n", "200", "--csv", str(csv)]
                if mecanismo == "pyro":
                    argumentos += ["--nombre", "sd.pinda.repositorio"]
                registrar("\nMedicion " + mecanismo + ":")
                resultado = subprocess.run(argumentos, text=True, stdout=subprocess.PIPE,
                                           stderr=subprocess.STDOUT, timeout=90)
                registrar(resultado.stdout.rstrip())
                if resultado.returncode:
                    raise RuntimeError(f"medir.py {mecanismo} devolvio {resultado.returncode}")
                shutil.copyfile(csv, destino / csv.name)
            registrar("\nMEDICIONES TERMINADAS")
            registrar("Adjuntar docs/informe/evidencias/medicion_terminal.txt")
            return 0
        except Exception as error:
            registrar(f"ERROR: {type(error).__name__}: {error}")
            return 1
        finally:
            archivo.flush()
            shutil.copyfile(corrida / "medicion_terminal.txt", destino / "medicion_terminal.txt")


if __name__ == "__main__":
    sys.exit(main())
