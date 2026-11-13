#!/bin/sh
# Genera los stubs de Python desde el contrato. Se corre DENTRO del contenedor.
#   docker compose run --rm --no-deps servidor sh generar.sh
python -m grpc_tools.protoc -I proto --python_out=. --grpc_python_out=. proto/servicio.proto
ls -l servicio_pb2.py servicio_pb2_grpc.py
