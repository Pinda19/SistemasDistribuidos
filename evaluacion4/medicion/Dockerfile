FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /app
RUN pip install --no-cache-dir grpcio==1.80.0 protobuf==6.33.6 Pyro5==5.16
COPY semana11/dominio.py semana11/servidor_grpc.py semana11/servicio_pb2.py semana11/servicio_pb2_grpc.py /app/grpc/
COPY semana12/dominio.py semana12/objetos.py semana12/servidor_pyro.py /app/pyro/
COPY evaluacion4/medicion/ /app/medicion/
